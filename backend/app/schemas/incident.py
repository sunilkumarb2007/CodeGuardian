from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

class IncidentIngestRequest(BaseModel):
    repository: str
    repository_id: Optional[UUID] = None
    branch: Optional[str] = "main"
    commit_sha: Optional[str] = None
    environment: Optional[str] = "production"
    service: Optional[str] = None
    endpoint: Optional[str] = None
    status_code: Optional[int] = None
    request_id: Optional[str] = None
    trace_id: Optional[str] = None
    exception: Optional[str] = None
    message: Optional[str] = None
    stack_trace: Optional[str] = None
    timestamp: Optional[datetime] = None
    source: Optional[str] = "webhook"
    metadata: Optional[Dict[str, Any]] = None

class IncidentIngestResponse(BaseModel):
    incident_id: UUID
    run_id: UUID
    status: str
    message: str

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
