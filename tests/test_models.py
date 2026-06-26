import pytest
from pydantic import ValidationError

from app.models.evidence import Evidence


def test_valid_evidence_object():
    """Verify that a complete and valid evidence object is successfully parsed."""
    data = {
        "schema_version": "1.0",
        "project": {
            "title": "Inventory System",
            "description": "A REST API for inventories",
            "outcomes": ["Build API", "Add Auth"],
        },
        "statistics": {
            "total_files": 10,
            "source_files": 5,
            "directories": 3,
            "lines_of_code": 1200,
        },
        "languages": [
            {"name": "Python", "confidence": 1.0},
            {"name": "SQL", "confidence": 0.8},
        ],
        "frameworks": [
            {"name": "FastAPI", "evidence": ["main.py", "requirements.txt"]}
        ],
        "dependencies": [
            {"name": "fastapi", "version": "0.115.0"},
            {"name": "pydantic", "version": "2.11.0"},
        ],
        "files": [
            {"path": "app/main.py", "language": "Python", "size": 1500},
        ],
        "directories": ["app", "app/api"],
        "classes": [
            {"name": "ItemService", "file": "app/services.py"},
        ],
        "functions": [
            {"name": "get_items", "file": "app/api.py"},
        ],
        "routes": [
            {"method": "GET", "path": "/items", "file": "app/api.py"},
        ],
        "databases": [
            {"type": "SQLite", "evidence": ["database.py"]},
        ],
        "deployment": [
            {"type": "Docker", "files": ["Dockerfile"]},
        ],
        "testing": [
            {"framework": "pytest", "files": 2},
        ],
        "documentation": [
            {"type": "README", "file": "README.md"},
        ],
        "configuration": [
            {"file": "pyproject.toml"},
        ],
        "metadata": {
            "parser_version": "1.0",
            "processing_time_ms": 350,
            "generated_at": "2026-06-26T10:00:00Z",
        },
    }

    evidence = Evidence(**data)
    assert evidence.schema_version == "1.0"
    assert evidence.project.title == "Inventory System"
    assert len(evidence.languages) == 2
    assert evidence.metadata.parser_version == "1.0"


def test_invalid_evidence_missing_metadata():
    """Verify that missing metadata raises a ValidationError."""
    data = {
        "project": {
            "title": "Inventory System",
        },
    }
    with pytest.raises(ValidationError):
        Evidence(**data)
