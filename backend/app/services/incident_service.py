from sqlalchemy.orm import Session
from uuid import UUID
from app.db.repositories import IncidentRepository
from app.schemas.incident import IncidentResponse, IncidentDetailResponse
from app.db import models

class IncidentService:
    def __init__(self, db: Session):
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
        import uuid
        # Find or create application and repository
        app = self.repo.db.query(models.Application).first()
        if not app:
            raise ValueError("No Application found in database to attach incident to.")
            
        repo_url = data.get('repository_url')
        repo = self.repo.db.query(models.Repository).filter_by(repository_url=repo_url).first() if repo_url else self.repo.db.query(models.Repository).first()
        repo_id = repo.id if repo else None
        
        # Get max incident_number
        max_num = self.repo.db.query(models.Incident).order_by(models.Incident.incident_number.desc()).first()
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
            created_at=models.datetime.utcnow(),
            updated_at=models.datetime.utcnow()
        )
        self.repo.save(incident)
        self.repo.db.flush() # ensure ID is generated
        return incident
