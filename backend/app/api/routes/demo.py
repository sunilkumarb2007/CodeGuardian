from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
import uuid
import logging
from typing import Dict, Any, Optional
from app.demo.demo_runner import DemoRunner

router = APIRouter()
logger = logging.getLogger(__name__)

class DemoRequest(BaseModel):
    repository_url: str

class DemoRunResponse(BaseModel):
    run_id: str
    status: str
    mode: str

class DemoResetResponse(BaseModel):
    status: str
    message: str

runner = DemoRunner()

@router.post("/run", response_model=DemoRunResponse)
def start_demo(req: DemoRequest, background_tasks: BackgroundTasks):
    if req.repository_url != "https://github.com/sunilkumarb2007/JavaAPICheck":
        raise HTTPException(
            status_code=400, 
            detail={
                "status": "failed",
                "stage": "investigation",
                "error_code": "DEMO_SCENARIO_NOT_AVAILABLE",
                "message": "No prepared investigation exists for this repository."
            }
        )
    
    run_id = str(uuid.uuid4())
    runner.initialize_run(run_id)
    background_tasks.add_task(runner.execute_async, run_id)
    
    return DemoRunResponse(run_id=run_id, status="started", mode="demo")

@router.get("/runs/{run_id}")
def get_run_status(run_id: str):
    state = runner.get_run(run_id)
    if not state:
        raise HTTPException(status_code=404, detail="Run not found")
    return state

@router.get("/runs/{run_id}/result")
def get_run_result(run_id: str):
    state = runner.get_run(run_id)
    if not state:
        raise HTTPException(status_code=404, detail="Run not found")
    return state.get("results", {})

@router.post("/runs/{run_id}/approve")
def approve_run(run_id: str, background_tasks: BackgroundTasks):
    try:
        runner.approve_and_continue(run_id)
        # Continue in background
        background_tasks.add_task(runner.execute_async, run_id)
        return {"status": "success", "message": "Run approved, continuing delivery"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/runs/{run_id}/reject")
def reject_run(run_id: str):
    try:
        runner.reject_patch(run_id)
        return {"status": "success", "message": "Patch rejected"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/reset", response_model=DemoResetResponse)
def reset_demo():
    from app.demo.demo_runner import DEMO_STATE_STORE
    DEMO_STATE_STORE.clear()
    return DemoResetResponse(status="success", message="Demo state reset.")
