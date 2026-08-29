"""
patch_normalizer.py
===================
Normalises and validates AI-generated unified diffs BEFORE they are handed to
git apply.

Contract
--------
* Input:  raw string from LLM (may have markdown fencing, pseudo-diff, etc.)
* Output: PatchValidationResult with:
    - cleaned: str           -- normalised diff text
    - passed:  bool          -- True only if the diff is structurally valid
    - reason:  str           -- human-readable error when passed=False
    - hunk_count: int        -- number of @@ hunks found

Rules enforced (hard rejections)
---------------------------------
1. Must contain at least one valid hunk header: @@ -N,N +N,N @@
2. Must contain at least one --- a/ or --- <path> file header
3. Must contain at least one +++ b/ or +++ <path> file header
4. Must NOT contain absolute paths (starts with / or drive letter C:)
5. Must NOT contain path traversal (../)
6. Must NOT contain only context/comment lines with no + or - changes
7. Must NOT be empty after stripping fencing
"""

import re
import logging
from dataclasses import dataclass, field
from typing import List

logger = logging.getLogger(__name__)


@dataclass
class PatchValidationResult:
    cleaned: str = ""
    passed: bool = False
    reason: str = ""
    hunk_count: int = 0
    changed_files: List[str] = field(default_factory=list)


class PatchNormalizer:
    """Strips markdown fencing and whitespace noise from LLM diff output."""

    _FENCE_RE = re.compile(r"```(?:diff|patch)?\s*\n?(.*?)```", re.DOTALL | re.IGNORECASE)

    @classmethod
    def normalize(cls, raw: str) -> str:
        if not raw:
            return ""
        
        # We now just clean up whitespace and skip leading prose lines
        lines = raw.splitlines()
        start_idx = None
        for i, line in enumerate(lines):
            if line.startswith("--- ") or line.startswith("diff --git"):
                start_idx = i
                break
        if start_idx is not None and start_idx > 0:
            logger.info(f"PatchNormalizer: skipped {start_idx} leading prose lines")
            return "\n".join(lines[start_idx:]).strip()
        return raw.strip()


class PatchValidator:
    """
    Validates a normalised unified diff for structural correctness.
    Pure Python pre-check — does NOT invoke git.
    """

    _HUNK_RE = re.compile(r"^@@\s+-\d+(?:,\d+)?\s+\+\d+(?:,\d+)?\s+@@", re.MULTILINE)
    _FROM_FILE_RE = re.compile(r"^---\s+\S+", re.MULTILINE)
    _TO_FILE_RE = re.compile(r"^\+\+\+\s+\S+", re.MULTILINE)
    _ABSOLUTE_PATH_RE = re.compile(r"^(?:---|\+\+\+)\s+(?:/|[A-Za-z]:)", re.MULTILINE)
    _TRAVERSAL_RE = re.compile(r"\.\./")

    @classmethod
    def validate(cls, diff: str) -> PatchValidationResult:
        result = PatchValidationResult(cleaned=diff)

        if not diff or not diff.strip():
            result.reason = "PATCH_EMPTY: diff is empty after normalisation"
            logger.warning(result.reason)
            return result

        if "```" in diff:
            result.reason = "PATCH_HAS_MARKDOWN_FENCES: diff contains markdown fences. Generate a pure unified diff."
            logger.warning(result.reason)
            return result

        hunks = cls._HUNK_RE.findall(diff)
        if not hunks:
            result.reason = (
                "PATCH_NO_HUNK_HEADERS: No valid '@@ -N,N +N,N @@' hunk header found. "
                "The patch appears to be a pseudo-diff. Generate a proper unified diff."
            )
            logger.warning(result.reason)
            return result

        result.hunk_count = len(hunks)

        if not cls._FROM_FILE_RE.search(diff):
            result.reason = (
                "PATCH_MISSING_FROM_HEADER: No '--- <file>' header found. "
                "Use '--- a/<filepath>' and '+++ b/<filepath>'."
            )
            logger.warning(result.reason)
            return result

        if not cls._TO_FILE_RE.search(diff):
            result.reason = (
                "PATCH_MISSING_TO_HEADER: No '+++ <file>' header found. "
                "Use '--- a/<filepath>' and '+++ b/<filepath>'."
            )
            logger.warning(result.reason)
            return result

        if cls._ABSOLUTE_PATH_RE.search(diff):
            result.reason = (
                "PATCH_ABSOLUTE_PATH: Patch contains an absolute file path. "
                "All paths must be relative to the repository root."
            )
            logger.warning(result.reason)
            return result

        if cls._TRAVERSAL_RE.search(diff):
            result.reason = (
                "PATCH_PATH_TRAVERSAL: Patch contains path traversal. Rejected."
            )
            logger.warning(result.reason)
            return result

        change_lines = [
            l for l in diff.splitlines()
            if (l.startswith("+") and not l.startswith("+++"))
            or (l.startswith("-") and not l.startswith("---"))
        ]
        if not change_lines:
            result.reason = (
                "PATCH_NO_CHANGES: Patch has hunk headers but no actual +/- change lines."
            )
            logger.warning(result.reason)
            return result

        files = []
        for line in diff.splitlines():
            if line.startswith("+++ "):
                path = line[4:].strip()
                if path.startswith("b/"):
                    path = path[2:]
                if path and path != "/dev/null":
                    files.append(path)
        result.changed_files = list(dict.fromkeys(files))

        result.passed = True
        logger.info(
            f"PatchValidator: PASSED -- {result.hunk_count} hunk(s), "
            f"{len(change_lines)} change lines, files={result.changed_files}"
        )
        return result


def normalize_and_validate(raw_diff: str) -> PatchValidationResult:
    """Convenience: normalise then validate."""
    cleaned = PatchNormalizer.normalize(raw_diff)
    result = PatchValidator.validate(cleaned)
    result.cleaned = cleaned
    return result
