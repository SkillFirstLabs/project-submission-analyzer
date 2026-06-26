"""
Test suite for Milestone 6: Project Scanner (Static Analysis Engine).

Tests cover all five sub-parsers individually and the ProjectScanner orchestrator
via an integration test using a fully synthetic project directory.
"""

import ast
import json
import os
import shutil
import zipfile
from pathlib import Path
from textwrap import dedent

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_workspace(tmp_path: Path, structure: dict) -> Path:
    """
    Create a synthetic project workspace from a dict structure.

    Keys are relative paths; values are file contents (str).
    If the value is None, the path is treated as an empty directory.
    """
    for rel_path, content in structure.items():
        full = tmp_path / rel_path
        if content is None:
            full.mkdir(parents=True, exist_ok=True)
        else:
            full.parent.mkdir(parents=True, exist_ok=True)
            full.write_text(content, encoding="utf-8")
    return tmp_path


# ===========================================================================
# LanguageParser
# ===========================================================================


class TestLanguageParser:
    def test_detects_python_files(self, tmp_path):
        from app.scanner.parsers.language_parser import LanguageParser

        make_workspace(
            tmp_path,
            {
                "main.py": "print('hello')",
                "utils.py": "def helper(): pass",
                "README.md": "# Readme",
            },
        )
        parser = LanguageParser()
        stats, files, dirs, languages = parser.parse(tmp_path)

        assert stats.total_files == 3
        assert stats.source_files == 2  # only .py files
        assert any(lang.name == "Python" for lang in languages)

    def test_detects_multiple_languages(self, tmp_path):
        from app.scanner.parsers.language_parser import LanguageParser

        make_workspace(
            tmp_path,
            {
                "app.py": "import flask",
                "index.js": "const express = require('express')",
                "styles.css": "body { color: red; }",
            },
        )
        parser = LanguageParser()
        stats, files, dirs, languages = parser.parse(tmp_path)

        lang_names = [l.name for l in languages]
        assert "Python" in lang_names
        assert "JavaScript" in lang_names

    def test_ignores_pycache(self, tmp_path):
        from app.scanner.parsers.language_parser import LanguageParser

        make_workspace(
            tmp_path,
            {
                "main.py": "x = 1",
                "__pycache__/main.cpython-311.pyc": "bytecode",
            },
        )
        parser = LanguageParser()
        stats, files, _, _ = parser.parse(tmp_path)

        # pyc is an ignored extension, __pycache__ is an ignored directory
        # only main.py should be counted
        assert stats.total_files == 1
        file_paths = [f.path for f in files]
        assert all("__pycache__" not in p for p in file_paths)

    def test_ignores_node_modules_and_venv(self, tmp_path):
        from app.scanner.parsers.language_parser import LanguageParser

        make_workspace(
            tmp_path,
            {
                "main.py": "x = 1",
                "node_modules/express/index.js": "const app = express();",
                ".venv/bin/activate": "bash script",
                "venv/lib/site-packages/package.py": "code",
            },
        )
        parser = LanguageParser()
        stats, files, dirs, _ = parser.parse(tmp_path)

        assert stats.total_files == 1
        file_paths = [f.path for f in files]
        assert "main.py" in file_paths
        assert all("node_modules" not in p for p in file_paths)
        assert all(".venv" not in p for p in file_paths)
        assert all("venv" not in p for p in file_paths)

    def test_language_confidence_sums_to_one_for_single_language(self, tmp_path):
        from app.scanner.parsers.language_parser import LanguageParser

        make_workspace(
            tmp_path,
            {"a.py": "x = 1", "b.py": "y = 2", "c.py": "z = 3"},
        )
        parser = LanguageParser()
        _, _, _, languages = parser.parse(tmp_path)

        assert len(languages) == 1
        assert languages[0].name == "Python"
        assert languages[0].confidence == pytest.approx(1.0)

    def test_directories_are_catalogued(self, tmp_path):
        from app.scanner.parsers.language_parser import LanguageParser

        make_workspace(
            tmp_path,
            {
                "src/main.py": "x = 1",
                "src/utils.py": "y = 2",
                "tests/test_main.py": "z = 3",
            },
        )
        parser = LanguageParser()
        _, _, dirs, _ = parser.parse(tmp_path)

        assert "src" in dirs or any("src" in d for d in dirs)
        assert "tests" in dirs or any("tests" in d for d in dirs)


