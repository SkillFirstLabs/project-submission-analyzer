import json
from pathlib import Path


CATALOG_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "skills_catalog.json"
)


def load_skill_catalog():
    with open(CATALOG_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def suggest_skills(zip_analysis):
    catalog = load_skill_catalog()

    file_tree = zip_analysis["file_tree"]
    source_files = zip_analysis["source_files"]

    combined_code = "\n".join(source_files.values()).lower()

    suggestions = []

    for skill in catalog:
        skill_name = skill["skill_name"]
        skill_lower = skill_name.lower()

        confidence = 0.0
        evidence = []

        # Python detection
        if skill_lower == "python":
            python_files = [
                file
                for file in file_tree
                if file.lower().endswith(".py")
            ]

            if python_files:
                confidence = 0.95
                evidence.append(
                    f"{len(python_files)} Python source file(s) found"
                )

        # FastAPI detection
        elif skill_lower == "fastapi":
            if (
                "from fastapi" in combined_code
                or "import fastapi" in combined_code
            ):
                confidence = 0.95
                evidence.append(
                    "FastAPI import found in source code"
                )

        # PostgreSQL detection
        elif skill_lower == "postgresql":
            postgres_patterns = [
                "postgresql",
                "psycopg",
                "asyncpg"
            ]

            if any(
                pattern in combined_code
                for pattern in postgres_patterns
            ):
                confidence = 0.90
                evidence.append(
                    "PostgreSQL-related dependency or code found"
                )

        # JavaScript detection
        elif skill_lower == "javascript":
            js_files = [
                file
                for file in file_tree
                if file.lower().endswith((".js", ".jsx"))
            ]

            if js_files:
                confidence = 0.90
                evidence.append(
                    f"{len(js_files)} JavaScript source file(s) found"
                )

        # HTML detection
        elif skill_lower == "html":
            html_files = [
                file
                for file in file_tree
                if file.lower().endswith(".html")
            ]

            if html_files:
                confidence = 0.90
                evidence.append(
                    f"{len(html_files)} HTML file(s) found"
                )

        # CSS detection
        elif skill_lower == "css":
            css_files = [
                file
                for file in file_tree
                if file.lower().endswith(".css")
            ]

            if css_files:
                confidence = 0.90
                evidence.append(
                    f"{len(css_files)} CSS file(s) found"
                )

        if confidence > 0:
            suggestions.append(
                {
                    "skill_id": skill["skill_id"],
                    "skill_name": skill_name,
                    "confidence": confidence,
                    "rationale": "; ".join(evidence)
                }
            )

    suggestions.sort(
        key=lambda item: item["confidence"],
        reverse=True
    )

    return suggestions