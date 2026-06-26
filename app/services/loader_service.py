from pathlib import Path

from app.models.project_context import ProjectContext
from app.models.project_file import ProjectFile


class LoaderService:

    MAX_FILE_SIZE = 100 * 1024   # 100 KB
    MAX_LINES = 500

    def process(self, context: ProjectContext) -> ProjectContext:

        root = Path(context.extract_path)

        loaded_files = []

        for file in context.selected_files:

            file_path = root / file.path

            try:

                if not file_path.exists():
                    file.loaded = False
                    file.error = "File not found"
                    continue

                if file_path.stat().st_size > self.MAX_FILE_SIZE:
                    file.loaded = False
                    file.error = "File too large"
                    continue

                content = self._read_file(file_path)

                if not content.strip():
                    file.loaded = False
                    file.error = "Empty file"
                    continue

                # Update ProjectFile
                file.content = content
                file.line_count = len(content.splitlines())
                file.char_count = len(content)
                file.loaded = True
                file.error = None

                loaded_files.append(file)

            except Exception as e:

                file.loaded = False
                file.error = str(e)

                loaded_files.append(file)

        context.loaded_files = loaded_files

        # Metadata
        context.metadata["loaded_files_count"] = len(loaded_files)

        return context

    def _read_file(self, file_path: Path) -> str:

        lines = []

        with open(
            file_path,
            "r",
            encoding="utf-8",
            errors="ignore"
        ) as f:

            for i, line in enumerate(f):

                if i >= self.MAX_LINES:
                    break

                lines.append(line)

        return "".join(lines)