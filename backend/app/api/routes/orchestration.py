from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Optional
import uuid

from app.services.orchestrator import CodeGuardianOrchestrator, RUN_STATE
from app.schemas.orchestration import OrchestrationRunState

router = APIRouter()

class OrchestrationRequest(BaseModel):
    repository_url: str
    supplied_incident_id: Optional[str] = None

class OrchestrationResponse(BaseModel):
    run_id: str
    status: str

@router.post("/run", response_model=OrchestrationResponse)
def start_orchestration(req: OrchestrationRequest, background_tasks: BackgroundTasks):
    run_id = str(uuid.uuid4())
    
    if "github.com" not in req.repository_url:
        raise HTTPException(status_code=400, detail="Only GitHub URLs are supported.")
        
    orchestrator = CodeGuardianOrchestrator()
    orchestrator.initialize_run(run_id, req.repository_url)
    
    background_tasks.add_task(
        orchestrator.execute_pipeline, 
        run_id, 
        req.repository_url, 
        req.supplied_incident_id
    )
    
    return OrchestrationResponse(run_id=run_id, status="started")

@router.get("/runs/{run_id}", response_model=OrchestrationRunState)
def get_run_status(run_id: str):
    if run_id not in RUN_STATE:
        raise HTTPException(status_code=404, detail="Run not found")
    return RUN_STATE[run_id]

@router.get("/runs/{run_id}/result")
def get_run_result(run_id: str):
    if run_id not in RUN_STATE:
        raise HTTPException(status_code=404, detail="Run not found")
    state = RUN_STATE[run_id]
    
    if state["status"] in ["running", "started", "pending"]:
        raise HTTPException(status_code=400, detail="Run not yet completed")
        
    return {
        "run_id": run_id,
        "status": state["status"],
        "results": state["results"],
        "error": state.get("error")
    }
