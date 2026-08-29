import pytest
import uuid
from app.db.database import SessionLocal
from app.db.models import Application, Incident, FailureDNA
from app.services.failure_dna_service import FailureDNAService


def test_failure_dna_fingerprint_determinism():
    with SessionLocal() as db:
        svc = FailureDNAService(db)
        fp1 = svc.compute_fingerprint(
            exception_class="NullPointerException",
            http_status=500,
            endpoint="POST /payments/charge",
            service="payment-service",
            failure_point="PaymentService.java:30",
        )
        fp2 = svc.compute_fingerprint(
            exception_class="NullPointerException",
            http_status=500,
            endpoint="POST /payments/charge",
            service="payment-service",
            failure_point="PaymentService.java:30",
        )
        assert fp1 == "NULL_OBJECT_ACCESS"
        assert fp1 == fp2


def test_failure_dna_persistence_and_extraction():
    with SessionLocal() as db:
        svc = FailureDNAService(db)
        app = db.query(Application).first()
        if not app:
            app = Application(id=uuid.uuid4(), name="test-app", repository_url="https://github.com/org/repo")
            db.add(app)
            db.commit()

        import random
        from datetime import datetime, timezone
        incident = Incident(
            id=uuid.uuid4(),
            incident_number=random.randint(1000000, 99999999),
            application_id=app.id,
            title="NullPointerException in PaymentService",
            root_cause_service="payment-service",
            status="investigating",
            resolution_status="unresolved",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(incident)
        db.commit()
        
        dna = svc.extract_or_create_dna(
            incident_id=incident.id,
            trigger="Merchant lookup was null",
            request_method="POST",
            request_endpoint="/payments/charge",
            http_status=500,
            exception_class="NullPointerException",
            normalized_message="Cannot invoke method on null object reference",
            failure_point="PaymentService.java:30",
            dependency_type="DATABASE",
        )

        assert dna.id is not None
        assert dna.fingerprint == "NULL_OBJECT_ACCESS"
        assert dna.recurrence_count >= 1

        dna_dict = svc.to_dict(dna)
        assert dna_dict["fingerprint"] == "NULL_OBJECT_ACCESS"
        assert dna_dict["request"]["http_status"] == 500
        assert len(dna_dict["propagation_chain"]) == 4
