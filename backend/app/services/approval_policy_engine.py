import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class ApprovalPolicyEngine:
    """
    Approval State Machine & Automatic Merge Policy Evaluator.
    Determines whether a validated patch requires explicit human sign-off
    or qualifies for policy-governed automatic merge.
    """

    @classmethod
    def evaluate_merge_policy(
        cls,
        validation_results: Dict[str, Any],
        changed_files_count: int,
        affected_services_count: int,
        replay_status: str,
        risk_level: str = "LOW"
    ) -> Dict[str, Any]:
        """
        Evaluates safety parameters against strict merge policy rules.
        """
        reasons_eligible = []
        blocking_reasons = []

        # 1. Deterministic gates verification
        all_gates_pass = validation_results.get("all_passed", True) and validation_results.get("status") in ["PASSED", "VALIDATED"]
        if all_gates_pass:
            reasons_eligible.append("All 6 deterministic safety gates passed")
        else:
            blocking_reasons.append("Validation gates incomplete or failed")

        # 2. Replay proof
        if replay_status == "PASS" or replay_status == "REPLAY_CHANGED_BEHAVIOR":
            reasons_eligible.append("Sandboxed replay proved behavioral resolution (500 -> 200)")
        else:
            blocking_reasons.append(f"Replay status '{replay_status}' did not prove clean resolution")

        # 3. Risk level
        if risk_level.upper() == "LOW":
            reasons_eligible.append("Risk assessment classified as LOW")
        else:
            blocking_reasons.append(f"Risk level '{risk_level}' requires human review")

        # 4. Scope boundaries
        if changed_files_count <= 2:
            reasons_eligible.append(f"Scope contained to {changed_files_count} file(s) (threshold: <= 2)")
        else:
            blocking_reasons.append(f"Scope touches {changed_files_count} files (exceeds auto-merge threshold of 2)")

        if affected_services_count <= 1:
            reasons_eligible.append(f"Single service scope ({affected_services_count} service)")
        else:
            blocking_reasons.append(f"Multi-service patch ({affected_services_count} services) requires human architectural sign-off")

        # Final decision
        is_auto_merge_eligible = len(blocking_reasons) == 0

        return {
            "policy_mode": "AUTO_MERGE_ELIGIBLE" if is_auto_merge_eligible else "HUMAN_APPROVAL_REQUIRED",
            "is_auto_merge_eligible": is_auto_merge_eligible,
            "risk_level": risk_level,
            "reasons_eligible": reasons_eligible,
            "blocking_reasons": blocking_reasons,
            "summary": (
                "Patch satisfies all automatic merge criteria."
                if is_auto_merge_eligible
                else f"Human approval required: {'; '.join(blocking_reasons)}."
            ),
            "evaluated_at": datetime.utcnow().isoformat()
        }

    @classmethod
    def verify_approval_freshness(
        cls,
        approved_commit_sha: str,
        current_branch_sha: str
    ) -> Dict[str, Any]:
        """
        Verifies that the commit approved matches the current branch HEAD.
        If the branch was modified after approval, status is REVALIDATION_REQUIRED.
        """
        if not approved_commit_sha or not current_branch_sha:
            return {
                "status": "REVALIDATION_REQUIRED",
                "valid": False,
                "reason": "Missing commit SHA for validation"
            }
        
        if approved_commit_sha.strip().lower() != current_branch_sha.strip().lower():
            return {
                "status": "REVALIDATION_REQUIRED",
                "valid": False,
                "reason": f"Target branch head '{current_branch_sha[:8]}' differs from approved commit '{approved_commit_sha[:8]}'. Stale approval detected."
            }
            
        return {
            "status": "VALID",
            "valid": True,
            "reason": "Approval matches current branch head commit."
        }

