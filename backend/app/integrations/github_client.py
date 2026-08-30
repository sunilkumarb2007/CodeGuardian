import os
import time
import json
import base64
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
        self._cached_token = None
        self._token_expires_at = 0
        self._auth_mode = "NONE"
        self.token = None
        self._init_auth()

    def _init_auth(self):
        # 1. Check if GitHub App can be used
        token = self._get_app_installation_token()
        if token:
            self.token = token
            self._auth_mode = "GITHUB_APP"
            logger.info("GitHubClient: Authenticated using GitHub App installation token.")
            return

        # 2. Fall back to PAT (development/testing only, disabled in production)
        if settings.app_env != "production" and settings.github_token:
            self.token = settings.github_token
            self._auth_mode = "PAT"
            logger.info("GitHubClient: Falling back to GITHUB_TOKEN (development-only PAT).")
            return

        self.token = None
        self._auth_mode = "UNAUTHENTICATED"
        logger.warning("GitHubClient: No GitHub App credentials or valid GITHUB_TOKEN found.")

    def get_auth_mode(self) -> str:
        return self._auth_mode

    def _generate_jwt(self, app_id: str, private_key_bytes: bytes) -> str:
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.hazmat.primitives.serialization import load_pem_private_key

        def b64url(data: bytes) -> str:
            return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')

        private_key = load_pem_private_key(private_key_bytes, password=None)
        header = {"alg": "RS256", "typ": "JWT"}
        now = int(time.time())
        payload = {
            "iat": now - 60,
            "exp": now + (10 * 60),
            "iss": str(app_id)
        }
        signing_input = f"{b64url(json.dumps(header).encode())}.{b64url(json.dumps(payload).encode())}".encode()
        sig = private_key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
        return f"{signing_input.decode()}.{b64url(sig)}"

    def _get_app_installation_token(self) -> Optional[str]:
        now = int(time.time())
        if self._cached_token and self._token_expires_at > now + 60:
            return self._cached_token

        app_id = settings.github_app_id
        if not app_id:
            return None

        # Look for private key
        key_bytes = None
        if settings.github_app_private_key:
            raw_key = settings.github_app_private_key
            if "\\n" in raw_key and "\n" not in raw_key:
                raw_key = raw_key.replace("\\n", "\n")
            key_bytes = raw_key.strip().encode('utf-8')
        elif settings.github_app_private_key_path and os.path.exists(settings.github_app_private_key_path):
            try:
                with open(settings.github_app_private_key_path, 'rb') as f:
                    key_bytes = f.read()
            except Exception as e:
                logger.warning(f"Failed to read GitHub App private key from path: {e}")
        else:
            # Check default secrets directory paths
            candidates = [
                os.path.join("secrets", "codeguardian-engineering.2026-08-29.private-key.pem"),
                os.path.join(os.path.dirname(__file__), "..", "..", "..", "secrets", "codeguardian-engineering.2026-08-29.private-key.pem"),
                "codeguardian-engineering.private-key.pem"
            ]
            for c in candidates:
                if os.path.exists(c):
                    try:
                        with open(c, 'rb') as f:
                            key_bytes = f.read()
                        break
                    except Exception as e:
                        logger.warning(f"Failed reading key candidate {c}: {e}")

        if not key_bytes:
            return None

        try:
            jwt_token = self._generate_jwt(app_id, key_bytes)
            jwt_headers = {
                "Authorization": f"Bearer {jwt_token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "CodeGuardian-App"
            }
            with httpx.Client(timeout=10.0) as client:
                r = client.get(f"{self.base_url}/app/installations", headers=jwt_headers)
                if r.status_code != 200:
                    logger.warning(f"GitHub App: Failed to list installations ({r.status_code})")
                    return None

                installations = r.json()
                if not installations:
                    logger.info("GitHub App: App exists but has 0 active installations.")
                    return None

                target_owner = (settings.github_owner or "").lower()
                selected_inst = installations[0]
                for inst in installations:
                    account_login = (inst.get("account", {}).get("login") or "").lower()
                    if target_owner and account_login == target_owner:
                        selected_inst = inst
                        break

                inst_id = selected_inst.get("id")
                token_resp = client.post(f"{self.base_url}/app/installations/{inst_id}/access_tokens", headers=jwt_headers)
                if token_resp.status_code == 201:
                    token_data = token_resp.json()
                    self._cached_token = token_data.get("token")
                    self._token_expires_at = now + 3000
                    return self._cached_token
                else:
                    logger.warning(f"GitHub App: Failed to generate installation token ({token_resp.status_code})")
                    return None
        except Exception as e:
            logger.warning(f"GitHub App token acquisition error: {e}")
            return None

    @property
    def headers(self) -> Dict[str, str]:
        # Ensure fresh token if app token expired
        if self._auth_mode == "GITHUB_APP":
            refreshed = self._get_app_installation_token()
            if refreshed:
                self.token = refreshed
        h = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "CodeGuardian-Delivery-Bot"
        }
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

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

    def merge_pull_request(self, owner: str, repo: str, pull_number: int, commit_title: str = "Merge PR by CodeGuardian") -> Dict[str, Any]:
        """Merge a pull request."""
        payload = {
            "commit_title": commit_title,
            "merge_method": "squash"
        }
        response = self._request("PUT", f"/repos/{owner}/{repo}/pulls/{pull_number}/merge", json=payload)
        return response.json()
