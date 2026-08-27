from datetime import timezone
import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
import json
import time

from app.main import app
from app.db.database import get_db, Base
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB

@compiles(JSONB, 'sqlite')
def compile_jsonb(type_, compiler, **kw):
    return 'JSON'

from sqlalchemy.dialects.postgresql import ARRAY
@compiles(ARRAY, 'sqlite')
def compile_array(type_, compiler, **kw):
    return 'JSON'

from app.core.config import settings
from app.db.models import Run

# Setup deterministic DB for tests — use shared in-memory SQLite to avoid disk I/O errors
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

import app.db.database
app.db.database.SessionLocal = TestingSessionLocal
import app.services.orchestrator
app.services.orchestrator.SessionLocal = TestingSessionLocal

# Create schema once at module level
Base.metadata.create_all(bind=engine)

@pytest.fixture(autouse=True)
def setup_db():
    # Wipe all data between tests without dropping/recreating schema
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
    yield


def wait_for_state(run_id: str, state: str, timeout: int = 10):
    for _ in range(timeout * 2):
        res = client.get(f"/api/orchestration/runs/{run_id}")
        if res.status_code == 200:
            data = res.json()
            if data["status"] == state or data["status"] in ["FAILED", "REJECTED", "DELIVERY_AUTH_REQUIRED", "HUMAN_REJECTED"]:
                return data
        time.sleep(0.5)
    return client.get(f"/api/orchestration/runs/{run_id}").json()

def test_test_1_invalid_repository():
    response = client.post("/api/orchestration/run", json={"repository_url": "invalid"})
    assert response.status_code == 200
    run_id = response.json()["run_id"]
    
    data = wait_for_state(run_id, "FAILED")
    assert data["status"] == "FAILED"
    assert "Invalid GitHub URL" in data.get("error", "")

def test_test_2_normal_repository(monkeypatch):
    def mock_clone(*args, **kwargs):
        pass
    def mock_inspect(*args, **kwargs):
        from app.schemas.orchestration import InspectionResult, ArchitectureSummary
        return InspectionResult(
            repository_url="https://github.com/CodeGuardian-AI/CodeGuardian",
            architecture=ArchitectureSummary(
                tech_stack=["python", "fastapi"],
                language="python",
                framework="fastapi",
                build_system="pip",
                test_framework="pytest",
                entry_points=["main.py"]
            ),
            static_analysis_passed=True,
            build_passed=True,
            test_passed=True
        )
    def mock_monitor(*args, **kwargs):
        return "NO_PREPARED_FAILURE"

    import app.services.git_workspace
    import app.services.inspection_service
    import app.services.failure_evidence_collector
    import app.services.github_metadata

    monkeypatch.setattr(app.services.git_workspace.GitWorkspace, "clone", mock_clone)
    monkeypatch.setattr(app.services.inspection_service.RepositoryInspectionService, "inspect_repository", mock_inspect)
    monkeypatch.setattr(app.services.failure_evidence_collector.FailureEvidenceCollector, "collect_evidence", mock_monitor)
    monkeypatch.setattr(app.services.github_metadata.GitHubMetadataService, "check_access", lambda *args, **kwargs: True)

    response = client.post("/api/orchestration/run", json={"repository_url": "https://github.com/CodeGuardian-AI/CodeGuardian"})
    assert response.status_code == 200
    run_id = response.json()["run_id"]
    
    data = wait_for_state(run_id, "NO_FAILURE_EVIDENCE") # Orchestrator stops here if no incident/evidence
    assert data["status"] == "NO_FAILURE_EVIDENCE"


