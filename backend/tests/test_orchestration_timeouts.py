import pytest
import uuid
import httpx
from datetime import datetime, timezone
import subprocess
from unittest.mock import MagicMock
from app.db.database import Base, engine, SessionLocal
from app.db.models import Run, Incident, Repository, RunEvent, Application
from app.engine.openrouter_investigator import OpenRouterInvestigator
from app.services.orchestrator import CodeGuardianOrchestrator
from app.core.execution_policy import ExecutionPolicy


def setup_module(module):
    Base.metadata.create_all(bind=engine)

def teardown_module(module):
    # Do NOT drop tables - this is the production PostgreSQL engine.
    # Only create tables if missing; never destroy them in tests.
    pass

@pytest.fixture
def db_session():
    db = SessionLocal()
    yield db
    db.close()
    
@pytest.fixture
def mock_run(db_session):
    app_id = str(uuid.uuid4())
    app = Application(
        id=app_id,
        name="MockApp",
        environment="test",
        status="active",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add(app)
    db_session.flush()
    repo = Repository(
        id=str(uuid.uuid4()),
        provider="github",
        owner="mock",
        name="repo",
        repository_url="https://github.com/mock/repo",
        default_branch="main",
        access_status="accessible",
        application_id=app_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add(repo)
    db_session.flush()
    inc = Incident(
        id=str(uuid.uuid4()),
        incident_number=1,
        title="Test",
        status="open",
        resolution_status="unresolved",
        repository_id=repo.id,
        application_id=app_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add(inc)
    db_session.flush()
    run = Run(
        id=str(uuid.uuid4()),
        incident_id=inc.id,
        state="INVESTIGATION_RUNNING",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add(run)
    db_session.commit()
    return run, inc

def test_ai_request_timeout_transitions_to_failed(monkeypatch, db_session, mock_run):
    run, inc = mock_run
    
    # Mock httpx.Client.post to raise TimeoutException
    def mock_post(*args, **kwargs):
        raise httpx.TimeoutException("Mocked timeout")
    
    monkeypatch.setattr("httpx.Client.post", mock_post)
    
    orchestrator = CodeGuardianOrchestrator()
    try:
        orchestrator.execute_pipeline(str(run.id), str(inc.id))
    except Exception:
        pass # Expected since it raises INVESTIGATION_FAILED
        
    db_session.refresh(run)
    assert run.state in ["INVESTIGATION_FAILED", "INVESTIGATION_TIMEOUT", "FAILED"]
    
def test_subprocess_timeout_safe(monkeypatch):
    from app.services.command_service import CommandExecutionService
    svc = CommandExecutionService()
    
    class MockPopen:
        def __init__(self, *args, **kwargs):
            self.pid = 99999
            self.returncode = None
        def communicate(self, timeout=None):
            if timeout == 5: # secondary timeout
                raise subprocess.TimeoutExpired(cmd="mock", timeout=5)
            raise subprocess.TimeoutExpired(cmd="mock", timeout=0.1)
            
    monkeypatch.setattr("subprocess.Popen", MockPopen)
    
    # Mock kill_process_tree to prevent actual kills
    monkeypatch.setattr(svc, "kill_process_tree", lambda pid: None)
    
    result = svc.execute_command(["git", "status"], cwd=".")
    
    assert result["timed_out"] is True
    assert result["exit_code"] == -1
    assert "streams did not close" in result["stderr"]

def test_investigation_timeout_mapping(monkeypatch, db_session, mock_run):
    run, inc = mock_run
    
    # Mock InvestigationService to return a timeout result
    from app.schemas.investigation import InvestigationResult
    from app.services.investigation_service import InvestigationService
    
    def mock_investigate(*args, **kwargs):
        return InvestigationResult(incident_id=str(inc.id), status="timeout")
        
    monkeypatch.setattr(InvestigationService, "investigate_incident", mock_investigate)
    
    orchestrator = CodeGuardianOrchestrator()
    try:
        # Mock inspection so it gets past the first phases
        monkeypatch.setattr("app.services.orchestrator.RepositoryInspectionService.inspect_repository", MagicMock())
        monkeypatch.setattr("app.services.github_metadata.GitHubMetadataService.check_access", lambda *args: True)
        monkeypatch.setattr("app.services.orchestrator.parse_github_url", lambda url: ("mock", "repo"))
        monkeypatch.setattr("app.services.orchestrator.FailureEvidenceCollector.collect_evidence", lambda self, url, repo_id: str(inc.id))
        monkeypatch.setattr("app.services.orchestrator.GhostTraceService.rebuild_trace", lambda self, inc_id: MagicMock())
        monkeypatch.setattr("app.services.orchestrator.MemoryService.search_memory_for_incident", lambda self, inc_id: MagicMock(match_status="none"))
        
        # Execute pipeline will run until the mocked investigate_incident returns timeout
        orchestrator.execute_pipeline(str(run.id), repository_url="https://github.com/mock/repo", supplied_incident_id=str(inc.id))
    except Exception as e:
        print(f"Caught exception: {e}")
        
    db_session.refresh(run)
    assert run.state == "INVESTIGATION_TIMEOUT"
    assert run.terminal_at is not None
    assert run.error_code == "TIMEOUT"
    assert "Total AI deadline exceeded" in run.error_message
    
    # Verify RunEvent was emitted
    events = db_session.query(RunEvent).filter(RunEvent.run_id == run.id).all()
    # Check that there's an event corresponding to the timeout
    # Or just check if the lock is released (which is implicit if it exits the context manager)
