from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.failure_lab_service import FailureLabService
from typing import List, Dict, Any

router = APIRouter()


@router.get("/scenarios")
def list_scenarios(db: Session = Depends(get_db)):
    """
    Returns available Failure Lab demonstration scenarios.
    """
    svc = FailureLabService(db)
    return svc.list_scenarios()


@router.post("/scenarios/{scenario_id}/run")
def run_scenario(scenario_id: str, db: Session = Depends(get_db)):
    """
    Launches a controlled scenario execution advancing through the deterministic pipeline.
    """
    svc = FailureLabService(db)
    return svc.execute_controlled_scenario(scenario_id)
