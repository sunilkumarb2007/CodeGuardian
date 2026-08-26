"""Prepared repository snapshot used by Demo Mode.

Demo Mode never clones or analyses an arbitrary repository. It reads the
prepared JavaAPICheck snapshot that ships with the backend, so the source
tree, file contents and paths shown in the UI are real files on disk.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

SNAPSHOT_ROOT = Path(__file__).resolve().parents[2] / "test_repo" / "JavaAPICheck-main"

REPOSITORY_NAME = "JavaAPICheck"
REPOSITORY_URL = "https://github.com/sunilkumarb2007/JavaAPICheck"

EXCLUDED_DIRS = {".git", "target", "node_modules", "__pycache__"}
EXCLUDED_SUFFIXES = {".jar", ".class", ".png", ".ico"}

LANGUAGE_BY_SUFFIX = {
    ".java": "java",
    ".xml": "xml",
    ".yml": "yaml",
    ".yaml": "yaml",
    ".properties": "properties",
    ".sql": "sql",
    ".md": "markdown",
    ".cmd": "batch",
    ".sh": "shell",
}

# Why the investigator opens a given file. Deterministic metadata, not inference.
FILE_OPEN_REASONS = {
    "payment-service/src/main/java/com/codeguardian/paymentservice/PaymentProcessingService.java":
        "The root stack trace frame points at charge() in this file.",
    "payment-service/src/main/java/com/codeguardian/paymentservice/DemoPaymentRepository.java":
        "The repository lookup feeds the variable that is dereferenced.",
    "payment-service/src/main/java/com/codeguardian/paymentservice/PaymentController.java":
        "The controller establishes the failing request context.",
    "payment-service/src/test/java/com/codeguardian/paymentservice/PaymentServiceApplicationTests.java":
        "Existing test asserts the current failing behaviour.",
    "payment-service/src/test/java/com/codeguardian/paymentservice/PaymentPatchRegressionTest.java":
        "Regression test that is enabled once the repair lands.",
}


def _language(path: Path) -> Optional[str]:
    return LANGUAGE_BY_SUFFIX.get(path.suffix.lower())


def snapshot_available() -> bool:
    return SNAPSHOT_ROOT.is_dir()


def list_files() -> List[Path]:
    """Every readable file of the prepared snapshot, relative to its root."""
    if not snapshot_available():
        return []
    files: List[Path] = []
    for path in sorted(SNAPSHOT_ROOT.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(SNAPSHOT_ROOT)
        if any(part in EXCLUDED_DIRS for part in relative.parts):
            continue
        if path.suffix.lower() in EXCLUDED_SUFFIXES:
            continue
        files.append(relative)
    return files


def read_file(relative_path: str) -> Optional[str]:
    path = SNAPSHOT_ROOT / relative_path
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8", errors="replace")


def source_files() -> List[Dict[str, Any]]:
    """Flat file list with content, as consumed by the source viewer."""
    entries: List[Dict[str, Any]] = []
    for relative in list_files():
        as_posix = relative.as_posix()
        content = read_file(as_posix) or ""
        entries.append(
            {
                "id": as_posix,
                "path": as_posix,
                "name": relative.name,
                "language": _language(relative),
                "lines": content.count("\n") + 1 if content else 0,
                "content": content,
                "reason": FILE_OPEN_REASONS.get(as_posix),
            }
        )
    return entries


def build_tree() -> List[Dict[str, Any]]:
    """Nested directory tree of the prepared snapshot."""
    root: Dict[str, Any] = {"children": {}}
    for relative in list_files():
        node = root
        parts = relative.parts
        for index, part in enumerate(parts):
            is_file = index == len(parts) - 1
            child = node["children"].get(part)
            if child is None:
                child = {
                    "name": part,
                    "path": "/".join(parts[: index + 1]),
                    "type": "file" if is_file else "directory",
                    "children": {},
                }
                if is_file:
                    child["language"] = _language(relative)
                    child["reason"] = FILE_OPEN_REASONS.get(relative.as_posix())
                node["children"][part] = child
            node = child

    def serialize(node: Dict[str, Any]) -> List[Dict[str, Any]]:
        items = []
        for child in node["children"].values():
            entry = {key: value for key, value in child.items() if key != "children"}
            if child["type"] == "directory":
                entry["children"] = serialize(child)
            items.append(entry)
        return sorted(items, key=lambda item: (item["type"] == "file", item["name"]))

    return serialize(root)