def test_test_3_java_api_check(monkeypatch):
    def mock_clone(*args, **kwargs):
        pass
    def mock_inspect(*args, **kwargs):
        from app.schemas.orchestration import InspectionResult, ArchitectureSummary
        return InspectionResult(
            repository_url="https://github.com/CodeGuardian-AI/JavaAPICheck",
            architecture=ArchitectureSummary(
                tech_stack=["java", "spring"],
                language="java",
                framework="spring",
                build_system="maven",
                test_framework="junit",
                entry_points=["Main.java"]
            ),
            static_analysis_passed=True,
            build_passed=True,
            test_passed=True
        )
    def mock_monitor(*args, **kwargs):
        import uuid
        return str(uuid.uuid4())

    def mock_monitor(*args, **kwargs):
        import uuid
        return str(uuid.uuid4())

    def mock_trace(*args, **kwargs):
        pass

    def mock_investigate(*args, **kwargs):
        from app.schemas.investigation import InvestigationResult, RootCauseAnalysis, HistoricalReference, PatchCandidateModel
        from app.db.models import Patch
        from app.db.database import SessionLocal
        from datetime import datetime
        import uuid
        incident_id = kwargs.get('incident_id') or args[1]
        
        # Save a patch to DB so orchestrator doesn't crash looking for it
        with SessionLocal() as db:
            p = Patch(
                id=uuid.uuid4(), incident_id=uuid.UUID(incident_id), diff="x", patch_number=1,
                affected_files=["x"], generated_by="mock",
                status="unvalidated", created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)
            )
            db.add(p)
            db.commit()
            
        return InvestigationResult(
            incident_id=incident_id,
            status="completed",
            root_cause=RootCauseAnalysis(service="x", summary="x", affected_file="x"),
            historical_reference=HistoricalReference(found=True, memory_status="verified", applicability="reference_only"),
            patch_candidate=PatchCandidateModel(status="unvalidated", files_changed=["x"], diff="x", explanation="x"),
            verification_requirements=["x"]
        )
        
    def mock_replay(*args, **kwargs):
        return "REPLAY_CHANGED_BEHAVIOR", {}, {}

    import app.services.git_workspace
    import app.services.inspection_service
    import app.services.failure_evidence_collector
    import app.services.ghosttrace_service
    import app.services.investigation_service
    import app.engine.replay_engine
    import app.services.github_metadata

    monkeypatch.setattr(app.services.git_workspace.GitWorkspace, "clone", mock_clone)
    monkeypatch.setattr(app.services.inspection_service.RepositoryInspectionService, "inspect_repository", mock_inspect)
    monkeypatch.setattr(app.services.failure_evidence_collector.FailureEvidenceCollector, "collect_evidence", mock_monitor)
    monkeypatch.setattr(app.services.ghosttrace_service.GhostTraceService, "rebuild_trace", mock_trace)
    monkeypatch.setattr(app.services.investigation_service.InvestigationService, "investigate_incident", mock_investigate)
    monkeypatch.setattr(app.engine.replay_engine.ReplayEngine, "run_replay", mock_replay)
    monkeypatch.setattr(app.services.github_metadata.GitHubMetadataService, "check_access", lambda *args, **kwargs: True)

    response = client.post("/api/orchestration/run", json={"repository_url": "https://github.com/CodeGuardian-AI/JavaAPICheck"})
    assert response.status_code == 200
    run_id = response.json()["run_id"]
    
    # Wait for the pipeline to reach WAITING_FOR_APPROVAL (or FAILED if it errors out)
    data = wait_for_state(run_id, "WAITING_FOR_APPROVAL")
    assert data["status"] == "WAITING_FOR_APPROVAL"

def test_test_4_openrouter_unavailable(monkeypatch):
    def mock_clone(*args, **kwargs):
        pass
    def mock_inspect(*args, **kwargs):
        from app.schemas.orchestration import InspectionResult, ArchitectureSummary
        return InspectionResult(
            repository_url="https://github.com/CodeGuardian-AI/TimeoutCheck",
            architecture=ArchitectureSummary(tech_stack=["node"], language="javascript", framework="express", build_system="npm", test_framework="jest", entry_points=["index.js"]),
            static_analysis_passed=True, build_passed=True, test_passed=True
        )
    def mock_monitor(*args, **kwargs):
        import uuid
        return str(uuid.uuid4())
    def mock_trace(*args, **kwargs):
        pass
    def mock_investigate(*args, **kwargs):
        from app.schemas.investigation import InvestigationResult
        incident_id = kwargs.get('incident_id') or args[1]
        return InvestigationResult(incident_id=incident_id, status="timeout")

    import app.services.git_workspace
    import app.services.inspection_service
    import app.services.failure_evidence_collector
    import app.services.ghosttrace_service
    import app.services.investigation_service
    import app.services.github_metadata

    monkeypatch.setattr(app.services.git_workspace.GitWorkspace, "clone", mock_clone)
    monkeypatch.setattr(app.services.inspection_service.RepositoryInspectionService, "inspect_repository", mock_inspect)
    monkeypatch.setattr(app.services.failure_evidence_collector.FailureEvidenceCollector, "collect_evidence", mock_monitor)
    monkeypatch.setattr(app.services.ghosttrace_service.GhostTraceService, "rebuild_trace", mock_trace)
    monkeypatch.setattr(app.services.investigation_service.InvestigationService, "investigate_incident", mock_investigate)
    monkeypatch.setattr(app.services.github_metadata.GitHubMetadataService, "check_access", lambda *args, **kwargs: True)

    response = client.post("/api/orchestration/run", json={"repository_url": "https://github.com/CodeGuardian-AI/TimeoutCheck"})
    assert response.status_code == 200
    run_id = response.json()["run_id"]

    data = wait_for_state(run_id, "INVESTIGATION_TIMEOUT")
    assert data["status"] == "INVESTIGATION_TIMEOUT"

