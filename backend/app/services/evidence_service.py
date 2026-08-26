from sqlalchemy.orm import Session
from uuid import UUID
from app.db.repositories import EvidenceRepository
from app.schemas.evidence import EvidenceResponse

class EvidenceService:
    def __init__(self, db: Session):
        self.repo = EvidenceRepository(db)

    def get_evidence_for_incident(self, incident_id: UUID) -> list[EvidenceResponse]:
        events = self.repo.get_by_incident_id(incident_id)
        return [EvidenceResponse.model_validate(ev) for ev in events]
