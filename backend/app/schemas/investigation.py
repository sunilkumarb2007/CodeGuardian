from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID

class RootCauseAnalysis(BaseModel):
    service: str
    summary: str
    affected_file: Optional[str] = None
    location: Optional[str] = None

class HistoricalReference(BaseModel):
    found: bool
    memory_status: Optional[str] = None
    applicability: Optional[str] = None

class PatchCandidateModel(BaseModel):
    id: Optional[UUID] = None
    status: str = "unvalidated"
    files_changed: List[str]
    diff: str
    explanation: str

class InvestigationResult(BaseModel):
    incident_id: UUID
    status: str
    root_cause: Optional[RootCauseAnalysis] = None
    historical_reference: Optional[HistoricalReference] = None
    patch_candidate: Optional[PatchCandidateModel] = None
    verification_requirements: List[str] = []
    assumptions: List[str] = []
    evidence_used: List[str] = []
