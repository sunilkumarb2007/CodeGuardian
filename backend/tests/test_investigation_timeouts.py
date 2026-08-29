import pytest
import time
import json
import httpx
import uuid
from unittest.mock import MagicMock
from app.engine.openrouter_investigator import OpenRouterInvestigator
from app.core.execution_policy import ExecutionPolicy

def test_streaming_response_exceeds_deadline(monkeypatch):
    """
    Test that a streaming response that yields chunks continuously will be
    interrupted by the wall-clock deadline, even if each chunk arrives within
    the httpx read timeout.
    """
    investigator = OpenRouterInvestigator()
    investigator.api_key = "fake_key"
    
    # We will simulate time passing during chunk iteration.
    mock_monotonic_time = [0.0]
    
    def fake_monotonic():
        return mock_monotonic_time[0]
    
    monkeypatch.setattr(time, "monotonic", fake_monotonic)
    monkeypatch.setattr(time, "time", fake_monotonic)
    
    class MockStreamResponse:
        def __init__(self):
            self.status_code = 200
        def raise_for_status(self):
            pass
        def iter_bytes(self, chunk_size=8192):
            # Yield chunks, advancing the clock each time.
            for i in range(200):
                # Each chunk advances time by 2 seconds
                mock_monotonic_time[0] += 2.0
                yield b"{\"status\":\"running\"}"
        def close(self):
            pass
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            self.close()

    def mock_stream(*args, **kwargs):
        return MockStreamResponse()
    
    monkeypatch.setattr("httpx.Client.stream", mock_stream)
    
    # Setup deadline 100 seconds from "now" (which is 0.0)
    deadline = 100.0
    
    with pytest.raises(RuntimeError) as exc_info:
        investigator.investigate("test prompt", deadline=deadline)
        
    assert "TIMEOUT" in str(exc_info.value)
    # The clock should have advanced just past the deadline (50 chunks * 2s = 100s)
    # Plus one more check that fails.
    assert mock_monotonic_time[0] >= deadline

def test_deadline_propagates_across_attempts(monkeypatch):
    """
    Test that the orchestrator's single absolute deadline is passed to the 
    InvestigationService and then to the OpenRouterInvestigator without resetting.
    """
    from app.services.investigation_service import InvestigationService
    from app.schemas.investigation import InvestigationResult
    
    # We will simulate time passing.
    mock_monotonic_time = [1000.0]
    def fake_monotonic():
        return mock_monotonic_time[0]
    
    monkeypatch.setattr(time, "monotonic", fake_monotonic)
    
    inv_svc = InvestigationService()
    
    # Mock the repositories and services used inside _get_context
    monkeypatch.setattr("app.services.investigation_service.IncidentRepository.get_by_id", lambda self, id: MagicMock(repository_id="repo1"))
    monkeypatch.setattr("app.services.investigation_service.EvidenceRepository.get_by_incident_id", lambda self, id: MagicMock())
    monkeypatch.setattr("app.services.investigation_service.TraceRepository.get_by_incident_id", lambda self, id: MagicMock(id="trace1"))
    monkeypatch.setattr("app.services.investigation_service.RepositoryFileRepository.get_files_by_repository_id", lambda self, id: [MagicMock(file_path="f1", source_snapshot="code")])
    monkeypatch.setattr("app.services.investigation_service.MemoryService.search_memory_for_incident", lambda self, id: MagicMock())
    monkeypatch.setattr("app.services.investigation_service.InvestigationContextBuilder.extract_relevant_source_files", lambda e, t, f: f)
    monkeypatch.setattr("app.services.investigation_service.InvestigationPromptBuilder.build_prompt", lambda **kwargs: "prompt")
    monkeypatch.setattr("app.db.database.SessionLocal", MagicMock())
    
    # Mock the LLM engine to simulate consuming time
    class MockEngine:
        def __init__(self):
            self.provider_name = "mock"
            self.calls = 0
            
        def investigate(self, prompt, deadline=None):
            self.calls += 1
            if self.calls == 1:
                # Attempt 1 consumes 100 seconds
                mock_monotonic_time[0] += 100.0
                return None # Simulates failure, triggering retry
            elif self.calls == 2:
                # Attempt 2 consumes 90 seconds
                mock_monotonic_time[0] += 90.0
                return None
            else:
                return InvestigationResult(incident_id="test", status="completed")

    mock_engine = MockEngine()
    monkeypatch.setattr(inv_svc, "openrouter_engine", mock_engine)
    monkeypatch.setattr(inv_svc, "deepseek_engine", mock_engine)
    monkeypatch.setattr(inv_svc, "sarvam_engine", mock_engine)
    monkeypatch.setattr(inv_svc, "db", MagicMock())
    monkeypatch.setattr("app.core.config.settings.openrouter_api_key", "fake")
    monkeypatch.setattr("app.core.config.settings.deepseek_api_key", "fake")
    monkeypatch.setattr("app.core.config.settings.sarvam_api_key", "fake")
    
    # Deadline is 180s from now (1180.0)
    deadline = mock_monotonic_time[0] + 180.0
    test_inc_id = str(uuid.uuid4())

    # Attempt 1 -> called, takes 100s (time is now 1100). Fails.
    # We invoke attempt 1 manually.
    res1 = inv_svc.investigate_incident(test_inc_id, attempt=1, deadline=deadline)
    assert res1.status in ("error_llm_failed", "OPENROUTER_EMPTY_RESPONSE")
    assert mock_engine.calls == 1
    
    # Attempt 2 -> called, takes 90s (time is now 1190). Fails.
    res2 = inv_svc.investigate_incident(test_inc_id, attempt=2, deadline=deadline)
    assert res2.status in ("error_llm_failed", "OPENROUTER_EMPTY_RESPONSE")
    assert mock_engine.calls == 2
    
    # Attempt 3 -> called, but time is 1190 > 1180. Should timeout immediately before calling LLM.
    res3 = inv_svc.investigate_incident(test_inc_id, attempt=3, deadline=deadline)
    assert res3.status == "timeout"
    # Engine investigate should NOT be called again
    assert mock_engine.calls == 2
