import pytest
import json
from unittest.mock import MagicMock, patch
from app.schemas.investigation import InvestigationResult, RootCauseAnalysis, PatchCandidateModel
from app.engine.sarvam_investigator import SarvamInvestigator

# 1. Complete Sarvam JSON
def test_1_complete_sarvam_json():
    payload = {
        "status": "completed",
        "root_cause": {
            "service": "payment-service",
            "summary": "Null dereference when merchant is not found",
            "affected_file": "payment-service/src/main/java/com/codeguardian/paymentservice/PaymentService.java",
            "location": "payment-service/src/main/java/com/codeguardian/paymentservice/PaymentService.java:30",
            "confidence": 1.0,
            "failure_mechanism": "NullPointerException"
        },
        "patch_candidate": {
            "status": "unvalidated",
            "files_changed": ["payment-service/src/main/java/com/codeguardian/paymentservice/PaymentService.java"],
            "diff": "--- a/payment-service/src/main/java/com/codeguardian/paymentservice/PaymentService.java\n+++ b/payment-service/src/main/java/com/codeguardian/paymentservice/PaymentService.java\n@@ -24,3 +24,5 @@\n+        if (merchant == null) throw new IllegalStateException();",
            "explanation": "Add defensive null guard"
        }
    }
    res = InvestigationResult.model_validate(payload)
    assert res.status == "completed"
    assert res.root_cause.service == "payment-service"
    assert len(res.patch_candidate.files_changed) == 1
    assert "--- a/" in res.patch_candidate.diff

# 2. String root cause
def test_2_string_root_cause():
    payload = {
        "root_cause": "The variable merchant was not found in the DB repository.",
        "patch_candidate": {
            "files_changed": ["PaymentService.java"],
            "diff": "--- a/PaymentService.java\n+++ b/PaymentService.java\n@@ -24,3 +24,5 @@\n+if (merchant == null) return;",
            "explanation": "Add null check"
        }
    }
    res = InvestigationResult.model_validate(payload)
    assert res.root_cause.summary == "The variable merchant was not found in the DB repository."
    assert res.root_cause.service == "unknown"

# 3. filesChanged objects
def test_3_files_changed_objects():
    payload = {
        "root_cause": {"summary": "Merchant is null"},
        "patch_candidate": {
            "filesChanged": [
                {"path": "PaymentService.java", "changeType": "modified"}
            ],
            "diff": "--- a/PaymentService.java\n+++ b/PaymentService.java\n@@ -24,3 +24,5 @@\n+if (merchant == null) return;",
            "explanation": "Add null check"
        }
    }
    res = InvestigationResult.model_validate(payload)
    assert res.patch_candidate.files_changed == ["PaymentService.java"]

# 4. Valid snippet patch (synthesizes unified diff)
def test_4_valid_snippet_patch():
    payload = {
        "file_path": "PaymentService.java",
        "root_cause": "Null merchant",
        "snippet": "if (merchant == null) {\n    throw new IllegalStateException();\n}",
        "description": "Defensive check"
    }
    res = InvestigationResult.model_validate(payload)
    assert "--- a/PaymentService.java" in res.patch_candidate.diff
    assert "+if (merchant == null)" in res.patch_candidate.diff
    assert res.patch_candidate.explanation == "Defensive check"

# 5. Truncated JSON
def test_5_truncated_json():
    incomplete_json = '{"root_cause": "Null deref", "patch_candidate": {"diff": "--- a/Pay'
    with pytest.raises(Exception):
        InvestigationResult.model_validate_json(incomplete_json)

# 6. finish_reason=length detection
def test_6_finish_reason_length_detection():
    inv = SarvamInvestigator()
    # Mock httpx response with finish_reason='length'
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [
            {
                "finish_reason": "length",
                "message": {
                    "content": None,
                    "reasoning_content": "Long internal thinking that ran out of tokens..."
                }
            }
        ]
    }
    with patch("httpx.Client.post", return_value=mock_resp):
        with pytest.raises(RuntimeError) as exc_info:
            inv.investigate("prompt", deadline=None)
        assert "AI_OUTPUT_TRUNCATED" in str(exc_info.value)

