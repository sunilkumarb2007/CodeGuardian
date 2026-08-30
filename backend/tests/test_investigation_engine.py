import pytest
import uuid
from app.engine.prompt_builder import InvestigationPromptBuilder
from app.db import models
from app.schemas.memory import MemorySearchResponse, MemoryMatchResponse, FailureMemoryResponse

def test_prompt_generation_with_memory_and_source():
    incident = models.Incident(
        id=uuid.uuid4(),
        title="HTTP 500 in Checkout",
        description="Checkout fails",
        status="open"
    )
    
    evidence = [
        models.EvidenceEvent(
            id=uuid.uuid4(),
            service_name="api-gateway",
            event_type="log",
            http_method="POST",
            endpoint="/checkout",
            status_code=500,
            error_code=None,
            error_message="Internal Server Error"
        )
    ]
    
    trace = models.FailureTrace(
        id=uuid.uuid4(),
        symptom_service="api-gateway",
        root_cause_candidate="payment-service",
        reasoning_summary="Payment failed downstream"
    )
    
    memory = MemorySearchResponse(
        incident_id=incident.id,
        match_status="match_found",
        matches=[
            MemoryMatchResponse(
                id=uuid.uuid4(),
                incident_id=incident.id,
                memory_id=uuid.uuid4(),
                similarity_score=0.85,
                match_reason="Pattern Match",
                matched_error_pattern=True,
                matched_root_cause=False,
                matched_affected_files=False,
                matched_code_context=False,
                verification_status="pending",
                created_at="2026-01-01T00:00:00",
                memory=FailureMemoryResponse(
                    id=uuid.uuid4(),
                    incident_id=uuid.uuid4(),
                    application_id=uuid.uuid4(),
                    error_pattern="Payment failure null object",
                    root_cause="Null object access",
                    affected_files=[],
                    code_change="Added null check",
                    memory_status="verified",
                    created_at="2026-01-01T00:00:00"
                )
            )
        ]
    )
    
    source_files = [
        models.RepositoryFile(
            id=uuid.uuid4(),
            file_path="src/payment.py",
            source_snapshot="def process_payment(obj):\n    obj.pay()"
        )
    ]
    
    prompt = InvestigationPromptBuilder.build_prompt(
        incident=incident,
        evidence=evidence,
        trace=trace,
        memory_response=memory,
        source_files=source_files
    )
    
    # Assertions
    assert "Incident: HTTP 500 in Checkout" in prompt
    assert "- api-gateway log Internal Server Error" in prompt
    assert "GhostTrace Candidate: payment-service" in prompt
    assert "File: src/payment.py" in prompt
    assert "def process_payment(obj):" in prompt
    assert "Return strictly this compact JSON object" in prompt

def test_prompt_generation_without_source():
    incident = models.Incident(
        id=uuid.uuid4(),
        title="HTTP 500",
        description="Fails",
        status="open"
    )
    
    trace = models.FailureTrace(
        id=uuid.uuid4(),
        symptom_service="api-gateway",
        root_cause_candidate="payment-service",
        reasoning_summary="Error"
    )
    
    prompt = InvestigationPromptBuilder.build_prompt(
        incident=incident,
        evidence=[],
        trace=trace,
        memory_response=MemorySearchResponse(incident_id=incident.id, match_status="no_match"),
        source_files=[]
    )
    
    assert "Incident: HTTP 500" in prompt
    assert "GhostTrace Candidate: payment-service" in prompt
