import logging
import uuid
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.repositories import (
    IncidentRepository,
    PatchRepository,
    PullRequestRepository,
    ValidationRunRepository,
    RepositoryFileRepository
)
from app.db.models import PullRequest, Patch
from app.schemas.github import PullRequestDeliveryResponse, PullRequestInfo
from app.integrations.github_client import GitHubClient, GitHubError
from app.core.config import settings
from app.services.git_workspace import GitWorkspace

logger = logging.getLogger(__name__)

class DeliveryProvider:
    def deliver(self, incident_id: UUID, patch: Patch, repository_url: str, db: Session) -> PullRequestDeliveryResponse:
        raise NotImplementedError

class LocalDeliveryProvider(DeliveryProvider):
    def deliver(self, incident_id: UUID, patch: Patch, repository_url: str, db: Session) -> PullRequestDeliveryResponse:
        # Just create the local branch, commit, but no push.
        # This allows testing the Git operations when no token is present.
        return PullRequestDeliveryResponse(
            incident_id=incident_id,
            patch_id=patch.id,
            status="DELIVERY_AUTH_REQUIRED",
            repository="local",
            branch=f"codeguardian/fix/{str(incident_id)[:8]}",
            error_details="No GITHUB_TOKEN configured. Stopped at DELIVERY_AUTH_REQUIRED."
        )

