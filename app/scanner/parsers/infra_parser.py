"""
Infrastructure Parser: detects testing frameworks, deployment configurations,
database technologies, documentation files, and configuration files.
"""

import fnmatch
from pathlib import Path
from typing import Dict, List

from app.config import get_logger
from app.models.evidence import (
    ConfigurationEvidence,
    DatabaseEvidence,
    DeploymentEvidence,
    DocumentationEvidence,
    TestingEvidence,
)
from app.scanner import constants

logger = get_logger("app.scanner.parsers.infra_parser")


class InfraParser:
    """
    Scans a project workspace to detect infrastructure and tooling by
    examining file names, directory names, and file contents.
    """

    def parse(
        self, workspace_dir: Path, all_files: list
    ) -> tuple[
        List[TestingEvidence],
        List[DeploymentEvidence],
        List[DatabaseEvidence],
        List[DocumentationEvidence],
        List[ConfigurationEvidence],
    ]:
        """
        Run all infrastructure sub-detectors.

        Args:
            workspace_dir: Root of the extracted project workspace.
            all_files: Pre-collected FileEvidence list from LanguageParser.

        Returns:
            Tuple of (testing, deployment, databases, documentation, configuration).
        """
        file_paths = [fe.path for fe in all_files]

        testing = self._detect_testing(workspace_dir, all_files)
        deployment = self._detect_deployment(workspace_dir, file_paths)
        databases = self._detect_databases(workspace_dir, all_files)
        documentation = self._detect_documentation(file_paths)
        configuration = self._detect_configuration(file_paths)

        logger.info(
            "Infra scan: %d test suites, %d deployment configs, %d databases, "
            "%d doc files, %d config files",
            len(testing),
            len(deployment),
            len(databases),
            len(documentation),
            len(configuration),
        )

        return testing, deployment, databases, documentation, configuration

    # ------------------------------------------------------------------
    # Testing detection
    # ------------------------------------------------------------------

    def _detect_testing(self, workspace_dir: Path, all_files: list) -> List[TestingEvidence]:
        """Count test files per framework."""
        framework_counts: Dict[str, int] = {}

        for file_ev in all_files:
            path = file_ev.path
            filename = Path(path).name
            ext = Path(path).suffix.lower()

            is_test = (
                any(filename.startswith(prefix) for prefix in constants.TEST_FILE_PREFIXES)
                or any(filename.endswith(suffix) for suffix in constants.TEST_FILE_SUFFIXES)
                or any(
                    part in constants.TEST_DIRECTORY_NAMES
                    for part in Path(path).parts[:-1]
                )
            )

            if is_test:
                framework = constants.TESTING_FRAMEWORK_MAP.get(ext, "unknown")
                framework_counts[framework] = framework_counts.get(framework, 0) + 1

        return [
            TestingEvidence(framework=fw, files=count)
            for fw, count in framework_counts.items()
        ]

    # ------------------------------------------------------------------
    # Deployment detection
    # ------------------------------------------------------------------

    def _detect_deployment(
        self, workspace_dir: Path, file_paths: List[str]
    ) -> List[DeploymentEvidence]:
        """Detect Docker, CI/CD, and other deployment configuration files."""
        deployment_hits: Dict[str, List[str]] = {}

        for rel_path in file_paths:
            filename = Path(rel_path).name

            # Check exact deployment file name matches
            deploy_type = constants.DEPLOYMENT_FILE_NAMES.get(filename)
            if deploy_type:
                deployment_hits.setdefault(deploy_type, []).append(rel_path)
                continue

            # Check CI/CD directory patterns (using fnmatch for wildcards)
            for pattern in constants.CI_CD_DIRECTORY_PATTERNS:
                if fnmatch.fnmatch(rel_path, f"*{pattern}*"):
                    deployment_hits.setdefault("CI/CD", []).append(rel_path)
                    break

            # GitHub Actions specifically
            if ".github/workflows" in rel_path and rel_path.endswith((".yml", ".yaml")):
                deployment_hits.setdefault("GitHub Actions", []).append(rel_path)

        return [
            DeploymentEvidence(type=deploy_type, files=files)
            for deploy_type, files in deployment_hits.items()
        ]

    # ------------------------------------------------------------------
    # Database detection
    # ------------------------------------------------------------------

    def _detect_databases(
        self, workspace_dir: Path, all_files: list
    ) -> List[DatabaseEvidence]:
        """Detect databases by scanning source files for import patterns."""
        db_hits: Dict[str, List[str]] = {}

        for file_ev in all_files:
            ext = Path(file_ev.path).suffix.lower()
            # Only scan source and config files
            if ext not in constants.SOURCE_FILE_EXTENSIONS and ext not in {".yaml", ".yml", ".toml", ".cfg", ".ini"}:
                continue

            file_path = workspace_dir / file_ev.path
            if not file_path.is_file():
                continue

            try:
                lines = []
                with open(file_path, encoding="utf-8", errors="ignore") as f:
                    for i, line in enumerate(f):
                        if i >= constants.PATTERN_SCAN_MAX_LINES:
                            break
                        lines.append(line)
                content = "".join(lines)
            except OSError:
                continue

            for db_name, patterns in constants.DATABASE_PATTERNS.items():
                for pattern in patterns:
                    if pattern in content:
                        db_hits.setdefault(db_name, []).append(file_ev.path)
                        break

        return [
            DatabaseEvidence(type=db_name, evidence=files)
            for db_name, files in db_hits.items()
        ]

    # ------------------------------------------------------------------
    # Documentation detection
    # ------------------------------------------------------------------

    def _detect_documentation(
        self, file_paths: List[str]
    ) -> List[DocumentationEvidence]:
        """Detect known documentation files."""
        docs = []
        for rel_path in file_paths:
            filename = Path(rel_path).name
            doc_type = constants.DOC_FILE_NAMES.get(filename)
            if doc_type:
                docs.append(DocumentationEvidence(type=doc_type, file=rel_path))
        return docs

    # ------------------------------------------------------------------
    # Configuration file detection
    # ------------------------------------------------------------------

    def _detect_configuration(
        self, file_paths: List[str]
    ) -> List[ConfigurationEvidence]:
        """Detect known project configuration files."""
        configs = []
        for rel_path in file_paths:
            filename = Path(rel_path).name
            if filename in constants.CONFIG_FILE_NAMES:
                configs.append(ConfigurationEvidence(file=rel_path))
        return configs
