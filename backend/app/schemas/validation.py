from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime

class ValidationChecks(BaseModel):
    patch_apply: str
    build: str
    tests: str
    replay: str
    regression: str
    safety: str

class ValidationRunResponse(BaseModel):
    id: UUID
    incident_id: UUID
    patch_id: UUID
    attempt: int
    status: str
    checks: ValidationChecks
    summary: str
    build_output: Optional[str] = None
    test_output: Optional[str] = None
    replay_output: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class RepairAttemptResponse(BaseModel):
    id: UUID
    incident_id: UUID
    patch_id: Optional[UUID] = None
    attempt_number: int
    status: str
    failure_reason: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)