def test_test_5_openrouter_malformed(monkeypatch):
    def mock_clone(*args, **kwargs):
        pass
    def mock_inspect(*args, **kwargs):
        from app.schemas.orchestration import InspectionResult, ArchitectureSummary
        return InspectionResult(
            repository_url="https://github.com/CodeGuardian-AI/MalformedCheck",
            architecture=ArchitectureSummary(tech_stack=["node"], language="javascript", framework="express", build_system="npm", test_framework="jest", entry_points=["index.js"]),
            static_analysis_passed=True, build_passed=True, test_passed=True
        )
    def mock_monitor(*args, **kwargs):
        import uuid
        return str(uuid.uuid4())
    def mock_trace(*args, **kwargs):
        pass
    def mock_investigate(*args, **kwargs):
        from app.schemas.investigation import InvestigationResult
        incident_id = kwargs.get('incident_id') or args[1]
        return InvestigationResult(incident_id=incident_id, status="schema_error")

    import app.services.git_workspace
    import app.services.inspection_service
    import app.services.failure_evidence_collector
    import app.services.ghosttrace_service
    import app.services.investigation_service
    import app.services.github_metadata

    monkeypatch.setattr(app.services.git_workspace.GitWorkspace, "clone", mock_clone)
    monkeypatch.setattr(app.services.inspection_service.RepositoryInspectionService, "inspect_repository", mock_inspect)
    monkeypatch.setattr(app.services.failure_evidence_collector.FailureEvidenceCollector, "collect_evidence", mock_monitor)
    monkeypatch.setattr(app.services.ghosttrace_service.GhostTraceService, "rebuild_trace", mock_trace)
    monkeypatch.setattr(app.services.investigation_service.InvestigationService, "investigate_incident", mock_investigate)
    monkeypatch.setattr(app.services.github_metadata.GitHubMetadataService, "check_access", lambda *args, **kwargs: True)

    response = client.post("/api/orchestration/run", json={"repository_url": "https://github.com/CodeGuardian-AI/MalformedCheck"})
    assert response.status_code == 200
    run_id = response.json()["run_id"]

    data = wait_for_state(run_id, "INVESTIGATION_SCHEMA_ERROR")
    assert data["status"] == "INVESTIGATION_SCHEMA_ERROR"

def test_test_6_unsafe_patch(monkeypatch):
    def mock_clone(*args, **kwargs): pass
    def mock_inspect(*args, **kwargs):
        from app.schemas.orchestration import InspectionResult, ArchitectureSummary
        return InspectionResult(repository_url="https://github.com/CodeGuardian-AI/UnsafeCheck", architecture=ArchitectureSummary(tech_stack=["node"], language="javascript", framework="express", build_system="npm", test_framework="jest", entry_points=["index.js"]), static_analysis_passed=True, build_passed=True, test_passed=True)
    def mock_monitor(*args, **kwargs):
        import uuid; return str(uuid.uuid4())
    def mock_trace(*args, **kwargs): pass
    def mock_investigate(*args, **kwargs):
        from app.schemas.investigation import InvestigationResult, RootCauseAnalysis, HistoricalReference, PatchCandidateModel
        import uuid; incident_id = kwargs.get('incident_id') or args[1]
        return InvestigationResult(incident_id=incident_id, status="PATCH_PATH_UNSAFE")

    import app.services.git_workspace
    import app.services.inspection_service
    import app.services.failure_evidence_collector
    import app.services.ghosttrace_service
    import app.services.investigation_service
    import app.services.github_metadata
    monkeypatch.setattr(app.services.git_workspace.GitWorkspace, "clone", mock_clone)
    monkeypatch.setattr(app.services.inspection_service.RepositoryInspectionService, "inspect_repository", mock_inspect)
    monkeypatch.setattr(app.services.failure_evidence_collector.FailureEvidenceCollector, "collect_evidence", mock_monitor)
    monkeypatch.setattr(app.services.ghosttrace_service.GhostTraceService, "rebuild_trace", mock_trace)
    monkeypatch.setattr(app.services.investigation_service.InvestigationService, "investigate_incident", mock_investigate)
    monkeypatch.setattr(app.services.github_metadata.GitHubMetadataService, "check_access", lambda *args, **kwargs: True)

    response = client.post("/api/orchestration/run", json={"repository_url": "https://github.com/CodeGuardian-AI/UnsafeCheck"})
    assert response.status_code == 200
    run_id = response.json()["run_id"]
    data = wait_for_state(run_id, "PATCH_PATH_UNSAFE")
    assert data["status"] == "PATCH_PATH_UNSAFE"

