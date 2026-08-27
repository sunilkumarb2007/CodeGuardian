import os
import requests
import logging
from typing import Optional, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

class GitHubMetadataService:
    def __init__(self, token: Optional[str] = None):
        self.token = token or settings.github_token
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"

    def get_repository_metadata(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Fetches authoritative metadata from GitHub API for a repository.
        Returns a dictionary with 'exists', 'is_private', 'default_branch', etc.
        """
        url = f"https://api.github.com/repos/{owner}/{repo}"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {
                    "exists": True,
                    "is_private": data.get("private", False),
                    "default_branch": data.get("default_branch", "main"),
                    "description": data.get("description", ""),
                    "language": data.get("language", ""),
                    "archived": data.get("archived", False)
                }
            elif response.status_code in (404, 401, 403):
                logger.warning(f"Repository {owner}/{repo} not found or access denied. Status: {response.status_code}")
                return {"exists": False, "error": f"HTTP {response.status_code}"}
            else:
                logger.error(f"GitHub API error fetching {owner}/{repo}: {response.status_code} {response.text}")
                return {"exists": False, "error": f"HTTP {response.status_code}"}
        except Exception as e:
            logger.error(f"Failed to fetch metadata for {owner}/{repo}: {e}")
            return {"exists": False, "error": str(e)}

    def check_access(self, owner: str, repo: str) -> bool:
        """Helper to quickly check if we have read access to the repository."""
        meta = self.get_repository_metadata(owner, repo)
        return meta.get("exists", False)