# ===========================================================================
# DependencyParser
# ===========================================================================


class TestDependencyParser:
    def test_requirements_txt_simple(self, tmp_path):
        from app.scanner.parsers.dependency_parser import DependencyParser

        make_workspace(
            tmp_path,
            {
                "requirements.txt": dedent(
                    """\
                    fastapi==0.100.0
                    pydantic>=2.0
                    uvicorn
                    # this is a comment
                    """
                )
            },
        )
        parser = DependencyParser()
        deps = parser.parse(tmp_path)

        names = [d.name.lower() for d in deps]
        assert "fastapi" in names
        assert "pydantic" in names
        assert "uvicorn" in names

    def test_requirements_txt_versions_parsed(self, tmp_path):
        from app.scanner.parsers.dependency_parser import DependencyParser

        make_workspace(
            tmp_path, {"requirements.txt": "requests==2.28.1\n"}
        )
        parser = DependencyParser()
        deps = parser.parse(tmp_path)

        req_dep = next((d for d in deps if d.name.lower() == "requests"), None)
        assert req_dep is not None
        assert req_dep.version == "2.28.1"

    def test_package_json(self, tmp_path):
        from app.scanner.parsers.dependency_parser import DependencyParser

        payload = {
            "name": "my-app",
            "dependencies": {"express": "^4.18.0", "axios": "1.0.0"},
            "devDependencies": {"jest": "^29.0.0"},
        }
        make_workspace(tmp_path, {"package.json": json.dumps(payload)})
        parser = DependencyParser()
        deps = parser.parse(tmp_path)

        names = [d.name.lower() for d in deps]
        assert "express" in names
        assert "axios" in names
        assert "jest" in names

    def test_go_mod(self, tmp_path):
        from app.scanner.parsers.dependency_parser import DependencyParser

        make_workspace(
            tmp_path,
            {
                "go.mod": dedent(
                    """\
                    module example.com/myapp

                    go 1.21

                    require (
                        github.com/gin-gonic/gin v1.9.1
                        github.com/stretchr/testify v1.8.0
                    )
                    """
                )
            },
        )
        parser = DependencyParser()
        deps = parser.parse(tmp_path)

        names = [d.name for d in deps]
        assert "github.com/gin-gonic/gin" in names

    def test_deduplication(self, tmp_path):
        from app.scanner.parsers.dependency_parser import DependencyParser

        make_workspace(
            tmp_path,
            {
                "requirements.txt": "requests==2.28.1\n",
                "requirements-dev.txt": "requests>=2.0\n",
            },
        )
        parser = DependencyParser()
        deps = parser.parse(tmp_path)

        req_count = sum(1 for d in deps if d.name.lower() == "requests")
        assert req_count == 1  # deduplicated

    def test_ignores_ignored_directories(self, tmp_path):
        from app.scanner.parsers.dependency_parser import DependencyParser

        make_workspace(
            tmp_path,
            {
                "requirements.txt": "requests==2.28.1\n",
                "node_modules/package.json": '{"dependencies": {"express": "^4.17.1"}}',
                ".venv/requirements.txt": "fastapi==0.100.0\n",
            },
        )
        parser = DependencyParser()
        deps = parser.parse(tmp_path)

        names = [d.name.lower() for d in deps]
        assert "requests" in names
        assert "express" not in names
        assert "fastapi" not in names


# ===========================================================================
# FrameworkParser
# ===========================================================================


