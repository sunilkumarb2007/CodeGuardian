from pydantic import BaseModel, Field, ConfigDict
from pydantic.alias_generators import to_camel
from typing import List, Optional
from uuid import UUID

class RootCauseAnalysis(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    service: str = Field(description="The service or component where the root cause exists.")
    summary: str = Field(description="A concise summary of the engineering failure mechanism.")
    affected_file: Optional[str] = Field(None, description="The specific file path containing the defect.")
    location: Optional[str] = Field(None, description="The specific class and method.")
    confidence: Optional[float] = Field(None, description="Confidence in this root cause (0.0 to 1.0).")
    failure_mechanism: Optional[str] = Field(None, description="Detailed explanation of how the failure occurs.")

class HistoricalReference(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    found: bool
    memory_status: Optional[str] = None
    applicability: Optional[str] = Field(None, description="HIGH, MEDIUM, LOW, or REFERENCE_ONLY")

class RepairPlanStep(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    action: str
    description: str

class RepairPlan(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    steps: List[RepairPlanStep]
    risk: str
    expected_behavior: str

class PatchCandidateModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    id: Optional[UUID] = None
    status: str = "unvalidated"
    files_changed: List[str] = Field(description="List of file paths modified by this patch.")
    diff: str = Field(description="The actual unified diff format patch.")
    explanation: str = Field(description="Concise engineering explanation of the patch. No private reasoning.")

class InvestigationResult(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    incident_id: Optional[UUID] = None
    status: str = "completed"
    root_cause: Optional[RootCauseAnalysis] = None
    historical_reference: Optional[HistoricalReference] = None
    repair_plan: Optional[RepairPlan] = None
    patch_candidate: Optional[PatchCandidateModel] = None
    verification_requirements: List[str] = []
    assumptions: List[str] = []
    evidence_used: List[str] = []
