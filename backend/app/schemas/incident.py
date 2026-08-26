from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from uuid import UUID
from datetime import datetime

class IncidentResponse(BaseModel):
    id: UUID
    incident_number: int
    title: str
    status: str
    resolution_status: str
    symptom_service: Optional[str] = None
    root_cause_service: Optional[str] = None
    error_fingerprint: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class IncidentDetailResponse(IncidentResponse):
    application_id: UUID
    repository_id: Optional[UUID] = None
    description: Optional[str] = None
    endpoint: Optional[str] = None
    http_method: Optional[str] = None
    observed_status_code: Optional[int] = None
    root_cause_summary: Optional[str] = None
    request_id: Optional[str] = None
    first_seen_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None
    updated_at: datetime
