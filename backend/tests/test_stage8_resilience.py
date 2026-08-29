import pytest
from app.schemas.investigation import InvestigationResult, RootCauseAnalysis, PatchCandidateModel

def test_valid_sarvam_standard_schema():
    payload = {
        "status": "completed",
        "root_cause": {
            "service": "payment-service",
            "summary": "Null dereference when merchant is not found in repository",
            "affected_file": "payment-service/src/main/java/com/codeguardian/paymentservice/PaymentService.java",
            "location": "payment-service/src/main/java/com/codeguardian/paymentservice/PaymentService.java:24",
            "confidence": 1.0,
            "failure_mechanism": "NullPointerException"
        },
        "patch_candidate": {
            "status": "unvalidated",
            "files_changed": [
                "payment-service/src/main/java/com/codeguardian/paymentservice/PaymentService.java"
            ],
            "diff": "--- a/payment-service/src/main/java/com/codeguardian/paymentservice/PaymentService.java\n+++ b/payment-service/src/main/java/com/codeguardian/paymentservice/PaymentService.java\n@@ -24,3 +24,5 @@\n+        if (merchant == null) {\n+            throw new IllegalStateException(\"Merchant not found\");\n+        }",
            "explanation": "Add null check in PaymentService"
        }
    }
    res = InvestigationResult.model_validate(payload)
    assert res.status == "completed"
    assert res.root_cause.service == "payment-service"
    assert len(res.patch_candidate.files_changed) == 1
    assert "--- a/" in res.patch_candidate.diff

def test_sarvam_resilient_raw_snippet_and_string_root_cause():
    """Tests the exact variant Sarvam 105B returned in live production."""
    payload = {
        "issue_type": "NullPointerException",
        "file_path": "PaymentService.java",
        "line_number": 30,
        "variable": "merchant",
        "root_cause": "The 'merchant' reference is null at the point of dereference on line 30.",
        "patch_candidate": {
            "type": "null_guard",
            "language": "java",
            "snippet": "if (merchant == null) {\n    throw new IllegalStateException(\"Merchant must not be null\");\n}\nmerchant.charge(amount);",
            "description": "Add a defensive null check before using the merchant object."
        },
        "confidence": 0.98,
        "severity": "high"
    }
    res = InvestigationResult.model_validate(payload)
    assert res.status == "completed"
    assert res.root_cause.summary.startswith("The 'merchant' reference is null")
    assert res.root_cause.service == "payment-service"
    assert res.patch_candidate.files_changed == ["PaymentService.java"]
    assert "--- a/PaymentService.java" in res.patch_candidate.diff
    assert "throw new IllegalStateException" in res.patch_candidate.diff
    assert res.patch_candidate.explanation.startswith("Add a defensive null check")

def test_sarvam_resilient_dict_files_changed():
    """Tests handling of filesChanged containing dictionaries instead of strings."""
    payload = {
        "root_cause": {
            "description": "Merchant is null"
        },
        "patch_candidate": {
            "filesChanged": [
                {"path": "PaymentService.java", "changeType": "modified"}
            ],
            "diff": "--- a/PaymentService.java\n+++ b/PaymentService.java\n@@ -24,3 +24,5 @@\n+if (merchant == null) return;",
            "explanation": "Add null check"
        }
    }
    res = InvestigationResult.model_validate(payload)
    assert res.root_cause.summary == "Merchant is null"
    assert res.patch_candidate.files_changed == ["PaymentService.java"]
