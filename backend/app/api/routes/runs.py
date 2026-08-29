from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.concurrency import run_in_threadpool
import asyncio
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
    
    raw_stages = ws.get("stages", [])
    stages_dict = {}
    if isinstance(raw_stages, list):
        for s in raw_stages:
            if isinstance(s, dict) and "id" in s:
                stages_dict[s["id"]] = s.get("status", "unknown")
            elif isinstance(s, dict) and "name" in s:
                stages_dict[s["name"]] = s.get("status", "unknown")
    elif isinstance(raw_stages, dict):
        stages_dict = raw_stages

    return {
        "run_id": str(ws.get("run_id") or ws.get("run", {}).get("id", run_id)),
        "status": ws.get("status") or ws.get("run", {}).get("status", "unknown"),
        "current_stage": ws.get("current_stage") or ws.get("run", {}).get("current_stage", "unknown"),
        "mode": ws.get("mode", "active"),
        "stages": stages_dict,
        "results": ws.get("results", {}),
        "error": ws.get("error") or ws.get("run", {}).get("error")
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


@router.get("/{run_id}/failure-dna")
def get_failure_dna(run_id: str, db: Session = Depends(get_db)):
    svc = WorkspaceService(db)
    ws = svc.get_run_workspace(run_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Run not found")
    return ws.get("failure_dna", {})


@router.get("/{run_id}/repair-candidates")
def get_repair_candidates(run_id: str, db: Session = Depends(get_db)):
    svc = WorkspaceService(db)
    ws = svc.get_run_workspace(run_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Run not found")
    return ws.get("repair_candidates", [])


@router.get("/{run_id}/impact")
def get_impact(run_id: str, db: Session = Depends(get_db)):
    svc = WorkspaceService(db)
    ws = svc.get_run_workspace(run_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Run not found")
    return ws.get("impact_analysis", {})


@router.get("/{run_id}/immunization")
def get_immunization(run_id: str, db: Session = Depends(get_db)):
    svc = WorkspaceService(db)
    ws = svc.get_run_workspace(run_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Run not found")
    return ws.get("immunization", {})

@router.websocket("/{run_id}/ws")
async def websocket_endpoint(websocket: WebSocket, run_id: str, db: Session = Depends(get_db)):
    await websocket.accept()
    svc = WorkspaceService(db)
    
    def fetch_state():
        return svc.get_run_workspace(run_id)

    try:
        while True:
            ws_data = await run_in_threadpool(fetch_state)
            if ws_data:
                raw_stages = ws_data.get("stages", [])
                stages_dict = {}
                if isinstance(raw_stages, list):
                    for s in raw_stages:
                        if isinstance(s, dict) and "id" in s:
                            stages_dict[s["id"]] = s.get("status", "unknown")
                        elif isinstance(s, dict) and "name" in s:
                            stages_dict[s["name"]] = s.get("status", "unknown")
                elif isinstance(raw_stages, dict):
                    stages_dict = raw_stages

                await websocket.send_json(ws_data)
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for run_id: {run_id}")
