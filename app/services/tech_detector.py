"""
Technology detector: infers languages, frameworks, and dependency managers
from file names, extensions, and import statements.
"""

import re
from pathlib import Path
from collections import Counter

from app.models.schemas import TechDetectionResult
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Framework / library detection rules
# Each rule: (pattern_in_file_content_or_name, framework_name)
# ---------------------------------------------------------------------------

_FRAMEWORK_SIGNATURES: list[tuple[str, str]] = [
    # Python web
    (r"from fastapi import|import fastapi", "FastAPI"),
    (r"from flask import|import flask", "Flask"),
    (r"from django", "Django"),
    (r"from tornado", "Tornado"),
    (r"from aiohttp", "aiohttp"),

    # Python ML/Data
    (r"import tensorflow|from tensorflow", "TensorFlow"),
    (r"import torch|from torch", "PyTorch"),
    (r"import sklearn|from sklearn", "scikit-learn"),
    (r"import pandas|from pandas|import pd\b", "Pandas"),
    (r"import numpy|from numpy|import np\b", "NumPy"),
    (r"import matplotlib", "Matplotlib"),
    (r"import seaborn", "Seaborn"),
    (r"import xgboost|from xgboost", "XGBoost"),
    (r"import lightgbm|from lightgbm", "LightGBM"),
    (r"import transformers|from transformers", "HuggingFace Transformers"),
    (r"import langchain|from langchain", "LangChain"),
    (r"import openai|from openai", "OpenAI SDK"),

    # JavaScript/TypeScript
    (r"from 'react'|from \"react\"|require\(['\"]react", "React"),
    (r"from 'next'|from \"next\"|require\(['\"]next", "Next.js"),
    (r"from 'vue'|from \"vue\"|require\(['\"]vue", "Vue.js"),
    (r"from '@angular/core'|require\(['\"]@angular", "Angular"),
    (r"from 'express'|require\(['\"]express", "Express.js"),
    (r"from 'fastify'|require\(['\"]fastify", "Fastify"),
    (r"from 'nestjs'|from '@nestjs/core'", "NestJS"),

    # Java
    (r"import org\.springframework", "Spring Framework"),
    (r"import javax\.servlet", "Java Servlet"),
    (r"@SpringBootApplication", "Spring Boot"),

    # Database / ORM
    (r"from sqlalchemy|import sqlalchemy", "SQLAlchemy"),
    (r"import pymongo|from pymongo", "PyMongo"),
    (r"import redis|from redis", "Redis"),
    (r"import psycopg2|from psycopg2", "PostgreSQL (psycopg2)"),
    (r"mongoose\.connect|require\(['\"]mongoose", "Mongoose"),
    (r"from prisma|require\(['\"]@prisma", "Prisma"),

    # Testing
    (r"import pytest|from pytest", "pytest"),
    (r"import unittest|from unittest", "unittest"),
    (r"from jest|require\(['\"]jest", "Jest"),
]

_COMPILED_SIGS = [
    (re.compile(pat, re.IGNORECASE), name)
    for pat, name in _FRAMEWORK_SIGNATURES
]

# Dependency / package manager files
_DEPENDENCY_FILES = {
    "requirements.txt": "Python (pip)",
    "requirements-dev.txt": "Python (pip-dev)",
    "pyproject.toml": "Python (pyproject)",
    "setup.py": "Python (setup.py)",
    "Pipfile": "Python (Pipenv)",
    "package.json": "Node.js (npm/yarn)",
    "yarn.lock": "Node.js (Yarn)",
    "pnpm-lock.yaml": "Node.js (pnpm)",
    "pom.xml": "Java (Maven)",
    "build.gradle": "Java/Kotlin (Gradle)",
    "build.gradle.kts": "Kotlin (Gradle KTS)",
    "Cargo.toml": "Rust (Cargo)",
    "go.mod": "Go (modules)",
    "composer.json": "PHP (Composer)",
    "Gemfile": "Ruby (Bundler)",
    "pubspec.yaml": "Dart/Flutter",
}


