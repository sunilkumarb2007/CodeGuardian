from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class IncidentSummary(BaseModel):
    id: str
    incident_number: Optional[str] = None
    title: Optional[str] = None
    endpoint: Optional[str] = None
    http_method: Optional[str] = None
    observed_status_code: Optional[int] = None
    error_fingerprint: Optional[str] = None
    root_cause_summary: Optional[str] = None


class RepositorySummary(BaseModel):
    id: Optional[str] = None
    name: str
    url: str
    default_branch: str = "main"
    commit_sha: Optional[str] = None
    language: Optional[str] = None
    framework: Optional[str] = None
    build_system: Optional[str] = None


class FailureSummary(BaseModel):
    type: str
    message: str
    symptom_service: Optional[str] = None
    stack_trace_snippet: Optional[str] = None


class RootCauseSummary(BaseModel):
    service: str
    summary: str
    affected_file: Optional[str] = None
    line_number: Optional[int] = None
    causal_chain: Optional[List[str]] = None


class RepairSummary(BaseModel):
    patch_id: Optional[str] = None
    patch_number: Optional[int] = None
    affected_files: List[str] = Field(default_factory=list)
    lines_added: int = 0
    lines_removed: int = 0
    diff_snippet: Optional[str] = None
    summary: Optional[str] = None


class VerificationSummary(BaseModel):
    replay: str = "N/A" # PASS, FAIL, N/A, NOT_REQUIRED
    build: str = "N/A"
    tests: str = "N/A"
    validation: str = "N/A" # e.g. "6 / 6 PASS", "FAILED", "NOT_REQUIRED"
    gates_passed: int = 0
    gates_total: int = 6
    gate_details: List[Dict[str, Any]] = Field(default_factory=list)
    validated_at: Optional[datetime] = None


class ApprovalSummary(BaseModel):
    status: str = "NOT_REQUIRED" # APPROVED, REJECTED, PENDING, NOT_REQUIRED
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    policy: Optional[str] = None


class DeliverySummary(BaseModel):
    status: str = "N/A" # DELIVERED, BLOCKED, FAILED, PENDING, N/A, NOT_REQUIRED
    provider: Optional[str] = None
    branch_name: Optional[str] = None
    pr_number: Optional[int] = None
    pr_url: Optional[str] = None
    merge_status: Optional[str] = None
    delivered_at: Optional[datetime] = None
    failure_reason: Optional[str] = None


class PostMergeSummary(BaseModel):
    verified: bool = False
    exit_code: Optional[int] = None
    merge_sha: Optional[str] = None
    verified_at: Optional[datetime] = None


class MemorySummary(BaseModel):
    updated: bool = False
    memory_id: Optional[str] = None
    error_fingerprint: Optional[str] = None
    updated_at: Optional[datetime] = None


class RepairReceiptResponse(BaseModel):
    receipt_id: str
    receipt_hash: str
    generated_at: datetime
    run_id: str
    receipt_type: str # REPAIR_RECEIPT, REPAIR_ATTEMPT_RECEIPT, ANALYSIS_RECEIPT
    lifecycle_status: str # DRAFT, VERIFIED, APPROVED, DELIVERED, COMPLETED, FAILED
    outcome: str # FAILURE_REPAIRED, NO_FAILURE_FOUND, REPAIR_NOT_DELIVERED, DELIVERY_BLOCKED, AI_TIMEOUT, VALIDATION_FAILED, DELIVERY_FAILED, etc.
    environment: str = "production"
    
    incident: IncidentSummary
    repository: RepositorySummary
    failure: FailureSummary
    root_cause: RootCauseSummary
    repair: RepairSummary
    verification: VerificationSummary
    approval: ApprovalSummary
    delivery: DeliverySummary
    post_merge: PostMergeSummary
    memory: MemorySummary
    
    ascii_receipt: str
