from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional
import uuid

from app.services.orchestrator import CodeGuardianOrchestrator
from app.schemas.orchestration import OrchestrationRunState
from app.db.database import get_db, SessionLocal
from app.db.models import Run
from sqlalchemy.orm import Session

router = APIRouter()

class OrchestrationRequest(BaseModel):
    repository_url: str
    supplied_incident_id: Optional[str] = None
    failure_input: Optional[dict] = None

class OrchestrationResponse(BaseModel):
    run_id: str
    status: str

@router.post("/run", response_model=OrchestrationResponse)
def start_orchestration(req: OrchestrationRequest, background_tasks: BackgroundTasks):
    validated_failure_input = None
    if req.failure_input:
        # Pre-validate structure
        fi = dict(req.failure_input)
        failure_type = fi.get("failure_type") or fi.get("error_code") or fi.get("type") or fi.get("exception")
        message = (
            fi.get("message")
            or fi.get("error_pattern")
            or fi.get("error_message")
            or (fi.get("stack_trace", "").split("\n")[0] if fi.get("stack_trace") else None)
        )
        source = fi.get("source") or "RUNTIME"
        timestamp = fi.get("timestamp") or datetime.now(timezone.utc).isoformat()

        missing = []
        if not failure_type:
            missing.append("failure_type")
        if not message:
            missing.append("message")
        if not source:
            missing.append("source")
        if not timestamp:
            missing.append("timestamp")

        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Failure evidence is incomplete. Missing required fields: {', '.join(missing)}"
            )

        fi["failure_type"] = failure_type
        fi["message"] = message
        fi["source"] = source
        fi["timestamp"] = timestamp
        validated_failure_input = fi

    orchestrator = CodeGuardianOrchestrator()
    run_id = orchestrator.initialize_run(req.repository_url)
    
    background_tasks.add_task(
        orchestrator.execute_pipeline, 
        run_id, 
        req.repository_url, 
        req.supplied_incident_id,
        validated_failure_input
    )
    
    return OrchestrationResponse(run_id=run_id, status="started")

@router.get("/runs/{run_id}", response_model=OrchestrationRunState)
def get_run_status(run_id: str, db: Session = Depends(get_db)):
    run = db.query(Run).filter(Run.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    repo_url = ""
    if run.repository_id:
        from app.db.models import Repository
        repo = db.query(Repository).filter(Repository.id == run.repository_id).first()
        if repo:
            repo_url = repo.repository_url
            
    return {
        "run_id": run.id,
        "repository_url": repo_url,
        "status": run.state,
        "current_stage": run.current_stage,
        "stages": {},
        "results": {},
        "error": run.error_message
    }

@router.get("/runs/{run_id}/result")
def get_run_result(run_id: str, db: Session = Depends(get_db)):
    run = db.query(Run).filter(Run.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    if run.state in ["running", "started", "pending", "CREATED", "REPOSITORY_LOADING"]:
        raise HTTPException(status_code=400, detail="Run not yet completed")
        
    return {
        "run_id": run.id,
        "status": run.state,
        "results": {},
        "error": run.error_message
    }

class ApprovalRequest(BaseModel):
    action: str
    reason: Optional[str] = None

@router.post("/runs/{run_id}/approval")
def handle_approval(run_id: str, req: ApprovalRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    run = db.query(Run).filter(Run.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
        
    if run.state != "WAITING_FOR_APPROVAL":
        raise HTTPException(status_code=400, detail="Run is not waiting for approval")
        
    if req.action == "approve":
        from app.engine.run_state_machine import RunState
        run.state = RunState.PATCH_APPROVED.value
        db.commit()
        
        orchestrator = CodeGuardianOrchestrator()
        background_tasks.add_task(orchestrator.continue_after_approval, run_id)
        return {"status": "PATCH_APPROVED"}
    elif req.action == "reject":
        from app.engine.run_state_machine import RunState
        from datetime import datetime
        run.state = RunState.REJECTED.value
        run.current_stage = RunState.REJECTED.value
        run.error_message = req.reason
        run.terminal_at = datetime.now(timezone.utc)
        db.commit()
        return {"status": "REJECTED"}
    else:
        raise HTTPException(status_code=400, detail="Invalid action")

@router.get("/runs/{run_id}/approve")
def handle_one_click_approval(run_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    run = db.query(Run).filter(Run.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
        
    if run.state != "WAITING_FOR_APPROVAL":
        return {"status": "Already processed or invalid state", "current_state": run.state}
        
    from app.engine.run_state_machine import RunState
    run.state = RunState.PATCH_APPROVED.value
    db.commit()
    
    orchestrator = CodeGuardianOrchestrator()
    background_tasks.add_task(orchestrator.continue_after_approval, run_id)
    return {"message": "Run Approved! Check GitHub for the PR and merge status."}


@router.websocket("/runs/{run_id}/ws")
async def orchestration_websocket_endpoint(websocket: WebSocket, run_id: str, db: Session = Depends(get_db)):
    from starlette.concurrency import run_in_threadpool
    from app.services.workspace_service import WorkspaceService
    import asyncio
    from fastapi import WebSocketDisconnect

    await websocket.accept()
    svc = WorkspaceService(db)
    
    def fetch_state():
        return svc.get_run_workspace(run_id)

    try:
        while True:
            ws_data = await run_in_threadpool(fetch_state)
            if ws_data:
                await websocket.send_json(ws_data)
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        pass

