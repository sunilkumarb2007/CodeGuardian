from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime

class EvidenceResponse(BaseModel):
    id: UUID
    incident_id: UUID
    service_name: Optional[str] = None
    event_type: str
    timestamp: datetime
    request_id: Optional[str] = None
    endpoint: Optional[str] = None
    http_method: Optional[str] = None
    status_code: Optional[int] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    source: Optional[str] = None
    metadata: Dict[str, Any] = Field(validation_alias="event_metadata")
    raw_payload: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