class TestFrameworkParser:
    def _file_evidence(self, path: str, language: str = "Python"):
        from app.models.evidence import FileEvidence
        return FileEvidence(path=path, language=language, size=100)

    def test_detects_fastapi(self, tmp_path):
        from app.scanner.parsers.framework_parser import FrameworkParser

        make_workspace(
            tmp_path,
            {"main.py": "from fastapi import FastAPI\napp = FastAPI()\n"},
        )
        fe = self._file_evidence("main.py")
        parser = FrameworkParser()
        frameworks = parser.parse(tmp_path, [fe])

        names = [f.name for f in frameworks]
        assert "FastAPI" in names

    def test_detects_flask(self, tmp_path):
        from app.scanner.parsers.framework_parser import FrameworkParser

        make_workspace(
            tmp_path,
            {"app.py": "from flask import Flask\napp = Flask(__name__)\n"},
        )
        fe = self._file_evidence("app.py")
        parser = FrameworkParser()
        frameworks = parser.parse(tmp_path, [fe])

        names = [f.name for f in frameworks]
        assert "Flask" in names

    def test_detects_react(self, tmp_path):
        from app.scanner.parsers.framework_parser import FrameworkParser

        make_workspace(
            tmp_path,
            {"App.jsx": "import React from 'react';\nexport default function App() {}"},
        )
        fe = self._file_evidence("App.jsx", "JavaScript")
        parser = FrameworkParser()
        frameworks = parser.parse(tmp_path, [fe])

        names = [f.name for f in frameworks]
        assert "React" in names

    def test_framework_evidence_includes_file_path(self, tmp_path):
        from app.scanner.parsers.framework_parser import FrameworkParser

        make_workspace(
            tmp_path,
            {"src/main.py": "from fastapi import FastAPI\n"},
        )
        fe = self._file_evidence("src/main.py")
        parser = FrameworkParser()
        frameworks = parser.parse(tmp_path, [fe])

        fastapi_fw = next((f for f in frameworks if f.name == "FastAPI"), None)
        assert fastapi_fw is not None
        assert "src/main.py" in fastapi_fw.evidence

    def test_no_false_positive_for_empty_file(self, tmp_path):
        from app.scanner.parsers.framework_parser import FrameworkParser

        make_workspace(tmp_path, {"empty.py": ""})
        fe = self._file_evidence("empty.py")
        parser = FrameworkParser()
        frameworks = parser.parse(tmp_path, [fe])

        assert len(frameworks) == 0


# ===========================================================================
# CodeParser
# ===========================================================================


class TestCodeParser:
    def _file_evidence(self, path: str):
        from app.models.evidence import FileEvidence
        return FileEvidence(path=path, language="Python", size=200)

    def test_extracts_classes(self, tmp_path):
        from app.scanner.parsers.code_parser import CodeParser

        make_workspace(
            tmp_path,
            {
                "models.py": dedent(
                    """\
                    class User:
                        pass

                    class Product:
                        pass
                    """
                )
            },
        )
        fe = self._file_evidence("models.py")
        parser = CodeParser()
        classes, functions, routes = parser.parse(tmp_path, [fe])

        class_names = [c.name for c in classes]
        assert "User" in class_names
        assert "Product" in class_names

    def test_extracts_functions(self, tmp_path):
        from app.scanner.parsers.code_parser import CodeParser

        make_workspace(
            tmp_path,
            {
                "utils.py": dedent(
                    """\
                    def calculate_total(items):
                        return sum(items)

                    async def fetch_data(url):
                        pass
                    """
                )
            },
        )
        fe = self._file_evidence("utils.py")
        parser = CodeParser()
        classes, functions, routes = parser.parse(tmp_path, [fe])

        func_names = [f.name for f in functions]
        assert "calculate_total" in func_names
        assert "fetch_data" in func_names

    def test_extracts_fastapi_routes(self, tmp_path):
        from app.scanner.parsers.code_parser import CodeParser

        make_workspace(
            tmp_path,
            {
                "routes.py": dedent(
                    """\
                    from fastapi import APIRouter
                    router = APIRouter()

                    @router.get("/users")
                    async def get_users():
                        return []

                    @router.post("/users")
                    async def create_user():
                        pass

                    @router.delete("/users/{id}")
                    async def delete_user(id: int):
                        pass
                    """
                )
            },
        )
        fe = self._file_evidence("routes.py")
        parser = CodeParser()
        classes, functions, routes = parser.parse(tmp_path, [fe])

        route_pairs = [(r.method, r.path) for r in routes]
        assert ("GET", "/users") in route_pairs
        assert ("POST", "/users") in route_pairs
        assert ("DELETE", "/users/{id}") in route_pairs

    def test_skips_files_with_syntax_errors(self, tmp_path):
        from app.scanner.parsers.code_parser import CodeParser

        make_workspace(
            tmp_path,
            {"broken.py": "def foo(\n  missing_close"},
        )
        fe = self._file_evidence("broken.py")
        parser = CodeParser()
        # Should not raise, just skip silently
        classes, functions, routes = parser.parse(tmp_path, [fe])
        assert classes == []
        assert functions == []
        assert routes == []

    def test_class_evidence_has_correct_file_path(self, tmp_path):
        from app.scanner.parsers.code_parser import CodeParser

        make_workspace(
            tmp_path,
            {"src/models.py": "class Item:\n    pass\n"},
        )
        fe = self._file_evidence("src/models.py")
        parser = CodeParser()
        classes, _, _ = parser.parse(tmp_path, [fe])

        assert classes[0].file == "src/models.py"

    def test_flask_route_decorator(self, tmp_path):
        from app.scanner.parsers.code_parser import CodeParser

        make_workspace(
            tmp_path,
            {
                "app.py": dedent(
                    """\
                    from flask import Flask
                    app = Flask(__name__)

                    @app.route("/home", methods=["GET"])
                    def home():
                        return "Hello"
                    """
                )
            },
        )
        fe = self._file_evidence("app.py")
        parser = CodeParser()
        _, _, routes = parser.parse(tmp_path, [fe])

        assert any(r.path == "/home" for r in routes)


