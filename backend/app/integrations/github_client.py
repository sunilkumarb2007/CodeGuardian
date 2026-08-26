import httpx
import logging
from typing import Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

class GitHubError(Exception):
    def __init__(self, message: str, status_code: int):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class GitHubClient:
    def __init__(self):
        self.base_url = settings.github_api_url.rstrip('/')
        self.token = settings.github_token
        
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "CodeGuardian-Delivery-Bot"
        }
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

    def _request(self, method: str, endpoint: str, **kwargs) -> httpx.Response:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            with httpx.Client(headers=self.headers, timeout=10.0) as client:
                response = client.request(method, url, **kwargs)
                
            if response.status_code >= 400:
                self._handle_error(response)
                
            return response
        except httpx.RequestError as e:
            logger.error(f"GitHub request failed: {e}")
            raise GitHubError(f"Network error: {str(e)}", 503)

    def _handle_error(self, response: httpx.Response):
        status = response.status_code
        try:
            data = response.json()
            message = data.get("message", "Unknown error")
        except Exception:
            message = response.text

        logger.error(f"GitHub API Error {status}: {message}")
        if status == 401:
            raise GitHubError("Unauthorized: Invalid GitHub token", status)
        elif status == 403:
            raise GitHubError("Forbidden: Insufficient permissions or rate limited", status)
        elif status == 404:
            raise GitHubError("Not Found: Repository or resource does not exist", status)
        elif status == 409:
            raise GitHubError("Conflict: Resource conflict (e.g. branch already exists)", status)
        elif status == 422:
            raise GitHubError(f"Validation Failed: {message}", status)
        else:
            raise GitHubError(f"GitHub API Error: {message}", status)

    def verify_repository(self, owner: str, repo: str) -> Dict[str, Any]:
        """Verify the repository exists and return its metadata."""
        return self._request("GET", f"/repos/{owner}/{repo}").json()

    def get_default_branch(self, owner: str, repo: str) -> str:
        """Get the actual default branch name from GitHub."""
        data = self.verify_repository(owner, repo)
        return data.get("default_branch", "main")

    def get_branch_sha(self, owner: str, repo: str, branch: str) -> str:
        """Get the SHA of a specific branch."""
        response = self._request("GET", f"/repos/{owner}/{repo}/git/ref/heads/{branch}")
        return response.json()["object"]["sha"]

    def create_branch(self, owner: str, repo: str, branch_name: str, sha: str) -> None:
        """Create a new branch from a given SHA."""
        payload = {
            "ref": f"refs/heads/{branch_name}",
            "sha": sha
        }
        self._request("POST", f"/repos/{owner}/{repo}/git/refs", json=payload)

    def get_file_sha(self, owner: str, repo: str, path: str, branch: str) -> Optional[str]:
        """Get the SHA of a file to update it."""
        try:
            response = self._request("GET", f"/repos/{owner}/{repo}/contents/{path}?ref={branch}")
            return response.json()["sha"]
        except GitHubError as e:
            if e.status_code == 404:
                return None
            raise

    def get_file_content(self, owner: str, repo: str, path: str, branch: str) -> str:
        """Get the decoded content of a file."""
        import base64
        response = self._request("GET", f"/repos/{owner}/{repo}/contents/{path}?ref={branch}")
        data = response.json()
        if "content" not in data:
            raise GitHubError(f"No content found for {path}", 404)
        encoded_content = data["content"]
        decoded = base64.b64decode(encoded_content).decode('utf-8')
        return decoded

    def update_file(self, owner: str, repo: str, path: str, branch: str, content_base64: str, commit_message: str, file_sha: Optional[str] = None) -> None:
        """Update or create a file in the repository."""
        payload = {
            "message": commit_message,
            "content": content_base64,
            "branch": branch
        }
        if file_sha:
            payload["sha"] = file_sha
            
        self._request("PUT", f"/repos/{owner}/{repo}/contents/{path}", json=payload)

    def create_pull_request(self, owner: str, repo: str, title: str, head: str, base: str, body: str) -> Dict[str, Any]:
        """Create a pull request and return its details."""
        payload = {
            "title": title,
            "head": head,
            "base": base,
            "body": body
        }
        response = self._request("POST", f"/repos/{owner}/{repo}/pulls", json=payload)
        return response.json()
