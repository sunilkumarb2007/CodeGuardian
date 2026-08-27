from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.workspace_service import WorkspaceService
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


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
    svc = WorkspaceService(db)
    run_data = svc.get_run_workspace(run_id)
    if not run_data:
        raise HTTPException(status_code=404, detail="Run not found")
    return run_data


@router.get("/{run_id}/agent-events")
def get_agent_events(run_id: str, db: Session = Depends(get_db)):
    svc = WorkspaceService(db)
    events = svc.get_events(run_id)
    return events


@router.get("/{run_id}/commands")
def get_commands(run_id: str, db: Session = Depends(get_db)):
    svc = WorkspaceService(db)
    commands = svc.get_commands(run_id)
    return commands


@router.get("/{run_id}/state", response_model=RunStateResponse)
def get_run_state(run_id: str, db: Session = Depends(get_db)):
    svc = WorkspaceService(db)
    ws = svc.get_run_workspace(run_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Run not found")
    
    return {
        "run_id": ws["run"]["id"],
        "status": ws["run"]["status"],
        "current_stage": ws["run"]["current_stage"],
        "mode": ws["run"]["mode"],
        "stages": {s["id"]: s["status"] for s in ws["stages"]},
        "results": {
            "repository": ws.get("repository", {}),
            "incident": ws.get("incident", {})
        },
        "error": ws["run"].get("error")
    }


@router.post("/{run_id}/approve")
def approve_run(run_id: str, background_tasks: BackgroundTasks):
    from app.services.orchestrator import CodeGuardianOrchestrator
    try:
        orchestrator = CodeGuardianOrchestrator()
        background_tasks.add_task(orchestrator.continue_after_approval, run_id)
        return {"status": "success", "message": "Approved. Delivery in progress."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{run_id}/reject")
def reject_run(run_id: str):
    from app.db.database import SessionLocal
    from app.db.models import Run
    from app.engine.run_state_machine import RunState
    try:
        with SessionLocal() as db:
            run = db.query(Run).filter(Run.id == run_id).first()
            if run:
                run.state = RunState.REJECTED.value
                db.commit()
        return {"status": "success"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{run_id}/changed-files/{file_id}/accept")
def accept_file(run_id: str, file_id: str, db: Session = Depends(get_db)):
    try:
        svc = WorkspaceService(db)
        return svc.record_file_decision(run_id, file_id, "accepted")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{run_id}/changed-files/{file_id}/reject")
def reject_file(run_id: str, file_id: str, db: Session = Depends(get_db)):
    try:
        svc = WorkspaceService(db)
        return svc.record_file_decision(run_id, file_id, "rejected")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