# ===========================================================================
# InfraParser
# ===========================================================================


class TestInfraParser:
    def _file_evidence(self, path: str, language: str = "Python"):
        from app.models.evidence import FileEvidence
        return FileEvidence(path=path, language=language, size=50)

    def test_detects_pytest(self, tmp_path):
        from app.scanner.parsers.infra_parser import InfraParser

        make_workspace(
            tmp_path,
            {
                "tests/test_main.py": "def test_hello(): pass",
                "tests/test_utils.py": "def test_add(): pass",
            },
        )
        files = [
            self._file_evidence("tests/test_main.py"),
            self._file_evidence("tests/test_utils.py"),
        ]
        parser = InfraParser()
        testing, deployment, databases, docs, config = parser.parse(tmp_path, files)

        framework_names = [t.framework for t in testing]
        assert "pytest" in framework_names
        pytest_entry = next(t for t in testing if t.framework == "pytest")
        assert pytest_entry.files == 2

    def test_detects_docker(self, tmp_path):
        from app.scanner.parsers.infra_parser import InfraParser

        make_workspace(
            tmp_path,
            {"Dockerfile": "FROM python:3.11\nCOPY . /app\n"},
        )
        files = [self._file_evidence("Dockerfile", "Unknown")]
        parser = InfraParser()
        _, deployment, _, _, _ = parser.parse(tmp_path, files)

        types = [d.type for d in deployment]
        assert "Docker" in types

    def test_detects_readme(self, tmp_path):
        from app.scanner.parsers.infra_parser import InfraParser

        make_workspace(tmp_path, {"README.md": "# My Project\n"})
        files = [self._file_evidence("README.md", "Unknown")]
        parser = InfraParser()
        _, _, _, docs, _ = parser.parse(tmp_path, files)

        doc_types = [d.type for d in docs]
        assert "README" in doc_types

    def test_detects_sqlite_database(self, tmp_path):
        from app.scanner.parsers.infra_parser import InfraParser

        make_workspace(
            tmp_path,
            {"db.py": "import sqlite3\nconn = sqlite3.connect('db.sqlite3')\n"},
        )
        files = [self._file_evidence("db.py")]
        parser = InfraParser()
        _, _, databases, _, _ = parser.parse(tmp_path, files)

        db_types = [d.type for d in databases]
        assert "SQLite" in db_types

    def test_detects_env_config(self, tmp_path):
        from app.scanner.parsers.infra_parser import InfraParser

        make_workspace(tmp_path, {".env.example": "DATABASE_URL=sqlite:///db.sqlite3\n"})
        files = [self._file_evidence(".env.example", "Unknown")]
        parser = InfraParser()
        _, _, _, _, config = parser.parse(tmp_path, files)

        config_paths = [c.file for c in config]
        assert ".env.example" in config_paths


