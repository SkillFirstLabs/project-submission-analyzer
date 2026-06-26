"""
Scanner-specific constants: language maps, ignored paths, framework patterns,
dependency manifests, and infrastructure detection helpers.

These constants are intentionally scoped to the scanner package and do NOT
belong in app/core/constants.py, which holds only application-wide values.
"""

from typing import Dict, FrozenSet, List, Set

# ---------------------------------------------------------------------------
# Directory / file traversal rules
# ---------------------------------------------------------------------------

IGNORED_DIRECTORIES: FrozenSet[str] = frozenset(
    {
        ".git",
        ".svn",
        ".hg",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "node_modules",
        ".venv",
        "venv",
        "env",
        ".env",
        "dist",
        "build",
        "target",
        "out",
        ".idea",
        ".vscode",
        ".DS_Store",
        "coverage",
        ".coverage",
        "htmlcov",
        "eggs",
        ".eggs",
        "site-packages",
    }
)

IGNORED_EXTENSIONS: FrozenSet[str] = frozenset(
    {
        ".pyc",
        ".pyo",
        ".pyd",
        ".class",
        ".o",
        ".obj",
        ".dll",
        ".so",
        ".dylib",
        ".exe",
        ".bin",
        ".dat",
        ".db",
        ".sqlite",
        ".sqlite3",
        ".lock",
        ".log",
        ".tmp",
        ".bak",
        ".swp",
        ".DS_Store",
    }
)

# ---------------------------------------------------------------------------
# Language detection: extension → language name
# ---------------------------------------------------------------------------

LANGUAGE_MAP: Dict[str, str] = {
    # Python
    ".py": "Python",
    ".pyw": "Python",
    ".pyi": "Python",
    # JavaScript / TypeScript
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    # Java / Kotlin / Scala
    ".java": "Java",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".scala": "Scala",
    # Go
    ".go": "Go",
    # C / C++
    ".c": "C",
    ".h": "C",
    ".cpp": "C++",
    ".cxx": "C++",
    ".cc": "C++",
    ".hpp": "C++",
    # C#
    ".cs": "C#",
    # Rust
    ".rs": "Rust",
    # Ruby
    ".rb": "Ruby",
    # PHP
    ".php": "PHP",
    # Swift
    ".swift": "Swift",
    # Dart
    ".dart": "Dart",
    # Shell
    ".sh": "Shell",
    ".bash": "Shell",
    ".zsh": "Shell",
    ".ps1": "PowerShell",
    # HTML / CSS
    ".html": "HTML",
    ".htm": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sass": "SCSS",
    ".less": "Less",
    # Data / Config
    ".json": "JSON",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".toml": "TOML",
    ".xml": "XML",
    ".sql": "SQL",
    # Other
    ".r": "R",
    ".R": "R",
    ".lua": "Lua",
    ".ex": "Elixir",
    ".exs": "Elixir",
    ".erl": "Erlang",
    ".hrl": "Erlang",
    ".hs": "Haskell",
    ".clj": "Clojure",
    ".cljs": "Clojure",
}

# ---------------------------------------------------------------------------
# Framework detection: framework name → list of import substrings
# Matched against file content (first 150 lines of source files).
# ---------------------------------------------------------------------------

