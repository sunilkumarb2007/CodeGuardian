import logging
import uuid
import os
from typing import Dict, Any, Optional

from app.db.database import SessionLocal
from app.services.inspection_service import RepositoryInspectionService
from app.services.triage_service import TriageService
from app.services.incident_service import IncidentService
from app.services.evidence_service import EvidenceService
from app.services.ghosttrace_service import GhostTraceService
from app.services.memory_service import MemoryService
from app.services.investigation_service import InvestigationService
from app.services.replay_service import ReplayService
from app.services.validation_service import ValidationService
from app.services.delivery_service import DeliveryService

logger = logging.getLogger(__name__)

# Temporary in-memory state, similar to demo
RUN_STATE = {}

class CodeGuardianOrchestrator:
    def __init__(self):
        pass

    def _update_stage(self, run_id: str, stage: str, status: str):
        if run_id in RUN_STATE:
            RUN_STATE[run_id]["stages"][stage] = status
            RUN_STATE[run_id]["current_stage"] = stage

    def _update_result(self, run_id: str, stage: str, data: Dict[str, Any]):
        if run_id in RUN_STATE:
            RUN_STATE[run_id]["results"][stage] = data

    def initialize_run(self, run_id: str, repository_url: str):
        RUN_STATE[run_id] = {
            "run_id": run_id,
            "repository_url": repository_url,
            "status": "started",
            "current_stage": "initialized",
            "stages": {
                "inspection": "pending",
                "triage": "pending",
                "failure_discovery": "pending",
                "evidence": "pending",
                "ghosttrace": "pending",
                "memory": "pending",
                "investigation": "pending",
                "patch": "pending",
                "replay": "pending",
                "build": "pending",
                "tests": "pending",
                "validation": "pending",
                "repair": "pending",
                "delivery": "pending"
            },
            "results": {},
            "error": None
        }

    def execute_pipeline(self, run_id: str, repository_url: str, supplied_incident_id: Optional[str] = None):
        try:
            logger.info(f"Orchestrator pipeline started: run_id={run_id}")
            # DB session handling
            db = SessionLocal()
            try:
                # 1. Inspection
                self._update_stage(run_id, "inspection", "running")
                inspect_svc = RepositoryInspectionService()
                
                from app.db import models
                import urllib.parse
                import uuid
                from datetime import datetime
                
                parsed = urllib.parse.urlparse(repository_url)
                parts = [p for p in parsed.path.split('/') if p]
                if len(parts) >= 2:
                    owner = parts[0]
                    repo_name = parts[1].replace('.git', '')
                else:
                    owner = "unknown"
                    repo_name = "unknown"
                    
                app = db.query(models.Application).first()
                if not app:
                    app = models.Application(id=uuid.uuid4(), name="DynamicApp", environment="test", status="active", created_at=datetime.utcnow(), updated_at=datetime.utcnow())
                    db.add(app)
                    db.flush()
                    
                repo = db.query(models.Repository).filter_by(repository_url=repository_url).first()
                if not repo:
                    repo = models.Repository(
                        id=uuid.uuid4(), application_id=app.id, provider="github", owner=owner, name=repo_name, 
                        repository_url=repository_url, default_branch="main", access_status="authorized",
                        created_at=datetime.utcnow(), updated_at=datetime.utcnow()
                    )
                    db.add(repo)
                    db.flush()
                    
                inspection_result = inspect_svc.inspect_repository(repository_url, db=db, repository_id=repo.id)
                
                self._update_result(run_id, "inspection", {
                    "tech_stack": inspection_result.architecture.tech_stack,
                    "has_docker": inspection_result.architecture.has_docker,
                    "static_analysis_passed": inspection_result.static_analysis_passed
                })
                self._update_stage(run_id, "inspection", "passed")
                # 2. Triage
                self._update_stage(run_id, "triage", "running")
                triage_svc = TriageService()
                incident_uuid = uuid.UUID(supplied_incident_id) if supplied_incident_id else None
                triage_decision = triage_svc.triage_failure(repository_url, inspection_result, incident_uuid, db=db)
                
                self._update_result(run_id, "triage", {
                    "decision_type": triage_decision.decision_type,
                    "incident_id": str(triage_decision.incident_id) if triage_decision.incident_id else None
                })
                self._update_stage(run_id, "triage", "passed")
                
                if triage_decision.decision_type == "no_actionable_defect":
                    RUN_STATE[run_id]["status"] = "completed_no_action"
                    logger.info(f"Pipeline stopped: no_actionable_defect for {run_id}")
                    db.commit()
                    return
                    
                incident_id = str(triage_decision.incident_id)
                
                if not incident_id:
                    raise ValueError("Triage failed to provide an incident_id for investigation.")

                # 3. GhostTrace
                self._update_stage(run_id, "ghosttrace", "running")
                gt_svc = GhostTraceService(db)
                trace = gt_svc.rebuild_trace(uuid.UUID(incident_id))
                
                self._update_result(run_id, "ghosttrace", {
                    "id": str(trace.id),
                    "root_cause_candidate": trace.root_cause_candidate,
                    "nodes": [{"service_name": n.service_name} for n in trace.nodes]
                })
                self._update_stage(run_id, "ghosttrace", "passed")
                
                # 4. Failure Memory
                self._update_stage(run_id, "memory", "running")
                mem_svc = MemoryService(db)
                memory_res = mem_svc.search_memory_for_incident(uuid.UUID(incident_id))
                
                self._update_result(run_id, "memory", {
                    "match_status": memory_res.match_status,
                    "match_score": memory_res.matches[0].similarity_score if memory_res.matches else None,
                    "matched_incident_id": str(memory_res.matches[0].incident_id) if memory_res.matches else None,
                })
                self._update_stage(run_id, "memory", "passed")
                
                # 5. AI Investigation
                self._update_stage(run_id, "investigation", "running")
                self._update_stage(run_id, "patch", "running")
                inv_svc = InvestigationService(db)
                # Pass architecture info derived from inspection_result
                arch_dict = {
                    "language": inspection_result.architecture.language,
                    "framework": inspection_result.architecture.framework,
                    "build_system": inspection_result.architecture.build_system,
                    "test_framework": inspection_result.architecture.test_framework
                } if inspection_result.architecture else None
                initial_inv_res = inv_svc.investigate_incident(incident_id, architecture=arch_dict)
                if initial_inv_res.status != "completed":
                    if initial_inv_res.status == "GEMINI_QUOTA_EXHAUSTED":
                        raise RuntimeError("GEMINI_QUOTA_EXHAUSTED")
                    raise ValueError(f"Investigation failed with status {initial_inv_res.status}")
                
                for attempt in range(1, 4):
                    self._update_stage(run_id, "patch", "running")
                    
                    patch_id = None
                    inv_res = None
                    compatibility_passed = False
                    
                    # Generation Loop (max 3 tries per attempt)
                    for gen_attempt in range(1, 4):
                        if attempt > 1 or gen_attempt > 1:
                            # Re-investigate based on validation or compatibility failure
                            inv_res = inv_svc.investigate_incident(incident_id, attempt=attempt * 10 + gen_attempt, architecture=arch_dict)
                        else:
                            # Use initial investigation result
                            inv_res = initial_inv_res
                            
                        if inv_res.status != "completed":
                            if inv_res.status == "GEMINI_QUOTA_EXHAUSTED":
                                raise RuntimeError("GEMINI_QUOTA_EXHAUSTED")
                            raise ValueError(f"Investigation failed with status {inv_res.status}")
                            
                        if not inv_res.patch_candidate:
                            logger.warning(f"Investigation returned no patch candidate on gen_attempt {gen_attempt}")
                            reason = "NO_PATCH_CANDIDATE_RETURNED"
                            continue

                        patch_id = str(inv_res.patch_candidate.id)
                        
                        # Validate compatibility
                        val_svc = ValidationService(db)
                        is_compat, reason = val_svc.check_patch_compatibility(uuid.UUID(patch_id), arch_dict)
                        if is_compat:
                            compatibility_passed = True
                            break
                        else:
                            logger.warning(f"Patch {patch_id} rejected due to: {reason}")
                            
                    if not compatibility_passed:
                        raise ValueError(f"Failed to generate compatible patch after 3 generation tries. Last reason: {reason}")
                        
                    self._update_result(run_id, "investigation", {
                        "root_cause": {
                            "service": inv_res.root_cause.service if inv_res.root_cause else None,
                            "summary": inv_res.root_cause.summary if inv_res.root_cause else None
                        } if inv_res.root_cause else None,
                        "patch_candidate": {
                            "id": str(inv_res.patch_candidate.id),
                            "status": inv_res.patch_candidate.status,
                            "diff": inv_res.patch_candidate.diff
                        } if inv_res.patch_candidate else None
                    })
                    self._update_stage(run_id, "investigation", "passed")
                    self._update_stage(run_id, "patch", "passed")

                    # 6. Replay
                    self._update_stage(run_id, "replay", "running")
                    import uuid
                    replay_svc = ReplayService(db)
                    rep_res = replay_svc.run_replay(uuid.UUID(incident_id), uuid.UUID(patch_id))
                    
                    self._update_result(run_id, "replay", {
                        "baseline_status": rep_res.baseline.status,
                        "patched_status": rep_res.patched.status
                    })
                    self._update_stage(run_id, "replay", "passed")
                    
                    # 7. Validation
                    self._update_stage(run_id, "validation", "running")
                    val_svc = ValidationService(db)
                    val_res = val_svc.run_validation(uuid.UUID(incident_id), uuid.UUID(patch_id))
                    
                    self._update_result(run_id, "validation", {
                        "build_passed": val_res.checks.build == "passed",
                        "tests_passed": val_res.checks.tests == "passed",
                        "replay_passed": val_res.checks.replay == "passed",
                        "safety_check": val_res.checks.safety == "passed",
                        "validation_status": "validated" if val_res.status == "passed" else "failed"
                    })
                    
                    if val_res.status == "passed":
                        self._update_stage(run_id, "validation", "passed")
                        break
                    else:
                        self._update_stage(run_id, "validation", "failed")
                        if attempt == 3:
                            raise ValueError("Patch failed validation phase after 3 attempts.")
                
                # 8. GitHub Delivery
                self._update_stage(run_id, "delivery", "running")
                del_svc = DeliveryService(db)
                del_res = del_svc.run_delivery(uuid.UUID(incident_id), uuid.UUID(patch_id), repository_url)
                
                self._update_result(run_id, "delivery", {
                    "pull_request_url": del_res.pull_request.url if del_res.pull_request else "",
                    "branch_name": del_res.branch,
                    "status": del_res.status
                })
                self._update_stage(run_id, "delivery", "passed")
                
                db.commit()
            except Exception:
                db.rollback()
                raise
            finally:
                db.close()

            RUN_STATE[run_id]["status"] = "completed"

        except Exception as e:
            logger.error(f"Error in generalized orchestrator: {e}", exc_info=True)
            if run_id in RUN_STATE:
                RUN_STATE[run_id]["status"] = "failed"
                RUN_STATE[run_id]["error"] = str(e)
                RUN_STATE[run_id]["stages"][RUN_STATE[run_id]["current_stage"]] = "failed"
