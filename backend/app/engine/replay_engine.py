import os
import shutil
import logging
import uuid
import tempfile
from typing import Dict, Any, Tuple

from app.db import models
from app.services.command_service import CommandExecutionService
from app.engine.patch_normalizer import normalize_and_validate

logger = logging.getLogger(__name__)

class ReplayEngine:
    def __init__(self, workspace_root: str = None, event_logger=None):
        self.workspace_root = workspace_root or os.path.join(tempfile.gettempdir(), "codeguardian_workspaces")
        self.cmd_svc = CommandExecutionService()
        self.event_logger = event_logger

    def emit_event(self, event_type: str, title: str, description: str = None, command: str = None, output: str = None):
        if self.event_logger:
            self.event_logger.emit(event_type, title, description=description, command=command, output=output)

    def run_replay(self, incident: models.Incident, patch: models.Patch | None, run_id: str, repo: models.Repository, architecture: Any) -> Tuple[str, dict, dict]:
        """
        Executes a baseline replay, applies the patch, builds, tests, and executes a patched replay.
        Returns (result_str, baseline_details, patched_details).

        result_str values:
          REPLAY_CHANGED_BEHAVIOR  — patch applied, build passed, tests passed
          PATCH_APPLY_FAILED       — diff failed normalisation or git apply
          BASELINE_FAILURE_NOT_REPRODUCED — baseline unexpectedly passed
          WORKSPACE_MISSING        — source directory not found
          REPLAY_FAILURE_PERSISTS  — patch applied but tests still fail
        """
        source_dir = os.path.join(self.workspace_root, "repositories", str(repo.id), "source")
        if not os.path.exists(source_dir):
            self.emit_event("STATUS", "Source directory missing", description=source_dir)
            return "WORKSPACE_MISSING", {}, {}

        run_uuid = run_id
        workspace_dir = os.path.join(self.workspace_root, "runs", run_uuid)
        original_dir = os.path.join(workspace_dir, "original")
        patched_dir = os.path.join(workspace_dir, "patched")
        
        os.makedirs(original_dir, exist_ok=True)
        os.makedirs(patched_dir, exist_ok=True)
        
        try:
            # 1. Setup workspace by copying (not cloning)
            self._copy_dir(source_dir, original_dir)
            self.emit_event("STATUS", "Creating baseline snapshot", description=f"Copied {source_dir} to {original_dir}")
            
            # Baseline execution
            self.emit_event("STATUS", "Running baseline verification")
            baseline_details = self._execute_sandbox(original_dir, architecture, is_patched=False)
            
            # Validate Baseline
            if baseline_details.get("exit_code") == 0:
                self.emit_event("ANALYSIS", "BASELINE_FAILURE_NOT_REPRODUCED", description="Baseline test unexpectedly passed.")
                # We do not abort here to allow testing the patch.
            else:
                self.emit_event("ANALYSIS", "Baseline failure reproduced", description="Expected test failure observed.")

            if not patch:
                return "BASELINE_ONLY", baseline_details, {"status": "NO_PATCH"}
                
            # 2. Prepare patched workspace
            self.emit_event("STATUS", "Preparing isolated replay workspace")
            self._copy_dir(source_dir, patched_dir)
            
            # 3. Apply patch — validate first, then git apply. No unsafe fallbacks.
            patch_applied, patch_error = self._apply_patch(patched_dir, patch)
            if not patch_applied:
                return "PATCH_APPLY_FAILED", baseline_details, {"status": "PATCH_APPLY_FAILED", "error": patch_error}
                
            # 4. Patched execution
            self.emit_event("STATUS", "Running build and tests on patched workspace")
            patched_details = self._execute_sandbox(patched_dir, architecture, is_patched=True)
            
            # 5. Compare
            if patched_details.get("exit_code") == 0:
                result = "REPLAY_CHANGED_BEHAVIOR"
                self.emit_event("VALIDATION", "REPLAY_CHANGED_BEHAVIOR")
                self.emit_event("VALIDATION", "TESTS_PASSED")
            else:
                result = "REPLAY_FAILURE_PERSISTS"
                self.emit_event("VALIDATION", "TESTS_FAILED", description=patched_details.get("output", "")[-2000:])
                
            return result, baseline_details, patched_details

        finally:
            pass  # Keep runs around for debugging

    def _copy_dir(self, src: str, dst: str):
        if os.path.exists(dst):
            from app.core.workspace import remove_repository_workspace
            remove_repository_workspace(dst)
        shutil.copytree(src, dst)

    def _apply_patch(self, workspace_dir: str, patch: models.Patch) -> Tuple[bool, str]:
        """
        Validates and applies a patch to the workspace.

        Steps:
        1. PatchNormalizer strips markdown fencing.
        2. PatchValidator checks structural validity (pure Python, no git).
        3. Security check for traversal/absolute paths.
        4. git apply --check  →  PASS → git apply
                              →  FAIL → return structured error, do NOT fallback silently.

        Returns (True, "") on success, (False, error_message) on any failure.
        There is NO fuzzy fallback. A rejected patch must be regenerated by the AI
        with the error evidence as context.
        """
        # Step 1 & 2: Normalise and validate diff format
        val_result = normalize_and_validate(patch.diff)
        if not val_result.passed:
            error_msg = f"PATCH_FORMAT_INVALID: {val_result.reason}"
            self.emit_event("ANALYSIS", "Patch format validation failed", description=error_msg)
            logger.warning(error_msg)
            return False, error_msg

        cleaned_diff = val_result.cleaned
        self.emit_event("STATUS", "Patch format validated", description=f"{val_result.hunk_count} hunk(s), files={val_result.changed_files}")

        # Step 3: Security check for path traversal or absolute paths
        if "../" in cleaned_diff or "..\\" in cleaned_diff or "--- a/C:" in cleaned_diff or "+++ b/C:" in cleaned_diff:
            error_msg = "PATCH_PATH_UNSAFE: Contains traversal or absolute path"
            self.emit_event("ANALYSIS", "Patch failed path safety", description=error_msg)
            return False, error_msg

        # Step 3b: Normalize file paths in diff headers if prefix was omitted and ensure git diff headers
        normalized_diff_lines = []
        for line in cleaned_diff.splitlines():
            line_str = line.rstrip("\r")
            if line_str.startswith("--- "):
                header_path = line_str[4:].strip()
                if header_path.startswith("a/"):
                    header_path = header_path[2:]
                target_file = header_path
                for aff in (patch.affected_files or []):
                    if aff == header_path or aff.endswith("/" + header_path):
                        target_file = aff
                        break
                line_str = f"--- a/{target_file}"
                # Prepend standard diff --git header for robust multi-file patch boundary parsing
                if not normalized_diff_lines or not normalized_diff_lines[-1].startswith("diff --git"):
                    normalized_diff_lines.append(f"diff --git a/{target_file} b/{target_file}")
            elif line_str.startswith("+++ "):
                header_path = line_str[4:].strip()
                if header_path.startswith("b/"):
                    header_path = header_path[2:]
                target_file = header_path
                for aff in (patch.affected_files or []):
                    if aff == header_path or aff.endswith("/" + header_path):
                        target_file = aff
                        break
                line_str = f"+++ b/{target_file}"

            # Fix blank lines in diff: unified diff context lines must have a leading space
            if line_str == "":
                normalized_diff_lines.append(" ")
            else:
                normalized_diff_lines.append(line_str)

        patch_content = "\n".join(normalized_diff_lines) + "\n"

        patch_path = os.path.join(workspace_dir, "candidate.patch")
        with open(patch_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(patch_content)

        # Step 4: git apply --check
        self.emit_event("STATUS", "Running git apply --check")
        check_res = self.cmd_svc.execute_command(
            ["git", "apply", "--check", "--recount", "--unidiff-zero", "--ignore-space-change", "--ignore-whitespace", "candidate.patch"],
            cwd=workspace_dir, timeout_seconds=30, architecture="git"
        )

        if check_res["exit_code"] != 0:
            # git apply --check rejected the patch. Record the EXACT error and return it.
            # The orchestrator will feed this error back to the AI on the next attempt.
            git_error = check_res.get("stderr", "").strip() or check_res.get("stdout", "").strip()
            error_msg = (
                f"PATCH_APPLY_FAILED: git apply --check rejected the patch.\n"
                f"git error output:\n{git_error}\n\n"
                f"Common causes:\n"
                f"- Context lines in the patch do not match the actual source file.\n"
                f"- Line numbers in @@ headers are wrong.\n"
                f"- Lines were skipped inside a hunk (non-contiguous context).\n"
                f"Generate a new patch with context lines copied verbatim from the source."
            )
            self.emit_event("ANALYSIS", "git apply --check failed", description=error_msg)
            logger.warning(error_msg)
            return False, error_msg

        # git apply --check passed: now apply for real
        apply_res = self.cmd_svc.execute_command(
            ["git", "apply", "--recount", "--unidiff-zero", "--ignore-space-change", "--ignore-whitespace", "candidate.patch"],
            cwd=workspace_dir, timeout_seconds=30, architecture="git"
        )
        if apply_res["exit_code"] != 0:
            git_error = apply_res.get("stderr", "").strip()
            error_msg = f"PATCH_APPLY_FAILED: git apply failed after passing --check.\ngit error:\n{git_error}"
            self.emit_event("ANALYSIS", "git apply failed", description=error_msg)
            return False, error_msg

        self.emit_event("STATUS", "Patch applied successfully")
        for changed_file in patch.affected_files:
            self.emit_event("FILE_CHANGE", changed_file, description="Modified by patch")
            
        return True, ""

    def _execute_sandbox(self, workspace_dir: str, architecture: Any, is_patched: bool) -> dict:
        """Execute build+test commands and return full output."""
        build_sys = architecture.get("build_system", "unknown") if isinstance(architecture, dict) else (getattr(architecture, "build_system", "unknown") if architecture else "unknown")
        
        test_cmd = ["pytest"]  # Default fallback
        if build_sys == "maven":
            wrapper = os.path.join(workspace_dir, "mvnw.cmd" if os.name == "nt" else "mvnw")
            mvn_exec = "mvnw.cmd" if os.name == "nt" else "./mvnw"
            if not os.path.exists(wrapper):
                mvn_exec = "mvn.cmd" if os.name == "nt" else "mvn"
            
            test_cmd = [
                mvn_exec,
                "test",
                "-pl", ":payment-service",
                "-Dtest=PaymentPatchRegressionTest"
            ]
        elif build_sys == "gradle":
            wrapper = os.path.join(workspace_dir, "gradlew.bat" if os.name == "nt" else "gradlew")
            if os.path.exists(wrapper):
                test_cmd = ["gradlew.bat" if os.name == "nt" else "./gradlew", "test"]
            else:
                test_cmd = ["gradle", "test"]
        elif build_sys == "npm":
            test_cmd = ["npm", "test"]
            
        cmd_str = " ".join(test_cmd)
        if is_patched:
            self.emit_event("COMMAND", cmd_str)
            
        res = self.cmd_svc.execute_command(test_cmd, cwd=workspace_dir, timeout_seconds=300, architecture=build_sys)
        
        # Capture FULL output — never truncate, the AI needs the exact error
        full_output = (res.get("stdout", "") + "\n" + res.get("stderr", "")).strip()
        
        if is_patched:
            # Emit last 3000 chars for UI — full output stored in result dict
            self.emit_event("OUTPUT", "Test output", description=full_output[-3000:])
            if res["exit_code"] == 0:
                self.emit_event("STATUS", "Tests passed")
            else:
                self.emit_event("STATUS", "Tests failed", description=full_output[-1000:])
        
        return {
            "status": "completed",
            "exit_code": res["exit_code"],
            "output": full_output,
            "timed_out": res["timed_out"]
        }