# 7. Incomplete diff detection
def test_7_incomplete_diff():
    # Hunk header present but cut off before any +/- lines
    payload = {
        "root_cause": "Null merchant",
        "patch_candidate": {
            "files_changed": ["PaymentService.java"],
            "diff": "--- a/PaymentService.java\n+++ b/PaymentService.java\n@@ -24,3 +24,5 @@",
            "explanation": "Cut off diff"
        }
    }
    res = InvestigationResult.model_validate(payload)
    # Validate helper in investigator detects incomplete diff
    inv = SarvamInvestigator()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [
            {
                "finish_reason": "stop",
                "message": {"content": json.dumps(payload)}
            }
        ]
    }
    with patch("httpx.Client.post", return_value=mock_resp):
        with pytest.raises(RuntimeError) as exc_info:
            inv.investigate("prompt", deadline=None)
        assert "AI_OUTPUT_TRUNCATED" in str(exc_info.value)

# 8. Truncation recovery succeeds
def test_8_truncation_recovery():
    inv = SarvamInvestigator()
    # First response is truncated by length, second response (recovery) succeeds
    resp1 = MagicMock()
    resp1.status_code = 200
    resp1.json.return_value = {
        "choices": [{"finish_reason": "length", "message": {"content": None}}]
    }
    
    valid_recovery = {
        "root_cause": "Null dereference in PaymentService",
        "root_cause_service": "payment-service",
        "affected_file": "PaymentService.java",
        "line": 30,
        "repair_summary": "Throw exception if merchant is null",
        "diff": "--- a/PaymentService.java\n+++ b/PaymentService.java\n@@ -24,3 +24,5 @@\n+if (merchant == null) throw new IllegalStateException();",
        "confidence": 1.0
    }
    resp2 = MagicMock()
    resp2.status_code = 200
    resp2.json.return_value = {
        "choices": [{"finish_reason": "stop", "message": {"content": json.dumps(valid_recovery)}}]
    }
    
    with patch("httpx.Client.post", side_effect=[resp1, resp2]):
        result = inv.investigate("prompt", deadline=None)
        assert result is not None
        assert result.status == "completed"
        assert result.patch_candidate.files_changed == ["PaymentService.java"]

# 9. AI Timeout
def test_9_ai_timeout():
    from app.services.investigation_service import InvestigationService
    import httpx
    inv = SarvamInvestigator()
    with patch("httpx.Client.post", side_effect=httpx.ReadTimeout("Timeout")):
        with pytest.raises(RuntimeError) as exc_info:
            inv.investigate("prompt", deadline=None)
        assert "AI_TIMEOUT" in str(exc_info.value)

# 10. AI Provider Error (HTTP 500)
def test_10_ai_provider_error():
    inv = SarvamInvestigator()
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    with patch("httpx.Client.post", return_value=mock_resp):
        with pytest.raises(RuntimeError) as exc_info:
            inv.investigate("prompt", deadline=None)
        assert "AI_PROVIDER_ERROR" in str(exc_info.value)

# 11. Invalid Schema Error
def test_11_invalid_schema():
    inv = SarvamInvestigator()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    # Returns completely unparseable garbage that cannot be repaired
    mock_resp.json.return_value = {
        "choices": [{"finish_reason": "stop", "message": {"content": "INVALID NOT JSON AT ALL"}}]
    }
    with patch("httpx.Client.post", return_value=mock_resp):
        with pytest.raises(RuntimeError) as exc_info:
            inv.investigate("prompt", deadline=None)
        assert "AI_SCHEMA_ERROR" in str(exc_info.value)

# 12. No Viable Repair Result
def test_12_no_viable_repair():
    payload = {
        "status": "no_repair_available",
        "root_cause": {"summary": "Root cause unknown or irreproducible"},
        "verification_requirements": ["Manual operator investigation required"]
    }
    res = InvestigationResult.model_validate(payload)
    assert res.status == "no_repair_available"
    assert res.patch_candidate is None
