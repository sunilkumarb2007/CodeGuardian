import re
from typing import Dict, Any, Tuple
from urllib.parse import urlparse
from app.integrations.github_client import GitHubClient, GitHubError

class GitHubServiceError(Exception):
    def __init__(self, message: str, code: str):
        self.message = message
        self.code = code
        super().__init__(self.message)

class GitHubService:
    def __init__(self):
        self.client = GitHubClient()
        
    def parse_url(self, url: str) -> Tuple[str, str]:
        """
        Parses a GitHub URL and extracts the owner and repository name.
        """
        if not url:
            raise GitHubServiceError("URL cannot be empty", "INVALID_GITHUB_URL")
            
        try:
            parsed = urlparse(url)
            if parsed.netloc not in ("github.com", "www.github.com"):
                raise GitHubServiceError("Not a valid GitHub URL", "INVALID_GITHUB_URL")
                
            path = parsed.path.strip("/").split("/")
            if len(path) < 2:
                raise GitHubServiceError("Invalid GitHub repository format", "INVALID_GITHUB_URL")
                
            owner = path[0]
            repo = path[1]
            if repo.endswith(".git"):
                repo = repo[:-4]
                
            return owner, repo
        except Exception as e:
            if isinstance(e, GitHubServiceError):
                raise
            raise GitHubServiceError("Failed to parse GitHub URL", "INVALID_GITHUB_URL")

    def fetch_metadata(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Fetches repository metadata from GitHub API.
        """
        try:
            data = self.client.verify_repository(owner, repo)
            return {
                "id": str(data.get("id")),
                "owner": data.get("owner", {}).get("login", owner),
                "repo": data.get("name", repo),
                "url": data.get("html_url"),
                "clone_url": data.get("clone_url"),
                "default_branch": data.get("default_branch", "main"),
                "description": data.get("description"),
                "visibility": data.get("visibility", "public"),
                "language": data.get("language")
            }
        except GitHubError as e:
            if e.status_code == 404:
                raise GitHubServiceError(f"Repository not found or inaccessible", "GITHUB_REPOSITORY_NOT_FOUND")
            elif e.status_code == 401:
                raise GitHubServiceError("GitHub authentication failed or required", "GITHUB_AUTH_REQUIRED")
            elif e.status_code == 403:
                raise GitHubServiceError("GitHub API rate limit exceeded or access forbidden", "GITHUB_RATE_LIMITED")
            else:
                raise GitHubServiceError(f"GitHub API Error: {e.message}", "GITHUB_API_ERROR")
