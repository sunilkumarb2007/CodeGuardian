import pytest
import uuid
from app.db.database import SessionLocal
from app.services.immunization_service import ImmunizationService


def test_immunization_guard_synthesis_and_status():
    with SessionLocal() as db:
        from datetime import datetime, timezone
        from app.db.models import Application, Incident
        import random

        app = db.query(Application).first()
        if not app:
            app = Application(id=uuid.uuid4(), name="test-app", repository_url="https://github.com/org/repo")
            db.add(app)
            db.commit()

        incident = Incident(
            id=uuid.uuid4(),
            incident_number=random.randint(1000000, 99999999),
            application_id=app.id,
            title="Immunization Test Incident",
            status="investigating",
            resolution_status="unresolved",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(incident)
        db.commit()

        svc = ImmunizationService(db)
        incident_id = incident.id
        fingerprint = "NULL_OBJECT_ACCESS"

        guard = svc.synthesize_regression_guard(
            incident_id=incident_id,
            fingerprint=fingerprint,
        )

        assert guard.id is not None
        assert guard.validation_status == "PASSED"
        assert guard.is_active is True
        assert "RegressionGuardTest" in guard.test_code

        status = svc.get_immunization_status(fingerprint)
        assert status["status"] == "PROTECTED"
        assert status["is_immunized"] is True
        assert status["active_guards_count"] >= 1
