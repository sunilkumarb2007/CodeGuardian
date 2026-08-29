from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.db.database import get_db
from app.schemas.incident import IncidentResponse, IncidentDetailResponse, IncidentIngestRequest, IncidentIngestResponse
from app.schemas.evidence import EvidenceResponse
from app.schemas.trace import GhostTraceResponse
from app.schemas.memory import MemorySearchResponse
from app.schemas.investigation import InvestigationResult
from app.schemas.replay import ReplayResponse
from app.schemas.validation import ValidationRunResponse
from app.schemas.github import PullRequestDeliveryResponse
from fastapi import BackgroundTasks

from app.services.incident_service import IncidentService
from app.services.evidence_service import EvidenceService
from app.services.ghosttrace_service import GhostTraceService
from app.services.memory_service import MemoryService
from app.services.investigation_service import InvestigationService

router = APIRouter()

@router.post("/ingest", response_model=IncidentIngestResponse, status_code=202)
def ingest_incident(request: IncidentIngestRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    service = IncidentService(db)
    result = service.ingest_incident(request, background_tasks)
    return result

@router.post("/webhook/{source}", response_model=IncidentIngestResponse, status_code=202)
def ingest_provider_webhook(
    source: str,
    payload: dict,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Provider-neutral Ingestion Gateway.
    Accepts raw webhooks from Render, Vercel, AWS, OTel, etc.,
    normalizes them, and launches autonomous investigation.
    """
    from app.services.incident_adapters import get_adapter_for_source
    adapter = get_adapter_for_source(source)
    normalized = adapter.normalize(payload)
    
    # Map normalized incident to IncidentIngestRequest
    ingest_req = IncidentIngestRequest(
        repository=normalized.repository,
        repository_id=UUID(normalized.repository_id) if normalized.repository_id else None,
        branch=normalized.branch,
        commit_sha=normalized.commit_sha,
        environment=normalized.environment,
        provider=normalized.provider,
        project=normalized.project,
        deployment_id=normalized.deployment_id,
        service=normalized.service,
        endpoint=normalized.endpoint,
        status_code=normalized.status_code,
        request_id=normalized.request_id,
        trace_id=normalized.trace_id,
        span_id=normalized.span_id,
        exception=normalized.exception,
        message=normalized.message,
        stack_trace=normalized.stack_trace,
        timestamp=normalized.timestamp,
        source=normalized.source,
        metadata=normalized.metadata,
    )
    
    service = IncidentService(db)
    return service.ingest_incident(ingest_req, background_tasks)


@router.get("", response_model=List[IncidentResponse])
def get_incidents(db: Session = Depends(get_db)):
    service = IncidentService(db)
    return service.get_all_incidents()

@router.get("/{incident_id}", response_model=IncidentDetailResponse)
def get_incident(incident_id: UUID, db: Session = Depends(get_db)):
    service = IncidentService(db)
    incident = service.get_incident_detail(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident

@router.get("/{incident_id}/evidence", response_model=List[EvidenceResponse])
def get_incident_evidence(incident_id: UUID, db: Session = Depends(get_db)):
    # Verify incident exists first
    service = IncidentService(db)
    if not service.get_incident_detail(incident_id):
        raise HTTPException(status_code=404, detail="Incident not found")
        
    ev_service = EvidenceService(db)
    return ev_service.get_evidence_for_incident(incident_id)

@router.get("/{incident_id}/trace", response_model=GhostTraceResponse)
def get_incident_trace(incident_id: UUID, db: Session = Depends(get_db)):
    # Verify incident exists first
    service = IncidentService(db)
    if not service.get_incident_detail(incident_id):
        raise HTTPException(status_code=404, detail="Incident not found")
        
    trace_service = GhostTraceService(db)
    trace = trace_service.get_trace_for_incident(incident_id)
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found for incident")
    return trace

@router.post("/{incident_id}/trace/rebuild", response_model=GhostTraceResponse)
def rebuild_incident_trace(incident_id: UUID, db: Session = Depends(get_db)):
    service = IncidentService(db)
    if not service.get_incident_detail(incident_id):
        raise HTTPException(status_code=404, detail="Incident not found")
        
    trace_service = GhostTraceService(db)
    trace = trace_service.rebuild_trace(incident_id)
    return trace

@router.get("/{incident_id}/memory", response_model=MemorySearchResponse)
def get_incident_memory(incident_id: UUID, db: Session = Depends(get_db)):
    # Verify incident exists first
    service = IncidentService(db)
    if not service.get_incident_detail(incident_id):
        raise HTTPException(status_code=404, detail="Incident not found")
        
    mem_service = MemoryService(db)
    response = mem_service.search_memory_for_incident(incident_id)
    if response.match_status == "error":
        raise HTTPException(status_code=500, detail="Error during memory search")
    return response

@router.post("/{incident_id}/investigate", response_model=InvestigationResult)
def investigate_incident(incident_id: UUID, db: Session = Depends(get_db)):
    service = IncidentService(db)
    if not service.get_incident_detail(incident_id):
        raise HTTPException(status_code=404, detail="Incident not found")
        
    inv_service = InvestigationService(db)
    result = inv_service.run_investigation(incident_id)
    
    if result.status == "error_incident_not_found":
        raise HTTPException(status_code=404, detail="Incident not found")
    if result.status == "error_trace_not_found":
        raise HTTPException(status_code=400, detail="GhostTrace must be run before investigation")
    if result.status == "error_llm_failed":
        raise HTTPException(status_code=500, detail="Investigation engine failed to produce a valid response")
        
    return result

@router.post("/{incident_id}/patches/{patch_id}/replay", response_model=ReplayResponse)
def replay_patch(
    incident_id: UUID,
    patch_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Phase 6: Ghost Replay execution.
    Executes a baseline replay and a patched replay in an isolated environment.
    """
    try:
        from app.services.replay_service import ReplayService
        replay_service = ReplayService(db)
        return replay_service.run_replay(incident_id, patch_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{incident_id}/patches/{patch_id}/validate", response_model=ValidationRunResponse)
def validate_patch(
    incident_id: UUID,
    patch_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Phase 7: Validation Engine execution.
    Executes context check, build, tests, replay validation and safety checks.
    """
    try:
        from app.services.validation_service import ValidationService
        validation_service = ValidationService(db)
        return validation_service.run_validation(incident_id, patch_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{incident_id}/patches/{patch_id}/deliver", response_model=PullRequestDeliveryResponse)
def deliver_patch(
    incident_id: UUID,
    patch_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Phase 8: GitHub Pull Request Delivery.
    Delivers a validated patch to a configured GitHub repository.
    """
    try:
        from app.services.delivery_service import DeliveryService
        delivery_service = DeliveryService(db)
        return delivery_service.run_delivery(incident_id, patch_id)
    except ValueError as e:
        if "GITHUB_INFRASTRUCTURE_FAILURE" in str(e):
            raise HTTPException(status_code=503, detail="GITHUB_INFRASTRUCTURE_FAILURE")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