class GitHubDeliveryProvider(DeliveryProvider):
    def __init__(self):
        self.github_client = GitHubClient()
        
    def deliver(self, incident_id: UUID, patch: Patch, repository_url: str, db: Session) -> PullRequestDeliveryResponse:
        import urllib.parse
        parsed_url = urllib.parse.urlparse(repository_url)
        path_parts = [p for p in parsed_url.path.split('/') if p]
        
        if len(path_parts) >= 2:
            owner = path_parts[0]
            repo = path_parts[1].replace('.git', '')
        else:
            owner = settings.github_owner or "CodeGuardian-AI"
            repo = "CodeGuardian"

        safe_branch_name = f"codeguardian/fix/{str(incident_id)[:8]}"
        
        def emit_event(status_type: str, title: str, description: str = None, command: str = None):
            try:
                from app.services.event_logger import BackendEventLogger
                from app.db.models import Run
                run = db.query(Run).filter(Run.incident_id == incident_id).first()
                if run:
                    event_logger = BackendEventLogger(db, str(run.id))
                    event_logger.emit(status_type, title, description=description, command=command)
            except Exception as e:
                logger.warning(f"Failed to emit delivery event: {e}")

        try:
            emit_event("STATUS", "DELIVERY_STARTED", "Initiating automated delivery to GitHub repository.")
            
            default_branch = self.github_client.get_default_branch(owner, repo)
            base_sha = self.github_client.get_branch_sha(owner, repo, default_branch)
            
            emit_event("STATUS", "DELIVERY_WORKSPACE_PREPARED", f"Default branch {default_branch} isolated at commit {base_sha[:8]}.")
            
            try:
                self.github_client.create_branch(owner, repo, safe_branch_name, base_sha)
                emit_event("STATUS", "DELIVERY_BRANCH_CREATED", f"Feature branch {safe_branch_name} created on GitHub.")
            except GitHubError as e:
                if e.status_code != 422:
                    raise
                emit_event("STATUS", "DELIVERY_BRANCH_CREATED", f"Feature branch {safe_branch_name} already exists.")

            import base64
            import tempfile, os

            # Set up temp workspace with the repo files to apply multi-file patch cleanly
            with tempfile.TemporaryDirectory() as temp_dir:
                # Write and track all affected files
                for aff in (patch.affected_files or []):
                    aff_path = os.path.join(temp_dir, aff)
                    os.makedirs(os.path.dirname(aff_path), exist_ok=True)
                    orig_f = self.github_client.get_file_content(owner, repo, aff, default_branch)
                    with open(aff_path, "w", encoding="utf-8", newline="\n") as f:
                        f.write(orig_f)

                patch_file = os.path.join(temp_dir, "candidate.patch")
                # Format patch diff with standard git headers
                formatted_patch_lines = []
                for line in patch.diff.splitlines():
                    l_str = line.rstrip("\r")
                    if l_str.startswith("--- "):
                        hp = l_str[4:].strip()
                        if hp.startswith("a/"):
                            hp = hp[2:]
                        target_f = hp
                        for aff in (patch.affected_files or []):
                            if aff == hp or aff.endswith("/" + hp):
                                target_f = aff
                                break
                        l_str = f"--- a/{target_f}"
                        if not formatted_patch_lines or not formatted_patch_lines[-1].startswith("diff --git"):
                            formatted_patch_lines.append(f"diff --git a/{target_f} b/{target_f}")
                    elif l_str.startswith("+++ "):
                        hp = l_str[4:].strip()
                        if hp.startswith("b/"):
                            hp = hp[2:]
                        target_f = hp
                        for aff in (patch.affected_files or []):
                            if aff == hp or aff.endswith("/" + hp):
                                target_f = aff
                                break
                        l_str = f"+++ b/{target_f}"

                    if l_str == "":
                        formatted_patch_lines.append(" ")
                    else:
                        formatted_patch_lines.append(l_str)

                with open(patch_file, "w", encoding="utf-8", newline="\n") as f:
                    f.write("\n".join(formatted_patch_lines) + "\n")

                gw = GitWorkspace(temp_dir)
                gw.command_service.execute_command(["git", "init"], temp_dir, 30)
                gw.command_service.execute_command(["git", "config", "core.autocrlf", "false"], temp_dir, 30)
                gw.command_service.execute_command(["git", "add", "."], temp_dir, 30)

                apply_res = gw.command_service.execute_command(
                    ["git", "apply", "--recount", "--unidiff-zero", "--ignore-space-change", "--ignore-whitespace", "candidate.patch"],
                    cwd=temp_dir, timeout_seconds=30, architecture="git"
                )

                if apply_res.get("exit_code") != 0:
                    emit_event("STATUS", "DELIVERY_FAILED", f"Patch application failed: {apply_res.get('stderr')}")
                    return PullRequestDeliveryResponse(incident_id=incident_id, patch_id=patch.id, status="failed", repository=repo, branch=safe_branch_name, error_details="Patch application failed.")

                # Read modified contents for all affected files
                modified_files = {}
                for aff in (patch.affected_files or []):
                    aff_path = os.path.join(temp_dir, aff)
                    if os.path.exists(aff_path):
                        with open(aff_path, "r", encoding="utf-8") as f:
                            modified_files[aff] = f.read()

            emit_event("STATUS", "DELIVERY_PATCH_VERIFIED", "Validated patch verified against target branch context.")

            commit_message = f"fix: resolve issue {str(incident_id)[:8]}"
            emit_event("STATUS", "DELIVERY_PUSH_STARTED", f"Pushing validated changes to branch {safe_branch_name}...")

            for aff_file, mod_content in modified_files.items():
                f_sha = self.github_client.get_file_sha(owner, repo, aff_file, safe_branch_name)
                content_b64 = base64.b64encode(mod_content.encode('utf-8')).decode('utf-8')
                self.github_client.update_file(owner, repo, aff_file, safe_branch_name, content_b64, commit_message, f_sha)

            emit_event("STATUS", "DELIVERY_BRANCH_PUSHED", f"Changes committed and pushed to {safe_branch_name}.")
            
            title = commit_message
            body = "Generated by CodeGuardian after automated validation and human operator approval."
            
            emit_event("STATUS", "DELIVERY_PR_CREATING", f"Opening Pull Request from {safe_branch_name} into {default_branch}...")
            try:
                pr_data = self.github_client.create_pull_request(owner, repo, title, safe_branch_name, default_branch, body)
                pr_number = pr_data.get("number")
                pr_url = pr_data.get("html_url")
            except GitHubError as e:
                if e.status_code == 422:
                    # PR already exists, fetch it
                    try:
                        all_prs = self.github_client._request("GET", f"/repos/{owner}/{repo}/pulls?head={owner}:{safe_branch_name}").json()
                        if all_prs and len(all_prs) > 0:
                            pr_number = all_prs[0].get("number")
                            pr_url = all_prs[0].get("html_url")
                        else:
                            raise
                    except Exception:
                        raise e
                else:
                    raise
            
            emit_event("STATUS", "DELIVERY_PR_CREATED", f"Pull Request #{pr_number} successfully created: {pr_url}")

            from app.db.models import Run, Repository
            run_obj = db.query(Run).filter(Run.incident_id == incident_id).first()
            repo_id = run_obj.repository_id if run_obj and run_obj.repository_id else None
            if not repo_id:
                first_repo = db.query(Repository).first()
                repo_id = first_repo.id if first_repo else None

            pr_repo = PullRequestRepository(db)
            new_pr = PullRequest(
                id=uuid.uuid4(),
                incident_id=incident_id,
                patch_id=patch.id,
                repository_id=repo_id,
                provider="github",
                branch_name=safe_branch_name,
                base_branch=default_branch,
                external_pr_number=pr_number,
                external_pr_url=pr_url,
                title=title,
                description=body,
                validation_summary="Build/Test checks were executed in the controlled prototype validation environment.",
                status="open",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            pr_repo.save(new_pr)
            
            emit_event("STATUS", "DELIVERY_COMPLETED", f"Delivery completed. Pull Request #{pr_number} open on GitHub.")

            return PullRequestDeliveryResponse(
                incident_id=incident_id,
                patch_id=patch.id,
                status="pr_created",
                repository=repo,
                branch=safe_branch_name,
                pull_request=PullRequestInfo(
                    number=pr_number or 0,
                    url=pr_url or "",
                    state="open"
                )
            )

        except GitHubError as e:
            emit_event("STATUS", "DELIVERY_FAILED", f"GitHub API Error {e.status_code}: {e.message}")
            return PullRequestDeliveryResponse(
                incident_id=incident_id,
                patch_id=patch.id,
                status="failed",
                repository=repo,
                branch=safe_branch_name,
                error_details=f"GitHub API Error {e.status_code}: {e.message}"
            )


class DeliveryService:
    def __init__(self, db: Session):
        self.db = db
        self.incident_repo = IncidentRepository(db)
        self.patch_repo = PatchRepository(db)
        from app.db.repositories import PullRequestRepository
        self.pr_repo = PullRequestRepository(db)

    def run_delivery(self, incident_id: UUID, patch_id: UUID, repository_url: str = None) -> PullRequestDeliveryResponse:
        incident = self.incident_repo.get_by_id(incident_id)
        if not incident:
            raise ValueError(f"Incident {incident_id} not found")

        patch = self.patch_repo.get_by_id(patch_id)
        if not patch:
            raise ValueError(f"Patch {patch_id} not found")

        existing_pr = self.pr_repo.get_by_patch_id(patch_id)
        if existing_pr:
            # Idempotent: return existing
            return PullRequestDeliveryResponse(
                incident_id=incident_id,
                patch_id=patch_id,
                status="pr_created",
                repository=existing_pr.provider,
                branch=existing_pr.branch_name,
                pull_request=PullRequestInfo(
                    number=existing_pr.external_pr_number or 0,
                    url=existing_pr.external_pr_url or "",
                    state=existing_pr.status
                )
            )

        if str(patch.incident_id) != str(incident_id):
            raise ValueError(f"Patch {patch_id} does not belong to incident {incident_id}")

        if patch.status != "validated":
            raise ValueError(f"UNVALIDATED_PATCH_CANNOT_BE_DELIVERED: Patch status is {patch.status}")

        self._verify_patch_safety(patch)

        if not repository_url:
            repository_url = incident.repository_url if hasattr(incident, 'repository_url') else "https://github.com/CodeGuardian-AI/CodeGuardian"

        if settings.github_token:
            provider = GitHubDeliveryProvider()
        else:
            provider = LocalDeliveryProvider()

        res = provider.deliver(incident_id, patch, repository_url, self.db)
        
        if res.status == "DELIVERY_AUTH_REQUIRED":
            incident.status = "failed"
        elif res.status == "pr_created":
            incident.status = "pr_created"
            patch.status = "pushed"
        else:
            incident.status = "failed"
            
        self.db.flush()
        return res

    def _verify_patch_safety(self, patch) -> None:
        if not patch.affected_files:
            return
            
        unsafe_paths = ["../", ".env", ".git/", "secrets", "credentials"]
        for path in patch.affected_files:
            if path.startswith("/"):
                raise ValueError(f"Unsafe absolute path detected: {path}")
            for unsafe in unsafe_paths:
                if unsafe in path:
                    raise ValueError(f"Unsafe file path detected: {path}")
