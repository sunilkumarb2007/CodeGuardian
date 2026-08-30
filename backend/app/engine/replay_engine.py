import os
import shutil
import logging
import uuid
import tempfile
import sys
from typing import Dict, Any, Tuple, List

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

    def _detect_commands(self, workspace_dir: str, architecture: Any) -> Tuple[List[str], List[str], str]:
        """
        Determines canonical build and test commands for the repository build system.
        Returns (build_cmd, test_cmd, build_sys).
        """
        build_sys = architecture.get("build_system", "unknown") if isinstance(architecture, dict) else (getattr(architecture, "build_system", "unknown") if architecture else "unknown")
        
        is_windows = (os.name == "nt")
        build_cmd = []
        test_cmd = []

        if build_sys == "maven" or os.path.exists(os.path.join(workspace_dir, "pom.xml")):
            build_sys = "maven"
            wrapper = "mvnw.cmd" if is_windows else "./mvnw"
            if not os.path.exists(os.path.join(workspace_dir, "mvnw.cmd" if is_windows else "mvnw")):
                wrapper = "mvn.cmd" if is_windows else "mvn"

            # Check if multi-module with payment-service
            if os.path.exists(os.path.join(workspace_dir, "payment-service")):
                build_cmd = [wrapper, "test-compile", "-pl", ":payment-service"]
                test_cmd = [wrapper, "test", "-pl", ":payment-service", "-Dtest=PaymentPatchRegressionTest"]
            else:
                build_cmd = [wrapper, "test-compile"]
                test_cmd = [wrapper, "test"]

        elif build_sys == "gradle" or os.path.exists(os.path.join(workspace_dir, "build.gradle")) or os.path.exists(os.path.join(workspace_dir, "build.gradle.kts")):
            build_sys = "gradle"
            wrapper = "gradlew.bat" if is_windows else "./gradlew"
            if not os.path.exists(os.path.join(workspace_dir, "gradlew.bat" if is_windows else "gradlew")):
                wrapper = "gradle"
            build_cmd = [wrapper, "classes", "testClasses"]
            test_cmd = [wrapper, "test"]

        elif build_sys in ["npm", "node"] or os.path.exists(os.path.join(workspace_dir, "package.json")):
            build_sys = "npm"
            build_cmd = ["npm", "run", "build", "--if-present"]
            test_cmd = ["npm", "test"]

        elif build_sys in ["cargo", "rust"] or os.path.exists(os.path.join(workspace_dir, "Cargo.toml")):
            build_sys = "rust"
            build_cmd = ["cargo", "check"]
            test_cmd = ["cargo", "test"]

        elif build_sys == "go" or os.path.exists(os.path.join(workspace_dir, "go.mod")):
            build_sys = "go"
            build_cmd = ["go", "build", "./..."]
            test_cmd = ["go", "test", "./..."]

        else:
            # Python / pytest fallback
            build_sys = "python"
            build_cmd = [sys.executable, "-m", "compileall", "-q", "."]
            test_cmd = ["pytest"]

        return build_cmd, test_cmd, build_sys

    def run_replay(self, incident: models.Incident, patch: models.Patch | None, run_id: str, repo: models.Repository, architecture: Any) -> Tuple[str, dict, dict]:
        """
        Executes baseline verification, applies the candidate patch, compiles (Stage 12),
        and runs tests (Stage 13) in an isolated workspace.
        """
        source_dir = os.path.join(self.workspace_root, "repositories", str(repo.id), "source")
        if not os.path.exists(source_dir):
            self.emit_event("STATUS", "Source directory missing", description=source_dir)
            return "WORKSPACE_MISSING", {}, {}

        run_uuid = str(run_id)
        workspace_dir = os.path.join(self.workspace_root, "runs", run_uuid)
        original_dir = os.path.join(workspace_dir, "original")
        patched_dir = os.path.join(workspace_dir, "patched")
        
        os.makedirs(original_dir, exist_ok=True)
        os.makedirs(patched_dir, exist_ok=True)
        
        try:
            # 1. Baseline setup & execution
            self._copy_dir(source_dir, original_dir)
            self.emit_event("STATUS", "Creating baseline snapshot", description=f"Copied {source_dir} to {original_dir}")
            
            build_cmd, test_cmd, build_sys = self._detect_commands(original_dir, architecture)
            
            self.emit_event("STATUS", "Running baseline verification")
            baseline_res = self.cmd_svc.execute_command(test_cmd, cwd=original_dir, timeout_seconds=300, architecture=build_sys)
            baseline_output = (baseline_res.get("stdout", "") + "\n" + baseline_res.get("stderr", "")).strip()
            
            baseline_details = {
                "status": "completed",
                "exit_code": baseline_res["exit_code"],
                "command": baseline_res["command"],
                "output": baseline_output,
                "test_summary": baseline_res.get("test_summary")
            }

            if baseline_details.get("exit_code") == 0:
                self.emit_event("ANALYSIS", "BASELINE_FAILURE_NOT_REPRODUCED", description="Baseline test unexpectedly passed.")
            else:
                self.emit_event("ANALYSIS", "Baseline failure reproduced", description="Expected test failure observed.")

            if not patch:
                return "BASELINE_ONLY", baseline_details, {"status": "NO_PATCH"}
                
            # 2. Prepare isolated patched workspace
            self.emit_event("STATUS", "Preparing isolated replay workspace")
            self._copy_dir(source_dir, patched_dir)
            
            # 3. Apply patch
            patch_applied, patch_error = self._apply_patch(patched_dir, patch)
            if not patch_applied:
                return "PATCH_APPLY_FAILED", baseline_details, {"status": "PATCH_APPLY_FAILED", "error": patch_error}
                
            # 4. Stage 12: Build execution
            self.emit_event("STATUS", "Stage 12: Compiling patched workspace")
            self.emit_event("COMMAND", " ".join(build_cmd))
            build_res = self.cmd_svc.execute_command(build_cmd, cwd=patched_dir, timeout_seconds=300, architecture=build_sys)
            build_output = (build_res.get("stdout", "") + "\n" + build_res.get("stderr", "")).strip()
            
            if build_res["exit_code"] != 0:
                self.emit_event("STATUS", "Stage 12 BUILD FAILED", description=build_output[-2000:])
                patched_details = {
                    "status": "BUILD_FAILED",
                    "build_passed": False,
                    "tests_passed": False,
                    "build_command": build_res["command"],
                    "build_exit_code": build_res["exit_code"],
                    "build_output": build_output,
                    "exit_code": build_res["exit_code"],
                    "output": build_output,
                    "duration_ms": build_res["duration_ms"]
                }
                return "BUILD_FAILED", baseline_details, patched_details

            self.emit_event("STATUS", "Stage 12 BUILD PASSED")

            # 5. Stage 13: Tests execution
            self.emit_event("STATUS", "Stage 13: Running regression tests on patched workspace")
            self.emit_event("COMMAND", " ".join(test_cmd))
            test_res = self.cmd_svc.execute_command(test_cmd, cwd=patched_dir, timeout_seconds=300, architecture=build_sys)
            test_output = (test_res.get("stdout", "") + "\n" + test_res.get("stderr", "")).strip()
            test_summary = test_res.get("test_summary")

            if test_res.get("recovery_action"):
                self.emit_event("ANALYSIS", f"Test launcher self-healing applied: {test_res['recovery_action']}")

            self.emit_event("OUTPUT", "Test output", description=test_output[-3000:])

            # Judge test success based authoritatively on process exit code and parsed counts
            test_passed = (test_res["exit_code"] == 0)
            if test_passed and test_summary:
                if test_summary.get("failed", 0) > 0 or test_summary.get("errors", 0) > 0:
                    test_passed = False

            patched_details = {
                "status": "completed" if test_passed else "TESTS_FAILED",
                "build_passed": True,
                "tests_passed": test_passed,
                "build_command": build_res["command"],
                "build_exit_code": build_res["exit_code"],
                "build_output": build_output,
                "test_command": test_res["command"],
                "test_exit_code": test_res["exit_code"],
                "test_summary": test_summary,
                "recovery_action": test_res.get("recovery_action"),
                "attempts": test_res.get("attempts", []),
                "exit_code": test_res["exit_code"],
                "output": test_output,
                "duration_ms": test_res["duration_ms"]
            }

            if test_passed:
                self.emit_event("STATUS", "Stage 13 TESTS PASSED")
                self.emit_event("VALIDATION", "REPLAY_CHANGED_BEHAVIOR")
                return "REPLAY_CHANGED_BEHAVIOR", baseline_details, patched_details
            else:
                self.emit_event("STATUS", "Stage 13 TESTS FAILED", description=test_output[-1000:])
                self.emit_event("VALIDATION", "TESTS_FAILED")
                return "REPLAY_FAILURE_PERSISTS", baseline_details, patched_details

        finally:
            pass

    def _copy_dir(self, src: str, dst: str):
        if os.path.exists(dst):
            from app.core.workspace import remove_repository_workspace
            remove_repository_workspace(dst)
        shutil.copytree(src, dst)

    def _apply_patch(self, workspace_dir: str, patch: models.Patch) -> Tuple[bool, str]:
        """
        Validates and applies a patch cleanly to the isolated workspace.
        """
        val_result = normalize_and_validate(patch.diff)
        if not val_result.passed:
            error_msg = f"PATCH_FORMAT_INVALID: {val_result.reason}"
            self.emit_event("ANALYSIS", "Patch format validation failed", description=error_msg)
            logger.warning(error_msg)
            return False, error_msg

        cleaned_diff = val_result.cleaned
        self.emit_event("STATUS", "Patch format validated", description=f"{val_result.hunk_count} hunk(s), files={val_result.changed_files}")

        # Security check for path traversal or absolute paths
        if "../" in cleaned_diff or "..\\" in cleaned_diff or "--- a/C:" in cleaned_diff or "+++ b/C:" in cleaned_diff:
            error_msg = "PATCH_PATH_UNSAFE: Contains traversal or absolute path"
            self.emit_event("ANALYSIS", "Patch failed path safety", description=error_msg)
            return False, error_msg

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

            if line_str == "":
                normalized_diff_lines.append(" ")
            else:
                normalized_diff_lines.append(line_str)

        patch_content = "\n".join(normalized_diff_lines) + "\n"

        patch_path = os.path.join(workspace_dir, "candidate.patch")
        with open(patch_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(patch_content)

        # git apply --check
        self.emit_event("STATUS", "Running git apply --check")
        check_res = self.cmd_svc.execute_command(
            ["git", "apply", "--check", "--recount", "--unidiff-zero", "--ignore-space-change", "--ignore-whitespace", "candidate.patch"],
            cwd=workspace_dir, timeout_seconds=30, architecture="git"
        )

        if check_res["exit_code"] != 0:
            git_error = check_res.get("stderr", "").strip() or check_res.get("stdout", "").strip()
            error_msg = f"PATCH_APPLY_FAILED: git apply --check rejected the patch.\ngit error:\n{git_error}"
            self.emit_event("ANALYSIS", "git apply --check failed", description=error_msg)
            logger.warning(error_msg)
            return False, error_msg

        # git apply
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
