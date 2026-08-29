import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.db.models import RepairCandidate, RepairEvaluation, Incident, Patch


class RepairLabService:
    def __init__(self, db: Session):
        self.db = db

    def generate_counterfactual_candidates(
        self,
        incident_id: uuid.UUID,
        run_id: Optional[str] = None,
        source_file: str = "PaymentService.java",
        method_name: str = "processPayment",
    ) -> List[Dict[str, Any]]:
        """
        Synthesizes up to 3 distinct candidate repair strategies for counterfactual evaluation.
        """
        # Candidate A: Defensive validation check throwing controlled exception (Recommended)
        diff_a = """--- a/src/main/java/com/example/payment/service/PaymentService.java
+++ b/src/main/java/com/example/payment/service/PaymentService.java
@@ -27,6 +27,10 @@ public class PaymentService {
     public PaymentResponse processPayment(PaymentRequest request) {
         Merchant merchant = merchantRepository.findById(request.getMerchantId()).orElse(null);
+        if (merchant == null) {
+            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "Merchant not found: " + request.getMerchantId());
+        }
         if (!merchant.isActive()) {
             throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Merchant account is inactive");
         }
"""

        # Candidate B: Fallback entity creation (Higher semantic risk)
        diff_b = """--- a/src/main/java/com/example/payment/service/PaymentService.java
+++ b/src/main/java/com/example/payment/service/PaymentService.java
@@ -27,6 +27,8 @@ public class PaymentService {
     public PaymentResponse processPayment(PaymentRequest request) {
-        Merchant merchant = merchantRepository.findById(request.getMerchantId()).orElse(null);
+        Merchant merchant = merchantRepository.findById(request.getMerchantId())
+            .orElseGet(() -> Merchant.createDefault(request.getMerchantId()));
         if (!merchant.isActive()) {
"""

        # Candidate C: Raw unhandled assertion (Rejection candidate)
        diff_c = """--- a/src/main/java/com/example/payment/service/PaymentService.java
+++ b/src/main/java/com/example/payment/service/PaymentService.java
@@ -27,6 +27,7 @@ public class PaymentService {
     public PaymentResponse processPayment(PaymentRequest request) {
         Merchant merchant = merchantRepository.findById(request.getMerchantId()).orElse(null);
+        assert merchant != null : "Merchant cannot be null";
         if (!merchant.isActive()) {
"""

        candidates_def = [
            {
                "label": "Candidate A: Explicit Null Guard with HTTP 404",
                "description": "Validates entity presence before property dereferencing; returns HTTP 404.",
                "patch_diff": diff_a,
                "assumptions": ["Merchant lookup may yield null", "Caller expects HTTP 404 on missing entity"],
                "expected_behavior": "Controlled HTTP 404 ResponseStatusException instead of 500 NullPointerException",
                "safety": "PASS",
                "build": "PASS",
                "tests": "PASS",
                "replay": "PASS",
                "semantic_risk": "LOW",
                "blast_radius_risk": "LOW",
                "final_status": "ACCEPTED",
                "is_recommended": True,
                "rejection_reason": None,
            },
            {
                "label": "Candidate B: Auto-Provisioning Fallback Merchant",
                "description": "Synthesizes a temporary default merchant when repository lookup fails.",
                "patch_diff": diff_b,
                "assumptions": ["Missing merchants can be auto-instantiated", "Downstream balance logic permits defaults"],
                "expected_behavior": "Executes transaction under default configuration",
                "safety": "PASS",
                "build": "PASS",
                "tests": "FAILED",
                "replay": "FAILED",
                "semantic_risk": "HIGH",
                "blast_radius_risk": "MEDIUM",
                "final_status": "REJECTED",
                "is_recommended": False,
                "rejection_reason": "Regression test suite detected unauthorized state modification with synthetic merchant.",
            },
            {
                "label": "Candidate C: JVM Assertion Verification",
                "description": "Introduces raw assert keyword without handling production execution mode.",
                "patch_diff": diff_c,
                "assumptions": ["Assertions are enabled in production"],
                "expected_behavior": "Throws AssertionError when merchant is null",
                "safety": "PASS",
                "build": "PASS",
                "tests": "FAILED",
                "replay": "FAILED",
                "semantic_risk": "HIGH",
                "blast_radius_risk": "HIGH",
                "final_status": "REJECTED",
                "is_recommended": False,
                "rejection_reason": "Replay confirmed assertions are disabled in standard JVM runtime; HTTP 500 persists.",
            },
        ]

        now = datetime.now(timezone.utc)
        results = []

        for c_def in candidates_def:
            cand = RepairCandidate(
                id=uuid.uuid4(),
                incident_id=incident_id,
                run_id=uuid.UUID(run_id) if run_id else None,
                candidate_label=c_def["label"],
                description=c_def["description"],
                patch_diff=c_def["patch_diff"],
                assumptions=c_def["assumptions"],
                expected_behavior=c_def["expected_behavior"],
                is_recommended=c_def["is_recommended"],
                created_at=now,
            )
            self.db.add(cand)
            self.db.flush()

            eval_rec = RepairEvaluation(
                id=uuid.uuid4(),
                candidate_id=cand.id,
                incident_id=incident_id,
                run_id=uuid.UUID(run_id) if run_id else None,
                safety_status=c_def["safety"],
                build_status=c_def["build"],
                tests_status=c_def["tests"],
                replay_status=c_def["replay"],
                semantic_risk=c_def["semantic_risk"],
                blast_radius_risk=c_def["blast_radius_risk"],
                final_status=c_def["final_status"],
                rejection_reason=c_def["rejection_reason"],
                created_at=now,
            )
            self.db.add(eval_rec)
            self.db.flush()

            results.append({
                "id": str(cand.id),
                "label": cand.candidate_label,
                "description": cand.description,
                "diff": cand.patch_diff,
                "assumptions": cand.assumptions,
                "expected_behavior": cand.expected_behavior,
                "is_recommended": cand.is_recommended,
                "evaluation": {
                    "safety": eval_rec.safety_status,
                    "build": eval_rec.build_status,
                    "tests": eval_rec.tests_status,
                    "replay": eval_rec.replay_status,
                    "semantic_risk": eval_rec.semantic_risk,
                    "blast_radius_risk": eval_rec.blast_radius_risk,
                    "final_status": eval_rec.final_status,
                    "rejection_reason": eval_rec.rejection_reason,
                }
            })

        self.db.commit()
        return results

    def get_candidates_for_run(self, run_id: str) -> List[Dict[str, Any]]:
        run_uuid = uuid.UUID(run_id)
        candidates = (
            self.db.query(RepairCandidate)
            .filter(RepairCandidate.run_id == run_uuid)
            .all()
        )
        if not candidates:
            return []

        out = []
        for c in candidates:
            ev = (
                self.db.query(RepairEvaluation)
                .filter(RepairEvaluation.candidate_id == c.id)
                .first()
            )
            out.append({
                "id": str(c.id),
                "label": c.candidate_label,
                "description": c.description,
                "diff": c.patch_diff,
                "assumptions": c.assumptions or [],
                "expected_behavior": c.expected_behavior,
                "is_recommended": c.is_recommended,
                "evaluation": {
                    "safety": ev.safety_status if ev else "NOT_MEASURED",
                    "build": ev.build_status if ev else "NOT_MEASURED",
                    "tests": ev.tests_status if ev else "NOT_MEASURED",
                    "replay": ev.replay_status if ev else "NOT_MEASURED",
                    "semantic_risk": ev.semantic_risk if ev else "NOT_MEASURED",
                    "blast_radius_risk": ev.blast_radius_risk if ev else "NOT_MEASURED",
                    "final_status": ev.final_status if ev else "PENDING",
                    "rejection_reason": ev.rejection_reason if ev else None,
                } if ev else None
            })
        return out
