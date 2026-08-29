import hashlib
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.repositories import IncidentRepository
from app.schemas.incident import IncidentResponse, IncidentDetailResponse, IncidentIngestRequest, IncidentIngestResponse
from app.db import models

logger = logging.getLogger(__name__)


class IncidentService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = IncidentRepository(db)

    def get_all_incidents(self) -> list[IncidentResponse]:
        incidents = self.repo.get_all()
        return [IncidentResponse.model_validate(inc) for inc in incidents]

    def get_incident_detail(self, incident_id: UUID) -> IncidentDetailResponse | None:
        incident = self.repo.get_by_id(incident_id)
        if incident:
            return IncidentDetailResponse.model_validate(incident)
        return None

    def create_incident(self, data: dict) -> models.Incident:
        # Find or create application and repository
        app = self.db.query(models.Application).first()
        if not app:
            raise ValueError("No Application found in database to attach incident to.")
            
        repo_url = data.get('repository_url')
        repo = self.db.query(models.Repository).filter_by(repository_url=repo_url).first() if repo_url else self.db.query(models.Repository).first()
        repo_id = repo.id if repo else None
        
        # Get max incident_number
        max_num = self.db.query(models.Incident).order_by(models.Incident.incident_number.desc()).first()
        next_num = (max_num.incident_number + 1) if max_num else 1

        incident = models.Incident(
            id=uuid.uuid4(),
            incident_number=next_num,
            application_id=app.id,
            repository_id=repo_id,
            title=f"Automated failure for {data.get('repository_url', 'unknown')}",
            description=data.get('failure_summary', 'Unknown failure'),
            status=data.get('status', 'investigating'),
            resolution_status="unresolved",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        self.db.add(incident)
        self.db.flush()  # ensure ID is generated
        return incident

    def _build_fingerprint(self, request: IncidentIngestRequest) -> str:
        """Build a stable deduplication fingerprint for this incident."""
        # Normalize the message to remove volatile tokens (IDs, timestamps, etc.)
        raw_msg = (request.message or "").strip()
        # Compose components
        components = [
            request.repository or "",
            request.service or "",
            request.exception or "",
            request.endpoint or "",
            str(request.status_code or ""),
        ]
        raw = "|".join(components)
        return hashlib.sha256(raw.encode()).hexdigest()[:64]

    def _find_active_incident(self, fingerprint: str, dedup_window_minutes: int = 10) -> Optional[models.Incident]:
        """Find an active (non-resolved) incident with the same fingerprint in the dedup window."""
        window_start = datetime.now(timezone.utc) - timedelta(minutes=dedup_window_minutes)
        incident = (
            self.db.query(models.Incident)
            .filter(
                models.Incident.error_fingerprint == fingerprint,
                models.Incident.resolution_status == "unresolved",
                models.Incident.last_seen_at >= window_start.replace(tzinfo=None),
            )
            .order_by(models.Incident.last_seen_at.desc())
            .first()
        )
        return incident

    def _find_or_create_repository(self, owner: str, repo_name: str) -> Optional[models.Repository]:
        """Find the registered repository by owner+name, or return None if not found."""
        repo = (
            self.db.query(models.Repository)
            .filter(
                models.Repository.owner == owner,
                models.Repository.name == repo_name,
            )
            .first()
        )
        return repo

    def _get_or_create_application(self) -> models.Application:
        """Get the first application or create a default one."""
        app = self.db.query(models.Application).first()
        if not app:
            app = models.Application(
                id=uuid.uuid4(),
                name="CodeGuardian",
                environment="production",
                status="active",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            self.db.add(app)
            self.db.flush()
        return app

    def ingest_incident(
        self,
        request: IncidentIngestRequest,
        background_tasks: BackgroundTasks,
    ) -> IncidentIngestResponse:
        """
        Production incident ingestion endpoint.
        
        Flow:
        1. Parse repository identity from "owner/name" string
        2. Look up registered repository
        3. Build deduplication fingerprint
        4. Deduplicate: return existing active incident if within window
        5. Create new Incident record
        6. Create new Run record  
        7. Persist both BEFORE background execution
        8. Return 202 with incident_id + run_id
        9. Launch existing 17-stage pipeline in background
        """
        # --- Step 1: Parse repository identity ---
        repo_str = (request.repository or "").strip()
        cleaned_repo = repo_str.replace("https://github.com/", "").replace("http://github.com/", "").strip("/")
        if "/" in cleaned_repo:
            parts = cleaned_repo.split("/", 1)
            owner = parts[0].strip()
            repo_name = parts[1].strip().replace(".git", "")
        else:
            owner = ""
            repo_name = cleaned_repo

        # --- Step 2: Find registered repository ---
        repo = None
        if request.repository_id:
            # Caller supplied a repository_id directly
            repo = self.db.query(models.Repository).filter(models.Repository.id == request.repository_id).first()
        
        if not repo and owner and repo_name:
            repo = self._find_or_create_repository(owner, repo_name)

        # Build repository_url for orchestrator
        if repo:
            repository_url = repo.repository_url
            repo_id = repo.id
        else:
            # Repository not yet registered — build the URL and let the orchestrator handle it
            repository_url = f"https://github.com/{owner}/{repo_name}" if owner and repo_name else None
            repo_id = None
            logger.warning(
                f"Repository '{repo_str}' not found in registry. "
                f"Will attempt to load via GitHub. Register the repository first for full monitoring."
            )

        if not repository_url:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=422,
                detail="Cannot determine repository URL. Provide 'repository' as 'owner/name' or a valid repository_id."
            )

        # --- Step 3: Build fingerprint for deduplication ---
        fingerprint = self._build_fingerprint(request)

        # --- Step 4: Deduplicate ---
        existing_incident = self._find_active_incident(fingerprint, dedup_window_minutes=10)
        
        if existing_incident:
            # Update last_seen and occurrence count
            existing_incident.last_seen_at = datetime.now(timezone.utc).replace(tzinfo=None)
            existing_incident.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
            self.db.flush()

            # Find the most recent active run for this incident
            existing_run = (
                self.db.query(models.Run)
                .filter(models.Run.incident_id == existing_incident.id)
                .order_by(models.Run.created_at.desc())
                .first()
            )
            
            if existing_run and existing_run.state not in ("COMPLETED", "FAILED", "REJECTED"):
                # Already investigating — return the active run
                self.db.commit()
                logger.info(
                    f"Deduplicated incident {existing_incident.id} (fingerprint={fingerprint[:16]}...) "
                    f"→ existing run {existing_run.id}"
                )
                return IncidentIngestResponse(
                    incident_id=existing_incident.id,
                    run_id=existing_run.id,
                    status="DEDUPLICATED",
                    message="Active investigation already in progress for this incident.",
                )

        # --- Step 5: Create new Incident ---
        app = self._get_or_create_application()
        
        max_num = self.db.query(models.Incident).order_by(models.Incident.incident_number.desc()).first()
        next_num = (max_num.incident_number + 1) if max_num else 1

        now = datetime.now(timezone.utc).replace(tzinfo=None)

        # Determine title
        if request.exception and request.service:
            title = f"{request.exception} in {request.service}"
        elif request.exception:
            title = request.exception
        elif request.message:
            title = request.message[:100]
        else:
            title = f"Production failure in {repo_str}"

        # Build description from available fields
        desc_parts = []
        if request.service:
            desc_parts.append(f"Service: {request.service}")
        if request.endpoint:
            desc_parts.append(f"Endpoint: {request.endpoint}")
        if request.status_code:
            desc_parts.append(f"Status: {request.status_code}")
        if request.environment:
            desc_parts.append(f"Environment: {request.environment}")
        if request.message:
            desc_parts.append(f"Message: {request.message}")
        if request.stack_trace:
            desc_parts.append(f"\nStack Trace:\n{request.stack_trace[:2000]}")
        description = "\n".join(desc_parts)

        incident = models.Incident(
            id=uuid.uuid4(),
            incident_number=next_num,
            application_id=app.id,
            repository_id=repo_id,
            title=title,
            description=description,
            endpoint=request.endpoint,
            http_method=None,  # will be derived from endpoint if needed
            observed_status_code=request.status_code,
            symptom_service=request.service,  # initial symptom — root cause may differ
            error_fingerprint=fingerprint,
            request_id=request.request_id,
            first_seen_at=now,
            last_seen_at=now,
            status="investigating",
            resolution_status="unresolved",
            created_at=now,
            updated_at=now,
        )
        self.db.add(incident)
        self.db.flush()  # Generate ID before creating Run

        # --- Step 6: Create EvidenceEvent from the ingested payload ---
        evidence = models.EvidenceEvent(
            id=uuid.uuid4(),
            incident_id=incident.id,
            service_name=request.service,
            event_type="error",
            timestamp=now,
            request_id=request.request_id,
            endpoint=request.endpoint,
            http_method=None,
            status_code=request.status_code,
            error_code=request.exception,
            error_message=request.message,
            stack_trace=request.stack_trace,
            source=request.source or "webhook",
            event_metadata={
                "trace_id": request.trace_id,
                "commit_sha": request.commit_sha,
                "branch": request.branch,
                "environment": request.environment,
                "source": request.source,
            },
            raw_payload=request.metadata or {},
            created_at=now,
        )
        self.db.add(evidence)

        # --- Step 7: Create Run record ---
        run_id = uuid.uuid4()
        run = models.Run(
            id=run_id,
            repository_id=repo_id,
            incident_id=incident.id,
            current_stage="CREATED",
            state="CREATED",
            created_at=now,
            updated_at=now,
        )
        self.db.add(run)

        # --- Persist BEFORE background task starts ---
        self.db.commit()
        logger.info(
            f"Ingested incident {incident.id} -> run {run_id} "
            f"(repo={repo_str}, fingerprint={fingerprint[:16]}...)"
        )

        # --- Step 8: Build failure_input_dict for the orchestrator ---
        # This is passed to the existing FailureEvidenceCollector so the 17-stage
        # pipeline can pick up the stack trace without re-fetching.
        failure_input_dict = {
            "failure_type": "RUNTIME_EXCEPTION",
            "message": request.message or "",
            "stack_trace": request.stack_trace or "",
            "source": "RUNTIME",
            "timestamp": now.isoformat(),
            "service": request.service,
            "exception": request.exception,
        }

        # --- Step 9: Launch existing 17-stage pipeline in background ---
        background_tasks.add_task(
            _run_pipeline_in_background,
            run_id=str(run_id),
            repository_url=repository_url,
            supplied_incident_id=str(incident.id),
            failure_input_dict=failure_input_dict,
        )

        return IncidentIngestResponse(
            incident_id=incident.id,
            run_id=run_id,
            status="ACCEPTED",
            message="Incident ingested. Autonomous investigation started.",
        )


def _run_pipeline_in_background(
    run_id: str,
    repository_url: str,
    supplied_incident_id: str,
    failure_input_dict: dict,
):
    """
    Called as a FastAPI BackgroundTask after the HTTP response is sent.
    Launches the existing 17-stage CodeGuardian orchestrator pipeline.
    This must NOT be a method on IncidentService as the DB session will be closed.
    """
    try:
        from app.services.orchestrator import CodeGuardianOrchestrator
        orchestrator = CodeGuardianOrchestrator()
        orchestrator.execute_pipeline(
            run_id=run_id,
            repository_url=repository_url,
            supplied_incident_id=supplied_incident_id,
            failure_input_dict=failure_input_dict,
        )
    except Exception as e:
        logger.error(
            f"Background pipeline failed for run {run_id}: {e}",
            exc_info=True,
        )
        # Persist failure state so the UI can show it
        try:
            from app.db.database import SessionLocal
            from app.db.models import Run
            with SessionLocal() as db:
                run = db.query(Run).filter(Run.id == run_id).first()
                if run:
                    run.state = "FAILED"
                    run.error_code = "PIPELINE_STARTUP_FAILED"
                    run.error_message = str(e)[:500]
                    from datetime import datetime, timezone
                    run.updated_at = datetime.now(timezone.utc)
                    db.commit()
        except Exception as db_err:
            logger.error(f"Failed to persist pipeline failure: {db_err}")
