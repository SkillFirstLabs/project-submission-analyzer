"""
Language Parser: walks the extracted workspace to build file statistics,
detect programming languages, and assemble the FileEvidence catalog.
"""

from pathlib import Path
from typing import Dict, List, Tuple

from app.config import get_logger
from app.models.evidence import FileEvidence, LanguageEvidence, ProjectStatistics
from app.scanner import constants

logger = get_logger("app.scanner.parsers.language_parser")


class LanguageParser:
    """
    Walks a project workspace directory and produces:
    - ProjectStatistics (file counts, LOC)
    - List[FileEvidence] (per-file catalog)
    - List[str] (relative directory paths)
    - List[LanguageEvidence] (language confidence scores)
    """

    def parse(
        self, workspace_dir: Path
    ) -> Tuple[ProjectStatistics, List[FileEvidence], List[str], List[LanguageEvidence]]:
        """
        Perform a full tree-walk of the workspace directory.

        Args:
            workspace_dir: Absolute path to the extracted project workspace.

        Returns:
            A tuple of (statistics, files, directories, languages).
        """
        file_catalog: List[FileEvidence] = []
        dir_set: List[str] = []
        language_counts: Dict[str, int] = {}
        total_files = 0
        source_files = 0
        total_loc = 0

        import os

        entries = []
        for root, dirs, files in os.walk(workspace_dir):
            # Prune ignored directories in-place so os.walk doesn't traverse them
            dirs[:] = [d for d in dirs if d not in constants.IGNORED_DIRECTORIES]
            root_path = Path(root)
            for d in dirs:
                entries.append(root_path / d)
            for f in files:
                entries.append(root_path / f)

        for entry in sorted(entries):
            relative = entry.relative_to(workspace_dir)
            relative_str = str(relative).replace("\\", "/")

            if entry.is_dir():
                dir_set.append(relative_str)
                continue

            if entry.is_file():
                # Skip ignored extensions
                if entry.suffix.lower() in constants.IGNORED_EXTENSIONS:
                    continue

                total_files += 1
                ext = entry.suffix.lower()
                language = constants.LANGUAGE_MAP.get(ext, "")

                # Count lines for source files
                loc = 0
                if ext in constants.SOURCE_FILE_EXTENSIONS:
                    source_files += 1
                    loc = self._count_lines(entry)
                    total_loc += loc
                    if language:
                        language_counts[language] = language_counts.get(language, 0) + 1

                file_catalog.append(
                    FileEvidence(
                        path=relative_str,
                        language=language or "Unknown",
                        size=entry.stat().st_size,
                    )
                )

        statistics = ProjectStatistics(
            total_files=total_files,
            source_files=source_files,
            directories=len(dir_set),
            lines_of_code=total_loc,
        )

        languages = self._build_language_evidence(language_counts, source_files)

        logger.info(
            "Language scan complete: %d total files, %d source files, %d languages detected",
            total_files,
            source_files,
            len(languages),
        )

        return statistics, file_catalog, dir_set, languages

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _count_lines(self, file_path: Path) -> int:
        """Count non-empty, non-comment lines in a source file."""
        try:
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                return sum(1 for line in f if line.strip())
        except OSError:
            return 0

    def _build_language_evidence(
        self, language_counts: Dict[str, int], total_source_files: int
    ) -> List[LanguageEvidence]:
        """Convert raw language counts to LanguageEvidence with confidence scores."""
        if total_source_files == 0:
            return []

        evidence = []
        for lang, count in sorted(language_counts.items(), key=lambda x: -x[1]):
            confidence = round(count / total_source_files, 4)
            evidence.append(LanguageEvidence(name=lang, confidence=confidence))

        return evidence