# ===========================================================================
# ProjectScanner – Integration Test
# ===========================================================================


class TestProjectScanner:
    """
    Full integration test: runs the ProjectScanner against a synthetic
    Python/FastAPI project directory and validates the Evidence output.
    """

    @pytest.fixture()
    def synthetic_project(self, tmp_path) -> Path:
        """Build a minimal but realistic synthetic FastAPI project."""
        make_workspace(
            tmp_path,
            {
                # Package files
                "requirements.txt": dedent(
                    """\
                    fastapi==0.100.0
                    uvicorn==0.23.0
                    pydantic>=2.0
                    """
                ),
                # Source files
                "main.py": dedent(
                    """\
                    from fastapi import FastAPI
                    from app.routes import router

                    app = FastAPI()
                    app.include_router(router)
                    """
                ),
                "app/__init__.py": "",
                "app/routes.py": dedent(
                    """\
                    from fastapi import APIRouter
                    router = APIRouter()

                    @router.get("/items")
                    async def list_items():
                        return []

                    @router.post("/items")
                    async def create_item():
                        pass
                    """
                ),
                "app/models.py": dedent(
                    """\
                    from pydantic import BaseModel

                    class Item(BaseModel):
                        name: str
                        price: float
                    """
                ),
                # Testing
                "tests/__init__.py": "",
                "tests/test_routes.py": dedent(
                    """\
                    def test_list_items():
                        assert True
                    """
                ),
                # Infra
                "Dockerfile": "FROM python:3.11-slim\nCOPY . /app\nCMD [\"uvicorn\", \"main:app\"]\n",
                "README.md": "# Inventory API\n\nA simple FastAPI project.\n",
                ".env.example": "DEBUG=false\nSECRET_KEY=changeme\n",
            },
        )
        return tmp_path

    def test_scan_returns_evidence_object(self, synthetic_project):
        from app.models.evidence import Evidence, ProjectInfo
        from app.scanner.project_scanner import ProjectScanner

        project_info = ProjectInfo(
            title="Inventory API",
            description="A test FastAPI project",
            outcomes=["Build REST API", "Use pydantic models"],
        )
        scanner = ProjectScanner()
        evidence = scanner.scan(synthetic_project, project_info)

        assert isinstance(evidence, Evidence)

    def test_scan_statistics(self, synthetic_project):
        from app.models.evidence import ProjectInfo
        from app.scanner.project_scanner import ProjectScanner

        project_info = ProjectInfo(title="Test", outcomes=[])
        scanner = ProjectScanner()
        evidence = scanner.scan(synthetic_project, project_info)

        assert evidence.statistics.total_files > 0
        assert evidence.statistics.source_files > 0

    def test_scan_detects_python_language(self, synthetic_project):
        from app.models.evidence import ProjectInfo
        from app.scanner.project_scanner import ProjectScanner

        project_info = ProjectInfo(title="Test", outcomes=[])
        scanner = ProjectScanner()
        evidence = scanner.scan(synthetic_project, project_info)

        lang_names = [l.name for l in evidence.languages]
        assert "Python" in lang_names

    def test_scan_detects_fastapi_framework(self, synthetic_project):
        from app.models.evidence import ProjectInfo
        from app.scanner.project_scanner import ProjectScanner

        project_info = ProjectInfo(title="Test", outcomes=[])
        scanner = ProjectScanner()
        evidence = scanner.scan(synthetic_project, project_info)

        fw_names = [f.name for f in evidence.frameworks]
        assert "FastAPI" in fw_names

    def test_scan_detects_routes(self, synthetic_project):
        from app.models.evidence import ProjectInfo
        from app.scanner.project_scanner import ProjectScanner

        project_info = ProjectInfo(title="Test", outcomes=[])
        scanner = ProjectScanner()
        evidence = scanner.scan(synthetic_project, project_info)

        route_pairs = [(r.method, r.path) for r in evidence.routes]
        assert ("GET", "/items") in route_pairs
        assert ("POST", "/items") in route_pairs

    def test_scan_detects_classes(self, synthetic_project):
        from app.models.evidence import ProjectInfo
        from app.scanner.project_scanner import ProjectScanner

        project_info = ProjectInfo(title="Test", outcomes=[])
        scanner = ProjectScanner()
        evidence = scanner.scan(synthetic_project, project_info)

        class_names = [c.name for c in evidence.classes]
        assert "Item" in class_names

    def test_scan_detects_dependencies(self, synthetic_project):
        from app.models.evidence import ProjectInfo
        from app.scanner.project_scanner import ProjectScanner

        project_info = ProjectInfo(title="Test", outcomes=[])
        scanner = ProjectScanner()
        evidence = scanner.scan(synthetic_project, project_info)

        dep_names = [d.name.lower() for d in evidence.dependencies]
        assert "fastapi" in dep_names
        assert "pydantic" in dep_names

    def test_scan_detects_testing(self, synthetic_project):
        from app.models.evidence import ProjectInfo
        from app.scanner.project_scanner import ProjectScanner

        project_info = ProjectInfo(title="Test", outcomes=[])
        scanner = ProjectScanner()
        evidence = scanner.scan(synthetic_project, project_info)

        assert len(evidence.testing) > 0
        framework_names = [t.framework for t in evidence.testing]
        assert "pytest" in framework_names

    def test_scan_detects_docker(self, synthetic_project):
        from app.models.evidence import ProjectInfo
        from app.scanner.project_scanner import ProjectScanner

        project_info = ProjectInfo(title="Test", outcomes=[])
        scanner = ProjectScanner()
        evidence = scanner.scan(synthetic_project, project_info)

        deploy_types = [d.type for d in evidence.deployment]
        assert "Docker" in deploy_types

    def test_scan_detects_readme_documentation(self, synthetic_project):
        from app.models.evidence import ProjectInfo
        from app.scanner.project_scanner import ProjectScanner

        project_info = ProjectInfo(title="Test", outcomes=[])
        scanner = ProjectScanner()
        evidence = scanner.scan(synthetic_project, project_info)

        doc_types = [d.type for d in evidence.documentation]
        assert "README" in doc_types

    def test_scan_metadata_fields_populated(self, synthetic_project):
        from app.models.evidence import ProjectInfo
        from app.scanner.project_scanner import ProjectScanner

        project_info = ProjectInfo(title="Test", outcomes=[])
        scanner = ProjectScanner()
        evidence = scanner.scan(synthetic_project, project_info)

        assert evidence.metadata.parser_version == "1.0"
        assert evidence.metadata.processing_time_ms >= 0
        assert evidence.metadata.generated_at != ""

    def test_scan_project_info_preserved(self, synthetic_project):
        from app.models.evidence import ProjectInfo
        from app.scanner.project_scanner import ProjectScanner

        project_info = ProjectInfo(
            title="Inventory API",
            description="A test project",
            outcomes=["Build API"],
        )
        scanner = ProjectScanner()
        evidence = scanner.scan(synthetic_project, project_info)

        assert evidence.project.title == "Inventory API"
        assert evidence.project.description == "A test project"
        assert "Build API" in evidence.project.outcomes

    def test_scan_raises_for_missing_workspace(self, tmp_path):
        from app.models.evidence import ProjectInfo
        from app.scanner.project_scanner import ProjectScanner

        project_info = ProjectInfo(title="Test", outcomes=[])
        scanner = ProjectScanner()
        missing_dir = tmp_path / "does_not_exist"

        with pytest.raises(RuntimeError, match="does not exist"):
            scanner.scan(missing_dir, project_info)
