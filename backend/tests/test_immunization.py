import pytest
import uuid
from app.db.database import SessionLocal
from app.services.immunization_service import ImmunizationService


def test_immunization_guard_synthesis_and_status():
    with SessionLocal() as db:
        svc = ImmunizationService(db)
        incident_id = uuid.uuid4()
        fingerprint = "NULL_OBJECT_ACCESS"

        guard = svc.synthesize_regression_guard(
            incident_id=incident_id,
            fingerprint=fingerprint,
        )

        assert guard.id is not None
        assert guard.validation_status == "PASSED"
        assert guard.is_active is True
        assert "PaymentServiceRegressionGuardTest" in guard.test_code

        status = svc.get_immunization_status(fingerprint)
        assert status["status"] == "PROTECTED"
        assert status["is_immunized"] is True
        assert status["active_guards_count"] >= 1
