from datetime import timezone
import uuid
import hashlib
from datetime import datetime
import logging
from sqlalchemy.orm import Session
from app.db import models
from app.db.repositories import IncidentRepository
from app.schemas.failure import FailureInput
from typing import Optional

logger = logging.getLogger(__name__)

def generate_fingerprint(failure_type: str, message: str, source: str) -> str:
    # A simple deterministic hash of stable components
    stable_string = f"{failure_type}|{message}|{source}".encode("utf-8")
    return hashlib.sha256(stable_string).hexdigest()

class FailureEvidenceCollector:
    def __init__(self, db: Session):
        self.db = db

    def collect_evidence(self, repository_url: str, repository_id: uuid.UUID, failure_input: Optional[FailureInput] = None) -> str:
        """
        Creates structured deterministic evidence from failure input.
        Returns the incident ID as string if successful, else 'NO_FAILURE_EVIDENCE'.
        """
        if not failure_input:
            logger.info(f"No failure evidence provided for repository: {repository_url}")
            return "NO_FAILURE_EVIDENCE"
            
        return self._handle_generic_failure(repository_url, repository_id, failure_input)

    def _handle_generic_failure(self, repository_url: str, repository_id: uuid.UUID, failure_input: FailureInput) -> str:
        inc_repo = IncidentRepository(self.db)
        repo_obj = self.db.query(models.Repository).filter(models.Repository.id == repository_id).first()
        app_id = repo_obj.application_id if repo_obj and repo_obj.application_id else uuid.uuid4()
        max_num = self.db.query(models.Incident).count() + 1

        fingerprint = generate_fingerprint(failure_input.failure_type, failure_input.message, failure_input.source)

        incident = models.Incident(
            id=uuid.uuid4(),
            incident_number=max_num,
            application_id=app_id,
            repository_id=repository_id,
            title=f"{failure_input.failure_type} in {failure_input.source}",
            description=failure_input.message,
            status="investigating",
            resolution_status="unresolved",
            error_fingerprint=fingerprint,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        inc_repo.save(incident)
        self.db.flush()

        src_file = getattr(failure_input, 'source_file', None)
        src_line = getattr(failure_input, 'source_line', None)
        service_attr = getattr(failure_input, 'service', None)
        
        svc_name = service_attr or "unknown-service"
        
        st_trace = failure_input.stack_trace
        if not st_trace and src_file:
            line_str = f":{src_line}" if src_line else ""
            st_trace = f"at {src_file}{line_str}"

        events = []
        events.append(
            models.EvidenceEvent(
                id=uuid.uuid4(), incident_id=incident.id,
                service_name=svc_name, event_type="error",
                timestamp=failure_input.timestamp or datetime.now(timezone.utc),
                error_message=failure_input.message,
                event_metadata={"exception": failure_input.failure_type, "command": failure_input.command, "exit_code": failure_input.exit_code, "source_file": src_file, "source_line": src_line},
                stack_trace=st_trace,
                created_at=datetime.now(timezone.utc)
            )
        )
        for e in events:
            self.db.add(e)
        self.db.flush()
        return str(incident.id)
