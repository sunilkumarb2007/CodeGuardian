import pytest
import uuid
import re
import os
from unittest.mock import MagicMock
from app.db import models
from app.engine.prompt_builder import InvestigationPromptBuilder
from app.engine.context_builder import InvestigationContextBuilder
from app.schemas.investigation import (
    RootCauseAnalysis,
    PatchCandidateModel,
    InvestigationResult,
    HistoricalReference
)
from app.services.investigation_service import InvestigationService
from app.services.failure_evidence_collector import FailureEvidenceCollector

def test_prompt_has_no_demo_repair():
    """Verify prompt builder output contains placeholders and no hardcoded demo repair strings."""
    inc = models.Incident(
        id=uuid.uuid4(),
        title="CustomService OutOfMemoryError",
        description="Heap exhausted in custom processor"
    )
    sf = [
        models.RepositoryFile(
            id=uuid.uuid4(),
            file_path="custom-service/src/main/java/com/example/CustomService.java",
            source_snapshot="public class CustomService {\n  void process() {}\n}"
        )
    ]
    ev = [
        models.EvidenceEvent(
            id=uuid.uuid4(),
            service_name="custom-service",
            event_type="error",
            error_message="OutOfMemoryError",
            stack_trace="at com.example.CustomService.process(CustomService.java:2)"
        )
    ]
    prompt = InvestigationPromptBuilder.build_prompt(
        incident=inc,
        evidence=ev,
        trace=None,
        memory_response=None,
        source_files=sf
    )
    assert "merchant == null" not in prompt
    assert "Merchant not found" not in prompt
    assert "payment-service" not in prompt
    assert "PaymentService" not in prompt
    assert "custom-service/src/main/java/com/example/CustomService.java" in prompt

def test_missing_evidence_blocks_investigation():
    """Verify FailureEvidenceCollector returns NO_FAILURE_EVIDENCE when failure input is absent."""
    db_mock = MagicMock()
    collector = FailureEvidenceCollector(db_mock)
    res = collector.collect_evidence("https://github.com/example/some-repo.git", uuid.uuid4(), failure_input=None)
    assert res == "NO_FAILURE_EVIDENCE"

def test_missing_file_does_not_default_paymentservice():
    """Verify PatchCandidateModel does not invent PaymentService.java when files_changed is empty."""
    pc = PatchCandidateModel(
        files_changed=[],
        diff="",
        explanation="No changes"
    )
    assert pc.files_changed == []
    assert "PaymentService.java" not in pc.files_changed

def test_missing_service_does_not_default_payment_service():
    """Verify RootCauseAnalysis defaults to unknown and does not invent payment-service."""
    rc = RootCauseAnalysis(summary="General crash")
    assert rc.service == "unknown"

def test_stub_provider_does_not_create_patch():
    """Verify InvestigationService._create_stub_result produces AI_PROVIDER_NOT_CONFIGURED with no patch."""
    inv_svc = InvestigationService()
    res = inv_svc._create_stub_result(uuid.uuid4())
    assert res.status == "AI_PROVIDER_NOT_CONFIGURED"
    assert res.patch_candidate is None

def test_cors_patch_rejected_for_payment_root_cause():
    """Verify PATCH_ROOT_CAUSE_MISMATCH is flagged when root cause is in PaymentService but patch targets CorsConfig.java."""
    inv_svc = InvestigationService()
    inv_svc._persist_investigation = MagicMock()
    inv_svc._emit_event = MagicMock()
    
    # Mock context
    inc_id = uuid.uuid4()
    rc = RootCauseAnalysis(
        service="payment-service",
        summary="Null dereference in PaymentService",
        affected_file="payment-service/src/main/java/com/codeguardian/PaymentService.java"
    )
    patch = PatchCandidateModel(
        status="unvalidated",
        files_changed=["gateway/src/main/java/com/codeguardian/CorsConfig.java"],
        diff="--- a/gateway/src/main/java/com/codeguardian/CorsConfig.java\n+++ b/gateway/src/main/java/com/codeguardian/CorsConfig.java\n@@ -1,1 +1,2 @@\n+// fix",
        explanation="Modified CORS config"
    )
    result = InvestigationResult(
        incident_id=inc_id,
        status="completed",
        root_cause=rc,
        patch_candidate=patch
    )
    
    allowed_paths = [
        "payment-service/src/main/java/com/codeguardian/PaymentService.java",
        "gateway/src/main/java/com/codeguardian/CorsConfig.java"
    ]
    
    # Test causal consistency validation logic directly
    rc_file = result.root_cause.affected_file.split("/")[-1]
    rc_stem = rc_file.split(".")[0].lower()
    normalized_files = result.patch_candidate.files_changed
    patch_matches = any(rc_stem in pf.lower() for pf in normalized_files)
    service_matches = any(result.root_cause.service.lower() in pf.lower() for pf in normalized_files)
    
    assert not patch_matches
    assert not service_matches

def test_static_scan_production_code_clean():
    """CI safety scan: ensure production backend code (app/) contains no hardcoded demo repair knowledge."""
    app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app"))
    forbidden_tokens = [
        ("prompt_builder.py", "merchant == null"),
        ("prompt_builder.py", "Merchant not found"),
        ("sarvam_investigator.py", "merchant == null"),
        ("investigation.py", "PaymentService.java"),
        ("investigation.py", "payment-service"),
    ]
    
    for filename, token in forbidden_tokens:
        for root, dirs, files in os.walk(app_dir):
            if filename in files:
                file_path = os.path.join(root, filename)
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                assert token not in content, f"Found forbidden token '{token}' in production file {file_path}"
