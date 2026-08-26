import time
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List
from uuid import UUID
from app.db.database import SessionLocal
from app.db.models import Application, Repository, Incident, EvidenceEvent, FailureTrace, FailureTraceNode, FailureTraceEdge, Investigation, Patch, ReplayRun, ValidationRun, FailureMemory, MemoryMatch, DemoRun, DemoEvent, DemoAction
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

DEMO_INCIDENT_ID = "d2a57169-6136-4cc7-83c6-3e21291cb14d"

STAGES_CONFIG = [
    ("repository", 0.5),
    ("inspection", 0.8),
    ("architecture", 0.7),
    ("failure_detection", 1.0),
    ("evidence", 1.0),
    ("ghosttrace", 1.2),
    ("memory", 1.0),
    ("investigation", 1.8),
    ("patch", 1.2),
    ("compatibility", 0.8),
    ("replay", 1.5),
    ("build", 1.0),
    ("tests", 1.0),
    ("validation", 1.2),
    ("approval", 0.0), # wait for human
    ("delivery", 1.2),
    ("memory_update", 0.8)
]

class DemoRunner:
    def __init__(self):
        self.incident_id = DEMO_INCIDENT_ID

    def initialize_run(self, run_id: str) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            demo_run = DemoRun(
                id=run_id,
                scenario_id="JavaAPICheck_NullPointer",
                incident_id=UUID(self.incident_id),
                mode="demo",
                status="running",
                current_stage="repository",
                started_at=datetime.utcnow(),
                presentation_sequence={
                    "stages": {stage: "pending" for stage, _ in STAGES_CONFIG},
                    "results": {},
                    "error": None
                }
            )
            demo_run.presentation_sequence["stages"]["completed"] = "pending"
            db.add(demo_run)
            db.commit()
            
            return {
                "run_id": demo_run.id,
                "status": demo_run.status,
                "current_stage": demo_run.current_stage,
                "mode": demo_run.mode,
                "stages": demo_run.presentation_sequence["stages"],
                "results": demo_run.presentation_sequence["results"],
                "error": demo_run.presentation_sequence["error"]
            }
        finally:
            db.close()

    def get_run(self, run_id: str) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            run = db.query(DemoRun).filter(DemoRun.id == run_id).first()
            if not run:
                return None
            return {
                "run_id": run.id,
                "status": run.status,
                "current_stage": run.current_stage,
                "mode": run.mode,
                "stages": run.presentation_sequence["stages"] if run.presentation_sequence else {},
                "results": run.presentation_sequence["results"] if run.presentation_sequence else {},
                "error": run.presentation_sequence.get("error") if run.presentation_sequence else None
            }
        finally:
            db.close()

    def get_run_workspace(self, run_id: str, db: Session) -> Dict[str, Any]:
        run = db.query(DemoRun).filter(DemoRun.id == run_id).first()
        if not run:
            return None
            
        results = run.presentation_sequence.get("results", {})
        
        workspace = {
            "run": {
                "id": run.id,
                "status": run.status,
                "current_stage": run.current_stage,
                "mode": run.mode
            },
            "repository": results.get("repository", {}),
            "architecture": results.get("architecture", {}),
            "incident": results.get("failure_detection", {}),
            "evidence": results.get("evidence", []),
            "trace": results.get("ghosttrace", {}),
            "memory": results.get("memory", {}),
            "investigation": results.get("investigation", {}),
            "patch": results.get("patch", {}),
            "replay": results.get("replay", {}),
            "build": results.get("build", {}),
            "tests": results.get("tests", {}),
            "validation": results.get("validation", {}),
            "delivery": results.get("delivery", {}),
            "memory_update": results.get("memory_update", {}),
            "agent_events": [
                {
                    "id": str(e.id),
                    "timestamp": e.timestamp.isoformat(),
                    "type": e.event_type,
                    "title": e.title,
                    "description": e.description,
                    "status": e.status,
                    "related_stage": "various" # simplification
                } for e in db.query(DemoEvent).filter(DemoEvent.run_id == run_id).order_by(DemoEvent.sequence).all()
            ],
            "command_log": [
                {
                    "id": str(c.id),
                    "timestamp": c.timestamp.isoformat(),
                    "command": c.command,
                    "display_command": f"$ {c.command}",
                    "output": c.output,
                    "status": c.status
                } for c in db.query(DemoEvent).filter(DemoEvent.run_id == run_id, DemoEvent.command.isnot(None)).order_by(DemoEvent.sequence).all()
            ]
        }
        return workspace

    def get_events(self, run_id: str, db: Session):
        events = db.query(DemoEvent).filter(DemoEvent.run_id == run_id).order_by(DemoEvent.sequence).all()
        return [
            {
                "id": str(e.id),
                "timestamp": e.timestamp.isoformat(),
                "type": e.event_type,
                "title": e.title,
                "description": e.description,
                "command": e.command,
                "output": e.output,
                "status": e.status
            } for e in events
        ]

    def get_commands(self, run_id: str, db: Session):
        events = db.query(DemoEvent).filter(DemoEvent.run_id == run_id, DemoEvent.command.isnot(None)).order_by(DemoEvent.sequence).all()
        return [
            {
                "id": str(e.id),
                "timestamp": e.timestamp.isoformat(),
                "command": e.command,
                "display_command": f"$ {e.command}",
                "output": e.output,
                "status": e.status
            } for e in events
        ]

    def execute_async(self, run_id: str):
        db = SessionLocal()
        try:
            seq = 0
            for stage_name, delay in STAGES_CONFIG:
                run = db.query(DemoRun).filter(DemoRun.id == run_id).first()
                if not run:
                    break
                
                seq += 1
                
                if stage_name == "delivery":
                    pass
                
                if stage_name == "approval":
                    run.current_stage = "approval"
                    run.status = "waiting_for_approval"
                    
                    # sqlalchemy jsonb mutation
                    ps = dict(run.presentation_sequence)
                    ps["stages"]["approval"] = "pending"
                    run.presentation_sequence = ps
                    
                    db.commit()
                    return 
                    
                run.current_stage = stage_name
                ps = dict(run.presentation_sequence)
                ps["stages"][stage_name] = "running"
                run.presentation_sequence = ps
                db.commit()
                
                time.sleep(delay)
                
                # Fetch fresh run after sleep
                run = db.query(DemoRun).filter(DemoRun.id == run_id).first()
                ps = dict(run.presentation_sequence)
                self._populate_stage_data(ps["results"], stage_name, db)
                ps["stages"][stage_name] = "passed"
                run.presentation_sequence = ps
                db.commit()
                
                self._create_stage_events(run_id, stage_name, seq, db)

            run = db.query(DemoRun).filter(DemoRun.id == run_id).first()
            if run:
                run.current_stage = "completed"
                run.status = "completed"
                run.completed_at = datetime.utcnow()
                ps = dict(run.presentation_sequence)
                ps["stages"]["completed"] = "passed"
                run.presentation_sequence = ps
                db.commit()

        except Exception as e:
            logger.error(f"Demo runner error: {e}")
            db.rollback()
            run = db.query(DemoRun).filter(DemoRun.id == run_id).first()
            if run:
                run.status = "failed"
                ps = dict(run.presentation_sequence)
                ps["error"] = str(e)
                curr = run.current_stage
                if curr:
                    ps["stages"][curr] = "failed"
                run.presentation_sequence = ps
                db.commit()
        finally:
            db.close()

    def approve_and_continue(self, run_id: str):
        db = SessionLocal()
        try:
            run = db.query(DemoRun).filter(DemoRun.id == run_id).first()
            if not run or run.status != "waiting_for_approval":
                raise ValueError("Run is not waiting for approval")
                
            run.status = "running"
            run.approval_state = "approved"
            ps = dict(run.presentation_sequence)
            ps["stages"]["approval"] = "passed"
            run.presentation_sequence = ps
            db.commit()
            
            remaining = False
            seq = 100
            for stage_name, delay in STAGES_CONFIG:
                if stage_name == "delivery":
                    remaining = True
                if remaining:
                    seq += 1
                    run = db.query(DemoRun).filter(DemoRun.id == run_id).first()
                    run.current_stage = stage_name
                    ps = dict(run.presentation_sequence)
                    ps["stages"][stage_name] = "running"
                    run.presentation_sequence = ps
                    db.commit()
                    
                    time.sleep(delay)
                    
                    run = db.query(DemoRun).filter(DemoRun.id == run_id).first()
                    ps = dict(run.presentation_sequence)
                    self._populate_stage_data(ps["results"], stage_name, db)
                    ps["stages"][stage_name] = "passed"
                    run.presentation_sequence = ps
                    db.commit()
                    
                    self._create_stage_events(run_id, stage_name, seq, db)
                    
            run = db.query(DemoRun).filter(DemoRun.id == run_id).first()
            run.current_stage = "completed"
            run.status = "completed"
            run.completed_at = datetime.utcnow()
            ps = dict(run.presentation_sequence)
            ps["stages"]["completed"] = "passed"
            run.presentation_sequence = ps
            db.commit()
        finally:
            db.close()

    def reject_patch(self, run_id: str):
        db = SessionLocal()
        try:
            run = db.query(DemoRun).filter(DemoRun.id == run_id).first()
            if not run or run.status != "waiting_for_approval":
                raise ValueError("Run is not waiting for approval")
                
            run.status = "failed"
            run.approval_state = "rejected"
            run.current_stage = "completed"
            run.completed_at = datetime.utcnow()
            ps = dict(run.presentation_sequence)
            ps["stages"]["approval"] = "failed"
            ps["error"] = "Patch rejected by reviewer."
            run.presentation_sequence = ps
            db.commit()
        finally:
            db.close()
            
    def _create_stage_events(self, run_id, stage, seq, db):
        ev = DemoEvent(
            run_id=run_id,
            sequence=seq,
            timestamp=datetime.utcnow(),
            event_type="system",
            title=f"Stage: {stage.capitalize()}",
            status="completed"
        )
        
        if stage == "inspection":
            ev.command = "inspect repository"
            ev.output = "15 files detected. Java / Spring Boot / Maven."
        elif stage == "ghosttrace":
            ev.command = "reconstruct failure"
            ev.output = "Root cause candidate found in PaymentProcessingService.charge()"
        elif stage == "memory":
            ev.command = "search failure memory"
            ev.output = "1 verified match for NULL_OBJECT_ACCESS."
        elif stage == "patch":
            ev.command = "prepare patch"
            ev.output = "1 file changed. Null guard added."
        elif stage == "replay":
            ev.command = "replay original failure && replay patched failure"
            ev.output = "Original: HTTP 500\nPatched: HTTP 200"
        elif stage == "validation":
            ev.command = "validate repair"
            ev.output = "All gates passed."
            
        db.add(ev)
        db.commit()
        
    def _populate_stage_data(self, res: dict, stage: str, db: Session):
        inc_uuid = UUID(self.incident_id)
        
        if stage == "repository":
            repo = db.query(Repository).filter(Repository.name == 'JavaAPICheck').first()
            if repo:
                res[stage] = {"url": repo.repository_url, "owner": repo.owner, "name": repo.name, "language": "Java"}
                
        elif stage == "inspection":
            res[stage] = {"files_scanned": 15, "top_files": ["pom.xml", "PaymentProcessingService.java"]}
            
        elif stage == "architecture":
            res[stage] = {"language": "Java", "framework": "Spring Boot", "build_tool": "Maven"}
            
        elif stage == "failure_detection":
            inc = db.query(Incident).filter(Incident.id == inc_uuid).first()
            if inc:
                res[stage] = {"fingerprint": inc.error_fingerprint, "title": inc.title, "symptom_service": inc.symptom_service}
                
        elif stage == "evidence":
            events = db.query(EvidenceEvent).filter(EvidenceEvent.incident_id == inc_uuid).order_by(EvidenceEvent.timestamp).all()
            res[stage] = [{"message": e.event_metadata.get("message"), "type": e.event_type} for e in events]
            
        elif stage == "ghosttrace":
            trace = db.query(FailureTrace).filter(FailureTrace.incident_id == inc_uuid).first()
            if trace:
                nodes = db.query(FailureTraceNode).filter(FailureTraceNode.failure_trace_id == trace.id).order_by(FailureTraceNode.sequence_number).all()
                res[stage] = {
                    "root_cause_candidate": trace.root_cause_candidate,
                    "nodes": [{"service_name": n.service_name, "node_type": n.node_type} for n in nodes]
                }
                
        elif stage == "memory":
            match = db.query(MemoryMatch).filter(MemoryMatch.incident_id == inc_uuid).first()
            if match:
                mem = db.query(FailureMemory).filter(FailureMemory.id == match.memory_id).first()
                res[stage] = {
                    "similarity": float(match.similarity_score),
                    "match_reason": match.match_reason,
                    "previous_fix": mem.code_change if mem else ""
                }
                
        elif stage == "investigation":
            inv = db.query(Investigation).filter(Investigation.incident_id == inc_uuid).first()
            if inv:
                res[stage] = {
                    "observation": "Payment service received checkout request. Repository lookup returned null.",
                    "evidence": "Stack trace points to PaymentProcessingService.java.",
                    "hypothesis": "paymentRecord is dereferenced without null validation.",
                    "decision": "Root cause is a missing null guard.",
                    "result": "Null guard is required before object access.",
                    "next_action": "Generate a minimal Java patch."
                }
                
        elif stage == "patch":
            patch = db.query(Patch).filter(Patch.incident_id == inc_uuid).first()
            if patch:
                res[stage] = {
                    "diff": patch.diff,
                    "affected_files": patch.affected_files
                }
                
        elif stage == "compatibility":
            res[stage] = {
                "language": "Java",
                "file_extension": ".java",
                "source_context": "matched",
                "deleted_lines": "found",
                "path_safety": "passed",
                "unexpected_files": "none",
                "secrets": "none",
                "result": "PASS"
            }
            
        elif stage == "replay":
            replays = db.query(ReplayRun).filter(ReplayRun.incident_id == inc_uuid).all()
            orig = next((r for r in replays if r.replay_type == 'original'), None)
            patched = next((r for r in replays if r.replay_type == 'patched'), None)
            res[stage] = {
                "original": {"status": "HTTP 500", "fingerprint": "NULL_OBJECT_ACCESS", "result": "FAILED"} if orig else {},
                "patched": {"status": "HTTP 200", "fingerprint": "none", "result": "PASSED"} if patched else {}
            }
            
        elif stage == "build":
            res[stage] = {"command": "mvnw.cmd clean test", "result": "PASS"}
            
        elif stage == "tests":
            res[stage] = {
                "test": "deterministicBugReturnsInternalServerError",
                "original": "FAIL / expected failure",
                "patched": "PASS",
                "summary": {"Tests run": 45, "Failures": 0, "Errors": 0, "Skipped": 1}
            }
            
        elif stage == "validation":
            val = db.query(ValidationRun).filter(ValidationRun.incident_id == inc_uuid).first()
            if val:
                res[stage] = {
                    "gates": [
                        {"name": "Patch Context", "result": "PASS"},
                        {"name": "Path Safety", "result": "PASS"},
                        {"name": "Replay", "result": "PASS"},
                        {"name": "Build", "result": "PASS"},
                        {"name": "Tests", "result": "PASS"},
                        {"name": "Final Validation", "result": "PASS"}
                    ],
                    "final": "validated"
                }
                
        elif stage == "delivery":
            res[stage] = {
                "branch": "feature/codeguardian/null-object-access",
                "base": "main",
                "commit": "fix: guard missing payment record",
                "pull_request": "DEMO-PR-001"
            }
            
        elif stage == "memory_update":
            res[stage] = {
                "error_fingerprint": "NULL_OBJECT_ACCESS",
                "root_cause": "paymentRecord is dereferenced without checking whether the repository lookup returned null.",
                "affected_file": "PaymentProcessingService.java",
                "code_change": "Null guard added.",
                "validation_result": "PASS",
                "delivery_result": "DEMO-PR-001",
                "status": "verified"
            }
