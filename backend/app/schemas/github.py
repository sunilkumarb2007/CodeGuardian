from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID

class PullRequestInfo(BaseModel):
    number: int
    url: str
    state: str

class PullRequestDeliveryResponse(BaseModel):
    incident_id: UUID
    patch_id: UUID
    status: str
    repository: str
    branch: str
    pull_request: Optional[PullRequestInfo] = None
    error_details: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)
