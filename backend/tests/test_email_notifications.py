import os
import uuid
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import SessionLocal
from app.db.models import Run, Incident, Patch, ValidationRun, Repository, Application, ApprovalDecision, NotificationItem
from app.engine.run_state_machine import RunState
from app.services.notification_service import NotificationService, EmailNotificationProvider, _ACTION_TOKENS_STORE, _APPROVAL_EMAIL_CACHE

client = TestClient(app)

@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


def get_or_create_app_and_repo(db):
    app = db.query(Application).first()
    if not app:
        app = Application(
            id=uuid.uuid4(),
            name="CodeGuardianApp",
            environment="production",
            status="active",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(app)
        db.commit()
    
    repo = db.query(Repository).filter_by(application_id=app.id).first()
    if not repo:
        repo = Repository(
            id=uuid.uuid4(),
            application_id=app.id,
            provider="github",
            owner="sunilkumarb2007",
            name="JavaAPICheck",
            repository_url="https://github.com/sunilkumarb2007/JavaAPICheck",
            default_branch="main",
            access_status="granted",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(repo)
        db.commit()
    return app, repo


def test_1_email_success():
    """Verify Resend provider dispatches email and returns real provider ID."""
    provider = EmailNotificationProvider()
    with patch("resend.Emails.send") as mock_send:
        mock_send.return_value = {"id": "resend_msg_test_12345"}
        res = provider.send(
            to_email="alerts@codeguardian.dev",
            subject="Test Subject",
            body="Test body",
            html_body="<p>Test HTML</p>"
        )
        assert res["success"] is True
        assert res["provider"] == "resend"
        assert res["provider_id"] == "resend_msg_test_12345"


def test_2_provider_failure():
    """Verify provider returns error dictionary without crashing on Resend API failure."""
    provider = EmailNotificationProvider()
    with patch("resend.Emails.send") as mock_send:
        mock_send.side_effect = Exception("Rate limit exceeded")
        res = provider.send(
            to_email="alerts@codeguardian.dev",
            subject="Test Subject",
            body="Test body"
        )
        assert res["success"] is False
        assert "Rate limit exceeded" in res["error"]


def test_3_duplicate_notification_idempotency(db):
    """Verify that emit_approval_email is strictly idempotent per run."""
    app, repo = get_or_create_app_and_repo(db)
    
    run_id = str(uuid.uuid4())
    inc_id = uuid.uuid4()

    inc_obj = Incident(
        id=inc_id,
        incident_number=int(datetime.now().timestamp()),
        application_id=app.id,
        repository_id=repo.id,
        title="Test Incident",
        status="detected",
        resolution_status="unresolved",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(inc_obj)
    db.commit()

    run_obj = Run(
        id=uuid.UUID(run_id),
        repository_id=repo.id,
        incident_id=inc_id,
        state="WAITING_FOR_APPROVAL",
        current_stage="approval",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    patch_obj = Patch(
        id=uuid.uuid4(),
        incident_id=inc_id,
        patch_number=1,
        diff="+ test diff",
        affected_files=["test.py"],
        status="validated",
        generated_by="sarvam",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    val_obj = ValidationRun(
        id=uuid.uuid4(),
        incident_id=inc_id,
        patch_id=patch_obj.id,
        status="passed",
        repair_verified=True,
        created_at=datetime.now(timezone.utc)
    )

    db.add_all([run_obj, patch_obj, val_obj])
    db.commit()

    with patch.object(EmailNotificationProvider, "send") as mock_send:
        mock_send.return_value = {"success": True, "provider": "resend", "provider_id": "res_first_msg"}
        
        # First emission
        res1 = NotificationService.emit_approval_email(run_id, db_session=db)
        assert res1["success"] is True
        assert res1["provider_id"] == "res_first_msg"
        assert mock_send.call_count == 1

        # Second emission (idempotent skip)
        res2 = NotificationService.emit_approval_email(run_id, db_session=db)
        assert res2["success"] is True
        assert res2["provider_id"] == "res_first_msg"
        assert mock_send.call_count == 1  # Not called again


def test_4_expired_token():
    """Verify expired token is rejected."""
    run_id = str(uuid.uuid4())
    token = NotificationService.generate_action_token(run_id, expiration_hours=-1)  # expired 1 hour ago
    
    valid, reason = NotificationService.validate_action_token(run_id, token)
    assert valid is False
    assert "expired" in reason.lower()


def test_5_wrong_token():
    """Verify token mismatch between runs is rejected."""
    run_1 = str(uuid.uuid4())
    run_2 = str(uuid.uuid4())
    token_1 = NotificationService.generate_action_token(run_1, expiration_hours=24)
    
    # Try validating token_1 against run_2
    valid, reason = NotificationService.validate_action_token(run_2, token_1)
    assert valid is False
    assert "mismatch" in reason.lower()


def test_6_approve_endpoint_validation_and_token(db):
    """Verify POST /api/runs/{run_id}/approve enforces state, validation, token, and records decision."""
    app, repo = get_or_create_app_and_repo(db)

    run_id = str(uuid.uuid4())
    inc_id = uuid.uuid4()

    inc_obj = Incident(
        id=inc_id,
        incident_number=int(datetime.now().timestamp()) + 1,
        application_id=app.id,
        repository_id=repo.id,
        title="Test Incident 2",
        status="detected",
        resolution_status="unresolved",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(inc_obj)
    db.commit()

    run_obj = Run(
        id=uuid.UUID(run_id),
        repository_id=repo.id,
        incident_id=inc_id,
        state="WAITING_FOR_APPROVAL",
        current_stage="approval",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    patch_obj = Patch(
        id=uuid.uuid4(),
        incident_id=inc_id,
        patch_number=1,
        diff="+ test diff",
        affected_files=["test.py"],
        status="validated",
        generated_by="sarvam",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    val_obj = ValidationRun(
        id=uuid.uuid4(),
        incident_id=inc_id,
        patch_id=patch_obj.id,
        status="passed",
        repair_verified=True,
        created_at=datetime.now(timezone.utc)
    )

    db.add_all([run_obj, patch_obj, val_obj])
    db.commit()

    token = NotificationService.generate_action_token(run_id)

    # Approve with valid token
    resp = client.post(f"/api/runs/{run_id}/approve?token={token}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"

    # Token should now be consumed
    valid, reason = NotificationService.validate_action_token(run_id, token)
    assert valid is False
    assert "consumed" in reason.lower()

    # Re-using the consumed token must fail with 403
    resp_reused = client.post(f"/api/runs/{run_id}/approve?token={token}")
    assert resp_reused.status_code == 403


def test_7_reject_endpoint_stops_delivery(db):
    """Verify POST /api/runs/{run_id}/reject stops delivery, marks REJECTED, and records decision."""
    app, repo = get_or_create_app_and_repo(db)

    run_id = str(uuid.uuid4())
    inc_id = uuid.uuid4()

    inc_obj = Incident(
        id=inc_id,
        incident_number=int(datetime.now().timestamp()) + 2,
        application_id=app.id,
        repository_id=repo.id,
        title="Test Incident 3",
        status="detected",
        resolution_status="unresolved",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(inc_obj)
    db.commit()

    run_obj = Run(
        id=uuid.UUID(run_id),
        repository_id=repo.id,
        incident_id=inc_id,
        state="WAITING_FOR_APPROVAL",
        current_stage="approval",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    patch_obj = Patch(
        id=uuid.uuid4(),
        incident_id=inc_id,
        patch_number=1,
        diff="+ test diff",
        affected_files=["test.py"],
        status="validated",
        generated_by="sarvam",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    val_obj = ValidationRun(
        id=uuid.uuid4(),
        incident_id=inc_id,
        patch_id=patch_obj.id,
        status="passed",
        repair_verified=True,
        created_at=datetime.now(timezone.utc)
    )

    db.add_all([run_obj, patch_obj, val_obj])
    db.commit()

    token = NotificationService.generate_action_token(run_id)

    resp = client.post(f"/api/runs/{run_id}/reject?token={token}")
    assert resp.status_code == 200
    assert resp.json()["decision"] == "REJECTED"

    db.refresh(run_obj)
    assert run_obj.state == "REJECTED"
    assert run_obj.current_stage == "approval"
    assert run_obj.error_code == "REJECTED_BY_USER"


def test_8_healthy_repository_does_not_get_repair_approval_email(db):
    """Verify healthy repo (NO_FAILURE_EVIDENCE) never dispatches repair approval emails."""
    run_id = str(uuid.uuid4())
    run_obj = Run(id=uuid.UUID(run_id), state="NO_FAILURE_EVIDENCE", current_stage="failure_detection", created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
    db.add(run_obj)
    db.commit()

    res = NotificationService.emit_approval_email(run_id, db_session=db)
    assert run_id not in _ACTION_TOKENS_STORE
