"""
CAG (Context-Augmented Generation) context builder.

Assembles a single rich context string from the scanned project that
is reused across all LLM prompts in one request. This avoids sending
the full codebase multiple times — build once, reuse everywhere.

The context is request-scoped only (no vector DB, no persistence).
"""

from pathlib import Path

from app.models.schemas import ProjectMetadata, TechDetectionResult, ProjectTree
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Max characters to include per file in the context
_MAX_FILE_CHARS = 3000
# Max total context characters sent to LLM
_MAX_CONTEXT_CHARS = 40000

# File priority order — most informative files first
_PRIORITY_EXTENSIONS = [
    ".py", ".js", ".ts", ".jsx", ".tsx",
    ".java", ".go", ".rs", ".cs", ".kt",
    ".ipynb",
    ".json", ".yaml", ".yml", ".toml",
    ".md", ".sql",
]


def _priority_key(path: str) -> int:
    ext = Path(path).suffix.lower()
    try:
        return _PRIORITY_EXTENSIONS.index(ext)
    except ValueError:
        return len(_PRIORITY_EXTENSIONS)


def build_context(
    metadata: ProjectMetadata,
    tree: ProjectTree,
    file_contents: dict[str, str],
    tech: TechDetectionResult,
) -> str:
    """
    Build the CAG context string.

    Structure:
    1. Project overview (title, description, stated outcomes)
    2. Technology summary
    3. File tree
    4. Key file contents (truncated to stay within limits)

    Args:
        metadata: project title / description / outcomes
        tree: scan result tree
        file_contents: relative_path → content
        tech: detected languages + frameworks

    Returns:
        A single formatted context string
    """
    sections: list[str] = []

    # --- Section 1: Project Overview ---
    sections.append(f"""=== PROJECT OVERVIEW ===
Title: {metadata.title}

Description:
{metadata.description}

Stated Outcomes:
{metadata.outcomes}
""")

    # --- Section 2: Technology Summary ---
    tech_lines = []
    if tech.languages:
        tech_lines.append(f"Languages: {', '.join(tech.languages)}")
    if tech.frameworks:
        tech_lines.append(f"Frameworks/Libraries: {', '.join(tech.frameworks)}")
    if tech.dependencies:
        dep_preview = tech.dependencies[:20]
        tech_lines.append(f"Dependencies ({len(tech.dependencies)} total): "
                          f"{', '.join(dep_preview)}"
                          + (" ..." if len(tech.dependencies) > 20 else ""))

    sections.append(f"""=== TECHNOLOGY STACK ===
{chr(10).join(tech_lines) if tech_lines else "No technology information detected."}
""")

    # --- Section 3: File Tree ---
    tree_lines = [f"Total files: {tree.total_files} "
                  f"(analyzed: {tree.analyzed_files}, skipped: {tree.skipped_files})"]
    for node in tree.nodes[:50]:  # cap tree listing
        status = "  [skipped]" if node.is_skipped else ""
        lang = f" ({node.language})" if node.language else ""
        tree_lines.append(f"  {node.path}{lang}{status}")
    if tree.total_files > 50:
        tree_lines.append(f"  ... and {tree.total_files - 50} more files")

    sections.append(f"""=== FILE STRUCTURE ===
{chr(10).join(tree_lines)}
""")

    # --- Section 4: Key File Contents ---
    # Sort files by priority (most informative first)
    sorted_paths = sorted(file_contents.keys(), key=_priority_key)

    content_section_parts = ["=== KEY FILE CONTENTS ==="]
    total_chars = sum(len(s) for s in sections)

    for rel_path in sorted_paths:
        if total_chars >= _MAX_CONTEXT_CHARS:
            content_section_parts.append(
                "\n[Context limit reached — remaining files omitted]"
            )
            break

        content = file_contents[rel_path]
        truncated = content[:_MAX_FILE_CHARS]
        was_truncated = len(content) > _MAX_FILE_CHARS
        trailer = "\n... [file truncated]" if was_truncated else ""

        block = (
            f"\n--- {rel_path} ---\n"
            f"{truncated}{trailer}\n"
        )
        content_section_parts.append(block)
        total_chars += len(block)

    sections.append("\n".join(content_section_parts))

    context = "\n".join(sections)

    logger.info("CAG context built", extra={
        "context_chars": len(context),
        "files_included": len(sorted_paths),
    })

    return context
