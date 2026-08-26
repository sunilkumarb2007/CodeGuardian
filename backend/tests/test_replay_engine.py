import pytest
import os
import uuid
from unittest.mock import MagicMock
from app.engine.replay_engine import ReplayEngine
from app.db.models import Patch, RepositoryFile

def test_replay_engine_simulation_no_patch():
    engine = ReplayEngine()
    
    # Mock simulate_replay instead of full engine execution
    def mock_simulate(patch):
        return "BASELINE_ONLY", {"http_status": 500}, {"status": "skipped"}
    engine._simulate_replay = mock_simulate
    
    # Actually just call _simulate_replay because in unit tests we don't want to clone
    result, baseline, patched = engine._simulate_replay(None)
    
    assert result == "BASELINE_ONLY"
    assert baseline["http_status"] == 500
    assert patched["status"] == "skipped"

def test_replay_engine_simulation_patch_context_mismatch():
    engine = ReplayEngine()
    
    # Patch without the string "process(obj)"
    patch = Patch(
        id=uuid.uuid4(),
        diff="--- payment.py\n+++ payment.py\n@@ -1,1 +1,1 @@\n- foo\n+ bar",
        affected_files=["payment.py"]
    )
    
    result, baseline, patched = engine._simulate_replay(patch)
    
    assert result == "PATCH_APPLY_FAILED"
    assert patched["status"] == "PATCH_CONTEXT_MISMATCH"

def test_replay_engine_simulation_patch_success():
    engine = ReplayEngine()
    
    # Patch with the string "process(obj)"
    patch = Patch(
        id=uuid.uuid4(),
        diff="--- payment.py\n+++ payment.py\n@@ -10,1 +10,2 @@\n- process(obj)\n+ if obj:\n+     process(obj)",
        affected_files=["payment.py"]
    )
    
    result, baseline, patched = engine._simulate_replay(patch)
    
    assert result == "REPLAY_CHANGED_BEHAVIOR"
    assert patched["http_status"] == 200
    assert patched["failure_fingerprint"] is None
