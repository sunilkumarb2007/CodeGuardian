import pytest
import uuid
from app.db.database import SessionLocal
from app.services.repair_lab_service import RepairLabService


def test_repair_lab_candidate_generation_and_evaluation():
    with SessionLocal() as db:
        svc = RepairLabService(db)
        incident_id = uuid.uuid4()
        run_id = str(uuid.uuid4())

        candidates = svc.generate_counterfactual_candidates(
            incident_id=incident_id,
            run_id=run_id,
        )

        assert len(candidates) == 3
        # Exactly 1 candidate recommended based on full verification proof
        recommended = [c for c in candidates if c["is_recommended"]]
        assert len(recommended) == 1
        assert recommended[0]["evaluation"]["final_status"] == "ACCEPTED"
        assert recommended[0]["evaluation"]["safety"] == "PASS"
        assert recommended[0]["evaluation"]["replay"] == "PASS"

        # Rejected candidates have explicit rejection reasons
        rejected = [c for c in candidates if not c["is_recommended"]]
        assert len(rejected) == 2
        for r in rejected:
            assert r["evaluation"]["final_status"] == "REJECTED"
            assert r["evaluation"]["rejection_reason"] is not None
