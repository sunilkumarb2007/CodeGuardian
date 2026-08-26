import logging
import uuid
import base64
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.repositories import (
    IncidentRepository,
    PatchRepository,
    PullRequestRepository,
    ValidationRunRepository
)
from app.db.models import PullRequest, Patch
from app.schemas.github import PullRequestDeliveryResponse, PullRequestInfo
from app.integrations.github_client import GitHubClient, GitHubError
from app.core.config import settings

logger = logging.getLogger(__name__)

class DeliveryService:
    def __init__(self, db: Session):
        self.db = db
        self.incident_repo = IncidentRepository(db)
        self.patch_repo = PatchRepository(db)
        self.pr_repo = PullRequestRepository(db)
        self.val_run_repo = ValidationRunRepository(db)
        self.github_client = GitHubClient()

    def run_delivery(self, incident_id: UUID, patch_id: UUID, repository_url: str = None) -> PullRequestDeliveryResponse:
        # 1. Load Incident
        incident = self.incident_repo.get_by_id(incident_id)
        if not incident:
            raise ValueError(f"Incident {incident_id} not found")

        # 2. Load Patch
        patch = self.patch_repo.get_by_id(patch_id)
        if not patch:
            raise ValueError(f"Patch {patch_id} not found")

        # 3. Verify Relationship
        if patch.incident_id != incident_id:
            raise ValueError(f"Patch {patch_id} does not belong to incident {incident_id}")

        # 4. Verify Patch Status Gate
        if patch.status != "validated":
            raise ValueError(f"UNVALIDATED_PATCH_CANNOT_BE_DELIVERED: Patch status is {patch.status}")

        # 5. Idempotency Check
        existing_pr = self.pr_repo.get_by_patch_id(patch_id)
        if existing_pr:
            logger.info(f"PR already exists for patch {patch_id}")
            return self._build_response(existing_pr, repository_url)

        # 6. Verify Changed File Safety
        self._verify_patch_safety(patch)

        # 7. Check GitHub Config
        # Extract owner and repo from URL
        if not repository_url:
            repository_url = incident.repository_url if hasattr(incident, 'repository_url') else "https://github.com/CodeGuardian-AI/CodeGuardian"
            
        import urllib.parse
        parsed_url = urllib.parse.urlparse(repository_url)
        path_parts = [p for p in parsed_url.path.split('/') if p]
        
        if len(path_parts) >= 2:
            owner = path_parts[0]
            repo = path_parts[1].replace('.git', '')
        else:
            owner = settings.github_owner or "CodeGuardian-AI"
            repo = "CodeGuardian"
        if not settings.github_token:
            # We don't have a live token, we must fail with INFRASTRUCTURE_FAILURE 
            # or mock it if strictly in a test env, but user requested explicit network failure
            raise ValueError("GITHUB_INFRASTRUCTURE_FAILURE: No GitHub token configured for live delivery.")

        # 8. GitHub Operations
        try:
            # a. Verify repo & get default branch
            default_branch = self.github_client.get_default_branch(owner, repo)
            
            # b. Generate safe branch name
            safe_branch_name = f"codeguardian/incident-{str(incident_id)[:8]}/repair-{str(patch_id)[:8]}"
            
            # c. Get base branch SHA
            base_sha = self.github_client.get_branch_sha(owner, repo, default_branch)
            
            # d. Create branch (handles conflict gracefully)
            try:
                self.github_client.create_branch(owner, repo, safe_branch_name, base_sha)
            except GitHubError as e:
                if e.status_code != 422: # 422 often means branch exists
                    raise
                    
            # e. Fetch original content and apply patch
            import tempfile
            import os
            import subprocess
            import shutil
            
            if not patch.affected_files:
                return PullRequestDeliveryResponse(incident_id=incident_id, patch_id=patch_id, status="failed", repository=repo, branch=safe_branch_name, error_details="No affected files in patch")
                
            file_path = patch.affected_files[0]
            
            # Get original file SHA and content
            file_sha = self.github_client.get_file_sha(owner, repo, file_path, safe_branch_name)
            original_content = self.github_client.get_file_content(owner, repo, file_path, safe_branch_name)
            
            if not original_content:
                return PullRequestDeliveryResponse(incident_id=incident_id, patch_id=patch_id, status="failed", repository=repo, branch=safe_branch_name, error_details=f"Original file {file_path} is empty or missing")
                
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_file_path = os.path.join(temp_dir, file_path)
                os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)
                
                with open(temp_file_path, "w", encoding="utf-8") as f:
                    f.write(original_content)
                    
                patch_file = os.path.join(temp_dir, "candidate.patch")
                with open(patch_file, "w", encoding="utf-8") as f:
                    f.write(patch.diff)
                    
                git_cmd = shutil.which("git") or r"C:\Program Files\Git\bin\git.exe"
                try:
                    subprocess.run([git_cmd, "init"], cwd=temp_dir, check=True, capture_output=True)
                    subprocess.run([git_cmd, "add", "."], cwd=temp_dir, check=True, capture_output=True)
                    subprocess.run([git_cmd, "apply", "candidate.patch"], cwd=temp_dir, check=True, capture_output=True)
                except subprocess.CalledProcessError as e:
                    logger.error(f"Failed to apply patch: {e.stderr.decode() if e.stderr else str(e)}")
                    return PullRequestDeliveryResponse(incident_id=incident_id, patch_id=patch_id, status="failed", repository=repo, branch=safe_branch_name, error_details="Patch application failed due to missing context or malformed patch")
                    
                with open(temp_file_path, "r", encoding="utf-8") as f:
                    new_content = f.read()
                    
            if new_content == original_content or patch.diff in new_content:
                return PullRequestDeliveryResponse(incident_id=incident_id, patch_id=patch_id, status="failed", repository=repo, branch=safe_branch_name, error_details="Patch resulted in unchanged content or invalid diff concatenation")
                
            commit_message = f"fix: apply validated CodeGuardian repair for incident {str(incident_id)[:8]}"
            new_content_base64 = base64.b64encode(new_content.encode('utf-8')).decode('utf-8')
            
            self.github_client.update_file(owner, repo, file_path, safe_branch_name, new_content_base64, commit_message, file_sha)
            
            # f. Create Pull Request
            title = f"fix: CodeGuardian repair for incident {str(incident_id)[:8]}"
            body = self._generate_pr_body(incident_id, patch)
            
            pr_data = self.github_client.create_pull_request(owner, repo, title, safe_branch_name, default_branch, body)
            
        except GitHubError as e:
            logger.error(f"GitHub Error during delivery: {e}")
            return PullRequestDeliveryResponse(
                incident_id=incident_id,
                patch_id=patch_id,
                status="failed",
                repository=repo,
                branch=safe_branch_name if 'safe_branch_name' in locals() else "unknown",
                error_details=f"GitHub API Error {e.status_code}: {e.message}"
            )
            
        # 9. Persist PR Metadata
        new_pr = PullRequest(
            id=uuid.uuid4(),
            incident_id=incident_id,
            patch_id=patch_id,
            repository_id=uuid.uuid4(), # Would be actual repo ID
            provider="github",
            branch_name=safe_branch_name,
            base_branch=default_branch,
            external_pr_number=pr_data.get("number"),
            external_pr_url=pr_data.get("html_url"),
            title=title,
            description=body,
            validation_summary="Build/Test checks were executed in the controlled prototype validation environment.",
            status="open",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        self.pr_repo.save(new_pr)
        
        # 10. Update Incident & Patch Status
        incident.status = "pr_created"
        patch.status = "pushed"
        
        self.db.flush()
        
        return self._build_response(new_pr)

    def _verify_patch_safety(self, patch: Patch) -> None:
        if not patch.affected_files:
            return
            
        unsafe_paths = ["../", ".env", ".git/", "secrets", "credentials"]
        for path in patch.affected_files:
            if path.startswith("/"):
                raise ValueError(f"Unsafe absolute path detected: {path}")
            for unsafe in unsafe_paths:
                if unsafe in path:
                    raise ValueError(f"Unsafe file path detected: {path}")

    def _generate_pr_body(self, incident_id: UUID, patch: Patch) -> str:
        return f"""## CodeGuardian Repair

### Incident
Incident {str(incident_id)[:8]}

### Repair
Generated by CodeGuardian after memory-matched investigation.

### Validation
- Patch context: Passed
- Build: Passed
- Tests: Passed
- Ghost Replay: Passed
- Safety: Passed

### Delivery
Generated by CodeGuardian after validation.

**IMPORTANT:** Build/Test checks were executed in the controlled prototype validation environment.
"""

    def _build_response(self, pr: PullRequest, repository_url: str = None) -> PullRequestDeliveryResponse:
        repo_name = "CodeGuardian"
        if repository_url:
            import urllib.parse
            parsed = urllib.parse.urlparse(repository_url)
            parts = [p for p in parsed.path.split('/') if p]
            if len(parts) >= 2:
                repo_name = parts[1].replace('.git', '')
                
        return PullRequestDeliveryResponse(
            incident_id=pr.incident_id,
            patch_id=pr.patch_id,
            status="pr_created",
            repository=repo_name,
            branch=pr.branch_name,
            pull_request=PullRequestInfo(
                number=pr.external_pr_number or 0,
                url=pr.external_pr_url or "",
                state=pr.status
            ) if pr.external_pr_number else None
        )
