import logging
from typing import List
from app.db.models import Patch, RepositoryFile

logger = logging.getLogger(__name__)

class PatchSafetyValidator:
    @staticmethod
    def validate(patch: Patch, all_files: List[RepositoryFile], architecture: dict | None) -> tuple[bool, str]:
        # 1. Check path safety
        for file_path in patch.affected_files:
            if file_path.startswith("/") or file_path.startswith("\\") or ":" in file_path:
                return False, "PATCH_PATH_UNSAFE"
            if "../" in file_path or "..\\" in file_path:
                return False, "PATCH_PATH_UNSAFE"
            if ".git/" in file_path or "/.git/" in file_path or ".env" in file_path:
                return False, "PATCH_PATH_UNSAFE"
                
        # 2. Check files exist in repository
        repo_paths = {f.file_path for f in all_files}
        for file_path in patch.affected_files:
            # We must normalize windows vs linux paths if needed, but assuming relative paths match
            # Let's check if the file ends with the patch affected file
            if not any(rf.endswith(file_path.replace("\\", "/")) or rf.endswith(file_path.replace("/", "\\")) for rf in repo_paths):
                return False, "PATCH_UNEXPECTED_FILE"
                
        # 3. Check language mismatch
        if architecture:
            lang = (architecture.get("language") or "").lower()
            allowed_extensions = []
            if lang == "java":
                allowed_extensions = [".java", ".xml", ".properties", ".yml", ".yaml", ".gradle", "pom.xml"]
            elif lang == "python":
                allowed_extensions = [".py", ".toml", ".txt", ".yml", ".yaml", "Pipfile"]
            elif lang in ["javascript/typescript", "node", "react"]:
                allowed_extensions = [".js", ".jsx", ".ts", ".tsx", ".json", ".css", ".html"]
                
            if allowed_extensions:
                for file_path in patch.affected_files:
                    if not any(file_path.endswith(ext) for ext in allowed_extensions):
                        return False, "PATCH_LANGUAGE_MISMATCH"

        # 4. Check context match (deleted lines exist)
        deleted_lines = []
        for line in patch.diff.split('\n'):
            if line.startswith('-') and not line.startswith('---'):
                deleted_lines.append(line[1:].strip())
                
        if deleted_lines:
            for del_line in deleted_lines:
                if not del_line:
                    continue
                found = False
                for f in all_files:
                    if any(f.file_path.endswith(af.replace("\\", "/")) or f.file_path.endswith(af.replace("/", "\\")) for af in patch.affected_files):
                        if f.source_snapshot and del_line in f.source_snapshot:
                            found = True
                            break
                if not found:
                    return False, "PATCH_CONTEXT_INVALID"

        return True, ""