FRAMEWORK_PATTERNS: Dict[str, List[str]] = {
    # Python backends
    "FastAPI": ["from fastapi", "import fastapi", "FastAPI("],
    "Flask": ["from flask", "import flask", "Flask(__name__)"],
    "Django": ["from django", "import django", "django.setup()"],
    "Starlette": ["from starlette", "import starlette"],
    "Tornado": ["from tornado", "import tornado"],
    "Sanic": ["from sanic", "import sanic"],
    "Litestar": ["from litestar", "import litestar"],
    # Python data / ML
    "SQLAlchemy": ["from sqlalchemy", "import sqlalchemy"],
    "Alembic": ["from alembic", "import alembic"],
    "Celery": ["from celery", "import celery"],
    "Pydantic": ["from pydantic", "import pydantic"],
    "Pandas": ["import pandas", "from pandas"],
    "NumPy": ["import numpy", "from numpy"],
    "PyTorch": ["import torch", "from torch"],
    "TensorFlow": ["import tensorflow", "from tensorflow"],
    "Scikit-learn": ["from sklearn", "import sklearn"],
    # JavaScript / TypeScript
    "React": ["import React", "from 'react'", 'from "react"'],
    "Next.js": ["from 'next'", 'from "next"', "next/router", "next/app"],
    "Vue": ["from 'vue'", 'from "vue"', "createApp(", "Vue.component("],
    "Angular": ["@NgModule", "@Component", "@Injectable", "from '@angular"],
    "Express": ["require('express')", 'require("express")', "from 'express'"],
    "NestJS": ["from '@nestjs", "@Module(", "@Controller(", "@Injectable("],
    "Svelte": [".svelte"],
    # Java
    "Spring Boot": [
        "import org.springframework.boot",
        "@SpringBootApplication",
        "@RestController",
    ],
    "Hibernate": ["import org.hibernate", "import javax.persistence"],
    # Other
    "Ruby on Rails": ["require 'rails'", "Rails.application"],
    "Laravel": ["use Illuminate\\", "use Laravel\\"],
}

# ---------------------------------------------------------------------------
# Dependency manifest files: file name → parser strategy key
# ---------------------------------------------------------------------------

DEPENDENCY_MANIFESTS: Dict[str, str] = {
    "requirements.txt": "requirements_txt",
    "requirements-dev.txt": "requirements_txt",
    "requirements-test.txt": "requirements_txt",
    "package.json": "package_json",
    "pom.xml": "pom_xml",
    "go.mod": "go_mod",
    "Pipfile": "pipfile",
    "pyproject.toml": "pyproject_toml",
    "build.gradle": "gradle",
    "build.gradle.kts": "gradle",
    "Gemfile": "gemfile",
    "composer.json": "composer_json",
    "Cargo.toml": "cargo_toml",
}

# ---------------------------------------------------------------------------
# Test file detection
# ---------------------------------------------------------------------------

TEST_FILE_PREFIXES: FrozenSet[str] = frozenset({"test_", "tests_"})
TEST_FILE_SUFFIXES: FrozenSet[str] = frozenset(
    {"_test.py", ".test.js", ".spec.js", ".test.ts", ".spec.ts", "_test.go"}
)
TEST_DIRECTORY_NAMES: FrozenSet[str] = frozenset({"tests", "test", "__tests__", "spec"})

TESTING_FRAMEWORK_MAP: Dict[str, str] = {
    ".py": "pytest",
    ".js": "jest",
    ".jsx": "jest",
    ".ts": "jest",
    ".tsx": "jest",
    ".java": "JUnit",
    ".go": "Go testing",
    ".rb": "RSpec",
    ".cs": "xUnit",
    ".rs": "Rust tests",
}

# ---------------------------------------------------------------------------
# Deployment / infrastructure files
# ---------------------------------------------------------------------------

DEPLOYMENT_FILE_NAMES: Dict[str, str] = {
    "Dockerfile": "Docker",
    "docker-compose.yml": "Docker Compose",
    "docker-compose.yaml": "Docker Compose",
    "docker-compose.override.yml": "Docker Compose",
    ".dockerignore": "Docker",
    "Procfile": "Heroku",
    "app.yaml": "Google App Engine",
    "serverless.yml": "Serverless Framework",
    "serverless.yaml": "Serverless Framework",
    "terraform.tf": "Terraform",
    "main.tf": "Terraform",
    "kubernetes.yml": "Kubernetes",
    "k8s.yml": "Kubernetes",
    "helm.yaml": "Helm",
}

CI_CD_DIRECTORY_PATTERNS: List[str] = [
    ".github/workflows",
    ".gitlab-ci.yml",
    ".circleci/config.yml",
    "Jenkinsfile",
    ".travis.yml",
    "azure-pipelines.yml",
    "bitbucket-pipelines.yml",
]

