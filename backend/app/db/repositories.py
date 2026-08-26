from typing import List, Optional, Type, TypeVar, Generic
from sqlalchemy.orm import Session
from uuid import UUID
from app.db.models import (
    Incident, EvidenceEvent, FailureTrace, Investigation, 
    FailureMemory, MemoryMatch, Patch, ReplayRun, 
    ValidationRun, RepairAttempt, PullRequest
)
from app.db import models

T = TypeVar("T")

class BaseRepository(Generic[T]):
    def __init__(self, db: Session, model: Type[T]):
        self.db = db
        self.model = model

    def save(self, instance: T) -> T:
        self.db.add(instance)
        return instance

    def get_by_id(self, id: UUID) -> Optional[T]:
        return self.db.query(self.model).filter(self.model.id == id).first()

class IncidentRepository(BaseRepository[models.Incident]):
    def __init__(self, db: Session):
        super().__init__(db, models.Incident)

    def get_all(self) -> List[models.Incident]:
        return self.db.query(models.Incident).all()

    def get_by_id(self, incident_id: UUID) -> Optional[models.Incident]:
        return self.db.query(models.Incident).filter(models.Incident.id == incident_id).first()

class EvidenceRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_incident_id(self, incident_id: UUID) -> List[models.EvidenceEvent]:
        return self.db.query(models.EvidenceEvent).filter(models.EvidenceEvent.incident_id == incident_id).all()

class TraceRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_incident_id(self, incident_id: UUID) -> Optional[models.FailureTrace]:
        return self.db.query(models.FailureTrace).filter(models.FailureTrace.incident_id == incident_id).order_by(models.FailureTrace.created_at.desc()).first()

    def get_nodes(self, trace_id: UUID) -> List[models.FailureTraceNode]:
        return self.db.query(models.FailureTraceNode).filter(models.FailureTraceNode.failure_trace_id == trace_id).all()

    def get_edges(self, trace_id: UUID) -> List[models.FailureTraceEdge]:
        return self.db.query(models.FailureTraceEdge).filter(models.FailureTraceEdge.failure_trace_id == trace_id).all()

class MemoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_match_by_incident_id(self, incident_id: UUID) -> Optional[models.MemoryMatch]:
        return self.db.query(models.MemoryMatch).filter(models.MemoryMatch.incident_id == incident_id).order_by(models.MemoryMatch.created_at.desc()).first()

    def get_memory_by_id(self, memory_id: UUID) -> Optional[models.FailureMemory]:
        return self.db.query(models.FailureMemory).filter(models.FailureMemory.id == memory_id).first()

    def get_verified_memories(self, application_id: UUID) -> List[models.FailureMemory]:
        return self.db.query(models.FailureMemory).filter(
            models.FailureMemory.application_id == application_id,
            models.FailureMemory.memory_status == 'verified'
        ).all()

    def save_match(self, match: models.MemoryMatch) -> models.MemoryMatch:
        # Check for existing match to make this idempotent
        existing = self.db.query(models.MemoryMatch).filter(
            models.MemoryMatch.incident_id == match.incident_id,
            models.MemoryMatch.memory_id == match.memory_id
        ).first()
        
        if existing:
            # Update existing
            existing.similarity_score = match.similarity_score
            existing.match_reason = match.match_reason
            existing.matched_error_pattern = match.matched_error_pattern
            existing.matched_root_cause = match.matched_root_cause
            existing.matched_affected_files = match.matched_affected_files
            existing.verification_status = match.verification_status
            return existing
        else:
            self.db.add(match)
            return match

class InvestigationRepository:
    def __init__(self, db: Session):
        self.db = db

    def save(self, investigation: models.Investigation) -> models.Investigation:
        self.db.add(investigation)
        return investigation

    def get_by_incident_id(self, incident_id: UUID) -> models.Investigation | None:
        return self.db.query(models.Investigation).filter(
            models.Investigation.incident_id == incident_id
        ).order_by(models.Investigation.created_at.desc()).first()


class PatchRepository:
    def __init__(self, db: Session):
        self.db = db

    def save(self, patch: models.Patch) -> models.Patch:
        self.db.add(patch)
        return patch

    def get_by_id(self, patch_id: UUID) -> models.Patch | None:
        return self.db.query(models.Patch).filter(
            models.Patch.id == patch_id
        ).first()

    def get_max_patch_number(self, incident_id: UUID) -> int:
        from sqlalchemy import func
        result = self.db.query(func.max(models.Patch.patch_number)).filter(
            models.Patch.incident_id == incident_id
        ).scalar()
        return result or 0

    def get_by_incident_id(self, incident_id: UUID) -> list[models.Patch]:
        return self.db.query(models.Patch).filter(
            models.Patch.incident_id == incident_id
        ).all()

    def get_candidates_by_incident_id(self, incident_id: UUID) -> list[models.Patch]:
        return self.db.query(models.Patch).filter(
            models.Patch.incident_id == incident_id,
            models.Patch.status == "unvalidated"
        ).order_by(models.Patch.created_at.desc()).all()


class RepositoryFileRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_files_by_repository_id(self, repository_id: UUID) -> list[models.RepositoryFile]:
        return self.db.query(models.RepositoryFile).filter(
            models.RepositoryFile.repository_id == repository_id
        ).all()


class ReplayRepository:
    def __init__(self, db: Session):
        self.db = db

    def save(self, replay_run: models.ReplayRun) -> models.ReplayRun:
        self.db.add(replay_run)
        return replay_run

class ValidationRunRepository(BaseRepository[models.ValidationRun]):
    def __init__(self, db: Session):
        super().__init__(db, models.ValidationRun)

class RepairAttemptRepository(BaseRepository[models.RepairAttempt]):
    def __init__(self, db: Session):
        super().__init__(db, models.RepairAttempt)

    def get_attempts_for_incident(self, incident_id: UUID) -> List[models.RepairAttempt]:
        return self.db.query(models.RepairAttempt).filter(models.RepairAttempt.incident_id == incident_id).order_by(models.RepairAttempt.attempt_number).all()

    def get_latest_attempt(self, incident_id: UUID) -> Optional[models.RepairAttempt]:
        return self.db.query(models.RepairAttempt).filter(models.RepairAttempt.incident_id == incident_id).order_by(models.RepairAttempt.attempt_number.desc()).first()

class PullRequestRepository(BaseRepository[models.PullRequest]):
    def __init__(self, db: Session):
        super().__init__(db, models.PullRequest)

    def get_by_patch_id(self, patch_id: UUID) -> Optional[models.PullRequest]:
        return self.db.query(models.PullRequest).filter(models.PullRequest.patch_id == patch_id).first()

