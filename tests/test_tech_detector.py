"""
Tests for technology detector.
"""

from app.services.tech_detector import detect_technologies


def test_detects_python_from_extensions():
    files = {
        "main.py": "print('hello')",
        "utils.py": "def helper(): pass",
    }
    result = detect_technologies(files)
    assert "Python" in result.languages


def test_detects_fastapi_framework():
    files = {
        "app.py": "from fastapi import FastAPI\napp = FastAPI()"
    }
    result = detect_technologies(files)
    assert "FastAPI" in result.frameworks


def test_detects_react_framework():
    files = {
        "App.jsx": "import React from 'react'\nexport default function App() { return <div/> }"
    }
    result = detect_technologies(files)
    assert "React" in result.frameworks


def test_parses_requirements_txt():
    files = {
        "requirements.txt": "fastapi==0.100.0\npydantic>=2.0\nuvicorn[standard]\n# comment\n"
    }
    result = detect_technologies(files)
    assert "fastapi" in result.dependencies
    assert "pydantic" in result.dependencies
    assert "uvicorn[standard]" not in result.dependencies  # extra stripped


def test_parses_package_json():
    files = {
        "package.json": '{"dependencies": {"react": "^18.0.0", "axios": "^1.0.0"}, "devDependencies": {"jest": "^29.0.0"}}'
    }
    result = detect_technologies(files)
    assert "react" in result.dependencies
    assert "jest" in result.dependencies


def test_no_files_returns_empty():
    result = detect_technologies({})
    assert result.languages == []
    assert result.frameworks == []
    assert result.dependencies == []


def test_multiple_languages_detected():
    files = {
        "backend.py": "import flask",
        "frontend.js": "const x = 1",
        "styles.css": "body { margin: 0; }",
    }
    result = detect_technologies(files)
    # Python and JS should be detected; CSS may or may not depending on config
    assert "Python" in result.languages
    assert "JavaScript" in result.languages
