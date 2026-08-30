import logging
from uuid import UUID
from app.db.models import Patch
from app.schemas.validation import ValidationChecks

logger = logging.getLogger(__name__)

class ValidationEngine:
    def __init__(self):
        pass

    def run_validation(self, patch: Patch, replay_response) -> dict:
        """
        Runs the full validation suite based on actual sandbox replay, build, and test execution.
        """
        logger.info(f"Starting deterministic validation for patch {patch.id}")
        
        # 1. Patch Safety & Context
        safety_passed = self._verify_patch_safety(patch)
        context_passed = self._verify_patch_context(patch)

        # 2. Extract actual results from sandbox execution (passed via replay_response)
        patched = getattr(replay_response, "patched", None)
        
        build_passed = False
        tests_passed = False
        build_output = ""
        test_output = ""

        if isinstance(patched, dict):
            build_passed = patched.get("build_passed", False) or (patched.get("status") == "completed")
            tests_passed = patched.get("tests_passed", False) or (patched.get("status") == "completed" and patched.get("exit_code") == 0)
            build_output = patched.get("build_output", "")
            test_output = patched.get("output", "")
        elif hasattr(patched, "status"):
            build_passed = getattr(patched, "build_passed", False) or (patched.status == "completed")
            tests_passed = getattr(patched, "tests_passed", False) or (patched.status == "completed")
            build_output = getattr(patched, "build_output", "")
            test_output = getattr(patched, "output", "")

        # 3. Replay Evaluation
        replay_result = getattr(replay_response, "result", "")
        replay_passed = (replay_result == "REPLAY_CHANGED_BEHAVIOR")
        regression_passed = tests_passed

        checks = ValidationChecks(
            patch_apply="passed" if context_passed else "failed",
            build="passed" if build_passed else "failed",
            tests="passed" if tests_passed else "failed",
            replay="passed" if replay_passed else "failed",
            regression="passed" if regression_passed else "failed",
            safety="passed" if safety_passed else "failed"
        )

        all_passed = (
            context_passed and
            build_passed and
            tests_passed and
            replay_passed and
            regression_passed and
            safety_passed
        )

        overall_status = "passed" if all_passed else "failed"
        
        # Determine specific failure reason if any
        failure_reason = None
        if not all_passed:
            if not safety_passed:
                failure_reason = "PATCH_SAFETY_FAILED"
            elif not context_passed:
                failure_reason = "PATCH_CONTEXT_MISMATCH"
            elif not build_passed:
                failure_reason = "BUILD_FAILED"
            elif not tests_passed:
                failure_reason = "TESTS_FAILED"
            elif not replay_passed:
                failure_reason = "REPLAY_FAILED"
            elif not regression_passed:
                failure_reason = "REGRESSION_FAILED"

        return {
            "checks": checks,
            "overall_status": overall_status,
            "failure_reason": failure_reason,
            "build_output": build_output,
            "test_output": test_output,
            "replay_passed": replay_passed
        }

    def _verify_patch_safety(self, patch: Patch) -> bool:
        dangerous_paths = [".env", "secrets", "credentials", ".git"]
        if not patch.affected_files:
            return True
            
        for file_path in patch.affected_files:
            for dangerous in dangerous_paths:
                if dangerous in file_path:
                    logger.warning(f"Patch {patch.id} modifies sensitive file: {file_path}")
                    return False
        return True

    def _verify_patch_context(self, patch: Patch) -> bool:
        if not patch.diff:
            return False
        return True
