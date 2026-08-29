import pytest
import uuid
from app.db.database import SessionLocal
from app.services.impact_service import ImpactService


def test_impact_analysis_blast_radius():
    with SessionLocal() as db:
        svc = ImpactService(db)
        incident_id = uuid.uuid4()

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
