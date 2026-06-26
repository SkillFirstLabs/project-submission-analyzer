"""
Project Scanner: orchestrates all sub-parsers and assembles the canonical Evidence object.

This is the single public entry point for the static analysis layer.
Usage:
    scanner = ProjectScanner()
    evidence = scanner.scan(workspace_dir, project_info)
"""

import time
from datetime import datetime, timezone
from pathlib import Path

from app.config import get_logger, get_settings
from app.models.evidence import Evidence, EvidenceMetadata, ProjectInfo
from app.scanner.constants import PARSER_VERSION
from app.scanner.parsers.code_parser import CodeParser
from app.scanner.parsers.dependency_parser import DependencyParser
from app.scanner.parsers.framework_parser import FrameworkParser
from app.scanner.parsers.infra_parser import InfraParser
from app.scanner.parsers.language_parser import LanguageParser

logger = get_logger("app.scanner.project_scanner")


class ProjectScanner:
    """
    Orchestrates all static analysis sub-parsers and returns a fully
    populated Evidence object.

    Processing pipeline:
        1. LanguageParser   → statistics, file catalog, directories, languages
        2. DependencyParser → dependencies
        3. FrameworkParser  → frameworks (uses file catalog from step 1)
        4. CodeParser       → classes, functions, HTTP routes (Python AST)
        5. InfraParser      → testing, deployment, databases, docs, config

    Returns:
        Evidence – the canonical output contract for the AI reasoning layer.
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        self._language_parser = LanguageParser()
        self._dependency_parser = DependencyParser()
        self._framework_parser = FrameworkParser()
        self._code_parser = CodeParser()
        self._infra_parser = InfraParser()

    def scan(self, workspace_dir: Path, project_info: ProjectInfo) -> Evidence:
        """
        Run the full static analysis pipeline on an extracted workspace.

        Args:
            workspace_dir: Absolute path to the extracted project directory.
            project_info: Project metadata from the API request.

        Returns:
            A fully-populated Evidence object.

        Raises:
            RuntimeError: If the workspace directory does not exist.
        """
        if not workspace_dir.is_dir():
            raise RuntimeError(
                f"Workspace directory does not exist: {workspace_dir}"
            )

        logger.info(
            "Starting project scan for '%s' in workspace: %s",
            project_info.title,
            workspace_dir,
        )

        start_time_ns = time.monotonic_ns()

        # ----------------------------------------------------------------
        # Step 1: Language detection + file catalog
        # ----------------------------------------------------------------
        statistics, file_catalog, directories, languages = self._language_parser.parse(
            workspace_dir
        )

        # Expose only source files to downstream parsers that need content scanning
        source_files_only = [
            fe for fe in file_catalog
            if fe.language not in ("Unknown", "JSON", "YAML", "XML", "TOML")
            or fe.path.endswith((".py", ".js", ".ts", ".jsx", ".tsx"))
        ]

        # ----------------------------------------------------------------
        # Step 2: Dependency manifests
        # ----------------------------------------------------------------
        dependencies = self._dependency_parser.parse(workspace_dir)

        # ----------------------------------------------------------------
        # Step 3: Framework detection (uses full file catalog)
        # ----------------------------------------------------------------
        frameworks = self._framework_parser.parse(workspace_dir, file_catalog)

        # ----------------------------------------------------------------
        # Step 4: Code structure (Python AST)
        # ----------------------------------------------------------------
        classes, functions, routes = self._code_parser.parse(
            workspace_dir, source_files_only
        )

        # ----------------------------------------------------------------
        # Step 5: Infrastructure and tooling
        # ----------------------------------------------------------------
        testing, deployment, databases, documentation, configuration = (
            self._infra_parser.parse(workspace_dir, file_catalog)
        )

        # ----------------------------------------------------------------
        # Assemble Evidence
        # ----------------------------------------------------------------
        processing_time_ms = (time.monotonic_ns() - start_time_ns) // 1_000_000
        generated_at = datetime.now(timezone.utc).isoformat()

        evidence = Evidence(
            schema_version="1.0",
            project=project_info,
            statistics=statistics,
            languages=languages,
            frameworks=frameworks,
            dependencies=dependencies,
            files=file_catalog,
            directories=directories,
            classes=classes,
            functions=functions,
            routes=routes,
            databases=databases,
            deployment=deployment,
            testing=testing,
            documentation=documentation,
            configuration=configuration,
            metadata=EvidenceMetadata(
                parser_version=PARSER_VERSION,
                processing_time_ms=int(processing_time_ms),
                generated_at=generated_at,
            ),
        )

        logger.info(
            "Scan complete for '%s': %d files, %d languages, %d frameworks, "
            "%d dependencies, %d classes, %d functions, %d routes in %d ms",
            project_info.title,
            statistics.total_files,
            len(languages),
            len(frameworks),
            len(dependencies),
            len(classes),
            len(functions),
            len(routes),
            processing_time_ms,
        )

        return evidence
