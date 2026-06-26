"""
scanner_service.py

Scans the extracted project directory and
collects metadata about every file.
"""

from pathlib import Path

from app.models.project_context import ProjectContext
from app.models.project_file import ProjectFile


class ScannerService:

    # Ignore these directories
    IGNORE_DIRECTORIES = {
        "__pycache__",
        ".git",
        ".idea",
        ".vscode",
        "node_modules",
        "venv",
        ".venv",
        "dist",
        "build",
        ".pytest_cache"
    }

    def process(
        self,
        context: ProjectContext
    ) -> ProjectContext:

        project_root = Path(context.extract_path)

        scanned_files = []

        for file in project_root.rglob("*"):

            if not file.is_file():
                continue

            # Skip ignored folders
            if any(
                ignored in file.parts
                for ignored in self.IGNORE_DIRECTORIES
            ):
                continue

            relative_path = file.relative_to(project_root)

            project_file = ProjectFile(

                name=file.name,

                path=str(relative_path).replace("\\", "/"),

                extension=file.suffix.lower(),

                size=file.stat().st_size

            )

            scanned_files.append(project_file)

        context.scanned_files = scanned_files

        context.metadata["files_scanned"] = len(scanned_files)

        return context