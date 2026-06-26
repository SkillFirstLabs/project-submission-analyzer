"""
Project scanner: walks the extracted temp directory, reads source files,
and builds the project tree + file content map used by all downstream services.
"""

import os
from pathlib import Path

from app.models.schemas import FileNode, ProjectTree
from app.core.config import get_settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Map file extensions to language names
EXTENSION_LANGUAGE_MAP: dict[str, str] = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".jsx": "JavaScript (JSX)",
    ".tsx": "TypeScript (TSX)",
    ".java": "Java",
    ".kt": "Kotlin",
    ".scala": "Scala",
    ".c": "C",
    ".cpp": "C++",
    ".cc": "C++",
    ".h": "C/C++ Header",
    ".hpp": "C++ Header",
    ".cs": "C#",
    ".go": "Go",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".php": "PHP",
    ".swift": "Swift",
    ".r": "R",
    ".m": "MATLAB/Objective-C",
    ".lua": "Lua",
    ".pl": "Perl",
    ".dart": "Dart",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sass": "Sass",
    ".less": "Less",
    ".json": "JSON",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".toml": "TOML",
    ".xml": "XML",
    ".sql": "SQL",
    ".md": "Markdown",
    ".ipynb": "Jupyter Notebook",
    ".tf": "Terraform",
    ".hcl": "HCL",
}

# Files/dirs to ignore entirely
IGNORE_DIRS = {
    "__pycache__", ".git", ".svn", ".hg", "node_modules",
    ".venv", "venv", "env", ".env", "dist", "build",
    ".pytest_cache", ".mypy_cache", ".ruff_cache",
    "eggs", ".eggs", "*.egg-info", ".dart_tool", ".gradle",
    "gradle", "bin", "obj", "target", "vendor", "pods",
    "bower_components", "jspm_packages",
}

IGNORE_FILES = {
    ".DS_Store", "Thumbs.db", ".gitignore", ".gitattributes",
}


class ScanResult:
    """Output of the project scan."""

    def __init__(
        self,
        tree: ProjectTree,
        file_contents: dict[str, str],   # relative_path → content
    ):
        self.tree = tree
        self.file_contents = file_contents


def scan_project(temp_dir: str) -> ScanResult:
    """
    Walk the extracted project directory, read source files, and build
    the project tree.

    Args:
        temp_dir: absolute path to the extraction temp directory

    Returns:
        ScanResult with tree metadata and file contents map
    """
    settings = get_settings()
    base = Path(temp_dir).resolve()
    nodes: list[FileNode] = []
    file_contents: dict[str, str] = {}

    for root, dirs, files in os.walk(base):
        # Prune ignored directories in-place so os.walk won't descend
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS
                   and not d.endswith(".egg-info")]

        for filename in files:
            if filename in IGNORE_FILES:
                continue

            abs_path = Path(root) / filename
            rel_path = str(abs_path.relative_to(base))
            ext = abs_path.suffix.lower()
            language = EXTENSION_LANGUAGE_MAP.get(ext)

            try:
                size_bytes = abs_path.stat().st_size
            except OSError:
                continue

            # Skip oversized files
            if size_bytes > settings.max_single_file_size_bytes:
                nodes.append(FileNode(
                    path=rel_path,
                    size_bytes=size_bytes,
                    language=language,
                    is_skipped=True,
                    skip_reason=f"File too large ({size_bytes} bytes)"
                ))
                continue

            # Try to read as UTF-8; fall back to latin-1; skip binaries
            content: str | None = None
            for encoding in ("utf-8", "latin-1"):
                try:
                    content = abs_path.read_text(encoding=encoding)
                    break
                except (UnicodeDecodeError, OSError):
                    continue

            if content is None:
                nodes.append(FileNode(
                    path=rel_path,
                    size_bytes=size_bytes,
                    language=language,
                    is_skipped=True,
                    skip_reason="Binary or unreadable file"
                ))
                continue

            nodes.append(FileNode(
                path=rel_path,
                size_bytes=size_bytes,
                language=language,
                is_skipped=False,
            ))
            file_contents[rel_path] = content

    analyzed = sum(1 for n in nodes if not n.is_skipped)
    skipped = sum(1 for n in nodes if n.is_skipped)

    tree = ProjectTree(
        root_dir=temp_dir,
        total_files=len(nodes),
        analyzed_files=analyzed,
        skipped_files=skipped,
        nodes=nodes,
    )

    logger.info("Project scan complete", extra={
        "total": len(nodes),
        "analyzed": analyzed,
        "skipped": skipped,
    })

    return ScanResult(tree=tree, file_contents=file_contents)
