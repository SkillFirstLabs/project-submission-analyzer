"""
Framework Parser: detects software frameworks and libraries used in the project
by scanning source file import statements against known pattern lists.
"""

from pathlib import Path
from typing import Dict, List

from app.config import get_logger
from app.models.evidence import FrameworkEvidence
from app.scanner import constants

logger = get_logger("app.scanner.parsers.framework_parser")


class FrameworkParser:
    """
    Scans source files for known framework import signatures and returns
    a list of FrameworkEvidence objects with supporting file references.
    """

    def parse(self, workspace_dir: Path, source_files: list) -> List[FrameworkEvidence]:
        """
        Detect frameworks by scanning the contents of source files.

        Args:
            workspace_dir: Root of the extracted project workspace.
            source_files: Pre-collected list of FileEvidence objects (from LanguageParser).
                          Used to iterate only known source files, avoiding redundant walks.

        Returns:
            List of FrameworkEvidence objects, each with a list of matching files.
        """
        # framework_name -> set of matching relative file paths
        framework_hits: Dict[str, set] = {name: set() for name in constants.FRAMEWORK_PATTERNS}

        for file_ev in source_files:
            file_path = workspace_dir / file_ev.path
            if not file_path.is_file():
                continue

            ext = file_path.suffix.lower()
            # Only deep-scan recognized source extensions
            if ext not in constants.SOURCE_FILE_EXTENSIONS and ext not in {
                ".json", ".yaml", ".yml", ".toml",
            }:
                continue

            try:
                lines = self._read_head(file_path)
            except OSError:
                continue

            content = "\n".join(lines)
            for framework, patterns in constants.FRAMEWORK_PATTERNS.items():
                for pattern in patterns:
                    if pattern in content:
                        framework_hits[framework].add(file_ev.path)
                        break  # one match is enough per framework per file

        results: List[FrameworkEvidence] = []
        for framework, files in framework_hits.items():
            if files:
                results.append(
                    FrameworkEvidence(
                        name=framework,
                        evidence=sorted(files),
                    )
                )

        # Sort by number of matching files (most confident first)
        results.sort(key=lambda x: -len(x.evidence))

        logger.info(
            "Framework scan complete: %d frameworks detected",
            len(results),
        )
        return results

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _read_head(self, file_path: Path) -> List[str]:
        """
        Read the first N lines of a file for pattern scanning.
        Ignores encoding errors gracefully.
        """
        lines = []
        with open(file_path, encoding="utf-8", errors="ignore") as f:
            for i, line in enumerate(f):
                if i >= constants.PATTERN_SCAN_MAX_LINES:
                    break
                lines.append(line)
        return lines
