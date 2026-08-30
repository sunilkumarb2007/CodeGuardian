import os
import sys
import time
import uuid
import logging
import argparse
from datetime import datetime, timezone, timedelta
from typing import Optional

from app.core.config import settings
from app.db.database import SessionLocal
from app.db.models import Run, Incident, EvidenceEvent
from app.engine.run_state_machine import RunState
from app.services.orchestrator import CodeGuardianOrchestrator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("codeguardian-worker")

STALE_HEARTBEAT_THRESHOLD_SECONDS = 180
POLL_INTERVAL_SECONDS = 3


def check_and_reap_stale_runs():
    """
    Detects abandoned/crashed runs where the worker process died unexpectedly.
    Marks them as FAILED deterministically rather than leaving them in RUNNING forever.
    """
    with SessionLocal() as db:
        try:
            stale_cutoff = datetime.now(timezone.utc) - timedelta(seconds=STALE_HEARTBEAT_THRESHOLD_SECONDS)
            # Find running runs that have not updated recently
            stale_runs = (
                db.query(Run)
                .filter(
                    Run.state.in_([
                        "RUNNING",
                        "REPOSITORY_CLONING",
                        "INSPECTING",
                        "INVESTIGATING",
                        "VALIDATING",
                        "DELIVERY_PREPARING",
                        "POST_MERGE_REPLAY_RUNNING"
                    ]),
                    Run.updated_at < stale_cutoff.replace(tzinfo=None)
                )
                .all()
            )

            for run in stale_runs:
                logger.warning(
                    f"[STALE DETECTOR] Run {run.id} has no heartbeat since {run.updated_at}. "
                    f"Marking as FAILED with error_code=WORKER_TERMINATED."
                )
                run.state = "FAILED"
                run.error_code = "WORKER_TERMINATED"
                run.error_message = (
                    f"Execution worker terminated unexpectedly or timed out beyond "
                    f"{STALE_HEARTBEAT_THRESHOLD_SECONDS}s heartbeat threshold."
                )
                run.terminal_at = datetime.now(timezone.utc).replace(tzinfo=None)
                run.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
            
            if stale_runs:
                db.commit()
        except Exception as e:
            logger.error(f"[STALE DETECTOR] Error scanning stale runs: {e}")


def execute_single_run(run_id: str):
    """
    Executes a single run by ID using the authoritative 17-stage CodeGuardian orchestrator.
    """
    logger.info(f"[WORKER] Starting execution of Run {run_id}")
    with SessionLocal() as db:
        run = db.query(Run).filter(Run.id == uuid.UUID(run_id)).first()
        if not run:
            logger.error(f"[WORKER] Run {run_id} not found in database.")
            return

        incident = db.query(Incident).filter(Incident.id == run.incident_id).first() if run.incident_id else None
        evidence = db.query(EvidenceEvent).filter(EvidenceEvent.incident_id == incident.id).first() if incident else None

        repo_url = "https://github.com/sunilkumarb2007/JavaAPICheck"
        if incident and hasattr(incident, 'repository') and incident.repository:
            repo_url = incident.repository.repository_url
        elif run.repository and hasattr(run.repository, 'repository_url'):
            repo_url = run.repository.repository_url

        failure_input_dict = None
        if evidence:
            failure_input_dict = {
                "failure_type": evidence.event_type or "RUNTIME_EXCEPTION",
                "message": evidence.error_message or "",
                "stack_trace": evidence.stack_trace or "",
                "service": evidence.service_name or "payment-service",
                "exception": evidence.error_code or "NullPointerException",
            }

    try:
        orchestrator = CodeGuardianOrchestrator()
        orchestrator.execute_run(
            repository_url=repo_url,
            supplied_run_id=run_id,
            supplied_incident_id=str(incident.id) if incident else None,
            failure_input=failure_input_dict
        )
        logger.info(f"[WORKER] Run {run_id} execution finished.")
    except Exception as e:
        logger.error(f"[WORKER] Uncaught error during run {run_id}: {e}", exc_info=True)
        with SessionLocal() as db:
            run = db.query(Run).filter(Run.id == uuid.UUID(run_id)).first()
            if run and run.state not in ("COMPLETED", "WAITING_FOR_APPROVAL", "REJECTED"):
                run.state = "FAILED"
                run.error_code = "WORKER_EXECUTION_ERROR"
                run.error_message = str(e)
                run.terminal_at = datetime.now(timezone.utc).replace(tzinfo=None)
                db.commit()


def run_worker_loop():
    """
    Main durable worker daemon loop.
    Polls PostgreSQL for queued runs, executes them, and performs heartbeat maintenance.
    """
    logger.info("=" * 60)
    logger.info("CODEGUARDIAN DURABLE WORKER DAEMON STARTED")
    logger.info(f"Environment: {settings.app_env} | AI Provider: {settings.ai_provider} ({settings.ai_model})")
    logger.info("=" * 60)

    while True:
        try:
            # 1. Clean up dead/stale runs
            check_and_reap_stale_runs()

            # 2. Pick up next queued/created run
            with SessionLocal() as db:
                pending_run = (
                    db.query(Run)
                    .filter(Run.state.in_(["CREATED", "QUEUED"]))
                    .order_by(Run.created_at.asc())
                    .first()
                )

                if pending_run:
                    run_id_str = str(pending_run.id)
                    # Atomically claim the run
                    pending_run.state = "INITIALIZED"
                    pending_run.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
                    db.commit()
                    logger.info(f"[WORKER] Claimed run {run_id_str}. Launching execution...")
                else:
                    run_id_str = None

            # 3. If run claimed, execute outside DB lock
            if run_id_str:
                execute_single_run(run_id_str)
            else:
                time.sleep(POLL_INTERVAL_SECONDS)

        except KeyboardInterrupt:
            logger.info("[WORKER] Worker shutdown requested by operator.")
            break
        except Exception as e:
            logger.error(f"[WORKER] Unexpected error in worker loop: {e}", exc_info=True)
            time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CodeGuardian Durable Background Worker")
    parser.add_argument("--run-id", type=str, help="Execute a specific Run ID and exit")
    args = parser.parse_args()

    if args.run_id:
        execute_single_run(args.run_id)
    else:
        run_worker_loop()