# ---------------------------------------------------------------------------
# Database detection: DB name → import/module substrings in source files
# ---------------------------------------------------------------------------

DATABASE_PATTERNS: Dict[str, List[str]] = {
    "SQLite": ["import sqlite3", "from sqlite3", "sqlite:///", "SQLite"],
    "PostgreSQL": [
        "import psycopg2",
        "from psycopg2",
        "postgresql://",
        "postgres://",
        "asyncpg",
    ],
    "MySQL": [
        "import mysql",
        "from mysql",
        "import pymysql",
        "mysql://",
        "mysql+pymysql",
    ],
    "MongoDB": ["import pymongo", "from pymongo", "MongoClient(", "mongodb://"],
    "Redis": ["import redis", "from redis", "redis://", "aioredis"],
    "SQLAlchemy (ORM)": [
        "from sqlalchemy",
        "import sqlalchemy",
        "create_engine(",
        "sessionmaker(",
    ],
    "Elasticsearch": ["from elasticsearch", "import elasticsearch"],
    "Cassandra": ["from cassandra", "import cassandra"],
}

# ---------------------------------------------------------------------------
# Documentation files
# ---------------------------------------------------------------------------

DOC_FILE_NAMES: Dict[str, str] = {
    "README.md": "README",
    "README.rst": "README",
    "README.txt": "README",
    "README": "README",
    "LICENSE": "LICENSE",
    "LICENSE.md": "LICENSE",
    "LICENSE.txt": "LICENSE",
    "CONTRIBUTING.md": "CONTRIBUTING",
    "CONTRIBUTING.rst": "CONTRIBUTING",
    "CHANGELOG.md": "CHANGELOG",
    "CHANGELOG.rst": "CHANGELOG",
    "CODE_OF_CONDUCT.md": "Code of Conduct",
    "SECURITY.md": "Security Policy",
    "ARCHITECTURE.md": "Architecture",
    "DESIGN.md": "Design Document",
    "API.md": "API Documentation",
}

# ---------------------------------------------------------------------------
# Configuration file detection
# ---------------------------------------------------------------------------

CONFIG_FILE_NAMES: Set[str] = {
    ".env",
    ".env.example",
    ".env.local",
    ".env.production",
    "config.yaml",
    "config.yml",
    "config.json",
    "config.toml",
    "settings.yaml",
    "settings.yml",
    "appsettings.json",
    "application.properties",
    "application.yml",
    ".eslintrc.json",
    ".eslintrc.js",
    ".prettierrc",
    ".babelrc",
    "tsconfig.json",
    "jest.config.js",
    "jest.config.ts",
    "webpack.config.js",
    "vite.config.ts",
    "vite.config.js",
    "next.config.js",
    "next.config.mjs",
    "nuxt.config.ts",
    "pyproject.toml",
    "setup.cfg",
    "setup.py",
    "tox.ini",
    "mypy.ini",
    ".flake8",
    "pytest.ini",
}

# ---------------------------------------------------------------------------
# Source file extensions for line-counting and deep analysis
# ---------------------------------------------------------------------------

SOURCE_FILE_EXTENSIONS: FrozenSet[str] = frozenset(
    {
        ".py", ".pyw", ".pyi",
        ".js", ".jsx", ".mjs", ".cjs",
        ".ts", ".tsx",
        ".java", ".kt", ".kts", ".scala",
        ".go",
        ".c", ".h", ".cpp", ".cxx", ".cc", ".hpp",
        ".cs",
        ".rs",
        ".rb",
        ".php",
        ".swift",
        ".dart",
        ".ex", ".exs",
        ".erl", ".hrl",
        ".hs",
        ".clj", ".cljs",
        ".r", ".R",
        ".lua",
    }
)

# Maximum number of lines to read from a file for framework/DB detection
PATTERN_SCAN_MAX_LINES: int = 150

# Parser version reported in EvidenceMetadata
PARSER_VERSION: str = "1.0"
