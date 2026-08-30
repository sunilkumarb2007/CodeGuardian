import uuid
import time
import pytest
from datetime import datetime, timezone

from app.db.database import SessionLocal
from app.db.models import (
    Application, Run, Incident, Patch, ValidationRun, PullRequest, FailureMemory, Repository
)
from app.engine.run_state_machine import RunState
from app.services.receipt_service import ReceiptService
from app.services.delivery_service import DeliveryService
from app.services.workspace_service import WorkspaceService
from app.services.orchestrator import CodeGuardianOrchestrator


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_app(db_session):
    app = Application(
        id=uuid.uuid4(),
        name=f"TestApp-{uuid.uuid4().hex[:6]}",
        description="Test Application",
        environment="production",
        repository_url="https://github.com/test/repo",
        status="active",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add(app)
    db_session.commit()
    return app


def create_incident(db, app_id, title="Test Defect", **kwargs):
    inc = Incident(
        id=kwargs.get("id", uuid.uuid4()),
        incident_number=int(time.time() * 1000) % 1000000000 + int(uuid.uuid4().int % 10000),
        application_id=app_id,
        title=title,
        status="detected",
        resolution_status="unresolved",
        observed_status_code=kwargs.get("observed_status_code", 500),
        error_fingerprint=kwargs.get("error_fingerprint", "TEST_ERROR"),
        root_cause_summary=kwargs.get("root_cause_summary", "Test root cause"),
        root_cause_service=kwargs.get("root_cause_service", "test-service"),
        endpoint=kwargs.get("endpoint", "/api/test"),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(inc)
    db.commit()
    return inc


def create_repository(db, app_id, name=None, **kwargs):
    repo_name = name or f"TestRepo-{uuid.uuid4().hex[:8]}"
    repo = Repository(
        id=kwargs.get("id", uuid.uuid4()),
        application_id=app_id,
        provider="github",
        owner=f"user-{uuid.uuid4().hex[:6]}",
        name=repo_name,
        repository_url=kwargs.get("repository_url", f"https://github.com/user/{repo_name}"),
        default_branch="main",
        access_status="granted",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(repo)
    db.commit()
    return repo


def create_patch(db, incident_id, status="unvalidated", **kwargs):
    patch = Patch(
        id=kwargs.get("id", uuid.uuid4()),
        incident_id=incident_id,
        patch_number=kwargs.get("patch_number", 1),
        diff=kwargs.get("diff", "--- a/File.java\n+++ b/File.java\n@@ -1,1 +1,2 @@\n+line"),
        affected_files=kwargs.get("affected_files", ["File.java"]),
        generation_reason="Fix bug",
        status=status,
        generated_by="sarvam-ai",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(patch)
    db.commit()
    return patch


def create_run(db, incident_id=None, repo_id=None, state="INITIALIZED", stage="repository", **kwargs):
    run = Run(
        id=kwargs.get("id", str(uuid.uuid4())),
        incident_id=incident_id,
        repository_id=repo_id,
        state=state,
        current_stage=stage,
        error_code=kwargs.get("error_code"),
        error_message=kwargs.get("error_message"),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        terminal_at=kwargs.get("terminal_at")
    )
    db.add(run)
    db.commit()
    return run


def test_1_validation_marks_patch_validated(db_session, test_app):
    incident = create_incident(db_session, test_app.id)
    patch = create_patch(db_session, incident.id, status="unvalidated")

    # Simulate validation engine completion
    val_run = ValidationRun(
        id=uuid.uuid4(),
        incident_id=incident.id,
        patch_id=patch.id,
        build_passed=True,
        tests_passed=True,
        replay_passed=True,
        original_failure_reproduced=True,
        repair_verified=True,
        exit_code=0,
        status="passed",
        created_at=datetime.now(timezone.utc)
    )
    patch.status = "validated"
    db_session.add(val_run)
    db_session.commit()

    db_session.refresh(patch)
    assert patch.status == "validated"
    
    saved_val = db_session.query(ValidationRun).filter(ValidationRun.patch_id == patch.id).first()
    assert saved_val is not None
    assert saved_val.repair_verified is True


def test_2_delivery_requires_validated_patch(db_session, test_app):
    incident = create_incident(db_session, test_app.id, title="Test NullPointer")
    patch = create_patch(db_session, incident.id, status="unvalidated")

    deliv_svc = DeliveryService(db_session)
    with pytest.raises(ValueError) as exc:
        deliv_svc.run_delivery(incident.id, patch.id, "https://github.com/test/repo")
    
    assert "DELIVERY_BLOCKED" in str(exc.value)
    assert "must be 'validated'" in str(exc.value)


def test_3_validation_patch_transaction_consistency(db_session, test_app):
    incident = create_incident(db_session, test_app.id, title="Test Transaction")
    patch = create_patch(db_session, incident.id, status="unvalidated")

    # Atomically validate
    val_run = ValidationRun(
        id=uuid.uuid4(),
        incident_id=incident.id,
        patch_id=patch.id,
        build_passed=True,
        tests_passed=True,
        replay_passed=True,
        repair_verified=True,
        status="passed",
        created_at=datetime.now(timezone.utc)
    )
    patch.status = "validated"
    db_session.add(val_run)
    db_session.commit()

    # Read back in a fresh session
    fresh_db = SessionLocal()
    try:
        p = fresh_db.query(Patch).filter(Patch.id == patch.id).first()
        v = fresh_db.query(ValidationRun).filter(ValidationRun.patch_id == patch.id).first()
        assert p.status == "validated"
        assert v.status == "passed"
    finally:
        fresh_db.close()


def test_4_stage16_failure_does_not_enter_stage17(db_session, test_app):
    incident = create_incident(db_session, test_app.id)
    repo = create_repository(db_session, test_app.id)
    patch = create_patch(db_session, incident.id, status="unvalidated")
    run = create_run(db_session, incident.id, repo.id, state=RunState.WAITING_FOR_APPROVAL.value, stage="approval")

    orchestrator = CodeGuardianOrchestrator()
    orchestrator.continue_after_approval(run.id)

    db_session.refresh(run)
    assert run.state == "FAILED"
    assert run.current_stage == "delivery"
    assert "DELIVERY_BLOCKED" in (run.error_code or "")
    
    # Assert Memory Update was NOT executed
    memories = db_session.query(FailureMemory).filter(FailureMemory.incident_id == incident.id).all()
    assert len(memories) == 0


def test_5_workspace_stage_resolution_on_failure(db_session):
    run = create_run(
        db_session,
        state="FAILED",
        stage="delivery",
        error_code="DELIVERY_FAILED",
        error_message="Delivery blocked: unvalidated patch"
    )

    ws_svc = WorkspaceService(db_session)
    ws = ws_svc.get_run_workspace(run.id)

    stages = ws.get("stages", [])
    stages_by_name = {s.get("id") or s.get("name"): s["status"] for s in stages}

    # Delivery stage must be failed
    assert stages_by_name["delivery"] == "failed"
    # Prior stages must be passed
    assert stages_by_name["validation"] == "passed"
    assert stages_by_name["approval"] == "passed"
    # Memory update stage MUST NOT be passed! It must be pending
    assert stages_by_name["memory_update"] == "pending"
    assert stages_by_name["completed"] == "pending"


def test_6_repair_receipt_completed(db_session, test_app):
    incident = create_incident(
        db_session,
        test_app.id,
        title="NullPointerException in PaymentService",
        endpoint="/api/v1/pay",
        observed_status_code=500,
        error_fingerprint="NULL_OBJECT_ACCESS",
        root_cause_summary="Merchant was null",
        root_cause_service="payment-service"
    )
    repo = create_repository(db_session, test_app.id)
    patch = create_patch(
        db_session,
        incident.id,
        status="validated",
        affected_files=["payment-service/PaymentService.java"],
        diff="--- a/PaymentService.java\n+++ b/PaymentService.java\n@@ -20,2 +20,4 @@\n+if (m == null) throw new Error();"
    )
    val_run = ValidationRun(
        id=uuid.uuid4(),
        incident_id=incident.id,
        patch_id=patch.id,
        build_passed=True,
        tests_passed=True,
        replay_passed=True,
        repair_verified=True,
        status="passed",
        created_at=datetime.now(timezone.utc)
    )
    pr = PullRequest(
        id=uuid.uuid4(),
        incident_id=incident.id,
        patch_id=patch.id,
        repository_id=repo.id,
        provider="github",
        branch_name="codeguardian/fix/test",
        base_branch="main",
        title="Fix NullPointerException",
        external_pr_number=17,
        external_pr_url="https://github.com/test/JavaAPICheck/pull/17",
        status="open",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    memory = FailureMemory(
        id=uuid.uuid4(),
        incident_id=incident.id,
        application_id=test_app.id,
        error_pattern="NullPointerException in PaymentService",
        error_fingerprint="NULL_OBJECT_ACCESS",
        root_cause="Merchant was null",
        affected_files=["payment-service/PaymentService.java"],
        searchable_text="NullPointerException merchant null",
        memory_status="verified",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    run = create_run(
        db_session,
        incident.id,
        repo.id,
        state="COMPLETED",
        stage="completed",
        terminal_at=datetime.now(timezone.utc)
    )

    db_session.add_all([val_run, pr, memory])
    db_session.commit()

    receipt_svc = ReceiptService(db_session)
    receipt = receipt_svc.generate_receipt(run.id)

    assert receipt is not None
    assert receipt.receipt_type == "REPAIR_RECEIPT"
    assert receipt.outcome == "FAILURE_REPAIRED"
    assert receipt.verification.validation == "6 / 6 PASS"
    assert receipt.delivery.status == "DELIVERED"
    assert receipt.delivery.pr_number == 17
    assert receipt.memory.updated is True
    assert receipt.receipt_hash is not None
    assert "CODEGUARDIAN" in receipt.ascii_receipt


def test_7_repair_receipt_failed_attempt(db_session, test_app):
    incident = create_incident(db_session, test_app.id, title="Test Failed Run")
    repo = create_repository(db_session, test_app.id)
    run = create_run(
        db_session,
        incident.id,
        repo.id,
        state="FAILED",
        stage="delivery",
        error_code="DELIVERY_BLOCKED",
        error_message="DELIVERY_BLOCKED: Patch status is 'unvalidated'"
    )

    receipt_svc = ReceiptService(db_session)
    receipt = receipt_svc.generate_receipt(run.id)

    assert receipt is not None
    assert receipt.receipt_type == "REPAIR_ATTEMPT_RECEIPT"
    assert receipt.outcome == "DELIVERY_BLOCKED"
    assert receipt.delivery.status == "BLOCKED"
    assert receipt.memory.updated is False
    assert "Reason" in receipt.ascii_receipt


def test_8_receipt_hash_deterministic(db_session):
    run = create_run(db_session, state="NO_FAILURE_EVIDENCE", stage="failure_detection")

    receipt_svc = ReceiptService(db_session)
    r1 = receipt_svc.generate_receipt(run.id)
    r2 = receipt_svc.generate_receipt(run.id)

    assert r1.receipt_hash == r2.receipt_hash
    assert r1.receipt_id == r2.receipt_id


def test_9_no_failure_analysis_receipt(db_session):
    run = create_run(db_session, state="NO_FAILURE_EVIDENCE", stage="failure_detection")

    receipt_svc = ReceiptService(db_session)
    receipt = receipt_svc.generate_receipt(run.id)

    assert receipt is not None
    assert receipt.receipt_type == "ANALYSIS_RECEIPT"
    assert receipt.outcome == "NO_FAILURE_FOUND"
    assert receipt.repair.affected_files == []
    assert receipt.repair.lines_added == 0
    assert receipt.delivery.status == "NOT_REQUIRED"
    assert receipt.memory.updated is False
