from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class FailureInput(BaseModel):
    failure_type: str
    message: str
    stack_trace: Optional[str] = None
    command: Optional[str] = None
    exit_code: Optional[int] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    source: str # e.g. "USER_STACK_TRACE", "BUILD", "TEST", "RUNTIME", "PREPARED_FIXTURE"
    timestamp: datetime
    repository_id: UUID
    run_id: str
