from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.concurrency import run_in_threadpool
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import uuid
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
def approve_run(
    run_id: str,
    background_tasks: BackgroundTasks,
    token: Optional[str] = None,
    db: Session = Depends(get_db)
):
    from app.db.models import Run, Patch, ValidationRun, ApprovalDecision
    from app.services.orchestrator import CodeGuardianOrchestrator
    from app.services.notification_service import NotificationService
    from app.engine.run_state_machine import RunState

    run = db.query(Run).filter(Run.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    # 1. If token provided, validate token integrity and unexpired state first
    if token:
        valid, reason = NotificationService.validate_action_token(run_id, token)
        if not valid:
            raise HTTPException(status_code=403, detail=reason)

    # 2. Validate run state
    if run.state != RunState.WAITING_FOR_APPROVAL.value and run.state != "WAITING_FOR_APPROVAL":
        raise HTTPException(
            status_code=400,
            detail=f"Run {run_id} is not awaiting approval (current state: '{run.state}')"
        )

    # 3. Validate patch status
    patch = db.query(Patch).filter(Patch.incident_id == run.incident_id).order_by(Patch.created_at.desc()).first()
    if not patch:
        raise HTTPException(status_code=400, detail="No patch candidate found for run")
    if patch.status != "validated":
        raise HTTPException(
            status_code=400,
            detail=f"Patch {patch.id} is not validated (current status: '{patch.status}')"
        )

    # 4. Validate validation run
    val_run = db.query(ValidationRun).filter(ValidationRun.patch_id == patch.id).order_by(ValidationRun.created_at.desc()).first()
    if not val_run or (not val_run.repair_verified and val_run.status != "passed"):
        raise HTTPException(
            status_code=400,
            detail="Validation run has not passed deterministic safety verification"
        )

    # 5. Consume action token
    if token:
        NotificationService.consume_action_token(run_id, token, action="approved")

    # 5. Record approval decision
    try:
        run_uuid = uuid.UUID(run_id) if len(run_id) == 36 else None
        if run_uuid:
            decision = ApprovalDecision(
                id=uuid.uuid4(),
                run_id=run_uuid,
                actor="developer",
                decision="APPROVED_FOR_PR",
                policy_evaluation={"risk_level": "LOW", "status": "APPROVED"},
                risk_level="LOW",
                auto_merge_eligible=True,
                comments="Approved by human reviewer",
                created_at=datetime.now(timezone.utc)
            )
            db.add(decision)
            db.commit()
    except Exception as e:
        logger.debug(f"ApprovalDecision commit skipped: {e}")

    # 6. Execute delivery via background task
    orchestrator = CodeGuardianOrchestrator()
    background_tasks.add_task(orchestrator.continue_after_approval, run_id)
    return {"status": "success", "message": "Approved. Delivery in progress."}


@router.post("/{run_id}/reject")
def reject_run(
    run_id: str,
    token: Optional[str] = None,
    db: Session = Depends(get_db)
):
    from app.db.models import Run, ApprovalDecision
    from app.services.notification_service import NotificationService
    from app.engine.run_state_machine import RunState

    run = db.query(Run).filter(Run.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    # If token provided, validate and consume
    if token:
        valid, reason = NotificationService.validate_action_token(run_id, token)
        if not valid:
            raise HTTPException(status_code=403, detail=reason)
        NotificationService.consume_action_token(run_id, token, action="rejected")

    # Record rejection decision
    try:
        run_uuid = uuid.UUID(run_id) if len(run_id) == 36 else None
        if run_uuid:
            decision = ApprovalDecision(
                id=uuid.uuid4(),
                run_id=run_uuid,
                actor="developer",
                decision="REJECTED",
                policy_evaluation={"risk_level": "LOW", "status": "REJECTED"},
                risk_level="LOW",
                auto_merge_eligible=False,
                comments="Rejected by human reviewer",
                created_at=datetime.now(timezone.utc)
            )
            db.add(decision)
    except Exception as e:
        logger.debug(f"ApprovalDecision reject commit skipped: {e}")

    run.state = RunState.REJECTED.value
    run.current_stage = "approval"
    run.error_code = "REJECTED_BY_USER"
    run.error_message = "Patch was rejected during human review. Delivery cancelled."
    run.terminal_at = datetime.now(timezone.utc)
    db.commit()

    return {"status": "success", "decision": "REJECTED", "message": "Patch rejected. Delivery cancelled."}


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


@router.get("/{run_id}/repair-receipt")
def get_repair_receipt(run_id: str, db: Session = Depends(get_db)):
    """
    Returns the authoritative Repair Receipt proof artifact for a run.
    Projected deterministically from PostgreSQL with SHA-256 integrity hash.
    """
    from app.services.receipt_service import ReceiptService
    svc = ReceiptService(db)
    receipt = svc.generate_receipt(run_id)
    if not receipt:
        raise HTTPException(status_code=404, detail=f"Receipt not found for run {run_id}")
    return receipt


@router.get("/{run_id}/repair-receipt/download")
def download_repair_receipt(
    run_id: str,
    format: str = "json",
    db: Session = Depends(get_db)
):
    """
    Downloads the authoritative Repair Receipt artifact as JSON or Markdown attachment.
    """
    from fastapi.responses import Response
    from app.services.receipt_service import ReceiptService
    svc = ReceiptService(db)
    receipt = svc.generate_receipt(run_id)
    if not receipt:
        raise HTTPException(status_code=404, detail=f"Receipt not found for run {run_id}")

    filename = f"repair-receipt-{run_id[:8]}"
    if format.lower() == "markdown" or format.lower() == "md":
        content = receipt.ascii_receipt
        media_type = "text/markdown; charset=utf-8"
        filename += ".md"
    else:
        content = receipt.model_dump_json(indent=2)
        media_type = "application/json; charset=utf-8"
        filename += ".json"

    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "X-Receipt-Hash": receipt.receipt_hash,
        "X-Receipt-ID": receipt.receipt_id
    }
    return Response(content=content, media_type=media_type, headers=headers)


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
