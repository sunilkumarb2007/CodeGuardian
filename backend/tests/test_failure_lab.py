import pytest
from app.db.database import SessionLocal
from app.services.failure_lab_service import FailureLabService


def test_failure_lab_scenarios_listing():
    with SessionLocal() as db:
        svc = FailureLabService(db)
        scenarios = svc.list_scenarios()
        assert len(scenarios) >= 5
        scenario_ids = [s["scenario_id"] for s in scenarios]
        assert "null_object_access" in scenario_ids
        assert "database_timeout" in scenario_ids
        assert "rate_limit_429" in scenario_ids


def test_failure_lab_execution():
    with SessionLocal() as db:
        svc = FailureLabService(db)
        result = svc.execute_controlled_scenario("null_object_access")
        assert result["status"] == "RUNNING"
        assert result["run_id"] is not None
        assert result["incident_id"] is not None
        assert result["scenario_id"] == "null_object_access"
