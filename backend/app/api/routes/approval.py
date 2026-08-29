from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.services.approval_policy_engine import ApprovalPolicyEngine
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/api/approval", tags=["Approval Center"])

class EvaluatePolicyRequest(BaseModel):
    validation_results: Dict[str, Any]
    changed_files_count: int = 1
    affected_services_count: int = 1
    replay_status: str = "PASS"
    risk_level: str = "LOW"

class ApprovalDecisionRequest(BaseModel):
    run_id: str
    actor: str = "developer"
    decision: str  # APPROVED_FOR_PR, APPROVED_FOR_MERGE, REJECTED
    comments: Optional[str] = None

@router.post("/evaluate-policy")
def evaluate_policy(req: EvaluatePolicyRequest):
    """
    Evaluates risk and automatic merge policy rules.
    """
    try:
        res = ApprovalPolicyEngine.evaluate_merge_policy(
            validation_results=req.validation_results,
            changed_files_count=req.changed_files_count,
            affected_services_count=req.affected_services_count,
            replay_status=req.replay_status,
            risk_level=req.risk_level
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Policy evaluation failed: {str(e)}")

@router.post("/{run_id}/decide")
def submit_decision(run_id: str, req: ApprovalDecisionRequest):
    """
    Records a human approval decision and dispatches workflow notifications.
    """
    NotificationService.emit_notification(
        run_id=run_id,
        notification_type="APPROVAL_DECIDED",
        title=f"Approval Decision: {req.decision}",
        message=f"Actor '{req.actor}' submitted decision '{req.decision}'.",
        action_url=f"/runs/{run_id}"
    )
    return {
        "run_id": run_id,
        "decision": req.decision,
        "actor": req.actor,
        "status": "RECORDED"
    }
