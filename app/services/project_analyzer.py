# Project Analyzer (Evidence-Based Version)

from pathlib import Path
import re


SUPPORTED_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx",
    ".java", ".html", ".css", ".sql",
    ".json", ".yml", ".yaml"
}

IGNORE_DIRS = {
    "node_modules",
    "venv",
    ".git",
    "__pycache__",
    "build",
    "dist",
    ".idea"
}


def extract_python_imports(content: str):
    """
    Extracts Python imports safely.
    """
    imports = set()

    try:
        import_lines = re.findall(
            r"^(?:from\s+([a-zA-Z0-9_\.]+)\s+import|import\s+([a-zA-Z0-9_\.]+))",
            content,
            re.MULTILINE
        )

        for imp in import_lines:
            for item in imp:
                if item:
                    imports.add(item.split(".")[0])

    except:
        pass

    return list(imports)


def extract_js_imports(content: str):
    """
    Extracts JS/TS imports safely.
    """
    imports = set()

    try:
        patterns = [
            r"import\s+.*?\s+from\s+['\"]([^'\"]+)['\"]",
            r"require\(['\"]([^'\"]+)['\"]\)"
        ]

        for pattern in patterns:
            found = re.findall(pattern, content)
            for f in found:
                imports.add(f.split("/")[0])

    except:
        pass

    return list(imports)


def analyze_project(project_path: Path):

    file_tree = []
    dependencies = []
    code_samples = []
    imports = set()

    for file in project_path.rglob("*"):

        # ignore junk dirs
        if any(ignored in str(file) for ignored in IGNORE_DIRS):
            continue

        if not file.is_file():
            continue

        relative_path = str(file.relative_to(project_path))
        file_tree.append(relative_path)

        # ---------------------------
        # READ FILE CONTENT
        # ---------------------------
        if file.suffix in SUPPORTED_EXTENSIONS:
            try:
                content = file.read_text(encoding="utf-8", errors="ignore")

                # store code sample (limited)
                if len(content.strip()) > 50:
                    code_samples.append({
                        "file": relative_path,
                        "snippet": content[:1200]
                    })

                # ---------------------------
                # PYTHON IMPORTS
                # ---------------------------
                if file.suffix == ".py":
                    imports.update(extract_python_imports(content))

                # ---------------------------
                # JS IMPORTS
                # ---------------------------
                if file.suffix in {".js", ".ts", ".jsx", ".tsx"}:
                    imports.update(extract_js_imports(content))

            except:
                continue

        # ---------------------------
        # DEPENDENCIES
        # ---------------------------
        if file.name == "requirements.txt":
            try:
                dependencies.extend(
                    [
                        line.strip()
                        for line in file.read_text().splitlines()
                        if line.strip() and not line.startswith("#")
                    ]
                )
            except:
                pass

        if file.name == "package.json":
            try:
                content = file.read_text(encoding="utf-8", errors="ignore")
                dependencies.append("NodeJS Project Detected")

                # try extract npm deps
                deps = re.findall(r'"([a-zA-Z0-9\-_]+)":\s*"\^?[\d\.]+"', content)
                dependencies.extend(deps)

            except:
                pass

        # ---------------------------
        # DOCKER / CI DETECTION (ONLY FACTUAL)
        # ---------------------------
        if file.name in {"Dockerfile", "docker-compose.yml", ".github"}:
            dependencies.append(f"DevOps: {file.name}")

    return {
        "file_tree": file_tree[:400],
        "dependencies": list(set(dependencies))[:150],
        "code_samples": code_samples[:25],
        "imports": list(imports)[:80]
    }