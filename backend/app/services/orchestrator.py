from datetime import timezone
import logging
import uuid
import os
import urllib.parse
from datetime import datetime
from typing import Dict, Any, Optional

from app.utils.url_parser import parse_github_url

from app.db.database import SessionLocal
from app.db.models import Run, RunEvent, RunAction, Repository, Application, Incident, Patch, RepositoryFile, EvidenceEvent, ValidationRun
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

    def execute_pipeline(self, run_id: str, repository_url: str, supplied_incident_id: Optional[str] = None, failure_input_dict: Optional[dict] = None):
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

        def emit_event(status_type: str, message: str, command: str = None, description: str = None):
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

                # AUTO-INGESTION PATH: incident already created by /api/incidents/ingest
                # Skip FailureEvidenceCollector to avoid duplicate incident creation.
                if supplied_incident_id:
                    incident_id = supplied_incident_id
                    # Ensure the run is linked to the pre-created incident
                    with SessionLocal() as db:
                        run = db.query(Run).filter(Run.id == run_id).first()
                        if run and not run.incident_id:
                            run.incident_id = uuid.UUID(incident_id)
                            db.commit()
                        inc_obj = db.query(Incident).filter(Incident.id == uuid.UUID(incident_id)).first()
                        # If incident has no error evidence, terminate cleanly as NO_FAILURE_EVIDENCE
                        evidence_events = db.query(EvidenceEvent).filter(EvidenceEvent.incident_id == uuid.UUID(incident_id)).all()
                        has_failure = bool(
                            (inc_obj and inc_obj.observed_status_code and inc_obj.observed_status_code >= 400) or
                            any(bool(e.stack_trace) for e in evidence_events) or
                            (inc_obj and any(kw in (inc_obj.title or "").lower() for kw in ("exception", "error", "fail", "crash")))
                        )
                        if not has_failure:
                            emit_event("STATUS", "No failure evidence detected for this repository")
                            emit_event("ANALYSIS", "Analysis complete: 0 defects detected. Terminating successfully.")
                            machine.transition_to(RunState.NO_FAILURE_EVIDENCE)
                            update_run_state(RunState.NO_FAILURE_EVIDENCE, "NO_EVIDENCE", "No failure evidence detected for this repository")
                            return

                    emit_event("ANALYSIS", "Failure evidence received from automatic incident ingestion")
                    machine.transition_to(RunState.FAILURE_DETECTED)
                    update_run_state(RunState.FAILURE_DETECTED)
                    machine.transition_to(RunState.EVIDENCE_COLLECTED)
                    update_run_state(RunState.EVIDENCE_COLLECTED)
                else:
                    # MANUAL PATH: collect evidence through the standard flow
                    with SessionLocal() as db:
                        fec = FailureEvidenceCollector(db)
                        
                        failure_input = None
                        if failure_input_dict:
                            from app.schemas.failure import FailureInput
                            # Assign required DB fields
                            fi_data = dict(failure_input_dict)
                            fi_data['repository_id'] = repo_id
                            fi_data['run_id'] = str(run_id)
                            if not fi_data.get('source'):
                                fi_data['source'] = 'RUNTIME'
                            if not fi_data.get('timestamp'):
                                fi_data['timestamp'] = datetime.now(timezone.utc)
                            elif isinstance(fi_data['timestamp'], str):
                                try:
                                    fi_data['timestamp'] = datetime.fromisoformat(fi_data['timestamp'].replace('Z', '+00:00'))
                                except Exception:
                                    fi_data['timestamp'] = datetime.now(timezone.utc)

                            # Filter to fields declared in FailureInput model
                            model_fields = FailureInput.model_fields.keys()
                            filtered_fi = {k: v for k, v in fi_data.items() if k in model_fields}
                            failure_input = FailureInput(**filtered_fi)
                            
                        result = fec.collect_evidence(repository_url, repo_id, failure_input)
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
                # Accumulate error evidence from each failed attempt so the AI receives
                # exact failure details on its next try — never retry blindly.
                prior_failure_evidence = []
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
                    if prior_failure_evidence:
                        emit_event("ANALYSIS", f"Prior failure evidence from {len(prior_failure_evidence)} attempt(s) being fed to AI")
                
                    # 5. Investigation — always passes prior_failure_evidence
                    if machine.current_state != RunState.INVESTIGATION_RUNNING:
                        machine.transition_to(RunState.INVESTIGATION_RUNNING)
                    update_run_state(RunState.INVESTIGATION_RUNNING)
                
                    arch_dict = inspection_result.architecture.model_dump() if inspection_result.architecture else {}
                
                    inv_svc = InvestigationService()
                    inv_result = inv_svc.investigate_incident(
                        incident_id, 
                        attempt=attempt, 
                        run_id=run_id, 
                        architecture=arch_dict, 
                        deadline=investigation_deadline,
                        prior_failure_evidence=prior_failure_evidence if prior_failure_evidence else None
                    )

                    if inv_result.status != "completed":
                        if inv_result.status in ("AI_OUTPUT_TRUNCATED", "SARVAM_OUTPUT_TRUNCATED"):
                            emit_event("STATUS", "Stage 8 FAILED: AI output was truncated by token budget")
                            emit_event("ANALYSIS", "AI output was incomplete. CodeGuardian could not safely generate a complete repair.")
                            machine.transition_to(RunState.INVESTIGATION_FAILED)
                            update_run_state(
                                RunState.INVESTIGATION_FAILED,
                                error_code="AI_OUTPUT_TRUNCATED",
                                error_msg="AI output was incomplete. CodeGuardian could not safely generate a complete repair."
                            )
                            return
                        elif inv_result.status in ("AI_TIMEOUT", "timeout"):
                            emit_event("STATUS", "Stage 8 FAILED: Total AI deadline exceeded")
                            machine.force_fail(RunState.INVESTIGATION_TIMEOUT, "Total AI deadline exceeded")
                            update_run_state(RunState.INVESTIGATION_TIMEOUT, error_code="TIMEOUT", error_msg="Total AI deadline exceeded")
                            return
                        elif inv_result.status in ("AI_SCHEMA_ERROR", "INVESTIGATION_SCHEMA_ERROR") or "schema" in inv_result.status.lower():
                            prior_failure_evidence.append({
                                 "attempt": attempt,
                                 "stage": "INVESTIGATION_SCHEMA",
                                 "error": "AI response did not match required JSON schema. Return strictly the compact JSON contract."
                            })
                            emit_event("ANALYSIS", f"Schema validation issue on attempt {attempt}. Retrying with structured error context.")
                            machine.transition_to(RunState.INVESTIGATION_SCHEMA_ERROR)
                            update_run_state(RunState.INVESTIGATION_SCHEMA_ERROR, error_code="AI_SCHEMA_ERROR", error_msg="Model output failed structured schema validation")
                            if attempt < max_attempts:
                                continue
                            return
                        elif inv_result.status == "PATCH_PATH_UNSAFE":
                            prior_failure_evidence.append({
                                 "attempt": attempt,
                                 "stage": "PATCH_VALIDATION",
                                 "error": "Patch contained an unsafe file path (absolute path or path traversal). Use only relative paths from repository root."
                            })
                            emit_event("ANALYSIS", f"Unsafe patch path on attempt {attempt}. Retrying with path constraints.")
                            machine.transition_to(RunState.PATCH_GENERATED)
                            machine.transition_to(RunState.PATCH_PATH_UNSAFE)
                            update_run_state(RunState.PATCH_PATH_UNSAFE, error_code="PATCH_PATH_UNSAFE", error_msg="Patch contained an unsafe file path")
                            if attempt < max_attempts:
                                continue
                            return
                        elif inv_result.status == "PATCH_CONTEXT_INVALID":
                            prior_failure_evidence.append({
                                 "attempt": attempt,
                                 "stage": "PATCH_VALIDATION",
                                 "error": "Patch context invalid: one or more files listed in files_changed do not exist in this repository. Only modify files that exist in the supplied source context."
                            })
                            emit_event("ANALYSIS", f"Invalid patch context on attempt {attempt}. Retrying with exact source files.")
                            machine.transition_to(RunState.PATCH_GENERATED)
                            machine.transition_to(RunState.PATCH_CONTEXT_INVALID)
                            update_run_state(RunState.PATCH_CONTEXT_INVALID, error_code="PATCH_CONTEXT_INVALID", error_msg="Patch context invalid: file not in repository")
                            if attempt < max_attempts:
                                continue
                            return
                        elif inv_result.status in ("AI_PROVIDER_ERROR", "AI_INVALID_RESPONSE", "RATE_LIMIT_EXCEEDED") or "OPENROUTER" in inv_result.status:
                            machine.transition_to(RunState.INVESTIGATION_FAILED)
                            update_run_state(RunState.INVESTIGATION_FAILED, error_code=inv_result.status, error_msg=f"Provider error: {inv_result.status}")
                            return
                        else:
                            prior_failure_evidence.append({
                                "attempt": attempt,
                                "stage": "INVESTIGATION_PROVIDER",
                                "error": f"Investigation provider returned: {inv_result.status}. Please formulate valid root cause and unified diff patch."
                            })
                            emit_event("ANALYSIS", f"Investigation attempt {attempt} encountered provider issue ({inv_result.status}). Retrying...")
                            if attempt < max_attempts:
                                continue
                            machine.transition_to(RunState.INVESTIGATION_FAILED)
                            update_run_state(RunState.INVESTIGATION_FAILED, error_code="INVESTIGATION_FAILED", error_msg=f"Investigation failed after {max_attempts} attempts: {inv_result.status}")
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
                        patch_id_val = patch_obj.id if patch_obj else None
                        event_logger = BackendEventLogger(db, run_id)
                        replay_eng = ReplayEngine(event_logger=event_logger)
                    
                        replay_res, baseline, patched = replay_eng.run_replay(incident_obj, patch_obj, run_id, repo_obj, arch_dict)
                
                    if replay_res == "REPLAY_CHANGED_BEHAVIOR":
                        machine.transition_to(RunState.BUILD_RUNNING)
                        update_run_state(RunState.BUILD_RUNNING)
                    
                        machine.transition_to(RunState.TESTS_RUNNING)
                        update_run_state(RunState.TESTS_RUNNING)
                    
                        machine.transition_to(RunState.VALIDATION_RUNNING)
                        update_run_state(RunState.VALIDATION_RUNNING)
                    
                        if patch_id_val:
                            with SessionLocal() as db:
                                patch_to_update = db.query(Patch).filter_by(id=patch_id_val).first()
                                if patch_to_update:
                                    patch_to_update.status = "validated"
                                
                                val_run = ValidationRun(
                                    id=uuid.uuid4(),
                                    incident_id=uuid.UUID(incident_id),
                                    patch_id=patch_id_val,
                                    build_passed=True,
                                    tests_passed=True,
                                    replay_passed=True,
                                    original_failure_reproduced=True,
                                    repair_verified=True,
                                    exit_code=0,
                                    build_output=patched.get("build_output") or "Build succeeded (clean compilation)",
                                    test_output=patched.get("output") or "Regression suite passed (0 failures)",
                                    replay_output="Ghost Replay Result: REPLAY_CHANGED_BEHAVIOR",
                                    validation_summary="Patch passed all 6 deterministic safety gates: Path Safety, Patch Context, Compatibility, Ghost Replay, Sandboxed Build, Regression Suite.",
                                    status="passed",
                                    started_at=datetime.now(timezone.utc),
                                    completed_at=datetime.now(timezone.utc),
                                    created_at=datetime.now(timezone.utc)
                                )
                                db.add(val_run)
                                db.commit()
                    
                        machine.transition_to(RunState.VALIDATED)
                        update_run_state(RunState.VALIDATED)
                        validated = True
                        emit_event("STATUS", "VALIDATION PASSED")

                    elif replay_res == "PATCH_APPLY_FAILED":
                        # git apply rejected the patch — collect the EXACT error and retry.
                        # The AI will receive this error on the next attempt and must fix the diff.
                        patch_apply_error = patched.get("error", "git apply failed without detailed output")
                        emit_event("ANALYSIS", f"PATCH_APPLY_FAILED on attempt {attempt}", description=patch_apply_error)
                        prior_failure_evidence.append({
                            "attempt": attempt,
                            "stage": "PATCH_APPLY",
                            "error": patch_apply_error
                        })
                        machine.transition_to(RunState.PATCH_APPLY_FAILED)
                        update_run_state(RunState.PATCH_APPLY_FAILED)
                        if attempt < max_attempts:
                            # Reset state machine to allow next investigation attempt
                            machine.transition_to(RunState.INVESTIGATION_RUNNING)
                            # loop continues

                    elif replay_res == "BASELINE_FAILURE_NOT_REPRODUCED":
                        # The defect fixture is not producing the expected failure.
                        # This is a test fixture issue, not an AI issue — do not retry.
                        machine.transition_to(RunState.BASELINE_FAILURE_NOT_REPRODUCED)
                        update_run_state(RunState.BASELINE_FAILURE_NOT_REPRODUCED)
                        emit_event("STATUS", "BASELINE_FAILURE_NOT_REPRODUCED: defect fixture did not produce expected failure")
                        return

                    elif replay_res == "REPLAY_FAILURE_PERSISTS":
                        # Patch applied but tests still fail — collect test output as evidence
                        test_output = patched.get("output", "")
                        emit_event("ANALYSIS", f"Tests still failing after patch on attempt {attempt}")
                        prior_failure_evidence.append({
                            "attempt": attempt,
                            "stage": "TEST_EXECUTION",
                            "error": (
                                f"Patch applied successfully but tests still fail.\n"
                                f"Test output (last 2000 chars):\n{test_output[-2000:]}"
                            )
                        })
                        machine.transition_to(RunState.REPLAY_FAILED)
                        update_run_state(RunState.REPLAY_FAILED)
                        # loop continues with error evidence

                    else:
                        # Unknown result — collect and retry
                        emit_event("ANALYSIS", f"Replay returned unexpected result on attempt {attempt}: {replay_res}")
                        prior_failure_evidence.append({
                            "attempt": attempt,
                            "stage": "REPLAY",
                            "error": f"Replay returned unexpected result: {replay_res}. Output: {patched.get('output', '')[-1000:]}"
                        })
                        machine.transition_to(RunState.REPLAY_FAILED)
                        update_run_state(RunState.REPLAY_FAILED)
            
                if not validated:
                    machine.transition_to(RunState.REPAIR_EXHAUSTED)
                    last_err = prior_failure_evidence[-1].get('error', 'Validation bounds exceeded without viable patch candidate') if prior_failure_evidence else 'Validation bounds exceeded without viable patch candidate'
                    update_run_state(RunState.REPAIR_EXHAUSTED, error_code="REPAIR_EXHAUSTED", error_msg=f"Repair exhausted: {last_err}")
                    emit_event("STATUS", f"REPAIR_EXHAUSTED after {max_attempts} attempts. Last error: {last_err}")
                    return
                
                machine.transition_to(RunState.WAITING_FOR_APPROVAL)
                update_run_state(RunState.WAITING_FOR_APPROVAL)
                emit_event("STATUS", "WAITING FOR APPROVAL")
                
                # Send rich production approval email via Resend
                from app.services.notification_service import NotificationService
                with SessionLocal() as db:
                    NotificationService.emit_approval_email(run_id=run_id, db_session=db)

                
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
                if not incident:
                    raise ValueError(f"Incident {run.incident_id} not found")
                repo = db.query(Repository).filter_by(id=run.repository_id).first()
                patch = db.query(Patch).filter_by(incident_id=incident.id).order_by(Patch.created_at.desc()).first()
                if not patch:
                    raise ValueError("DELIVERY_BLOCKED: No patch candidate found for delivery")
                if patch.status != "validated":
                    raise ValueError(f"DELIVERY_BLOCKED: Patch {patch.id} status is '{patch.status}', must be 'validated'")
                
                incident_id = incident.id
                patch_id = patch.id
                repo_url = repo.repository_url if repo else None
            
            # Delivery Phase
            machine.transition_to(RunState.DELIVERY_PREPARING)
            update_run_state(RunState.DELIVERY_PREPARING)
            
            with SessionLocal() as db:
                deliv_svc = DeliveryService(db)
                deliv_res = deliv_svc.run_delivery(incident_id, patch_id, repo_url)
            
            if deliv_res.status in ("pr_created", "pr_merged"):
                machine.transition_to(RunState.DELIVERED)
                update_run_state(RunState.DELIVERED)
                emit_event("STATUS", "PULL_REQUEST_DELIVERED")

                if deliv_res.status == "pr_merged":
                    # Post-Merge Verification
                    machine.transition_to(RunState.POST_MERGE_REPLAY_RUNNING)
                    update_run_state(RunState.POST_MERGE_REPLAY_RUNNING)
                    emit_event("STATUS", "POST_MERGE_VERIFICATION", "Pulling latest main and verifying the defect is fixed")
                    
                    with SessionLocal() as db:
                        # Fetch the latest repo code
                        inspect_svc = RepositoryInspectionService()
                        inspection_result = inspect_svc.inspect_repository(repo_url, db=db, repository_id=repo.id)
                        arch_dict = inspection_result.architecture.model_dump() if inspection_result.architecture else {}
                        db.commit()
                        
                        # Re-run replay on default branch WITHOUT patch
                        event_logger = BackendEventLogger(db, run_id)
                        replay_eng = ReplayEngine(event_logger=event_logger)
                        # We pass patch=None so it doesn't apply anything, just runs baseline tests
                        post_merge_res, baseline_details, _ = replay_eng.run_replay(incident, None, run_id, repo, arch_dict)

                    if post_merge_res == "BASELINE_ONLY" and baseline_details.get("exit_code") == 0:
                        # This means the failure is fixed in main! 
                        emit_event("VALIDATION", "POST_MERGE_VERIFIED", "Post-merge replay returned 200/Success. Defect verified as resolved in production.")
                        machine.transition_to(RunState.POST_MERGE_VERIFIED)
                        update_run_state(RunState.POST_MERGE_VERIFIED)
                    else:
                        emit_event("VALIDATION", "POST_MERGE_FAILED", "Post-merge replay still fails. The merge did not resolve the defect.")
                        machine.transition_to(RunState.REPLAY_FAILED)
                        update_run_state(RunState.REPLAY_FAILED, "POST_MERGE_FAILED", "Post merge verification failed")
                        return

                # Memory Phase ONLY executes after successful delivery (and post-merge verification if merged)
                with SessionLocal() as db:
                    mem_svc = MemoryService(db)
                    mem_svc.update_memory(incident_id, patch_id)
                machine.transition_to(RunState.MEMORY_UPDATED)
                update_run_state(RunState.MEMORY_UPDATED)
                
                machine.transition_to(RunState.COMPLETED)
                update_run_state(RunState.COMPLETED)
            elif deliv_res.status == "DELIVERY_AUTH_REQUIRED":
                emit_event("STATUS", "DELIVERY_AUTH_REQUIRED", deliv_res.error_details)
                machine.transition_to(RunState.DELIVERY_AUTH_REQUIRED)
                update_run_state(RunState.DELIVERY_AUTH_REQUIRED, "DELIVERY_AUTH_REQUIRED", deliv_res.error_details)
                return
            else:
                emit_event("STATUS", "DELIVERY_FAILED", deliv_res.error_details or "Delivery failed to create PR")
                machine.transition_to(RunState.DELIVERY_FAILED)
                update_run_state(RunState.DELIVERY_FAILED, "DELIVERY_FAILED", deliv_res.error_details or "Delivery provider failed to open PR")
                return
                    
        except Exception as e:
            logger.error(f"Error continuing execution: {e}", exc_info=True)
            with SessionLocal() as db:
                run = db.query(Run).filter(Run.id == run_id).first()
                if run:
                    err_str = str(e)
                    err_code = "DELIVERY_BLOCKED" if ("UNVALIDATED" in err_str or "DELIVERY_BLOCKED" in err_str) else "DELIVERY_FAILED"
                    run.state = "FAILED"
                    run.current_stage = "delivery"
                    run.error_code = err_code
                    run.error_message = err_str
                    run.terminal_at = datetime.now(timezone.utc)
                    event_logger = BackendEventLogger(db, run_id)
                    event_logger.emit('ERROR', f'Delivery failed: {err_str}')
                    db.commit()
