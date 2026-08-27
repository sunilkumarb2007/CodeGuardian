import urllib.parse
from typing import Optional, Tuple

def parse_github_url(url: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Safely parses a GitHub URL and extracts the owner and repository name.
    Handles various formats:
    - https://github.com/owner/repo
    - https://github.com/owner/repo.git
    - git@github.com:owner/repo.git
    - http://github.com/owner/repo/
    
    Returns:
        (owner, repo) if parsing succeeds, else (None, None).
    """
    if not url:
        return None, None

    # Handle SSH format git@github.com:owner/repo.git
    if url.startswith("git@github.com:"):
        path = url.replace("git@github.com:", "")
        parts = [p for p in path.split('/') if p]
        if len(parts) >= 2:
            owner = parts[0]
            repo = parts[1].replace('.git', '')
            return owner, repo
            
    # Handle standard HTTP/HTTPS formats
    try:
        parsed = urllib.parse.urlparse(url)
        # Verify it's actually github
        if parsed.netloc not in ("github.com", "www.github.com"):
            # If netloc is empty (e.g. github.com/owner/repo without schema)
            if url.startswith("github.com/") or url.startswith("www.github.com/"):
                path = url.split("/", 1)[1] if "/" in url else ""
            else:
                return None, None
        else:
            path = parsed.path
            
        parts = [p for p in path.split('/') if p]
        if len(parts) >= 2:
            owner = parts[0]
            repo = parts[1].replace('.git', '')
            return owner, repo
    except Exception:
        pass
        
    return None, None

def build_github_url(owner: str, repo: str) -> str:
    """Reconstructs a clean canonical github url."""
    return f"https://github.com/{owner}/{repo}"
