import os

LANGUAGE_EXTENSIONS = {
    ".py": "Python",
    ".java": "Java",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".html": "HTML",
    ".css": "CSS",
    ".cpp": "C++",
    ".c": "C",
    ".cs": "C#",
    ".php": "PHP",
    ".go": "Go",
    ".rs": "Rust",
}


def analyze_project_stats(project_path: str):
    language_count = {}
    total_files = 0
    total_lines = 0

    for root, _, files in os.walk(project_path):
        for file in files:
            total_files += 1

            extension = os.path.splitext(file)[1].lower()

            if extension in LANGUAGE_EXTENSIONS:
                language = LANGUAGE_EXTENSIONS[extension]
                language_count[language] = language_count.get(language, 0) + 1

            file_path = os.path.join(root, file)

            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    total_lines += sum(1 for _ in f)
            except Exception:
                pass

    primary_language = "Unknown"

    if language_count:
        primary_language = max(language_count, key=language_count.get)

    return {
        "primary_language": primary_language,
        "language_distribution": language_count,
        "total_files": total_files,
        "total_lines": total_lines,
    }