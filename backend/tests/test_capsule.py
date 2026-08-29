import pytest
import uuid
from app.db.database import SessionLocal
from app.services.capsule_service import CapsuleService


def test_capsule_export_and_import_validation():
    with SessionLocal() as db:
        from datetime import datetime, timezone
        from app.db.models import Application, Incident

        app = db.query(Application).first()
        if not app:
            app = Application(
                id=uuid.uuid4(),
                name="TestApp",
                environment="test",
                status="active",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.add(app)
            db.flush()

        max_inc = db.query(Incident).order_by(Incident.incident_number.desc()).first()
        next_num = (max_inc.incident_number + 1) if max_inc else 1

        incident = Incident(
            id=uuid.uuid4(),
            incident_number=next_num,
            application_id=app.id,
            title="Capsule Test Incident",
            status="detected",
            resolution_status="unresolved",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(incident)
        db.commit()

        from app.db.models import Run
        run = Run(
            id=uuid.uuid4(),
            incident_id=incident.id,
            state="COMPLETED",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(run)
        db.commit()

        svc = CapsuleService(db)
        incident_id = incident.id
        run_id = str(run.id)

        # Test export
        capsule_data = svc.generate_capsule(
            incident_id=incident_id,
            run_id=run_id,
        )

        assert capsule_data["id"] is not None
        assert capsule_data["size_bytes"] > 0
        assert capsule_data["manifest"]["version"] == "1.0.0"
        assert len(capsule_data["zip_bytes"]) > 0

        # Test valid import
        import_res = svc.validate_and_import(capsule_data["zip_bytes"])
        assert import_res["valid"] is True
        assert import_res["status"] == "VERIFIED"
        assert import_res["files_count"] >= 5


def test_capsule_traversal_rejection():
    with SessionLocal() as db:
        svc = CapsuleService(db)
        with pytest.raises(ValueError):
            svc.validate_and_import(b"Not a zip file payload")
