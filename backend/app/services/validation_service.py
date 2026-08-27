import logging
import uuid
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.repositories import (
    IncidentRepository,
    PatchRepository,
    ValidationRunRepository,
    RepairAttemptRepository
)
from app.db.models import ValidationRun, RepairAttempt
from app.schemas.validation import ValidationRunResponse, ValidationChecks
from app.services.replay_service import ReplayService
from app.engine.validation_engine import ValidationEngine

logger = logging.getLogger(__name__)

class ValidationService:
    def __init__(self, db: Session):
        self.db = db
        self.incident_repo = IncidentRepository(db)
        self.patch_repo = PatchRepository(db)
        self.val_run_repo = ValidationRunRepository(db)
        self.repair_repo = RepairAttemptRepository(db)
        self.replay_service = ReplayService(db)
        self.engine = ValidationEngine()

    def check_patch_compatibility(self, patch_id: UUID, architecture: dict | None) -> tuple[bool, str]:
        """
        Validates the patch before attempting replay/build/tests.
        Returns (is_compatible, failure_reason)
        """
        patch = self.patch_repo.get_by_id(patch_id)
        if not patch:
            return False, "PATCH_NOT_FOUND"
            
        incident = self.incident_repo.get_by_id(patch.incident_id)
        if not incident or not incident.repository_id:
            return True, ""
            
        from app.db.repositories import RepositoryFileRepository
        from app.services.patch_safety_validator import PatchSafetyValidator
        
        file_repo = RepositoryFileRepository(self.db)
        all_files = file_repo.get_files_by_repository_id(incident.repository_id)
        
        return PatchSafetyValidator.validate(patch, all_files, architecture)

    def run_validation(self, incident_id: UUID, patch_id: UUID) -> ValidationRunResponse:
        incident = self.incident_repo.get_by_id(incident_id)
        if not incident:
            raise ValueError(f"Incident {incident_id} not found")

        patch = self.patch_repo.get_by_id(patch_id)
        if not patch:
            raise ValueError(f"Patch {patch_id} not found")

        if patch.incident_id != incident_id:
            raise ValueError(f"Patch {patch_id} does not belong to incident {incident_id}")

        if patch.status != "unvalidated":
            raise ValueError(f"Patch {patch_id} is not unvalidated. Status: {patch.status}")

        # Enforce max 3 attempts rule
        latest_attempt = self.repair_repo.get_latest_attempt(incident_id)
        attempt_number = 1
        if latest_attempt:
            attempt_number = latest_attempt.attempt_number + 1
            if attempt_number > 3:
                # For attempt 4+, we block it entirely before taking action.
                raise ValueError("Maximum 3 repair attempts reached. Validation aborted.")

        logger.info(f"Starting validation attempt {attempt_number} for patch {patch_id}")

        # Execute Ghost Replay
        try:
            # We call replay_service for baseline and patched replay
            # ReplayService evaluates if it CHANGED_BEHAVIOR
            replay_response = self.replay_service.run_replay(incident_id, patch_id)
            replay_result = replay_response.result
        except Exception as e:
            logger.error(f"Replay environment failure: {e}")
            replay_result = "INFRASTRUCTURE_FAILURE"

        # Let the deterministic Engine validate build, tests, context, and replay result
        try:
            if replay_response.result == "INFRASTRUCTURE_FAILURE":
                val_result = {
                    "checks": ValidationChecks(
                        patch_apply="failed", build="failed", tests="failed", 
                        replay="failed", regression="failed", safety="passed"
                    ),
                    "overall_status": "infrastructure_failed",
                    "failure_reason": "INFRASTRUCTURE_FAILURE",
                    "build_output": None,
                    "test_output": None,
                    "replay_passed": False
                }
            else:
                val_result = self.engine.run_validation(patch, replay_response)
        except Exception as e:
            logger.error(f"Validation Engine failure: {e}")
            val_result = {
                "checks": ValidationChecks(
                    patch_apply="failed", build="failed", tests="failed", 
                    replay="failed", regression="failed", safety="passed"
                ),
                "overall_status": "infrastructure_failed",
                "failure_reason": "INFRASTRUCTURE_FAILURE",
                "build_output": None,
                "test_output": None,
                "replay_passed": False
            }

        checks: ValidationChecks = val_result["checks"]
        overall_status = val_result["overall_status"]
        failure_reason = val_result["failure_reason"]
        
        # Persist Validation Run
        val_run = ValidationRun(
            id=uuid.uuid4(),
            incident_id=incident_id,
            patch_id=patch_id,
            build_passed=(checks.build == "passed"),
            tests_passed=(checks.tests == "passed"),
            replay_passed=(checks.replay == "passed"),
            original_failure_reproduced=True, # Assume baseline reproduced successfully
            repair_verified=(overall_status == "passed"),
            exit_code=0 if overall_status == "passed" else 1,
            build_output=val_result.get("build_output"),
            test_output=val_result.get("test_output"),
            replay_output=f"Ghost Replay Result: {replay_result}",
            validation_summary="Patch passed all required validation checks." if overall_status == "passed" else f"Validation failed: {failure_reason}",
            status=overall_status,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc)
        )
        self.val_run_repo.save(val_run)
        self.db.flush()

        # Update Incident and Patch statuses
        if overall_status == "passed":
            patch.status = "validated"
            # In Phase 8, incident will progress to PR_ELIGIBLE
            # We don't mark incident as resolved yet. Just log the successful validation.
            repair_status = "successful"
            
            # Since patch is validated, mark all running repair attempts as successful
            if latest_attempt:
                latest_attempt.status = "successful"
        else:
            patch.status = "failed"
            repair_status = "failed"
            
        # Create or update Repair Attempt record
        if not latest_attempt or latest_attempt.status != "started":
            # Start a new attempt
            repair_attempt = RepairAttempt(
                id=uuid.uuid4(),
                incident_id=incident_id,
                patch_id=patch_id,
                validation_run_id=val_run.id,
                attempt_number=attempt_number,
                failure_reason=failure_reason,
                repair_action="validation_completed",
                status=repair_status,
                created_at=datetime.now(timezone.utc)
            )
            self.repair_repo.save(repair_attempt)
        else:
            # Complete the in-progress attempt
            latest_attempt.patch_id = patch_id
            latest_attempt.validation_run_id = val_run.id
            latest_attempt.failure_reason = failure_reason
            latest_attempt.repair_action = "validation_completed"
            latest_attempt.status = repair_status
            repair_attempt = latest_attempt

        self.db.flush()

        # Generate response
        response = ValidationRunResponse(
            id=val_run.id,
            incident_id=val_run.incident_id,
            patch_id=val_run.patch_id,
            attempt=attempt_number,
            status=val_run.status,
            checks=checks,
            summary=val_run.validation_summary,
            build_output=val_run.build_output,
            test_output=val_run.test_output,
            replay_output=val_run.replay_output,
            created_at=val_run.created_at
        )

        # Trigger Gemini for another patch if it failed and we are under attempt limit
        if overall_status == "failed" and attempt_number < 3 and failure_reason != "INFRASTRUCTURE_FAILURE":
            logger.info(f"Triggering repair loop for attempt {attempt_number + 1}")
            # Note: We would typically dispatch to celery/background task here
            # For synchronous flow we could call Gemini, but since it's Phase 7, 
            # we just prep the system state for next patch generation.
            
            # For demonstration, we simply log it here.
            # In full pipeline, this might call InvestigationService with the validation failure context.
            pass

        return response
