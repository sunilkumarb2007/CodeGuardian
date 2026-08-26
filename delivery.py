"""Delivery providers for the demo run.

The simulated provider performs a *real* git workflow (init, branch, apply,
commit) inside an isolated workspace generated from the prepared snapshot, so
the branch, diff and commit SHA shown in the UI are genuine. It never talks to
GitHub and never touches the user's repository, and it labels the pull request
as simulated instead of inventing a github.com URL.
"""

import shutil
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.demo import repo_snapshot

GIT_AUTHOR_NAME = "CodeGuardian Demo"
GIT_AUTHOR_EMAIL = "demo@codeguardian.local"

DEFAULT_WORKSPACE_ROOT = Path(__file__).resolve().parents[2] / ".demo_workspaces"


class DeliveryError(RuntimeError):
    pass


@dataclass
class DeliveryRequest:
    run_id: str
    base_branch: str
    branch_name: str
    commit_message: str
    commit_description: str
    diff: str


@dataclass
class DeliveryResult:
    mode: str
    payload: Dict[str, Any]
    commands: List[Dict[str, str]] = field(default_factory=list)


class DeliveryProvider(ABC):
    """Boundary that a real GitHub implementation can later replace."""

    mode: str

    @abstractmethod
    def deliver(self, request: DeliveryRequest) -> DeliveryResult:
        raise NotImplementedError


def split_diff_per_file(diff: str) -> List[str]:
    """Split a concatenated unified diff into one applyable patch per file."""
    patches: List[str] = []
    current: Optional[List[str]] = None
    for line in (diff or "").splitlines():
        if line.startswith("--- "):
            if current:
                patches.append(current)
            current = [line]
        elif current is not None:
            current.append(line)
    if current:
        patches.append(current)

    result = []
    for lines in patches:
        while lines and not lines[-1].strip():
            lines.pop()
        result.append("\n".join(lines) + "\n")
    return result


class SimulatedDeliveryProvider(DeliveryProvider):
    mode = "simulated"

    def __init__(self, workspace_root: Optional[Path] = None):
        configured = settings.codeguardian_demo_workspace_root
        self.workspace_root = workspace_root or (
            Path(configured) if configured else DEFAULT_WORKSPACE_ROOT
        )

    # -- git helpers -------------------------------------------------
    def _git(self, workspace: Path, *args: str, stdin: Optional[str] = None) -> str:
        completed = subprocess.run(
            ["git", *args],
            cwd=workspace,
            input=stdin,
            text=True,
            capture_output=True,
            timeout=30,
        )
        if completed.returncode != 0:
            raise DeliveryError(
                f"git {' '.join(args)} failed: {completed.stderr.strip() or completed.stdout.strip()}"
            )
        return (completed.stdout or "").strip()

    def _prepare_workspace(self, run_id: str) -> Path:
        workspace = self.workspace_root / run_id
        if workspace.exists():
            shutil.rmtree(workspace)
        workspace.mkdir(parents=True)
        for relative in repo_snapshot.list_files():
            target = workspace / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(repo_snapshot.SNAPSHOT_ROOT / relative, target)
        return workspace

    # -- provider ----------------------------------------------------
    def deliver(self, request: DeliveryRequest) -> DeliveryResult:
        if not repo_snapshot.snapshot_available():
            raise DeliveryError("Prepared repository snapshot is not available")

        workspace = self._prepare_workspace(request.run_id)
        commands: List[Dict[str, str]] = []

        def record(command: str, output: str) -> None:
            commands.append({"command": command, "output": output})

        self._git(workspace, "init", "-q")
        self._git(workspace, "symbolic-ref", "HEAD", f"refs/heads/{request.base_branch}")
        self._git(workspace, "config", "user.name", GIT_AUTHOR_NAME)
        self._git(workspace, "config", "user.email", GIT_AUTHOR_EMAIL)
        record("git init", f"Initialized demo workspace on {request.base_branch}")

        self._git(workspace, "add", "-A")
        self._git(workspace, "commit", "-q", "-m", "chore: import prepared repository snapshot")
        base_commit = self._git(workspace, "rev-parse", "HEAD")

        self._git(workspace, "checkout", "-q", "-b", request.branch_name)
        record(f"git checkout -b {request.branch_name}", f"Switched to a new branch '{request.branch_name}'")

        patches = split_diff_per_file(request.diff)
        if not patches:
            raise DeliveryError("Patch contains no file changes")
        for patch in patches:
            self._git(
                workspace,
                "apply",
                "-p1",
                "--recount",
                "--whitespace=nowarn",
                "-",
                stdin=patch,
            )
        diff_stat = self._git(workspace, "diff", "--stat")
        record("git apply", diff_stat)

        self._git(workspace, "add", "-A")
        self._git(
            workspace,
            "commit",
            "-q",
            "-m",
            request.commit_message,
            "-m",
            request.commit_description,
        )
        commit_sha = self._git(workspace, "rev-parse", "HEAD")
        show_stat = self._git(workspace, "show", "--stat", "--oneline", "--no-color", "HEAD")
        record(f"git commit -m \"{request.commit_message}\"", show_stat)

        changed_files = [
            line for line in self._git(
                workspace, "diff", "--name-only", f"{request.base_branch}..{request.branch_name}"
            ).splitlines() if line
        ]

        payload = {
            "mode": self.mode,
            "base": request.base_branch,
            "branch": request.branch_name,
            "commit": request.commit_message,
            "commit_sha": commit_sha,
            "commit_short_sha": commit_sha[:7],
            "base_commit_sha": base_commit,
            "files": changed_files,
            "diff_stat": diff_stat,
            "workspace_path": str(workspace),
            "repository": repo_snapshot.REPOSITORY_URL,
            "pull_request": "SIMULATED PULL REQUEST",
            "pull_request_url": None,
            "pull_request_title": request.commit_message,
            "pull_request_description": request.commit_description,
            "pull_request_state": "READY FOR MERGE",
            "note": (
                "Simulated delivery. The branch, diff and commit are real inside an isolated "
                "local workspace; no GitHub pull request was created."
            ),
        }
        return DeliveryResult(mode=self.mode, payload=payload, commands=commands)


class GitHubDeliveryProvider(DeliveryProvider):
    """Real delivery boundary. Intentionally not enabled for Demo Mode."""

    mode = "real"

    def deliver(self, request: DeliveryRequest) -> DeliveryResult:
        raise DeliveryError(
            "Real GitHub delivery is not enabled. Set CODEGUARDIAN_DELIVERY_MODE=simulated "
            "or implement GitHubDeliveryProvider with an authorized token."
        )


def get_delivery_provider() -> DeliveryProvider:
    if (settings.codeguardian_delivery_mode or "simulated").lower() == "real":
        return GitHubDeliveryProvider()
    return SimulatedDeliveryProvider()
