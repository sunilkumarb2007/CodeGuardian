import pytest
import uuid
from unittest.mock import MagicMock
from app.engine.validation_engine import ValidationEngine
from app.db.models import Patch

def _create_mock_replay_response(result_val="REPLAY_CHANGED_BEHAVIOR", patched_status="completed", http_status=200):
    response = MagicMock()
    response.result = result_val
    response.patched = MagicMock()
    response.patched.status = patched_status
    response.patched.http_status = http_status
    response.patched.output = "mock output"
    return response

def test_validation_engine_success():
    engine = ValidationEngine()
    
    patch = Patch(
        id=uuid.uuid4(),
        diff="--- a\n+++ b\n@@ -10,1 +10,2 @@\n- process(obj)\n+ if obj:\n+     process(obj)",
        affected_files=["src/payment_service.py"]
    )
    
    replay_response = _create_mock_replay_response()
    result = engine.run_validation(patch, replay_response=replay_response)
    
    assert result["overall_status"] == "passed"
    assert result["checks"].patch_apply == "passed"
    assert result["checks"].build == "passed"
    assert result["checks"].tests == "passed"
    assert result["checks"].replay == "passed"
    assert result["checks"].regression == "passed"
    assert result["checks"].safety == "passed"
    assert result["failure_reason"] is None

def test_validation_engine_patch_context_mismatch():
    engine = ValidationEngine()
    
    patch = Patch(
        id=uuid.uuid4(),
        diff="--- a\n+++ b\n@@ -1,1 +1,1 @@\n- foo\n+ bar",
        affected_files=["src/payment_service.py"]
    )
    
    replay_response = _create_mock_replay_response()
    result = engine.run_validation(patch, replay_response=replay_response)
    
    assert result["overall_status"] == "failed"
    assert result["checks"].patch_apply == "failed"
    assert result["failure_reason"] == "PATCH_CONTEXT_MISMATCH"

def test_validation_engine_safety_failure():
    engine = ValidationEngine()
    
    patch = Patch(
        id=uuid.uuid4(),
        diff="--- a\n+++ b\n@@ -1,1 +1,1 @@\n- process(obj)\n+ if obj:\n+     process(obj)",
        affected_files=["src/.env.production"]
    )
    
    replay_response = _create_mock_replay_response()
    result = engine.run_validation(patch, replay_response=replay_response)
    
    assert result["overall_status"] == "failed"
    assert result["checks"].safety == "failed"
    assert result["failure_reason"] == "PATCH_SAFETY_FAILED"

def test_validation_engine_replay_failure():
    engine = ValidationEngine()
    
    patch = Patch(
        id=uuid.uuid4(),
        diff="--- a\n+++ b\n@@ -10,1 +10,2 @@\n- process(obj)\n+ if obj:\n+     process(obj)",
        affected_files=["src/payment_service.py"]
    )
    
    replay_response = _create_mock_replay_response(result_val="BASELINE_ONLY")
    result = engine.run_validation(patch, replay_response=replay_response)
    
    assert result["overall_status"] == "failed"
    assert result["checks"].replay == "failed"
    assert result["failure_reason"] == "REPLAY_FAILED"
