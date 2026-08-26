import pytest
import uuid
from app.engine.memory_engine import MemoryEngine, FailureSignature
from app.db.models import FailureMemory

def test_exact_error_fingerprint():
    engine = MemoryEngine()
    signature = FailureSignature(
        error_fingerprint="NULL_OBJECT_ACCESS",
        symptom_service="api-gateway",
        root_cause_service="payment-service",
        error_pattern="Error in checkout"
    )
    
    mem1 = FailureMemory(
        id=uuid.uuid4(),
        error_fingerprint="NULL_OBJECT_ACCESS",
        root_cause="payment service failure",
        searchable_text="payment service failure null_object_access api-gateway",
        error_pattern="Error in checkout"
    )
    
    candidates = engine.match(signature, [mem1])
    assert len(candidates) == 1
    assert candidates[0].matched_error_pattern is True
    # Verify score is a sum of matched weights (Fingerprint 0.4 + Root Cause 0.3 + Pattern 0.1 + Symptom 0.2) = 1.0
    assert candidates[0].similarity_score >= 0.8
    
def test_same_root_cause_service():
    engine = MemoryEngine()
    signature = FailureSignature(
        error_fingerprint="UNKNOWN",
        symptom_service="api-gateway",
        root_cause_service="auth-service",
        error_pattern="Login failed"
    )
    
    mem1 = FailureMemory(
        id=uuid.uuid4(),
        error_fingerprint="DB_TIMEOUT",
        root_cause="auth-service timeout",
        searchable_text="auth-service timeout api-gateway login",
        error_pattern="Login timeout"
    )
    
    candidates = engine.match(signature, [mem1])
    assert len(candidates) == 1
    # Match root cause (0.3), symptom (0.2), pattern (0.1) = 0.6
    assert candidates[0].similarity_score >= 0.6
    assert candidates[0].matched_root_cause is True

def test_unrelated_incident():
    engine = MemoryEngine()
    signature = FailureSignature(
        error_fingerprint="DATABASE_TIMEOUT",
        symptom_service="api-gateway",
        root_cause_service="payment-service",
        error_pattern="Payment failure"
    )
    
    mem1 = FailureMemory(
        id=uuid.uuid4(),
        error_fingerprint="OOM_KILLED",
        root_cause="frontend server out of memory",
        searchable_text="frontend server out of memory",
        error_pattern="Frontend crashed"
    )
    
    candidates = engine.match(signature, [mem1])
    # No matches, score 0 < MIN_THRESHOLD
    assert len(candidates) == 0

def test_deterministic_ranking():
    engine = MemoryEngine()
    signature = FailureSignature(
        error_fingerprint="NULL_OBJECT_ACCESS",
        symptom_service="payment-service",
        root_cause_service="payment-service",
        error_pattern="crash"
    )
    
    id1 = uuid.uuid4()
    id2 = uuid.uuid4()
    mem1 = FailureMemory(
        id=id1,
        error_fingerprint="NULL_OBJECT_ACCESS", # 0.4
        root_cause="payment-service failed", # 0.3
        searchable_text="payment-service", # 0.2
        error_pattern="crash" # 0.1 -> 1.0
    )
    mem2 = FailureMemory(
        id=id2,
        error_fingerprint="NULL_OBJECT_ACCESS", # 0.4
        root_cause="unknown",
        searchable_text="unknown",
        error_pattern="unknown" # -> 0.4
    )
    
    candidates = engine.match(signature, [mem1, mem2])
    assert len(candidates) == 2
    assert candidates[0].memory.id == id1
    assert candidates[1].memory.id == id2
