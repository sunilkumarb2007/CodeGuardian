import os
import stat
import shutil
import time
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class WorkspaceCleanupError(Exception):
    pass

def handle_remove_readonly(func, path, exc):
    """
    Error handler for shutil.rmtree that handles read-only files (like Git packfiles).
    """
    excvalue = exc[1]
    if func in (os.rmdir, os.remove, os.unlink):
        try:
            os.chmod(path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO) # 0777
            func(path)
        except Exception as e:
            logger.warning(f"Failed to remove {path} after changing permissions: {e}")
    else:
        raise

def remove_repository_workspace(path: str):
    """
    Safely removes a repository workspace directory, handling read-only files.
    """
    path_obj = Path(path)
    if not path_obj.exists():
        return
        
    # Safety check: Never delete outside temp/CodeGuardian directories
    str_path = str(path_obj.resolve())
    if "codeguardian" not in str_path.lower() and "temp" not in str_path.lower() and "tmp" not in str_path.lower():
        raise WorkspaceCleanupError(f"Safety violation: Refusing to delete path outside CodeGuardian workspace: {path}")

    # Retry logic
    max_retries = 3
    for attempt in range(max_retries):
        try:
            shutil.rmtree(str_path, onerror=handle_remove_readonly)
            break
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(0.5)
            else:
                logger.error(f"Failed to remove workspace {path} after {max_retries} attempts: {e}")
                
    if path_obj.exists():
        raise WorkspaceCleanupError(f"Failed to completely remove workspace directory: {path}")