def detect_technologies(
    file_contents: dict[str, str]
) -> TechDetectionResult:
    """
    Analyse file names and content to detect languages, frameworks,
    and dependencies.

    Args:
        file_contents: mapping of relative_path → file content

    Returns:
        TechDetectionResult
    """
    language_counter: Counter = Counter()
    frameworks_found: set[str] = set()
    dep_files_found: list[str] = []
    all_dependencies: list[str] = []

    for rel_path, content in file_contents.items():
        filename = Path(rel_path).name.lower()
        ext = Path(rel_path).suffix.lower()

        # --- Language detection by extension ---
        from app.services.project_scanner import EXTENSION_LANGUAGE_MAP
        lang = EXTENSION_LANGUAGE_MAP.get(ext)
        if lang and ext not in {".json", ".yaml", ".yml", ".toml", ".xml",
                                 ".md", ".txt", ".rst"}:
            language_counter[lang] += 1

        # --- Dependency file detection ---
        canonical_filename = Path(rel_path).name  # preserve case for some files
        for dep_file, manager in _DEPENDENCY_FILES.items():
            if canonical_filename.lower() == dep_file.lower():
                dep_files_found.append(rel_path)
                deps = _parse_dependency_file(dep_file.lower(), content)
                all_dependencies.extend(deps)
                break

        # --- Framework detection from imports ---
        for compiled_pat, fw_name in _COMPILED_SIGS:
            if compiled_pat.search(content):
                frameworks_found.add(fw_name)

    # Sort languages by frequency, take top languages
    sorted_languages = [lang for lang, _ in language_counter.most_common()]

    # Deduplicate dependencies
    unique_deps = sorted(set(all_dependencies))

    result = TechDetectionResult(
        languages=sorted_languages,
        frameworks=sorted(frameworks_found),
        dependencies=unique_deps[:100],  # cap at 100
        dependency_files_found=dep_files_found,
    )

    logger.info("Tech detection complete", extra={
        "languages": sorted_languages,
        "frameworks": list(frameworks_found),
        "dep_files": len(dep_files_found),
    })

    return result


def _parse_dependency_file(filename: str, content: str) -> list[str]:
    """Extract package names from common dependency files."""
    deps: list[str] = []

    if filename in ("requirements.txt", "requirements-dev.txt"):
        for line in content.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                # Strip version specifiers: requests>=2.0 → requests
                pkg = re.split(r"[>=<!;#\[]", line)[0].strip()
                if pkg:
                    deps.append(pkg)

    elif filename == "package.json":
        import json
        try:
            data = json.loads(content)
            for section in ("dependencies", "devDependencies", "peerDependencies"):
                deps.extend(data.get(section, {}).keys())
        except json.JSONDecodeError:
            pass

    elif filename == "pyproject.toml":
        # Simple extraction without full TOML parser
        for line in content.splitlines():
            m = re.match(r'^\s*"?([\w\-\.]+)\s*[>=<!]', line)
            if m:
                deps.append(m.group(1))

    elif filename in ("pom.xml",):
        # Extract artifactId values
        for m in re.finditer(r"<artifactId>(.*?)</artifactId>", content):
            deps.append(m.group(1).strip())

    elif filename in ("build.gradle", "build.gradle.kts"):
        for m in re.finditer(
            r"(?:implementation|compile|api|testImplementation)"
            r"\s*['\"]([^'\"]+)['\"]",
            content
        ):
            deps.append(m.group(1).split(":")[-1])  # group:artifact:version → artifact

    elif filename == "cargo.toml":
        in_deps = False
        for line in content.splitlines():
            if "[dependencies]" in line or "[dev-dependencies]" in line:
                in_deps = True
                continue
            if line.startswith("[") and in_deps:
                in_deps = False
            if in_deps:
                m = re.match(r"^([\w\-]+)\s*=", line)
                if m:
                    deps.append(m.group(1))

    return deps
