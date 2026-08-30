import pytest
import uuid
from app.db.database import SessionLocal
from app.services.impact_service import ImpactService


def test_impact_analysis_blast_radius():
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
            title="Impact Test Incident",
            status="investigating",
            resolution_status="unresolved",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(incident)
        db.commit()

        svc = ImpactService(db)
        incident_id = incident.id

        impact = svc.analyze_blast_radius(
            incident_id=incident_id,
            changed_files=["src/main/java/com/example/payment/service/PaymentService.java"],
        )

        assert impact.id is not None
        assert impact.risk_level in ["LOW", "MEDIUM", "HIGH"]
        assert len(impact.affected_callers) >= 1
        assert len(impact.affected_endpoints) >= 1

        impact_dict = svc.to_dict(impact)
        assert impact_dict["metrics"]["files_affected"] == 1
        assert impact_dict["metrics"]["callers_affected"] >= 1
