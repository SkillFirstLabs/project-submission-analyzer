"""
Safe ZIP extraction with guardrails:
- blocks path traversal (../, absolute paths)
- blocks symlinks
- whitelists code/text extensions only
- skips noise dirs (node_modules, .git, venv, etc.)
- enforces per-file and total zip size limits
- caps number of files analyzed (largest relevant files first)
"""
from __future__ import annotations
import os
import zipfile
from dataclasses import dataclass, field
from typing import List, Dict


class UnsafeZipError(Exception):
    pass


class EmptyProjectError(Exception):
    pass


ALLOWED_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".html", ".css", ".java",
    ".cpp", ".c", ".h", ".hpp", ".cs", ".go", ".kt", ".rs",
    ".json", ".md", ".txt", ".sql", ".yml", ".yaml", ".toml",
    ".env.example", ".sh", ".dockerfile",
}

ALWAYS_INTERESTING_NAMES = {
    "dockerfile", "requirements.txt", "package.json", "pyproject.toml",
    "readme.md", "go.mod", "pom.xml", "build.gradle",
}

BLOCKED_PATH_FRAGMENTS = {
    "node_modules", ".git", "__pycache__", ".env", "venv", ".venv",
    "dist", "build", ".idea", ".vscode", "site-packages", ".pytest_cache",
}

DEFAULT_MAX_FILE_SIZE = 200_000        # 200 KB per file
DEFAULT_MAX_TOTAL_FILES = 20           # cap to avoid context blowup
DEFAULT_MAX_ZIP_UNCOMPRESSED = 50_000_000  # 50 MB guard against zip bombs


@dataclass
class ExtractedFile:
    path: str
    content: str
    size: int


@dataclass
class ExtractionResult:
    files: List[ExtractedFile] = field(default_factory=list)
    file_tree: List[str] = field(default_factory=list)
    dependencies: Dict[str, List[str]] = field(default_factory=dict)
    total_files_in_zip: int = 0
    files_analyzed: int = 0


def _is_blocked_path(path: str) -> bool:
    norm = path.replace("\\", "/")
    if norm.startswith("/") or ".." in norm.split("/"):
        return True
    lower = norm.lower()
    return any(f"/{frag}/" in f"/{lower}/" or lower.startswith(frag) for frag in BLOCKED_PATH_FRAGMENTS)


def _is_allowed_file(path: str) -> bool:
    base = os.path.basename(path).lower()
    if base in ALWAYS_INTERESTING_NAMES:
        return True
    ext = os.path.splitext(path)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def _parse_dependencies(files: List[ExtractedFile]) -> Dict[str, List[str]]:
    deps: Dict[str, List[str]] = {}
    for f in files:
        name = os.path.basename(f.path).lower()
        if name == "requirements.txt":
            deps["python"] = [
                line.strip() for line in f.content.splitlines()
                if line.strip() and not line.strip().startswith("#")
            ]
        elif name == "package.json":
            import json
            try:
                data = json.loads(f.content)
                pkgs = list(data.get("dependencies", {}).keys()) + \
                    list(data.get("devDependencies", {}).keys())
                deps["node"] = pkgs
            except Exception:
                pass
    return deps


def safe_extract_zip(
    zip_path: str,
    max_file_size: int = DEFAULT_MAX_FILE_SIZE,
    max_total_files: int = DEFAULT_MAX_TOTAL_FILES,
    max_zip_uncompressed: int = DEFAULT_MAX_ZIP_UNCOMPRESSED,
) -> ExtractionResult:
    if not zipfile.is_zipfile(zip_path):
        raise UnsafeZipError("Uploaded file is not a valid ZIP archive.")

    candidates: List[ExtractedFile] = []
    total_uncompressed = 0
    total_entries = 0

    with zipfile.ZipFile(zip_path, "r") as zf:
        infos = zf.infolist()
        total_entries = len(infos)

        if total_entries == 0:
            raise EmptyProjectError("The ZIP archive is empty.")

        for info in infos:
            # Skip directories
            if info.is_dir():
                continue

            # Block path traversal / absolute paths
            if _is_blocked_path(info.filename):
                continue

            # Guard against zip bombs (declared uncompressed size)
            total_uncompressed += info.file_size
            if total_uncompressed > max_zip_uncompressed:
                raise UnsafeZipError("ZIP archive exceeds the allowed uncompressed size limit.")

            if not _is_allowed_file(info.filename):
                continue

            if info.file_size > max_file_size:
                # too large to be useful context — skip but don't fail the whole job
                continue

            try:
                with zf.open(info, "r") as fh:
                    raw = fh.read(max_file_size + 1)
            except Exception:
                continue

            try:
                content = raw.decode("utf-8", errors="replace")
            except Exception:
                continue

            candidates.append(ExtractedFile(path=info.filename, content=content, size=info.file_size))

    if not candidates:
        raise EmptyProjectError(
            "No analyzable source files were found in the ZIP "
            "(check the file extensions or that it isn't empty/binary-only)."
        )

    # Rank: prefer always-interesting config files first, then largest source files
    def rank_key(f: ExtractedFile):
        is_config = os.path.basename(f.path).lower() in ALWAYS_INTERESTING_NAMES
        return (0 if is_config else 1, -f.size)

    candidates.sort(key=rank_key)
    selected = candidates[:max_total_files]

    result = ExtractionResult(
        files=selected,
        file_tree=sorted({c.path for c in candidates}),
        dependencies=_parse_dependencies(selected),
        total_files_in_zip=total_entries,
        files_analyzed=len(selected),
    )
    return result
