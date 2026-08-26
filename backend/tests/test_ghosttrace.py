import pytest
from datetime import datetime, timedelta
import uuid

from app.engine.ghosttrace_engine import GhostTraceEngine
from app.db.models import EvidenceEvent

def create_event(service, event_type, status_code=None, error_code=None, req_id=None, time_offset=0):
    return EvidenceEvent(
        id=uuid.uuid4(),
        service_name=service,
        event_type=event_type,
        status_code=status_code,
        error_code=error_code,
        request_id=req_id,
        timestamp=datetime.utcnow() + timedelta(seconds=time_offset)
    )

def test_ghosttrace_scenario_1_clear_chain():
    """
    API 500 -> Payment 503 -> Database timeout
    Expected: Payment/database failure ranked as root-cause candidate.
    """
    engine = GhostTraceEngine()
    req_id = "req-1"
    
    events = [
        create_event("api-gateway", "http", 500, None, req_id, 2),
        create_event("payment-service", "error", 503, None, req_id, 1),
        create_event("postgresql", "database", None, "DATABASE_TIMEOUT", req_id, 0),
    ]
    
    result = engine.reconstruct(events)
    assert result.status == "reconstructed"
    assert result.root_cause_candidate in ["postgresql", "payment-service"]
    assert len(result.nodes) == 3

def test_ghosttrace_scenario_2_missing_evidence():
    """
    Only API 500
    Expected: partial evidence.
    """
    engine = GhostTraceEngine()
    events = [
        create_event("api-gateway", "http", 500, None, "req-1", 0)
    ]
    
    result = engine.reconstruct(events)
    assert result.status == "reconstructed" 
    assert result.root_cause_candidate == "api-gateway"
    
def test_ghosttrace_scenario_3_insufficient_evidence_no_errors():
    """
    No errors
    Expected: partial status.
    """
    engine = GhostTraceEngine()
    events = [
        create_event("api-gateway", "http", 200, None, "req-1", 0)
    ]
    
    result = engine.reconstruct(events)
    assert result.status == "partial"
    assert result.root_cause_candidate is None

def test_ghosttrace_scenario_4_temporal_correlation_without_request_id():
    """
    Temporal correlation without request_id.
    """
    engine = GhostTraceEngine()
    events = [
        create_event("api-gateway", "http", 500, None, None, 1),
        create_event("payment-service", "error", 503, None, None, 0),
        create_event("postgresql", "database", None, "DATABASE_TIMEOUT", None, 100), # far outside window
    ]
    
    result = engine.reconstruct(events)
    assert result.status == "reconstructed"
    assert result.root_cause_candidate == "payment-service"

def test_ghosttrace_scenario_5_determinism():
    """
    Same input -> same output.
    """
    engine = GhostTraceEngine()
    events = [
        create_event("api-gateway", "http", 500, None, "req-1", 2),
        create_event("payment-service", "error", 503, None, "req-1", 1),
    ]
    
    res1 = engine.reconstruct(events)
    res2 = engine.reconstruct(events)
    
    assert res1.root_cause_candidate == res2.root_cause_candidate
    assert len(res1.nodes) == len(res2.nodes)

def test_ghosttrace_scenario_6_missing_metadata():
    """
    Missing optional metadata does not crash.
    """
    engine = GhostTraceEngine()
    # Empty events
    events = [
        EvidenceEvent(id=uuid.uuid4(), event_type="test", timestamp=datetime.utcnow())
    ]
    result = engine.reconstruct(events)
    assert result.status == "partial"
