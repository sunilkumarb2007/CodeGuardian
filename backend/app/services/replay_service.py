from datetime import timezone
import uuid
from datetime import datetime
from uuid import UUID
import logging
from sqlalchemy.orm import Session

from app.db import models
from app.db.repositories import (
    IncidentRepository,
    PatchRepository,
    RepositoryFileRepository,
    ReplayRepository
)
from app.engine.replay_engine import ReplayEngine
from app.schemas.replay import ReplayResponse, ReplayResultDetails

logger = logging.getLogger(__name__)

class ReplayService:
    def __init__(self, db: Session):
        self.db = db
        self.incident_repo = IncidentRepository(db)
        self.patch_repo = PatchRepository(db)
        self.file_repo = RepositoryFileRepository(db)
        self.replay_repo = ReplayRepository(db)
        self.engine = ReplayEngine()

    def run_replay(self, incident_id: UUID, patch_id: UUID, run_id: str | None = None) -> ReplayResponse:
        logger.info(f"Starting Ghost Replay for incident {incident_id}, patch {patch_id}")
        
        # 1. Validate inputs
        incident = self.incident_repo.get_by_id(incident_id)
        if not incident:
            return self._error_response(incident_id, patch_id, "Incident not found")
            
        patch = self.patch_repo.get_by_id(patch_id)
        if not patch or patch.incident_id != incident_id:
            return self._error_response(incident_id, patch_id, "Patch not found or belongs to different incident")
            
        if patch.status != "unvalidated":
            return self._error_response(incident_id, patch_id, f"Patch status is {patch.status}, must be unvalidated")

        # 2. Retrieve source context
        source_files = []
        if incident.repository_id:
            source_files = self.file_repo.get_files_by_repository_id(incident.repository_id)
            
        # 3. Execute Engine
        overall_result, baseline_details, patched_details = self.engine.run_replay(incident, patch, source_files, run_id=run_id)
        
        # 4. Determine DB Status (mapped to allowed constraints)
        if overall_result == "PATCH_APPLY_FAILED":
            db_status = "failed"
        elif overall_result == "REPLAY_CHANGED_BEHAVIOR":
            db_status = "passed"
        elif overall_result == "REPLAY_FAILURE_PERSISTS":
            db_status = "passed" # The replay ran successfully, even if behavior didn't change
        else:
            db_status = "failed"

        # 5. Persist Baseline Replay Run
        baseline_run = models.ReplayRun(
            id=uuid.uuid4(),
            incident_id=incident_id,
            patch_id=None,
            replay_type="original",
            endpoint="POST /checkout",
            http_method="POST",
            expected_status_code=500,
            actual_status_code=baseline_details.get("http_status"),
            expected_behavior="HTTP 500",
            actual_behavior=baseline_details.get("failure_fingerprint", str(baseline_details.get("http_status"))),
            reproduced_failure=(baseline_details.get("http_status") == 500),
            execution_output=baseline_details.get("output"),
            environment={},
            status=db_status if patched_details.get("status") != "PATCH_APPLY_FAILED" else "failed",
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc)
        )
        self.replay_repo.save(baseline_run)
        
        # 6. Persist Patched Replay Run
        patched_run = models.ReplayRun(
            id=uuid.uuid4(),
            incident_id=incident_id,
            patch_id=patch.id,
            replay_type="patched",
            endpoint="POST /checkout",
            http_method="POST",
            expected_status_code=200,
            actual_status_code=patched_details.get("http_status"),
            expected_behavior="HTTP 200",
            actual_behavior=patched_details.get("failure_fingerprint", str(patched_details.get("http_status"))),
            reproduced_failure=(patched_details.get("http_status") == 500),
            execution_output=patched_details.get("output"),
            environment={},
            status=db_status,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc)
        )
        self.replay_repo.save(patched_run)
        self.db.flush()

        # 7. Return Response
        return ReplayResponse(
            incident_id=incident_id,
            patch_id=patch_id,
            replay_id=patched_run.id,
            baseline=ReplayResultDetails(**baseline_details),
            patched=ReplayResultDetails(**patched_details),
            result=overall_result
        )
        
    def _error_response(self, incident_id: UUID, patch_id: UUID, reason: str) -> ReplayResponse:
        return ReplayResponse(
            incident_id=incident_id,
            patch_id=patch_id,
            replay_id=uuid.uuid4(),
            baseline=ReplayResultDetails(status="error", output=reason),
            patched=ReplayResultDetails(status="error", output=reason),
            result="ERROR"
        )
