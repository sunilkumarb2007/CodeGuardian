import os
import logging
from typing import List, Dict, Any, Optional
from app.services.command_service import CommandExecutionService

logger = logging.getLogger(__name__)

class GitWorkspace:
    def __init__(self, workspace_root: str):
        self.workspace_root = workspace_root
        self.command_service = CommandExecutionService()
        os.makedirs(self.workspace_root, exist_ok=True)

    def _get_git_executable(self) -> str:
        # Assuming Windows, we just call "git". CommandExecutionService takes care of path resolution.
        return "git"

    def clone(self, repo_url: str, target_dir: str, timeout: int = 120) -> Dict[str, Any]:
        git_exe = self._get_git_executable()
        cmd = [git_exe, "clone", repo_url, target_dir]
        return self.command_service.execute_command(cmd, self.workspace_root, timeout, architecture="git")

    def status(self, repo_dir: str, timeout: int = 30) -> Dict[str, Any]:
        git_exe = self._get_git_executable()
        cmd = [git_exe, "status", "--porcelain"]
        return self.command_service.execute_command(cmd, repo_dir, timeout, architecture="git")

    def checkout(self, repo_dir: str, branch_or_commit: str, timeout: int = 30) -> Dict[str, Any]:
        git_exe = self._get_git_executable()
        cmd = [git_exe, "checkout", branch_or_commit]
        return self.command_service.execute_command(cmd, repo_dir, timeout, architecture="git")

    def create_branch(self, repo_dir: str, branch_name: str, timeout: int = 30) -> Dict[str, Any]:
        git_exe = self._get_git_executable()
        cmd = [git_exe, "checkout", "-b", branch_name]
        return self.command_service.execute_command(cmd, repo_dir, timeout, architecture="git")

    def apply_patch(self, repo_dir: str, patch_file_path: str, check_only: bool = False, timeout: int = 60) -> Dict[str, Any]:
        git_exe = self._get_git_executable()
        cmd = [git_exe, "apply"]
        if check_only:
            cmd.append("--check")
        cmd.append(patch_file_path)
        return self.command_service.execute_command(cmd, repo_dir, timeout, architecture="git")

    def diff(self, repo_dir: str, check_only: bool = False, timeout: int = 30) -> Dict[str, Any]:
        git_exe = self._get_git_executable()
        cmd = [git_exe, "diff"]
        if check_only:
            cmd.append("--check")
        return self.command_service.execute_command(cmd, repo_dir, timeout, architecture="git")

    def commit(self, repo_dir: str, message: str, timeout: int = 30) -> Dict[str, Any]:
        git_exe = self._get_git_executable()
        # Ensure changes are added
        add_cmd = [git_exe, "add", "."]
        add_res = self.command_service.execute_command(add_cmd, repo_dir, timeout, architecture="git")
        if add_res.get("exit_code") != 0:
            return add_res

        cmd = [git_exe, "commit", "-m", message]
        return self.command_service.execute_command(cmd, repo_dir, timeout, architecture="git")

    def log(self, repo_dir: str, n: int = 1, timeout: int = 30) -> Dict[str, Any]:
        git_exe = self._get_git_executable()
        cmd = [git_exe, "log", f"-{n}", "--format=%H"]
        return self.command_service.execute_command(cmd, repo_dir, timeout, architecture="git")

    def push(self, repo_dir: str, remote: str, branch: str, timeout: int = 120) -> Dict[str, Any]:
        git_exe = self._get_git_executable()
        cmd = [git_exe, "push", remote, branch]
        return self.command_service.execute_command(cmd, repo_dir, timeout, architecture="git")
