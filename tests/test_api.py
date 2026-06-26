"""
Integration tests for the /api/v1/analyze-submission endpoint.

The test_analyze_submission_success test mocks the AIService so it doesn't
make real Gemini API calls — tests run fully offline and deterministically.
"""

import io
import zipfile
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.models.evaluation import EvaluationReportModel, SummaryModel
from app.models.skill import SkillModel
from app.models.viva import VivaQuestion
from app.services.ai_service import AIAnalysisResult

client = TestClient(app)


def create_mock_zip(files_dict: dict) -> io.BytesIO:
    """Helper: create an in-memory ZIP archive from a dict of filename → content."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for filename, content in files_dict.items():
            zf.writestr(filename, content)
    zip_buffer.seek(0)
    return zip_buffer


def _make_mock_ai_result() -> AIAnalysisResult:
    """Return a canned AIAnalysisResult to inject in place of a real Gemini call."""
    return AIAnalysisResult(
        suggested_skills=[
            SkillModel(
                skill_id="sk-py-001",
                skill_name="Python",
                confidence=0.95,
                rationale="Python is the primary language.",
            )
        ],
        evaluation_report=EvaluationReportModel(
            skills=[
                SkillModel(
                    skill_id="sk-py-001",
                    skill_name="Python",
                    confidence=0.95,
                    rationale="Python is the primary language.",
                )
            ],
            summary=SummaryModel(
                overall_alignment="strong",
                alignment_score=0.90,
                narrative="Good submission.",
                strengths=["Clean code"],
                gaps=[],
            ),
            outcome_evaluation=[],
        ),
        viva_questions=[
            VivaQuestion(
                skill_id="sk-py-001",
                skill_name="Python",
                question_type="conceptual",
                question="What is a Python generator?",
                expected_answer_hint="A function that uses yield.",
            )
        ],
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_root_endpoint():
    """Verify the root endpoint returns a minimal status response."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "message": "Project Submission AI Analyzer API",
        "status": "running",
    }


def test_analyze_submission_success():
    """
    Valid request with a real ZIP → mocked AI → 200 with correct response shape.

    The AIService is patched so no real Gemini call is made.
    This makes the test deterministic and offline-safe.
    """
    files_dict = {f"file_{i}.py": "print('hello')" for i in range(12)}
    zip_data = create_mock_zip(files_dict)

    form_data = {
        "project_title": "Test Project",
        "project_description": "A test project description",
        "project_outcomes": "Build REST API",
        "questions_per_skill": "2",
    }
    files = {"zip_file": ("project.zip", zip_data, "application/zip")}

    with patch("app.api.routes.AIService.analyze", return_value=_make_mock_ai_result()):
        response = client.post(
            "/api/v1/analyze-submission",
            data=form_data,
            files=files,
        )

    assert response.status_code == 200

    data = response.json()
    assert data["project_title"] == "Test Project"
    assert len(data["suggested_skills"]) == 1
    assert data["suggested_skills"][0]["skill_name"] == "Python"
    assert data["evaluation_report"]["summary"]["overall_alignment"] == "strong"
    assert len(data["viva_questions"]) == 1
    assert data["viva_questions"][0]["question_type"] == "conceptual"
    assert data["metadata"]["files_analyzed"] == 12


def test_analyze_submission_unsupported_archive():
    """Non-ZIP file → HTTP 415 with UNSUPPORTED_ARCHIVE error code."""
    text_data = io.BytesIO(b"some text data")

    form_data = {
        "project_title": "Test Project",
        "project_outcomes": "Outcome 1",
    }
    files = {"zip_file": ("project.txt", text_data, "text/plain")}

    response = client.post(
        "/api/v1/analyze-submission",
        data=form_data,
        files=files,
    )
    assert response.status_code == 415

    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "UNSUPPORTED_ARCHIVE"
    assert "ZIP" in data["error"]["message"]


def test_analyze_submission_validation_error_missing_zip():
    """Missing ZIP file → HTTP 422 VALIDATION_ERROR."""
    form_data = {
        "project_title": "Test Project",
        "project_outcomes": "Outcome 1",
    }

    response = client.post("/api/v1/analyze-submission", data=form_data)
    assert response.status_code == 422

    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "Field 'zip_file'" in data["error"]["message"]


def test_analyze_submission_validation_error_empty_fields():
    """Blank project title → HTTP 400 VALIDATION_ERROR."""
    zip_data = io.BytesIO(b"dummy zip data")

    form_data = {
        "project_title": "   ",  # whitespace-only
        "project_outcomes": "Outcome 1",
    }
    files = {"zip_file": ("project.zip", zip_data, "application/zip")}

    response = client.post(
        "/api/v1/analyze-submission",
        data=form_data,
        files=files,
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert "Project title cannot be empty" in response.json()["error"]["message"]
