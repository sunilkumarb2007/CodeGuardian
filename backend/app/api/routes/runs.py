from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.demo.demo_runner import DemoRunner
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
demo_runner = DemoRunner()


class RunStateResponse(BaseModel):
    run_id: str
    status: str
    current_stage: str
    mode: str
    stages: dict
    results: dict
    error: str | None


class ActionRequest(BaseModel):
    pass


@router.get("/{run_id}/workspace")
def get_workspace(run_id: str, db: Session = Depends(get_db)):
    """
    Returns the aggregated investigation workspace.
    This replaces dozens of individual UI calls.
    """
    run_data = demo_runner.get_run_workspace(run_id, db)
    if not run_data:
        raise HTTPException(status_code=404, detail="Run not found")
    return run_data


@router.get("/{run_id}/agent-events")
def get_agent_events(run_id: str, db: Session = Depends(get_db)):
    events = demo_runner.get_events(run_id, db)
    return events


@router.get("/{run_id}/commands")
def get_commands(run_id: str, db: Session = Depends(get_db)):
    commands = demo_runner.get_commands(run_id, db)
    return commands


@router.get("/{run_id}/state", response_model=RunStateResponse)
def get_run_state(run_id: str):
    run = demo_runner.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.post("/{run_id}/approve")
def approve_run(run_id: str):
    try:
        demo_runner.approve_and_continue(run_id)
        return {"status": "success"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{run_id}/reject")
def reject_run(run_id: str):
    try:
        demo_runner.reject_patch(run_id)
        return {"status": "success"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{run_id}/changed-files/{file_id}/accept")
def accept_file(run_id: str, file_id: str):
    # Mock file accept
    return {"status": "accepted", "file_id": file_id}


@router.post("/{run_id}/changed-files/{file_id}/reject")
def reject_file(run_id: str, file_id: str):
    # Mock file reject
    return {"status": "rejected", "file_id": file_id}

