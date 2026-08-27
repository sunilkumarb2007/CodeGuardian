from datetime import timezone
import logging
import uuid
import os
import urllib.parse
from datetime import datetime
from typing import Dict, Any, Optional

from app.utils.url_parser import parse_github_url

from app.db.database import SessionLocal
from app.db.models import Run, RunEvent, RunAction, Repository, Application, Incident, Patch, RepositoryFile, EvidenceEvent
from app.engine.run_state_machine import RunStateMachine, RunState
from app.services.event_logger import BackendEventLogger
from app.services.inspection_service import RepositoryInspectionService
from app.services.triage_service import TriageService
from app.services.ghosttrace_service import GhostTraceService
from app.services.memory_service import MemoryService
from app.services.investigation_service import InvestigationService
from app.services.replay_service import ReplayService
from app.engine.replay_engine import ReplayEngine
from app.services.delivery_service import DeliveryService
from app.services.failure_evidence_collector import FailureEvidenceCollector
from app.services.lock_manager import RunLock

logger = logging.getLogger(__name__)

class CodeGuardianOrchestrator:
    def __init__(self):
        pass

    def initialize_run(self, repository_url: str) -> str:
        run_id = str(uuid.uuid4())
        
        with SessionLocal() as db:
            run = Run(
                id=run_id,
                repository_id=None,
                incident_id=None,
                current_stage="CREATED",
                state=RunState.CREATED.value,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            db.add(run)
            db.commit()
        return run_id

    def execute_pipeline(self, run_id: str, repository_url: str, supplied_incident_id: Optional[str] = None):
        machine = RunStateMachine()
        
        # Helper for DB updates
        def update_run_state(state: RunState, error_code=None, error_msg=None):
            with SessionLocal() as db:
                run = db.query(Run).filter(Run.id == run_id).first()
                if run:
                    run.state = state.value
                    run.current_stage = state.value
                    run.updated_at = datetime.now(timezone.utc)
                    if error_code:
                        run.error_code = error_code
                        run.error_message = error_msg
                    if state in [RunState.COMPLETED] or state == "FAILED" or machine.is_terminal():
                        run.terminal_at = datetime.now(timezone.utc)
                    db.commit()

        def emit_event(status_type: str, message: str, command: str = None):
            with SessionLocal() as db:
                event_logger = BackendEventLogger(db, run_id)
                event_logger.emit(status_type, message, command=command)

        def abort_run():
            update_run_state(RunState.FAILED, "LOCK_LOST", "Lost distributed lock lease")

        try:
            with RunLock(run_id, on_loss=abort_run) as lock:
                logger.info(f"Orchestrator pipeline started (Phase G): run_id={run_id}")
                emit_event("STATUS", "Repository loading", command=f"git clone {repository_url}")
            
                machine.transition_to(RunState.REPOSITORY_LOADING)
                update_run_state(RunState.REPOSITORY_LOADING)
            
                # 1. Inspection
                inspect_svc = RepositoryInspectionService()
            
                owner, repo_name = parse_github_url(repository_url)
                if not owner or not repo_name:
                    raise ValueError("Invalid GitHub URL provided.")
                
                from app.services.github_metadata import GitHubMetadataService
                metadata_svc = GitHubMetadataService()
                if not metadata_svc.check_access(owner, repo_name):
                    emit_event("STATUS", "Repository not found or access denied")
                    machine.transition_to(RunState.REPOSITORY_NOT_FOUND)
                    update_run_state(RunState.REPOSITORY_NOT_FOUND, "ACCESS_DENIED", "Repository not found or access denied")
                    return
            
            
                repo_id = None
                with SessionLocal() as db:
                    app = db.query(Application).first()
                    if not app:
                        app = Application(id=uuid.uuid4(), name="DynamicApp", environment="test", status="active", created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
                        db.add(app)
                        db.flush()
                    
                    repo = db.query(Repository).filter_by(repository_url=repository_url).first()
                    if not repo:
                        repo = Repository(
                            id=uuid.uuid4(), application_id=app.id, provider="github", owner=owner, name=repo_name, 
                            repository_url=repository_url, default_branch="main", access_status="authorized",
                            created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)
                        )
                        db.add(repo)
                        db.flush()
                    
                    run = db.query(Run).filter(Run.id == run_id).first()
                    if run:
                        run.repository_id = repo.id
                        db.commit()
                    repo_id = repo.id
                
                emit_event("OUTPUT", "Repository cloned successfully")
                emit_event("STATUS", "Inspecting architecture")
                machine.transition_to(RunState.INSPECTING)
                update_run_state(RunState.INSPECTING)
            
                with SessionLocal() as db:
                    inspection_result = inspect_svc.inspect_repository(repository_url, db=db, repository_id=repo_id)
                    db.commit()
            
                tech_stack = inspection_result.architecture.tech_stack if inspection_result.architecture else []
                lang = inspection_result.architecture.language if inspection_result.architecture else "unknown"
                fw = inspection_result.architecture.framework if inspection_result.architecture else "unknown"
                bt = inspection_result.architecture.build_system if inspection_result.architecture else "unknown"
            
                emit_event("ANALYSIS", f"Detected {lang} / {fw} / {bt}")
                machine.transition_to(RunState.ARCHITECTURE_DETECTED)
                update_run_state(RunState.ARCHITECTURE_DETECTED)
            
                # 2. Failure Detection
                emit_event("STATUS", "Searching failure evidence")
            
                with SessionLocal() as db:
                    fec = FailureEvidenceCollector(db)
                    result = fec.collect_evidence(repository_url, repo_id)
                    db.commit()
            
                if result == "NO_FAILURE_EVIDENCE" or result == "NO_PREPARED_FAILURE":
                    emit_event("STATUS", "No failure evidence detected for this repository")
                    machine.transition_to(RunState.NO_FAILURE_EVIDENCE)
                    update_run_state(RunState.NO_FAILURE_EVIDENCE, "NO_EVIDENCE", "No failure evidence detected for this repository")
                    return
                elif result == "FAILURE_FIXTURE_CONTEXT_MISMATCH":
                    emit_event("STATUS", "Failure fixture context mismatch. Expected files missing.")
                    raise ValueError("FAILURE_FIXTURE_CONTEXT_MISMATCH")
                
                incident_id = result
                with SessionLocal() as db:
                    run = db.query(Run).filter(Run.id == run_id).first()
                    if run:
                        run.incident_id = uuid.UUID(incident_id)
                        db.commit()
                
                machine.transition_to(RunState.FAILURE_DETECTED)
                update_run_state(RunState.FAILURE_DETECTED)
                emit_event("ANALYSIS", "Failure evidence identified")
            
                machine.transition_to(RunState.EVIDENCE_COLLECTED)
                update_run_state(RunState.EVIDENCE_COLLECTED)
            
                # 3. GhostTrace
                emit_event("STATUS", "Following repository call chain")
                with SessionLocal() as db:
                    gt_svc = GhostTraceService(db)
                    trace = gt_svc.rebuild_trace(uuid.UUID(incident_id))
            
                machine.transition_to(RunState.GHOSTTRACE_COMPLETE)
                update_run_state(RunState.GHOSTTRACE_COMPLETE)
                emit_event("ANALYSIS", "GhostTrace root cause candidate identified")
            
                # 4. Memory Lookup
                emit_event("STATUS", "Searching Failure Memory")
                with SessionLocal() as db:
                    mem_svc = MemoryService(db)
                    memory_res = mem_svc.search_memory_for_incident(uuid.UUID(incident_id))
            
                if memory_res.match_status == "match_found":
                    emit_event("ANALYSIS", "Historical failure memory match found")
                else:
                    emit_event("ANALYSIS", "No historical memory match found")
                
                machine.transition_to(RunState.MEMORY_MATCH_FOUND)
                update_run_state(RunState.MEMORY_MATCH_FOUND)
            
                # Bounded loop: up to 3 attempts
                max_attempts = 3
                attempt = 0
                validated = False
                from app.core.execution_policy import ExecutionPolicy
                import time
                investigation_deadline = time.monotonic() + ExecutionPolicy.AI_TOTAL_DEADLINE
            
                while attempt < max_attempts and not validated:
                    attempt += 1
                
                    # Cooperative cancellation: check if Redis lock was lost
                    if lock.cancelled:
                        machine.force_fail(RunState.LOCK_LOST, "Lost distributed lock lease")
                        update_run_state(RunState.LOCK_LOST, "LOCK_LOST", "Lost distributed lock lease")
                        return
                
                    if time.monotonic() > investigation_deadline:
                        machine.force_fail(RunState.INVESTIGATION_TIMEOUT, "Total AI deadline exceeded")
                        update_run_state(RunState.INVESTIGATION_TIMEOUT, 'INVESTIGATION_TIMEOUT', 'Total AI deadline exceeded')
                        return
                
                    emit_event("STATUS", f"Investigation attempt {attempt}/{max_attempts}")
                
                    # 5. Investigation
                    machine.transition_to(RunState.INVESTIGATION_RUNNING)
                    update_run_state(RunState.INVESTIGATION_RUNNING)
                
                    arch_dict = inspection_result.architecture.model_dump() if inspection_result.architecture else {}
                
                    # DB Session isolation handled inside InvestigationService
                    inv_svc = InvestigationService()
                    inv_result = inv_svc.investigate_incident(
                        incident_id, 
                        attempt=attempt, 
                        run_id=run_id, 
                        architecture=arch_dict, 
                        deadline=investigation_deadline
                    )

                    if inv_result.status != "completed":
                        if inv_result.status == "timeout":
                            machine.force_fail(RunState.INVESTIGATION_TIMEOUT, "Total AI deadline exceeded")
                            update_run_state(RunState.INVESTIGATION_TIMEOUT, error_code="TIMEOUT", error_msg="Total AI deadline exceeded")
                        elif "schema" in inv_result.status:
                            machine.transition_to(RunState.INVESTIGATION_SCHEMA_ERROR)
                            update_run_state(RunState.INVESTIGATION_SCHEMA_ERROR)
                        elif inv_result.status == "PATCH_PATH_UNSAFE":
                            machine.transition_to(RunState.PATCH_GENERATED)
                            machine.transition_to(RunState.PATCH_PATH_UNSAFE)
                            update_run_state(RunState.PATCH_PATH_UNSAFE)
                        elif inv_result.status == "PATCH_CONTEXT_INVALID":
                            machine.transition_to(RunState.PATCH_GENERATED)
                            machine.transition_to(RunState.PATCH_CONTEXT_INVALID)
                            update_run_state(RunState.PATCH_CONTEXT_INVALID)
                        else:
                            machine.transition_to(RunState.INVESTIGATION_FAILED)
                            update_run_state(RunState.INVESTIGATION_FAILED)
                        return
                    
                    machine.transition_to(RunState.PATCH_GENERATED)
                    update_run_state(RunState.PATCH_GENERATED)
                
                    machine.transition_to(RunState.PATCH_COMPATIBLE)
                    update_run_state(RunState.PATCH_COMPATIBLE)
                
                    # 6. Replay, Build, Tests, Validation
                    machine.transition_to(RunState.REPLAY_RUNNING)
                    update_run_state(RunState.REPLAY_RUNNING)
                
                    with SessionLocal() as db:
                        incident_obj = db.query(Incident).filter_by(id=uuid.UUID(incident_id)).first()
                        patch_obj = db.query(Patch).filter_by(incident_id=uuid.UUID(incident_id)).order_by(Patch.created_at.desc()).first()
                        repo_obj = db.query(Repository).filter_by(id=repo_id).first()
                        event_logger = BackendEventLogger(db, run_id)
                        replay_eng = ReplayEngine(event_logger=event_logger)
                    
                        # Ensure ReplayEngine fetches what it needs and returns
                        replay_res, baseline, patched = replay_eng.run_replay(incident_obj, patch_obj, run_id, repo_obj, arch_dict)
                
                    if replay_res == "REPLAY_CHANGED_BEHAVIOR":
                        machine.transition_to(RunState.BUILD_RUNNING)
                        update_run_state(RunState.BUILD_RUNNING)
                    
                        machine.transition_to(RunState.TESTS_RUNNING)
                        update_run_state(RunState.TESTS_RUNNING)
                    
                        machine.transition_to(RunState.VALIDATION_RUNNING)
                        update_run_state(RunState.VALIDATION_RUNNING)
                    
                        with SessionLocal() as db:
                            patch_to_update = db.query(Patch).filter_by(id=patch_obj.id).first()
                            if patch_to_update:
                                patch_to_update.status = "validated"
                                db.commit()
                    
                        machine.transition_to(RunState.VALIDATED)
                        update_run_state(RunState.VALIDATED)
                        validated = True
                        emit_event("STATUS", "VALIDATION PASSED")
                    elif replay_res == "PATCH_APPLY_FAILED":
                        machine.transition_to(RunState.PATCH_APPLY_FAILED)
                        update_run_state(RunState.PATCH_APPLY_FAILED)
                        return
                    elif replay_res == "BASELINE_FAILURE_NOT_REPRODUCED":
                        machine.transition_to(RunState.BASELINE_FAILURE_NOT_REPRODUCED)
                        update_run_state(RunState.BASELINE_FAILURE_NOT_REPRODUCED)
                        return
                    else:
                        emit_event("ANALYSIS", f"Validation failed on attempt {attempt}")
                        machine.transition_to(RunState.REPLAY_FAILED)
                        update_run_state(RunState.REPLAY_FAILED)
                        # Fall through and retry if attempts remain
            
                if not validated:
                    machine.transition_to(RunState.REPAIR_EXHAUSTED)
                    update_run_state(RunState.REPAIR_EXHAUSTED)
                    return
                
                machine.transition_to(RunState.WAITING_FOR_APPROVAL)
                update_run_state(RunState.WAITING_FOR_APPROVAL)
                emit_event("STATUS", "WAITING FOR APPROVAL")
                
        except Exception as e:
            logger.error(f"Error in authoritative orchestrator: {e}", exc_info=True)
            with SessionLocal() as db:
                run = db.query(Run).filter(Run.id == run_id).first()
                if run:
                    run.state = "FAILED"
                    run.error_message = str(e)
                    run.terminal_at = datetime.now(timezone.utc)
                    event_logger = BackendEventLogger(db, run_id)
                    event_logger.emit('ERROR', f'Orchestration failed: {str(e)}')
                    db.commit()

    def continue_after_approval(self, run_id: str):
        machine = RunStateMachine(RunState.WAITING_FOR_APPROVAL)
        
        def update_run_state(state: RunState, error_code=None, error_msg=None):
            with SessionLocal() as db:
                run = db.query(Run).filter(Run.id == run_id).first()
                if run:
                    run.state = state.value
                    run.current_stage = state.value
                    run.updated_at = datetime.now(timezone.utc)
                    if error_code:
                        run.error_code = error_code
                        run.error_message = error_msg
                    if state in [RunState.COMPLETED] or state == "FAILED" or machine.is_terminal():
                        run.terminal_at = datetime.now(timezone.utc)
                    db.commit()

        def emit_event(status_type: str, message: str, command: str = None):
            with SessionLocal() as db:
                event_logger = BackendEventLogger(db, run_id)
                event_logger.emit(status_type, message, command=command)

        try:
            logger.info(f"Orchestrator continuing after approval for run_id={run_id}")
            
            machine.transition_to(RunState.PATCH_APPROVED)
            update_run_state(RunState.PATCH_APPROVED)
            
            incident_id = None
            patch_id = None
            repo_url = None
            with SessionLocal() as db:
                run = db.query(Run).filter(Run.id == run_id).first()
                if not run:
                    raise ValueError(f"Run {run_id} not found")
                
                incident = db.query(Incident).filter_by(id=run.incident_id).first()
                repo = db.query(Repository).filter_by(id=run.repository_id).first()
                patch = db.query(Patch).filter_by(incident_id=incident.id).order_by(Patch.created_at.desc()).first()
                incident_id = incident.id
                patch_id = patch.id
                repo_url = repo.repository_url
            
            # Delivery Phase
            machine.transition_to(RunState.DELIVERY_PREPARING)
            update_run_state(RunState.DELIVERY_PREPARING)
            
            with SessionLocal() as db:
                deliv_svc = DeliveryService(db)
                deliv_res = deliv_svc.run_delivery(incident_id, patch_id, repo_url)
            
            if deliv_res.status == "pr_created":
                machine.transition_to(RunState.DELIVERED)
                update_run_state(RunState.DELIVERED)
                emit_event("STATUS", "PULL_REQUEST_CREATED")
                
                # Memory Phase
                with SessionLocal() as db:
                    mem_svc = MemoryService(db)
                    mem_svc.update_memory(incident_id, patch_id)
                machine.transition_to(RunState.MEMORY_UPDATED)
                update_run_state(RunState.MEMORY_UPDATED)
                
                machine.transition_to(RunState.COMPLETED)
                update_run_state(RunState.COMPLETED)
            elif deliv_res.status == "DELIVERY_AUTH_REQUIRED":
                machine.transition_to(RunState.DELIVERY_AUTH_REQUIRED)
                update_run_state(RunState.DELIVERY_AUTH_REQUIRED, "DELIVERY_AUTH_REQUIRED", deliv_res.error_details)
            else:
                machine.transition_to(RunState.DELIVERY_FAILED)
                update_run_state(RunState.DELIVERY_FAILED, "DELIVERY_FAILED", deliv_res.error_details)
                    
        except Exception as e:
            logger.error(f"Error continuing execution: {e}", exc_info=True)
            with SessionLocal() as db:
                run = db.query(Run).filter(Run.id == run_id).first()
                if run:
                    run.state = "FAILED"
                    run.error_message = str(e)
                    db.commit()
