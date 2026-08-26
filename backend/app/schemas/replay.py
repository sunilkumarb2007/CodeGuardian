from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class ReplayResultDetails(BaseModel):
    status: str
    http_status: Optional[int] = None
    failure_fingerprint: Optional[str] = None
    output: Optional[str] = None

class ReplayResponse(BaseModel):
    incident_id: UUID
    patch_id: UUID
    replay_id: UUID
    baseline: ReplayResultDetails
    patched: ReplayResultDetails
    result: str
