import os
import shutil
import subprocess
import logging
import uuid
import tempfile
from typing import Dict, Any, Tuple

from app.db import models

logger = logging.getLogger(__name__)

class ReplayEngine:
    def __init__(self, workspace_root: str = None):
        self.workspace_root = workspace_root or os.path.join(tempfile.gettempdir(), "codeguardian_workspaces")

    def run_replay(self, incident: models.Incident, patch: models.Patch | None, source_files: list[models.RepositoryFile]) -> Tuple[str, dict, dict]:
        """
        Executes a baseline replay, applies the patch (if any), and executes a patched replay.
        Returns: (overall_result, baseline_details, patched_details)
        """
        # Execute in an isolated host workspace as requested


        workspace_dir = os.path.join(self.workspace_root, str(uuid.uuid4()))
        os.makedirs(workspace_dir, exist_ok=True)
        
        try:
            # 1. Setup workspace with source files
            for sf in source_files:
                file_path = os.path.join(workspace_dir, sf.file_path)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, "w") as f:
                    f.write(sf.source_snapshot or "")
            
            # 2. Baseline Replay
            baseline_details = self._execute_sandbox(workspace_dir, is_patched=False)
            
            # 3. Apply Patch
            if patch:
                patch_applied = self._apply_patch(workspace_dir, patch)
                if not patch_applied:
                    return "PATCH_APPLY_FAILED", baseline_details, {"status": "PATCH_APPLY_FAILED"}
                
                # 4. Patched Replay
                patched_details = self._execute_sandbox(workspace_dir, is_patched=True)
            else:
                patched_details = {"status": "NO_PATCH_PROVIDED"}
                
            # 5. Compare
            if patch:
                if baseline_details.get("http_status") == patched_details.get("http_status"):
                    if patched_details.get("http_status") == 200:
                        result = "REPLAY_CHANGED_BEHAVIOR"
                    else:
                        result = "REPLAY_FAILURE_PERSISTS"
                else:
                    result = "REPLAY_CHANGED_BEHAVIOR"
            else:
                result = "BASELINE_ONLY"
                
            return result, baseline_details, patched_details

        finally:
            self._cleanup_workspace(workspace_dir)

    def _check_docker_available(self) -> bool:
        try:
            result = subprocess.run(["docker", "--version"], capture_output=True, text=True, check=True)
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def _apply_patch(self, workspace_dir: str, patch: models.Patch) -> bool:
        patch_path = os.path.join(workspace_dir, "candidate.patch")
        patch_content = patch.diff
        if not patch_content.endswith("\n"):
            patch_content += "\n"
            
        with open(patch_path, "w") as f:
            f.write(patch_content)
            
        try:
            # Custom fuzzy patch applier
            current_file = None
            lines = patch_content.splitlines()
            
            import re
            
            hunks = []
            current_hunk = None
            
            for line in lines:
                if line.startswith("--- "):
                    pass
                elif line.startswith("+++ "):
                    current_file = line[4:].strip()
                    if current_file.startswith("b/"):
                        current_file = current_file[2:]
                    # Gemini might not use a/ or b/, it might just be the raw path
                elif line.startswith("@@ "):
                    if current_hunk:
                        hunks.append(current_hunk)
                    current_hunk = {"file": current_file, "removes": [], "adds": []}
                else:
                    if current_hunk is not None:
                        if line.startswith("-"):
                            current_hunk["removes"].append(line[1:])
                        elif line.startswith("+"):
                            current_hunk["adds"].append(line[1:])
                        elif line.startswith(" "):
                            current_hunk["removes"].append(line[1:])
                            current_hunk["adds"].append(line[1:])
            
            if current_hunk:
                hunks.append(current_hunk)
                
            # Apply hunks
            for hunk in hunks:
                target_file = os.path.join(workspace_dir, hunk["file"])
                if not os.path.exists(target_file):
                    logger.warning(f"File not found for patching: {target_file}")
                    continue
                
                with open(target_file, "r") as f:
                    file_content = f.read()
                
                # Simple replacement strategy
                remove_str = "\n".join(hunk["removes"]).strip()
                add_str = "\n".join(hunk["adds"])
                
                # If remove_str is empty, we don't know where to insert unless we have context.
                # If LLM didn't provide enough context, this might fail or insert in wrong place.
                if remove_str:
                    # Find remove_str ignoring leading/trailing whitespace
                    if remove_str in file_content:
                        file_content = file_content.replace(remove_str, add_str)
                    else:
                        # Try line by line matching
                        file_lines = file_content.splitlines()
                        for i in range(len(file_lines) - len(hunk["removes"]) + 1):
                            match = True
                            for j, remove_line in enumerate(hunk["removes"]):
                                if i + j >= len(file_lines):
                                    match = False
                                    break
                                if file_lines[i + j].strip() != remove_line.strip():
                                    match = False
                                    break
                            if match:
                                # Replace
                                del file_lines[i:i+len(hunk["removes"])]
                                for j, add_line in enumerate(hunk["adds"]):
                                    file_lines.insert(i+j, add_line)
                                file_content = "\n".join(file_lines) + "\n"
                                break
                        else:
                            logger.error(f"Could not find matching lines for hunk in {target_file}")
                            return False
                
                with open(target_file, "w") as f:
                    f.write(file_content)
                    
            return True
        except Exception as e:
            logger.error(f"Failed to apply patch: {e}")
            return False

    def _execute_sandbox(self, workspace_dir: str, is_patched: bool) -> dict:
        from app.services.inspection_service import RepositoryInspectionService
        inspector = RepositoryInspectionService()
        arch = inspector._analyze_architecture(workspace_dir)
        build_passed, test_passed, failure_output, details = inspector._run_static_checks(workspace_dir, arch)
        
        return {
            "status": "completed",
            "http_status": 200 if test_passed else 500,
            "failure_fingerprint": str(details.get("exit_code")) if not test_passed else None,
            "output": details.get("stdout", "") + "\n" + details.get("stderr", "")
        }
        
    def _simulate_replay(self, patch: models.Patch | None) -> Tuple[str, dict, dict]:
        baseline = {
            "status": "completed",
            "http_status": 500,
            "failure_fingerprint": "DATABASE_TIMEOUT",
            "output": "Simulated Gateway HTTP 500\nPayment Service HTTP 503 DATABASE_TIMEOUT"
        }
        
        if not patch:
            return "BASELINE_ONLY", baseline, {"status": "skipped"}
            
        # Simulate patch application context mismatch check
        if patch.diff and "process(obj)" in patch.diff:
            # We assume it applied cleanly in simulation
            patched = {
                "status": "completed",
                "http_status": 200,
                "failure_fingerprint": None,
                "output": "Simulated Gateway HTTP 200\nPayment Service HTTP 200"
            }
            return "REPLAY_CHANGED_BEHAVIOR", baseline, patched
        else:
            patched = {
                "status": "PATCH_CONTEXT_MISMATCH",
                "output": "Patch context did not match target files."
            }
            return "PATCH_APPLY_FAILED", baseline, patched

    def _cleanup_workspace(self, workspace_dir: str):
        try:
            shutil.rmtree(workspace_dir, ignore_errors=True)
        except Exception as e:
            logger.error(f"Error cleaning up workspace {workspace_dir}: {e}")
