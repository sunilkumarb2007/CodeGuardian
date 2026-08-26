from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

class FailureMemoryResponse(BaseModel):
    id: UUID
    incident_id: UUID
    application_id: UUID
    error_pattern: str
    error_fingerprint: Optional[str] = None
    root_cause: str
    affected_files: Any
    code_change: Optional[str] = None
    patch_summary: Optional[str] = None
    validation_result: Optional[Dict[str, Any]] = None
    pull_request_history: Optional[Dict[str, Any]] = None
    memory_status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class MemoryMatchResponse(BaseModel):
    id: UUID
    incident_id: UUID
    memory_id: UUID
    similarity_score: Optional[float] = None
    match_reason: Optional[str] = None
    matched_error_pattern: bool
    matched_root_cause: bool
    matched_affected_files: bool
    matched_code_context: bool
    verification_status: str
    created_at: datetime
    memory: Optional[FailureMemoryResponse] = None

    model_config = ConfigDict(from_attributes=True)

class MemorySearchResponse(BaseModel):
    incident_id: UUID
    match_status: str
    matches: List[MemoryMatchResponse] = []
    
    model_config = ConfigDict(from_attributes=True)
