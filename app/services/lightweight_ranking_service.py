from app.models.project_context import ProjectContext
from app.models.project_file import ProjectFile


class LightweightRankingService:

    MAX_FILES = 30

    IMPORTANT_FILES = {
        "main.py": 100,
        "app.py": 100,
        "manage.py": 90,
        "requirements.txt": 80,
        "pyproject.toml": 80,
        "Dockerfile": 80,
        "docker-compose.yml": 80,
        "README.md": 70,
        "package.json": 80,
    }

    IMPORTANT_DIRECTORIES = {
        "routes": 60,
        "controller": 60,
        "controllers": 60,
        "service": 55,
        "services": 55,
        "model": 50,
        "models": 50,
        "auth": 60,
        "middleware": 55,
        "api": 40,
        "config": 40,
    }

    SOURCE_EXTENSION_SCORE = {
        ".py": 30,
        ".js": 20,
        ".ts": 20,
        ".java": 30,
        ".sql": 20,
    }

    def process(self, context: ProjectContext) -> ProjectContext:

        ranked_files = []

        for file in context.scanned_files:

            score = 0
            reasons = []

            # -----------------------
            # Filename scoring
            # -----------------------
            if file.name in self.IMPORTANT_FILES:
                score += self.IMPORTANT_FILES[file.name]
                reasons.append("Important project file")

            # -----------------------
            # Directory scoring
            # -----------------------
            lower_path = file.path.lower()

            for folder, value in self.IMPORTANT_DIRECTORIES.items():
                if folder in lower_path:
                    score += value
                    reasons.append(f"Located in '{folder}'")

            # -----------------------
            # Extension scoring
            # -----------------------
            if file.extension in self.SOURCE_EXTENSION_SCORE:
                score += self.SOURCE_EXTENSION_SCORE[file.extension]
                reasons.append("Source code file")

            # -----------------------
            # Size heuristic
            # -----------------------
            if 100 <= file.size <= 50_000:
                score += 10
                reasons.append("Valid file size")

            elif file.size > 200_000:
                score -= 20
                reasons.append("Very large file")

            # Update ProjectFile
            file.score = score
            file.reasons = reasons

            ranked_files.append(file)

        # Sort by score
        ranked_files.sort(key=lambda x: x.score, reverse=True)

        # Store ranked files
        context.ranked_files = ranked_files

        # Select top files
        context.selected_files = ranked_files[: self.MAX_FILES]

        # Metadata
        context.metadata["ranked_files_count"] = len(ranked_files)
        context.metadata["selected_files_count"] = len(context.selected_files)

        return context