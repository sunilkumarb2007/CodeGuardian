import os
import shutil
import logging
import uuid
import tempfile
from typing import Dict, Any, Tuple

from app.db import models
from app.services.command_service import CommandExecutionService

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
                return "BASELINE_FAILURE_NOT_REPRODUCED", baseline_details, {}
            else:
                self.emit_event("ANALYSIS", "Baseline failure reproduced", description="Expected test failure observed.")

            if not patch:
                return "BASELINE_ONLY", baseline_details, {"status": "NO_PATCH"}
                
            # 2. Prepare patched workspace
            self.emit_event("STATUS", "Preparing isolated replay workspace")
            self._copy_dir(source_dir, patched_dir)
            
            # 3. Apply patch using real git apply --check first
            patch_applied = self._apply_patch(patched_dir, patch)
            if not patch_applied:
                return "PATCH_APPLY_FAILED", baseline_details, {"status": "PATCH_APPLY_FAILED"}
                
            # 4. Patched execution
            self.emit_event("STATUS", "Running build")
            patched_details = self._execute_sandbox(patched_dir, architecture, is_patched=True)
            
            # 5. Compare
            if patched_details.get("exit_code") == 0:
                result = "REPLAY_CHANGED_BEHAVIOR"
                self.emit_event("VALIDATION", "REPLAY_CHANGED_BEHAVIOR")
                self.emit_event("VALIDATION", "TESTS_PASSED")
            else:
                result = "REPLAY_FAILURE_PERSISTS"
                self.emit_event("VALIDATION", "TESTS_FAILED")
                
            return result, baseline_details, patched_details

        finally:
            pass # Keep runs around for debugging in Phase D

    def _copy_dir(self, src: str, dst: str):
        if os.path.exists(dst):
            from app.core.workspace import remove_repository_workspace
            remove_repository_workspace(dst)
        shutil.copytree(src, dst)

    def _apply_patch(self, workspace_dir: str, patch: models.Patch) -> bool:
        patch_path = os.path.join(workspace_dir, "candidate.patch")
        # Fix blank lines in LLM diffs which should have a single space prefix
        patch_lines = []
        for line in patch.diff.splitlines():
            line = line.rstrip("\r")
            if line == "":
                patch_lines.append(" ")
            else:
                patch_lines.append(line)
        patch_content = "\n".join(patch_lines) + "\n"
            
        with open(patch_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(patch_content)
            
        # Security checks
        if ".." in patch_content or "--- a/C:" in patch_content or "+++ b/C:" in patch_content or "--- a//" in patch_content or "+++ b//" in patch_content:
            self.emit_event("ANALYSIS", "Patch failed path safety", description="Contains traversal or absolute path")
            return False
            
        self.emit_event("STATUS", "Applying patch")
        
        # Git apply --check
        check_res = self.cmd_svc.execute_command(["git", "apply", "--check", "--recount", "--ignore-space-change", "--ignore-whitespace", "-C1", "candidate.patch"], cwd=workspace_dir, timeout_seconds=10, architecture="git")
        if check_res["exit_code"] != 0:
            self.emit_event("OUTPUT", "git apply --check failed", description=check_res["stderr"])
            return False
            
        # Git apply
        apply_res = self.cmd_svc.execute_command(["git", "apply", "--recount", "--ignore-space-change", "--ignore-whitespace", "-C1", "candidate.patch"], cwd=workspace_dir, timeout_seconds=10, architecture="git")
        if apply_res["exit_code"] != 0:
            self.emit_event("OUTPUT", "git apply failed", description=apply_res["stderr"])
            return False
            
        for changed_file in patch.affected_files:
            self.emit_event("FILE_CHANGE", changed_file, description="Modified by patch")
            
        return True

    def _execute_sandbox(self, workspace_dir: str, architecture: Any, is_patched: bool) -> dict:
        # Resolve build/test commands based on architecture allowlist
        build_sys = architecture.get("build_system", "unknown") if isinstance(architecture, dict) else (getattr(architecture, "build_system", "unknown") if architecture else "unknown")
        lang = architecture.get("language", "unknown") if isinstance(architecture, dict) else (getattr(architecture, "language", "unknown") if architecture else "unknown")
        
        test_cmd = ["pytest"] # Default fallback
        if build_sys == "maven":
            test_cmd = ["mvnw.cmd" if os.name == "nt" else "./mvnw", "test"]
        elif build_sys == "gradle":
            test_cmd = ["gradlew.bat" if os.name == "nt" else "./gradlew", "test"]
        elif build_sys == "npm":
            test_cmd = ["npm", "test"]
            
        cmd_str = " ".join(test_cmd)
        if is_patched:
            self.emit_event("COMMAND", cmd_str)
            
        res = self.cmd_svc.execute_command(test_cmd, cwd=workspace_dir, timeout_seconds=300, architecture=build_sys)
        
        if is_patched:
            self.emit_event("OUTPUT", "Tests run", output=res["stdout"][-1000:])
            if res["exit_code"] == 0:
                self.emit_event("STATUS", "Tests passed")
            else:
                self.emit_event("STATUS", "Tests failed")
        
        return {
            "status": "completed",
            "exit_code": res["exit_code"],
            "output": res["stdout"] + "\n" + res["stderr"],
            "timed_out": res["timed_out"]
        }
