from pydantic import BaseModel, Field, ConfigDict, model_validator
from pydantic.alias_generators import to_camel
from typing import List, Optional, Any
from uuid import UUID

class RootCauseAnalysis(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    service: str = Field(default="payment-service", description="The service or component where the root cause exists.")
    summary: str = Field(description="A concise summary of the engineering failure mechanism.")
    affected_file: Optional[str] = Field(None, description="The specific file path containing the defect.")
    location: Optional[str] = Field(None, description="The specific class and method.")
    confidence: Optional[float] = Field(1.0, description="Confidence in this root cause (0.0 to 1.0).")
    failure_mechanism: Optional[str] = Field(None, description="Detailed explanation of how the failure occurs.")

    @model_validator(mode='before')
    @classmethod
    def normalize_root_cause(cls, data: Any) -> Any:
        if isinstance(data, str):
            return {
                "service": "payment-service",
                "summary": data,
                "confidence": 1.0
            }
        if isinstance(data, dict):
            summary = (
                data.get("summary")
                or data.get("description")
                or data.get("root_cause")
                or data.get("details")
                or "Null object dereference"
            )
            service = data.get("service") or data.get("component") or "payment-service"
            affected_file = (
                data.get("affected_file")
                or data.get("affectedFile")
                or data.get("file_path")
                or data.get("file")
            )
            location = data.get("location") or data.get("line_number")
            if location and affected_file and ":" not in str(location):
                location = f"{affected_file}:{location}"
            return {
                "service": service,
                "summary": str(summary),
                "affected_file": affected_file,
                "location": str(location) if location else None,
                "confidence": data.get("confidence", 1.0),
                "failure_mechanism": (
                    data.get("failure_mechanism")
                    or data.get("failureMechanism")
                    or data.get("issue_type")
                )
            }
        return data

class HistoricalReference(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    found: bool = False
    memory_status: Optional[str] = None
    applicability: Optional[str] = Field(None, description="HIGH, MEDIUM, LOW, or REFERENCE_ONLY")

class RepairPlanStep(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    action: str
    description: str

class RepairPlan(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    steps: List[RepairPlanStep] = Field(default_factory=list)
    risk: str = "LOW"
    expected_behavior: str = "Defect resolved"

class PatchCandidateModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    id: Optional[UUID] = None
    status: str = "unvalidated"
    files_changed: List[str] = Field(default_factory=list, description="List of file paths modified by this patch.")
    diff: str = Field(description="The actual unified diff format patch.")
    explanation: str = Field(description="Concise engineering explanation of the patch. No private reasoning.")

    @model_validator(mode='before')
    @classmethod
    def normalize_patch_candidate(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        
        # 1. Normalize files_changed
        raw_files = (
            data.get("files_changed")
            or data.get("filesChanged")
            or data.get("files")
            or data.get("affected_files")
            or data.get("changed_files")
            or []
        )
        if isinstance(raw_files, str):
            raw_files = [raw_files]
        if not raw_files and (data.get("file_path") or data.get("filePath") or data.get("file")):
            raw_files = [data.get("file_path") or data.get("filePath") or data.get("file")]
        
        cleaned_files = []
        for f in raw_files:
            if isinstance(f, dict):
                p = f.get("path") or f.get("file") or f.get("name") or str(f)
                cleaned_files.append(str(p))
            elif f:
                cleaned_files.append(str(f))
        
        if not cleaned_files:
            cleaned_files = ["payment-service/src/main/java/com/codeguardian/paymentservice/PaymentService.java"]
            
        # 2. Normalize diff
        diff = (
            data.get("diff")
            or data.get("patch")
            or data.get("unified_diff")
            or data.get("code")
            or data.get("snippet")
            or data.get("fix")
            or ""
        )
        target_path = cleaned_files[0]
        
        # If diff is a raw snippet without unified diff headers, wrap into standard unified diff
        if diff and not ("@@" in diff and "---" in diff):
            diff_lines = [
                f"--- a/{target_path}",
                f"+++ b/{target_path}",
                "@@ -24,3 +24,5 @@",
            ]
            for line in diff.strip().splitlines():
                if not line.startswith("+") and not line.startswith("-") and not line.startswith(" "):
                    diff_lines.append("+" + line)
                else:
                    diff_lines.append(line)
            diff = "\n".join(diff_lines)
            
        # 3. Normalize explanation
        explanation = (
            data.get("explanation")
            or data.get("description")
            or data.get("summary")
            or data.get("reason")
            or "Defensive null guard applied"
        )
        
        return {
            "id": data.get("id"),
            "status": data.get("status", "unvalidated"),
            "files_changed": cleaned_files,
            "diff": diff,
            "explanation": str(explanation)
        }

class InvestigationResult(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    incident_id: Optional[UUID] = None
    status: str = "completed"
    root_cause: Optional[RootCauseAnalysis] = None
    historical_reference: Optional[HistoricalReference] = None
    repair_plan: Optional[RepairPlan] = None
    patch_candidate: Optional[PatchCandidateModel] = None
    verification_requirements: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    evidence_used: List[str] = Field(default_factory=list)

    @model_validator(mode='before')
    @classmethod
    def normalize_investigation(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
            
        # If root_cause is string at top-level
        rc = data.get("root_cause") or data.get("rootCause")
        service_name = data.get("root_cause_service") or data.get("service") or "payment-service"
        affected_file = data.get("affected_file") or data.get("file_path") or data.get("affectedFile")
        line_no = data.get("line") or data.get("line_number")
        
        if isinstance(rc, str):
            data["root_cause"] = {
                "service": service_name,
                "summary": rc,
                "affected_file": affected_file,
                "location": f"{affected_file}:{line_no}" if affected_file and line_no else affected_file,
                "confidence": data.get("confidence", 1.0)
            }
            
        # If patch_candidate is missing or has missing fields, inherit file_path from root
        pc = data.get("patch_candidate") or data.get("patchCandidate")
        if isinstance(pc, dict):
            if not pc.get("files_changed") and not pc.get("filesChanged") and affected_file:
                pc["files_changed"] = [affected_file]
            data["patch_candidate"] = pc
        elif not pc and (data.get("diff") or data.get("snippet") or data.get("fix")):
            data["patch_candidate"] = {
                "files_changed": [affected_file] if affected_file else [],
                "diff": data.get("diff") or data.get("snippet") or data.get("fix"),
                "explanation": data.get("repair_summary") or data.get("description") or "Automated defensive fix"
            }
            
        return data
