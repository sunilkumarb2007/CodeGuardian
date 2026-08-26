from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

class ArchitectureSummary(BaseModel):
    tech_stack: List[str]
    language: Optional[str] = None
    framework: Optional[str] = None
    build_system: Optional[str] = None
    test_framework: Optional[str] = None
    entry_points: List[str] = []
    has_docker: bool = False
    source_root: Optional[str] = None
    test_root: Optional[str] = None
    build_command: Optional[str] = None
    test_command: Optional[str] = None
    configuration_files: List[str] = []
    
    model_config = ConfigDict(from_attributes=True)

class InspectionResult(BaseModel):
    repository_url: str
    architecture: ArchitectureSummary
    static_analysis_passed: bool
    build_passed: bool
    test_passed: bool
    failure_output: Optional[str] = None
    static_analysis_details: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(from_attributes=True)

class TriageDecision(BaseModel):
    decision_type: str # "runtime_evidence", "supplied_failure", "generic_defect", "no_actionable_defect"
    incident_id: Optional[UUID] = None
    failure_summary: Optional[str] = None
    confidence: float
    
    model_config = ConfigDict(from_attributes=True)

class OrchestrationRunState(BaseModel):
    run_id: UUID
    repository_url: str
    status: str
    current_stage: str
    stages: Dict[str, str]
    results: Dict[str, Any]
    error: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)