def test_test_7_patch_doesnt_apply(monkeypatch):
    def mock_clone(*args, **kwargs): pass
    def mock_inspect(*args, **kwargs):
        from app.schemas.orchestration import InspectionResult, ArchitectureSummary
        return InspectionResult(repository_url="https://github.com/CodeGuardian-AI/ApplyCheck", architecture=ArchitectureSummary(tech_stack=["node"], language="javascript", framework="express", build_system="npm", test_framework="jest", entry_points=["index.js"]), static_analysis_passed=True, build_passed=True, test_passed=True)
    def mock_monitor(*args, **kwargs):
        import uuid; return str(uuid.uuid4())
    def mock_trace(*args, **kwargs): pass
    def mock_investigate(*args, **kwargs):
        from app.schemas.investigation import InvestigationResult, RootCauseAnalysis, HistoricalReference, PatchCandidateModel
        from app.db.models import Patch
        from app.db.database import SessionLocal
        from datetime import datetime
        import uuid
        incident_id = kwargs.get('incident_id') or args[1]
        with SessionLocal() as db:
            p = Patch(id=uuid.uuid4(), incident_id=uuid.UUID(incident_id), diff="x", patch_number=1, affected_files=["x"], generated_by="mock", status="unvalidated", created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
            db.add(p)
            db.commit()
        return InvestigationResult(incident_id=incident_id, status="completed", root_cause=RootCauseAnalysis(service="x", summary="x", affected_file="x"), historical_reference=HistoricalReference(found=True, memory_status="verified", applicability="reference_only"), patch_candidate=PatchCandidateModel(status="unvalidated", files_changed=["x"], diff="x", explanation="x"), verification_requirements=["x"])
    def mock_replay(*args, **kwargs): return "PATCH_APPLY_FAILED", {}, {}

    import app.services.git_workspace
    import app.services.inspection_service
    import app.services.failure_evidence_collector
    import app.services.ghosttrace_service
    import app.services.investigation_service
    import app.engine.replay_engine
    import app.services.github_metadata
    monkeypatch.setattr(app.services.git_workspace.GitWorkspace, "clone", mock_clone)
    monkeypatch.setattr(app.services.inspection_service.RepositoryInspectionService, "inspect_repository", mock_inspect)
    monkeypatch.setattr(app.services.failure_evidence_collector.FailureEvidenceCollector, "collect_evidence", mock_monitor)
    monkeypatch.setattr(app.services.ghosttrace_service.GhostTraceService, "rebuild_trace", mock_trace)
    monkeypatch.setattr(app.services.investigation_service.InvestigationService, "investigate_incident", mock_investigate)
    monkeypatch.setattr(app.engine.replay_engine.ReplayEngine, "run_replay", mock_replay)
    monkeypatch.setattr(app.services.github_metadata.GitHubMetadataService, "check_access", lambda *args, **kwargs: True)

    response = client.post("/api/orchestration/run", json={"repository_url": "https://github.com/CodeGuardian-AI/ApplyCheck"})
    assert response.status_code == 200
    run_id = response.json()["run_id"]
    data = wait_for_state(run_id, "PATCH_APPLY_FAILED")
    assert data["status"] == "PATCH_APPLY_FAILED"

def test_test_8_baseline_doesnt_reproduce(monkeypatch):
    def mock_clone(*args, **kwargs): pass
    def mock_inspect(*args, **kwargs):
        from app.schemas.orchestration import InspectionResult, ArchitectureSummary
        return InspectionResult(repository_url="https://github.com/CodeGuardian-AI/BaselineCheck", architecture=ArchitectureSummary(tech_stack=["node"], language="javascript", framework="express", build_system="npm", test_framework="jest", entry_points=["index.js"]), static_analysis_passed=True, build_passed=True, test_passed=True)
    def mock_monitor(*args, **kwargs):
        import uuid; return str(uuid.uuid4())
    def mock_trace(*args, **kwargs): pass
    def mock_investigate(*args, **kwargs):
        from app.schemas.investigation import InvestigationResult, RootCauseAnalysis, HistoricalReference, PatchCandidateModel
        from app.db.models import Patch
        from app.db.database import SessionLocal
        from datetime import datetime
        import uuid
        incident_id = kwargs.get('incident_id') or args[1]
        with SessionLocal() as db:
            p = Patch(id=uuid.uuid4(), incident_id=uuid.UUID(incident_id), diff="x", patch_number=1, affected_files=["x"], generated_by="mock", status="unvalidated", created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
            db.add(p)
            db.commit()
        return InvestigationResult(incident_id=incident_id, status="completed", root_cause=RootCauseAnalysis(service="x", summary="x", affected_file="x"), historical_reference=HistoricalReference(found=True, memory_status="verified", applicability="reference_only"), patch_candidate=PatchCandidateModel(status="unvalidated", files_changed=["x"], diff="x", explanation="x"), verification_requirements=["x"])
    def mock_replay(*args, **kwargs): return "BASELINE_FAILURE_NOT_REPRODUCED", {}, {}

    import app.services.git_workspace
    import app.services.inspection_service
    import app.services.failure_evidence_collector
    import app.services.ghosttrace_service
    import app.services.investigation_service
    import app.engine.replay_engine
    import app.services.github_metadata
    monkeypatch.setattr(app.services.git_workspace.GitWorkspace, "clone", mock_clone)
    monkeypatch.setattr(app.services.inspection_service.RepositoryInspectionService, "inspect_repository", mock_inspect)
    monkeypatch.setattr(app.services.failure_evidence_collector.FailureEvidenceCollector, "collect_evidence", mock_monitor)
    monkeypatch.setattr(app.services.ghosttrace_service.GhostTraceService, "rebuild_trace", mock_trace)
    monkeypatch.setattr(app.services.investigation_service.InvestigationService, "investigate_incident", mock_investigate)
    monkeypatch.setattr(app.engine.replay_engine.ReplayEngine, "run_replay", mock_replay)
    monkeypatch.setattr(app.services.github_metadata.GitHubMetadataService, "check_access", lambda *args, **kwargs: True)

    response = client.post("/api/orchestration/run", json={"repository_url": "https://github.com/CodeGuardian-AI/BaselineCheck"})
    assert response.status_code == 200
    run_id = response.json()["run_id"]
    data = wait_for_state(run_id, "BASELINE_FAILURE_NOT_REPRODUCED")
    assert data["status"] == "BASELINE_FAILURE_NOT_REPRODUCED"

def test_test_9_patch_fails_validation(monkeypatch):
    def mock_clone(*args, **kwargs): pass
    def mock_inspect(*args, **kwargs):
        from app.schemas.orchestration import InspectionResult, ArchitectureSummary
        return InspectionResult(repository_url="https://github.com/CodeGuardian-AI/ValidationCheck", architecture=ArchitectureSummary(tech_stack=["node"], language="javascript", framework="express", build_system="npm", test_framework="jest", entry_points=["index.js"]), static_analysis_passed=True, build_passed=True, test_passed=True)
    def mock_monitor(*args, **kwargs):
        import uuid; return str(uuid.uuid4())
    def mock_trace(*args, **kwargs): pass
    def mock_investigate(*args, **kwargs):
        from app.schemas.investigation import InvestigationResult, RootCauseAnalysis, HistoricalReference, PatchCandidateModel
        from app.db.models import Patch
        from app.db.database import SessionLocal
        from datetime import datetime
        import uuid
        incident_id = kwargs.get('incident_id') or args[1]
        with SessionLocal() as db:
            p = Patch(id=uuid.uuid4(), incident_id=uuid.UUID(incident_id), diff="x", patch_number=1, affected_files=["x"], generated_by="mock", status="unvalidated", created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
            db.add(p)
            db.commit()
        return InvestigationResult(incident_id=incident_id, status="completed", root_cause=RootCauseAnalysis(service="x", summary="x", affected_file="x"), historical_reference=HistoricalReference(found=True, memory_status="verified", applicability="reference_only"), patch_candidate=PatchCandidateModel(status="unvalidated", files_changed=["x"], diff="x", explanation="x"), verification_requirements=["x"])
    def mock_replay(*args, **kwargs): return "REPLAY_FAILURE_PERSISTS", {}, {}

    import app.services.git_workspace
    import app.services.inspection_service
    import app.services.failure_evidence_collector
    import app.services.ghosttrace_service
    import app.services.investigation_service
    import app.engine.replay_engine
    import app.services.github_metadata
    monkeypatch.setattr(app.services.git_workspace.GitWorkspace, "clone", mock_clone)
    monkeypatch.setattr(app.services.inspection_service.RepositoryInspectionService, "inspect_repository", mock_inspect)
    monkeypatch.setattr(app.services.failure_evidence_collector.FailureEvidenceCollector, "collect_evidence", mock_monitor)
    monkeypatch.setattr(app.services.ghosttrace_service.GhostTraceService, "rebuild_trace", mock_trace)
    monkeypatch.setattr(app.services.investigation_service.InvestigationService, "investigate_incident", mock_investigate)
    monkeypatch.setattr(app.engine.replay_engine.ReplayEngine, "run_replay", mock_replay)
    monkeypatch.setattr(app.services.github_metadata.GitHubMetadataService, "check_access", lambda *args, **kwargs: True)

    response = client.post("/api/orchestration/run", json={"repository_url": "https://github.com/CodeGuardian-AI/ValidationCheck"})
    assert response.status_code == 200
    run_id = response.json()["run_id"]
    data = wait_for_state(run_id, "REPAIR_EXHAUSTED")
    assert data["status"] == "REPAIR_EXHAUSTED"

def test_test_10_delivery_rejection(monkeypatch):
    def mock_clone(*args, **kwargs): pass
    def mock_inspect(*args, **kwargs):
        from app.schemas.orchestration import InspectionResult, ArchitectureSummary
        return InspectionResult(repository_url="https://github.com/CodeGuardian-AI/RejectCheck", architecture=ArchitectureSummary(tech_stack=["node"], language="javascript", framework="express", build_system="npm", test_framework="jest", entry_points=["index.js"]), static_analysis_passed=True, build_passed=True, test_passed=True)
    def mock_monitor(*args, **kwargs):
        import uuid; return str(uuid.uuid4())
    def mock_trace(*args, **kwargs): pass
    def mock_investigate(*args, **kwargs):
        from app.schemas.investigation import InvestigationResult, RootCauseAnalysis, HistoricalReference, PatchCandidateModel
        from app.db.models import Patch
        from app.db.database import SessionLocal
        from datetime import datetime
        import uuid
        incident_id = kwargs.get('incident_id') or args[1]
        with SessionLocal() as db:
            p = Patch(id=uuid.uuid4(), incident_id=uuid.UUID(incident_id), diff="x", patch_number=1, affected_files=["x"], generated_by="mock", status="unvalidated", created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
            db.add(p)
            db.commit()
        return InvestigationResult(incident_id=incident_id, status="completed", root_cause=RootCauseAnalysis(service="x", summary="x", affected_file="x"), historical_reference=HistoricalReference(found=True, memory_status="verified", applicability="reference_only"), patch_candidate=PatchCandidateModel(status="unvalidated", files_changed=["x"], diff="x", explanation="x"), verification_requirements=["x"])
    def mock_replay(*args, **kwargs): return "REPLAY_CHANGED_BEHAVIOR", {}, {}

    import app.services.git_workspace
    import app.services.inspection_service
    import app.services.failure_evidence_collector
    import app.services.ghosttrace_service
    import app.services.investigation_service
    import app.engine.replay_engine
    import app.services.github_metadata
    monkeypatch.setattr(app.services.git_workspace.GitWorkspace, "clone", mock_clone)
    monkeypatch.setattr(app.services.inspection_service.RepositoryInspectionService, "inspect_repository", mock_inspect)
    monkeypatch.setattr(app.services.failure_evidence_collector.FailureEvidenceCollector, "collect_evidence", mock_monitor)
    monkeypatch.setattr(app.services.ghosttrace_service.GhostTraceService, "rebuild_trace", mock_trace)
    monkeypatch.setattr(app.services.investigation_service.InvestigationService, "investigate_incident", mock_investigate)
    monkeypatch.setattr(app.engine.replay_engine.ReplayEngine, "run_replay", mock_replay)
    monkeypatch.setattr(app.services.github_metadata.GitHubMetadataService, "check_access", lambda *args, **kwargs: True)

    response = client.post("/api/orchestration/run", json={"repository_url": "https://github.com/CodeGuardian-AI/RejectCheck"})
    assert response.status_code == 200
    run_id = response.json()["run_id"]
    data = wait_for_state(run_id, "WAITING_FOR_APPROVAL")
    assert data["status"] == "WAITING_FOR_APPROVAL"

    # Reject
    response = client.post(f"/api/orchestration/runs/{run_id}/approval", json={"action": "reject", "reason": "No thanks"})
    assert response.status_code == 200
    data = wait_for_state(run_id, "REJECTED")
    assert data["status"] == "REJECTED"

def test_test_11_delivery_auth(monkeypatch):
    def mock_clone(*args, **kwargs): pass
    def mock_inspect(*args, **kwargs):
        from app.schemas.orchestration import InspectionResult, ArchitectureSummary
        return InspectionResult(repository_url="https://github.com/CodeGuardian-AI/AuthCheck", architecture=ArchitectureSummary(tech_stack=["node"], language="javascript", framework="express", build_system="npm", test_framework="jest", entry_points=["index.js"]), static_analysis_passed=True, build_passed=True, test_passed=True)
    def mock_monitor(*args, **kwargs):
        from app.db.models import Incident
        from app.db.database import SessionLocal
        from datetime import datetime
        import uuid
        incident_id = uuid.uuid4()
        with SessionLocal() as db:
            inc = Incident(id=incident_id, incident_number=1, application_id=uuid.uuid4(), repository_id=uuid.uuid4(), title="Test Incident", status="open", resolution_status="unresolved", created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
            db.add(inc)
            db.commit()
        return str(incident_id)
    def mock_trace(*args, **kwargs): pass
    def mock_investigate(*args, **kwargs):
        from app.schemas.investigation import InvestigationResult, RootCauseAnalysis, HistoricalReference, PatchCandidateModel
        from app.db.models import Patch
        from app.db.database import SessionLocal
        from datetime import datetime
        import uuid
        incident_id = kwargs.get('incident_id') or args[1]
        with SessionLocal() as db:
            p = Patch(id=uuid.uuid4(), incident_id=uuid.UUID(incident_id), diff="x", patch_number=1, affected_files=["x"], generated_by="mock", status="unvalidated", created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
            db.add(p)
            db.commit()
        return InvestigationResult(incident_id=incident_id, status="completed", root_cause=RootCauseAnalysis(service="x", summary="x", affected_file="x"), historical_reference=HistoricalReference(found=True, memory_status="verified", applicability="reference_only"), patch_candidate=PatchCandidateModel(status="unvalidated", files_changed=["x"], diff="x", explanation="x"), verification_requirements=["x"])
    def mock_replay(*args, **kwargs): return "REPLAY_CHANGED_BEHAVIOR", {}, {}
    def mock_delivery(*args, **kwargs):
        from app.schemas.orchestration import DeliveryResult
        return DeliveryResult(status="DELIVERY_AUTH_REQUIRED", error_details="Need auth")

    import app.services.git_workspace
    import app.services.inspection_service
    import app.services.failure_evidence_collector
    import app.services.ghosttrace_service
    import app.services.investigation_service
    import app.engine.replay_engine
    import app.services.delivery_service
    import app.services.github_metadata
    monkeypatch.setattr(app.services.git_workspace.GitWorkspace, "clone", mock_clone)
    monkeypatch.setattr(app.services.inspection_service.RepositoryInspectionService, "inspect_repository", mock_inspect)
    monkeypatch.setattr(app.services.failure_evidence_collector.FailureEvidenceCollector, "collect_evidence", mock_monitor)
    monkeypatch.setattr(app.services.ghosttrace_service.GhostTraceService, "rebuild_trace", mock_trace)
    monkeypatch.setattr(app.services.investigation_service.InvestigationService, "investigate_incident", mock_investigate)
    monkeypatch.setattr(app.engine.replay_engine.ReplayEngine, "run_replay", mock_replay)
    monkeypatch.setattr(app.services.delivery_service.DeliveryService, "run_delivery", mock_delivery)
    monkeypatch.setattr(app.services.github_metadata.GitHubMetadataService, "check_access", lambda *args, **kwargs: True)

    response = client.post("/api/orchestration/run", json={"repository_url": "https://github.com/CodeGuardian-AI/AuthCheck"})
    assert response.status_code == 200
    run_id = response.json()["run_id"]
    data = wait_for_state(run_id, "WAITING_FOR_APPROVAL")
    
    response = client.post(f"/api/orchestration/runs/{run_id}/approval", json={"action": "approve"})
    assert response.status_code == 200
    data = wait_for_state(run_id, "DELIVERY_AUTH_REQUIRED")
    assert data["status"] == "DELIVERY_AUTH_REQUIRED"

def test_test_12_delivery_failed(monkeypatch):
    def mock_clone(*args, **kwargs): pass
    def mock_inspect(*args, **kwargs):
        from app.schemas.orchestration import InspectionResult, ArchitectureSummary
        return InspectionResult(repository_url="https://github.com/CodeGuardian-AI/FailCheck", architecture=ArchitectureSummary(tech_stack=["node"], language="javascript", framework="express", build_system="npm", test_framework="jest", entry_points=["index.js"]), static_analysis_passed=True, build_passed=True, test_passed=True)
    def mock_monitor(*args, **kwargs):
        from app.db.models import Incident
        from app.db.database import SessionLocal
        from datetime import datetime
        import uuid
        incident_id = uuid.uuid4()
        with SessionLocal() as db:
            inc = Incident(id=incident_id, incident_number=1, application_id=uuid.uuid4(), repository_id=uuid.uuid4(), title="Test Incident", status="open", resolution_status="unresolved", created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
            db.add(inc)
            db.commit()
        return str(incident_id)
    def mock_trace(*args, **kwargs): pass
    def mock_investigate(*args, **kwargs):
        from app.schemas.investigation import InvestigationResult, RootCauseAnalysis, HistoricalReference, PatchCandidateModel
        from app.db.models import Patch
        from app.db.database import SessionLocal
        from datetime import datetime
        import uuid
        incident_id = kwargs.get('incident_id') or args[1]
        with SessionLocal() as db:
            p = Patch(id=uuid.uuid4(), incident_id=uuid.UUID(incident_id), diff="x", patch_number=1, affected_files=["x"], generated_by="mock", status="unvalidated", created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
            db.add(p)
            db.commit()
        return InvestigationResult(incident_id=incident_id, status="completed", root_cause=RootCauseAnalysis(service="x", summary="x", affected_file="x"), historical_reference=HistoricalReference(found=True, memory_status="verified", applicability="reference_only"), patch_candidate=PatchCandidateModel(status="unvalidated", files_changed=["x"], diff="x", explanation="x"), verification_requirements=["x"])
    def mock_replay(*args, **kwargs): return "REPLAY_CHANGED_BEHAVIOR", {}, {}
    def mock_delivery(*args, **kwargs):
        from app.schemas.orchestration import DeliveryResult
        return DeliveryResult(status="DELIVERY_FAILED", error_details="API Error")

    import app.services.git_workspace
    import app.services.inspection_service
    import app.services.failure_evidence_collector
    import app.services.ghosttrace_service
    import app.services.investigation_service
    import app.engine.replay_engine
    import app.services.delivery_service
    import app.services.github_metadata
    monkeypatch.setattr(app.services.git_workspace.GitWorkspace, "clone", mock_clone)
    monkeypatch.setattr(app.services.inspection_service.RepositoryInspectionService, "inspect_repository", mock_inspect)
    monkeypatch.setattr(app.services.failure_evidence_collector.FailureEvidenceCollector, "collect_evidence", mock_monitor)
    monkeypatch.setattr(app.services.ghosttrace_service.GhostTraceService, "rebuild_trace", mock_trace)
    monkeypatch.setattr(app.services.investigation_service.InvestigationService, "investigate_incident", mock_investigate)
    monkeypatch.setattr(app.engine.replay_engine.ReplayEngine, "run_replay", mock_replay)
    monkeypatch.setattr(app.services.delivery_service.DeliveryService, "run_delivery", mock_delivery)
    monkeypatch.setattr(app.services.github_metadata.GitHubMetadataService, "check_access", lambda *args, **kwargs: True)

    response = client.post("/api/orchestration/run", json={"repository_url": "https://github.com/CodeGuardian-AI/FailCheck"})
    assert response.status_code == 200
    run_id = response.json()["run_id"]
    data = wait_for_state(run_id, "WAITING_FOR_APPROVAL")
    
    response = client.post(f"/api/orchestration/runs/{run_id}/approval", json={"action": "approve"})
    assert response.status_code == 200
    data = wait_for_state(run_id, "DELIVERY_FAILED")
    assert data["status"] == "DELIVERY_FAILED"

def test_test_13_delivered(monkeypatch):
    def mock_clone(*args, **kwargs): pass
    def mock_inspect(*args, **kwargs):
        from app.schemas.orchestration import InspectionResult, ArchitectureSummary
        return InspectionResult(repository_url="https://github.com/CodeGuardian-AI/SuccessCheck", architecture=ArchitectureSummary(tech_stack=["node"], language="javascript", framework="express", build_system="npm", test_framework="jest", entry_points=["index.js"]), static_analysis_passed=True, build_passed=True, test_passed=True)
    def mock_monitor(*args, **kwargs):
        from app.db.models import Incident
        from app.db.database import SessionLocal
        from datetime import datetime
        import uuid
        incident_id = uuid.uuid4()
        with SessionLocal() as db:
            inc = Incident(id=incident_id, incident_number=1, application_id=uuid.uuid4(), repository_id=uuid.uuid4(), title="Test Incident", status="open", resolution_status="unresolved", created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
            db.add(inc)
            db.commit()
        return str(incident_id)
    def mock_trace(*args, **kwargs): pass
    def mock_investigate(*args, **kwargs):
        from app.schemas.investigation import InvestigationResult, RootCauseAnalysis, HistoricalReference, PatchCandidateModel
        from app.db.models import Patch
        from app.db.database import SessionLocal
        from datetime import datetime
        import uuid
        incident_id = kwargs.get('incident_id') or args[1]
        with SessionLocal() as db:
            p = Patch(id=uuid.uuid4(), incident_id=uuid.UUID(incident_id), diff="x", patch_number=1, affected_files=["x"], generated_by="mock", status="unvalidated", created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
            db.add(p)
            db.commit()
        return InvestigationResult(incident_id=incident_id, status="completed", root_cause=RootCauseAnalysis(service="x", summary="x", affected_file="x"), historical_reference=HistoricalReference(found=True, memory_status="verified", applicability="reference_only"), patch_candidate=PatchCandidateModel(status="unvalidated", files_changed=["x"], diff="x", explanation="x"), verification_requirements=["x"])
    def mock_replay(*args, **kwargs): return "REPLAY_CHANGED_BEHAVIOR", {}, {}
    def mock_delivery(*args, **kwargs):
        from app.schemas.orchestration import DeliveryResult
        return DeliveryResult(status="pr_created", pr_url="https://github.com/x/pull/1")

    import app.services.git_workspace
    import app.services.inspection_service
    import app.services.failure_evidence_collector
    import app.services.ghosttrace_service
    import app.services.investigation_service
    import app.engine.replay_engine
    import app.services.delivery_service
    import app.services.memory_service
    import app.services.github_metadata
    monkeypatch.setattr(app.services.git_workspace.GitWorkspace, "clone", mock_clone)
    monkeypatch.setattr(app.services.inspection_service.RepositoryInspectionService, "inspect_repository", mock_inspect)
    monkeypatch.setattr(app.services.failure_evidence_collector.FailureEvidenceCollector, "collect_evidence", mock_monitor)
    monkeypatch.setattr(app.services.ghosttrace_service.GhostTraceService, "rebuild_trace", mock_trace)
    monkeypatch.setattr(app.services.investigation_service.InvestigationService, "investigate_incident", mock_investigate)
    monkeypatch.setattr(app.engine.replay_engine.ReplayEngine, "run_replay", mock_replay)
    monkeypatch.setattr(app.services.delivery_service.DeliveryService, "run_delivery", mock_delivery)
    monkeypatch.setattr(app.services.memory_service.MemoryService, "update_memory", lambda *args, **kwargs: None)
    monkeypatch.setattr(app.services.github_metadata.GitHubMetadataService, "check_access", lambda *args, **kwargs: True)

    response = client.post("/api/orchestration/run", json={"repository_url": "https://github.com/CodeGuardian-AI/SuccessCheck"})
    assert response.status_code == 200
    run_id = response.json()["run_id"]
    data = wait_for_state(run_id, "WAITING_FOR_APPROVAL")

    response = client.post(f"/api/orchestration/runs/{run_id}/approval", json={"action": "approve"})
    assert response.status_code == 200
    data = wait_for_state(run_id, "COMPLETED")
    assert data["status"] == "COMPLETED"
