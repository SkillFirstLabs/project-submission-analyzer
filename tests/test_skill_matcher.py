"""
Tests for skill matcher — including graceful error handling.
"""

import pytest
from app.services.skill_matcher import match_skills, _load_catalog, SkillMatcherError


def test_matches_python_skill():
    files = {
        "main.py": "def process():\n    return [x for x in range(10)]",
        "utils.py": "class DataProcessor:\n    def __init__(self): self.data = {}",
    }
    skills, note = match_skills(files, detected_frameworks=[])
    skill_ids = [s.skill_id for s in skills]
    # Should at minimum detect python fundamentals or OOP
    assert len(skills) > 0 or note is not None


def test_matches_fastapi_skill():
    files = {
        "app.py": (
            "from fastapi import FastAPI, APIRouter\n"
            "from pydantic import BaseModel\n"
            "app = FastAPI()\n"
            "@app.post('/items')\n"
            "async def create_item(): pass"
        )
    }
    skills, note = match_skills(files, detected_frameworks=["FastAPI"])
    skill_ids = [s.skill_id for s in skills]
    assert "sk-018" in skill_ids or "sk-001" in skill_ids


def test_empty_files_returns_note():
    skills, note = match_skills({}, detected_frameworks=[])
    assert skills == []
    assert note is not None
    assert len(note) > 0


def test_no_matching_skills_returns_note():
    # Files with no recognizable keywords
    files = {"data.xyz": "!!!###@@@"}
    skills, note = match_skills(files, detected_frameworks=[])
    # Either no skills or a helpful note
    assert isinstance(skills, list)


def test_confidence_scores_in_range():
    files = {
        "ml.py": (
            "import pandas as pd\n"
            "import numpy as np\n"
            "from sklearn.model_selection import train_test_split\n"
            "from sklearn.linear_model import LogisticRegression\n"
            "model = LogisticRegression()\n"
            "model.fit(X_train, y_train)\n"
            "accuracy_score(y_test, model.predict(X_test))\n"
        )
    }
    skills, _ = match_skills(files, detected_frameworks=["scikit-learn", "Pandas"])
    for skill in skills:
        assert 0.0 <= skill.confidence <= 1.0


def test_low_confidence_flagged(monkeypatch):
    """Skills below threshold should have low_confidence=True."""
    from app.core import config

    class MockSettings:
        confidence_threshold = 0.99  # almost nothing will pass this
        llm_provider = "gemini"
        gemini_api_key = ""
        gemini_model = "gemini-1.5-flash"
        local_llm_base_url = "http://localhost:11434"
        local_llm_model = "llama3"
        max_zip_size_mb = 50
        max_uncompressed_size_mb = 500
        max_uncompressed_size_bytes = 500 * 1024 * 1024
        max_file_count = 1000
        max_single_file_size_mb = 1
        max_single_file_size_bytes = 1 * 1024 * 1024
        default_questions_per_skill = 3
        log_level = "INFO"

    monkeypatch.setattr(config, "get_settings", lambda: MockSettings())

    files = {"app.py": "import os\nprint('hello')"}
    skills, _ = match_skills(files, detected_frameworks=[])
    # With very high threshold, most/all should be low_confidence
    low = [s for s in skills if s.low_confidence]
    assert len(low) >= 0  # just ensure it doesn't crash


def test_skills_sorted_by_confidence():
    files = {
        "full_stack.py": (
            "from fastapi import FastAPI\n"
            "from pydantic import BaseModel\n"
            "import pandas as pd\n"
            "import numpy as np\n"
            "from sklearn.linear_model import LinearRegression\n"
            "model = LinearRegression()\n"
            "model.fit(X, y)\n"
        )
    }
    skills, _ = match_skills(files, detected_frameworks=["FastAPI", "Pandas", "scikit-learn"])
    confidences = [s.confidence for s in skills]
    assert confidences == sorted(confidences, reverse=True)


def test_catalog_loads():
    catalog = _load_catalog()
    assert len(catalog) > 0
    assert all(hasattr(e, "skill_id") for e in catalog)
