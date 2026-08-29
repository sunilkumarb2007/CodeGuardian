from app.db import models
from app.schemas.memory import MemorySearchResponse
from typing import List, Optional

class InvestigationPromptBuilder:
    @staticmethod
    def build_prompt(
        incident: models.Incident,
        evidence: list[models.EvidenceEvent],
        trace: models.FailureTrace,
        memory_response: MemorySearchResponse,
        source_files: list[models.RepositoryFile],
        architecture: dict | None = None,
        prior_failure_evidence: Optional[List[dict]] = None
    ) -> str:
        prompt = []
        
        # 1. System Role and Task
        prompt.append("You are CodeGuardian automated program repair engine.")
        prompt.append("Analyze the failure and return ONLY the completed JSON object matching the InvestigationResult schema.")
        prompt.append("Do NOT provide any preamble, reasoning, explanation, or code blocks outside the JSON object.")
        
        lang = (architecture.get("language") or "Java") if architecture else "Java"
        prompt.append(f"\nLanguage: {lang}")
        prompt.append(f"Incident: {incident.title} - {incident.description}")
        
        # Evidence
        prompt.append("\n[Evidence]")
        for e in evidence:
            prompt.append(f"- {e.service_name} {e.event_type} {e.error_message}")
            if e.stack_trace:
                prompt.append(f"  Stack: {e.stack_trace}")
                
        # Trace
        if trace:
            prompt.append(f"\nCandidate: {trace.root_cause_candidate} ({trace.reasoning_summary})")

        # Prior failure evidence if any
        if prior_failure_evidence:
            prompt.append("\n[Prior Attempt Feedback]")
            for pf in prior_failure_evidence:
                prompt.append(f"- Attempt {pf.get('attempt')}: {pf.get('stage')} error: {pf.get('error')}")

        # Source files
        prompt.append("\n[Source Code]")
        for sf in source_files[:2]:
            prompt.append(f"File: {sf.file_path}")
            prompt.append(sf.source_snapshot or "Empty")
            prompt.append("---")

        # Required JSON output format
        prompt.append("\nReturn strictly this JSON structure:")
        prompt.append("""{
  "status": "completed",
  "root_cause": {
    "service": "payment-service",
    "summary": "Null dereference when merchant is not found in repository",
    "affected_file": "payment-service/src/main/java/com/codeguardian/paymentservice/PaymentService.java",
    "location": "payment-service/src/main/java/com/codeguardian/paymentservice/PaymentService.java:24",
    "confidence": 1.0,
    "failure_mechanism": "NullPointerException"
  },
  "historical_reference": {
    "found": true,
    "memory_status": "verified",
    "applicability": "direct_match"
  },
  "repair_plan": {
    "steps": [
      {"action": "ADD_NULL_CHECK", "description": "Throw IllegalStateException if merchant is null in PaymentService"}
    ],
    "risk": "LOW",
    "expected_behavior": "Throws descriptive IllegalStateException when merchant is null"
  },
  "patch_candidate": {
    "status": "unvalidated",
    "files_changed": [
      "payment-service/src/main/java/com/codeguardian/paymentservice/PaymentService.java"
    ],
    "diff": "--- a/payment-service/src/main/java/com/codeguardian/paymentservice/PaymentService.java\\n+++ b/payment-service/src/main/java/com/codeguardian/paymentservice/PaymentService.java\\n@@ -24,3 +24,5 @@\\n+        if (merchant == null) {\\n+            throw new IllegalStateException(\\"Merchant not found for code: \\" + request.merchantCode());\\n+        }",
    "explanation": "Add null check in PaymentService"
  },
  "verification_requirements": ["Run maven test"],
  "assumptions": ["Merchant lookup returns null for unknown merchant codes"],
  "evidence_used": ["StackTrace"]
}""")
        return "\n".join(prompt)
