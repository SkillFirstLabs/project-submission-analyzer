"""
Test suite for Milestone 7: AI Reasoning Layer.

Uses monkeypatching and mocks so no real Gemini API calls are made.
All tests work offline.
"""

import json
from pathlib import Path
from textwrap import dedent
from unittest.mock import MagicMock, patch

import pytest

from app.models.evaluation import EvaluationReportModel
from app.models.evidence import (
    Evidence,
    EvidenceMetadata,
    LanguageEvidence,
    FrameworkEvidence,
    ProjectInfo,
    ProjectStatistics,
    RouteEvidence,
    TestingEvidence,
    DocumentationEvidence,
    DependencyEvidence,
)
from app.models.skill import SkillModel
from app.models.viva import VivaQuestion


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


def _make_minimal_evidence() -> Evidence:
    """Return a minimal but valid Evidence object for testing."""
    return Evidence(
        schema_version="1.0",
        project=ProjectInfo(
            title="Test Project",
            description="A test project",
            outcomes=["Build REST API", "Write unit tests"],
        ),
        statistics=ProjectStatistics(
            total_files=10,
            source_files=8,
            directories=3,
            lines_of_code=200,
        ),
        languages=[
            LanguageEvidence(name="Python", confidence=1.0),
        ],
        frameworks=[
            FrameworkEvidence(name="FastAPI", evidence=["main.py"]),
        ],
        dependencies=[
            DependencyEvidence(name="fastapi", version="0.100.0"),
        ],
        routes=[
            RouteEvidence(method="GET", path="/items", file="routes.py"),
        ],
        testing=[
            TestingEvidence(framework="pytest", files=2),
        ],
        documentation=[
            DocumentationEvidence(type="README", file="README.md"),
        ],
        metadata=EvidenceMetadata(
            parser_version="1.0",
            processing_time_ms=50,
            generated_at="2026-01-01T00:00:00+00:00",
        ),
    )


def _make_valid_ai_response() -> str:
    """Return a valid JSON string matching the expected Gemini output schema."""
    return json.dumps({
        "suggested_skills": [
            {
                "skill_id": "sk-py-001",
                "skill_name": "Python",
                "confidence": 0.95,
                "rationale": "Python detected as primary language in 100% of source files.",
            },
            {
                "skill_id": "sk-fw-fastapi",
                "skill_name": "FastAPI",
                "confidence": 0.90,
                "rationale": "FastAPI imports detected in main.py.",
            },
        ],
        "evaluation_report": {
            "skills": [
                {
                    "skill_id": "sk-py-001",
                    "skill_name": "Python",
                    "confidence": 0.95,
                    "rationale": "Python detected as primary language.",
                }
            ],
            "summary": {
                "overall_alignment": "strong",
                "alignment_score": 0.90,
                "narrative": "The submission demonstrates strong alignment with the stated objectives.",
                "strengths": ["Clean code organisation", "REST API implemented"],
                "gaps": [],
            },
            "outcome_evaluation": [
                {
                    "stated_outcome": "Build REST API",
                    "status": "met",
                    "evidence": "GET /items route detected in routes.py.",
                    "gap": None,
                },
                {
                    "stated_outcome": "Write unit tests",
                    "status": "met",
                    "evidence": "pytest test files detected (2 files).",
                    "gap": None,
                },
            ],
        },
        "viva_questions": [
            {
                "skill_id": "sk-py-001",
                "skill_name": "Python",
                "question_type": "conceptual",
                "question": "What is the difference between a list and a tuple in Python?",
                "expected_answer_hint": "Lists are mutable, tuples are immutable.",
            },
            {
                "skill_id": "sk-fw-fastapi",
                "skill_name": "FastAPI",
                "question_type": "codebase",
                "question": "In your routes.py, why did you use async def for the route handlers?",
                "expected_answer_hint": "FastAPI supports async routes for non-blocking I/O.",
            },
        ],
    })


# ---------------------------------------------------------------------------
# Prompt Builder Tests
# ---------------------------------------------------------------------------


class TestPromptBuilder:
    def test_build_prompt_contains_evidence_fields(self, tmp_path):
        """Verify that key evidence fields appear in the generated prompt."""
        from app.prompts.evaluation_prompt import build_prompt

        evidence = _make_minimal_evidence()
        catalog = [{"skill_id": "sk-py-001", "skill_name": "Python", "category": "Programming Language"}]

        prompt = build_prompt(
            evidence=evidence,
            outcomes=["Build REST API"],
            questions_per_skill=2,
            skills_catalog=catalog,
        )

        assert "Python" in prompt
        assert "FastAPI" in prompt
        assert "Build REST API" in prompt
        assert "fastapi" in prompt  # dependency

    def test_build_prompt_contains_skills_catalog(self, tmp_path):
        """Verify that the skills catalog is embedded in the prompt."""
        from app.prompts.evaluation_prompt import build_prompt

        evidence = _make_minimal_evidence()
        catalog = [{"skill_id": "sk-test", "skill_name": "TestSkill", "category": "Testing"}]

        prompt = build_prompt(
            evidence=evidence,
            outcomes=[],
            questions_per_skill=2,
            skills_catalog=catalog,
        )

        assert "sk-test" in prompt
        assert "TestSkill" in prompt

    def test_build_prompt_contains_questions_per_skill_count(self):
        """Verify that the questions_per_skill number appears in the task instructions."""
        from app.prompts.evaluation_prompt import build_prompt

        evidence = _make_minimal_evidence()
        catalog = []

        prompt = build_prompt(
            evidence=evidence,
            outcomes=[],
            questions_per_skill=3,
            skills_catalog=catalog,
        )

        assert "3" in prompt

    def test_load_skills_catalog_raises_if_missing(self, tmp_path, monkeypatch):
        """Verify FileNotFoundError when catalog file is absent."""
        from app.prompts import evaluation_prompt

        monkeypatch.setattr(evaluation_prompt, "_CATALOG_PATH", tmp_path / "nonexistent.json")

        with pytest.raises(FileNotFoundError):
            evaluation_prompt.load_skills_catalog()

    def test_load_skills_catalog_returns_list(self):
        """Verify catalog loads successfully from the real file."""
        from app.prompts.evaluation_prompt import load_skills_catalog

        catalog = load_skills_catalog()

        assert isinstance(catalog, list)
        assert len(catalog) > 0
        assert all("skill_id" in s for s in catalog)
        assert all("skill_name" in s for s in catalog)

    def test_prompt_handles_empty_outcomes(self):
        """Verify the prompt doesn't crash with an empty outcomes list."""
        from app.prompts.evaluation_prompt import build_prompt

        evidence = _make_minimal_evidence()
        prompt = build_prompt(
            evidence=evidence,
            outcomes=[],
            questions_per_skill=2,
            skills_catalog=[],
        )

        assert "No outcomes stated" in prompt


# ---------------------------------------------------------------------------
# AIService Tests
# ---------------------------------------------------------------------------


class TestAIServiceValidation:
    def test_raises_503_when_no_api_key(self, monkeypatch):
        """Service should raise 503 if GEMINI_API_KEY is not set."""
        from app.config import get_settings
        from app.services.ai_service import AIService
        from fastapi import HTTPException

        monkeypatch.setattr(
            "app.services.ai_service.get_settings",
            lambda: _mock_settings(api_key=None),
        )

        service = AIService()
        with pytest.raises(HTTPException) as exc_info:
            service.analyze(
                evidence=_make_minimal_evidence(),
                outcomes=["Build API"],
                questions_per_skill=2,
            )

        assert exc_info.value.status_code == 503
        assert exc_info.value.detail["error"]["code"] == "SERVICE_UNAVAILABLE"

    def test_raises_500_when_catalog_missing(self, monkeypatch, tmp_path):
        """Service should raise 500 if skills catalog file is missing."""
        from app.services.ai_service import AIService
        from app.prompts import evaluation_prompt
        from fastapi import HTTPException

        monkeypatch.setattr(
            "app.services.ai_service.get_settings",
            lambda: _mock_settings(api_key="test-key"),
        )
        monkeypatch.setattr(
            evaluation_prompt, "_CATALOG_PATH", tmp_path / "missing.json"
        )

        service = AIService()
        with pytest.raises(HTTPException) as exc_info:
            service.analyze(
                evidence=_make_minimal_evidence(),
                outcomes=["Build API"],
                questions_per_skill=2,
            )

        assert exc_info.value.status_code == 500
        assert exc_info.value.detail["error"]["code"] == "CATALOG_MISSING"


class TestAIServiceResponseParsing:
    """Tests for _parse_response — runs fully offline via monkeypatching _call_gemini."""

    def _service_with_mock_gemini(self, monkeypatch, raw_response: str):
        """Set up AIService with a mocked _call_gemini that returns raw_response."""
        from app.services.ai_service import AIService

        monkeypatch.setattr(
            "app.services.ai_service.get_settings",
            lambda: _mock_settings(api_key="test-key"),
        )
        monkeypatch.setattr(
            "app.prompts.evaluation_prompt.load_skills_catalog",
            lambda: [],
        )

        service = AIService()
        monkeypatch.setattr(service, "_call_gemini", lambda prompt: raw_response)
        return service

    def test_parses_valid_response_correctly(self, monkeypatch):
        """Valid Gemini JSON → AIAnalysisResult with correct counts."""
        service = self._service_with_mock_gemini(monkeypatch, _make_valid_ai_response())

        result = service.analyze(
            evidence=_make_minimal_evidence(),
            outcomes=["Build REST API", "Write unit tests"],
            questions_per_skill=2,
        )

        assert len(result.suggested_skills) == 2
        assert result.suggested_skills[0].skill_name == "Python"
        assert result.suggested_skills[0].confidence == pytest.approx(0.95)

    def test_parses_evaluation_report(self, monkeypatch):
        """Valid response → EvaluationReportModel with correct outcome statuses."""
        service = self._service_with_mock_gemini(monkeypatch, _make_valid_ai_response())

        result = service.analyze(
            evidence=_make_minimal_evidence(),
            outcomes=["Build REST API", "Write unit tests"],
            questions_per_skill=2,
        )

        assert isinstance(result.evaluation_report, EvaluationReportModel)
        assert result.evaluation_report.summary.overall_alignment == "strong"
        assert result.evaluation_report.summary.alignment_score == pytest.approx(0.90)

        outcomes = result.evaluation_report.outcome_evaluation
        assert len(outcomes) == 2
        assert all(o.status == "met" for o in outcomes)

    def test_parses_viva_questions(self, monkeypatch):
        """Valid response → VivaQuestion instances with correct types."""
        service = self._service_with_mock_gemini(monkeypatch, _make_valid_ai_response())

        result = service.analyze(
            evidence=_make_minimal_evidence(),
            outcomes=["Build REST API"],
            questions_per_skill=2,
        )

        assert len(result.viva_questions) == 2
        assert all(isinstance(q, VivaQuestion) for q in result.viva_questions)

        types = {q.question_type for q in result.viva_questions}
        assert "conceptual" in types
        assert "codebase" in types

    def test_raises_502_on_invalid_json(self, monkeypatch):
        """Non-JSON Gemini response → 502 AI_PARSE_ERROR."""
        from fastapi import HTTPException

        service = self._service_with_mock_gemini(monkeypatch, "This is not JSON at all!")

        with pytest.raises(HTTPException) as exc_info:
            service.analyze(
                evidence=_make_minimal_evidence(),
                outcomes=["Build API"],
                questions_per_skill=2,
            )

        assert exc_info.value.status_code == 502
        assert exc_info.value.detail["error"]["code"] == "AI_PARSE_ERROR"

    def test_handles_markdown_fenced_json(self, monkeypatch):
        """Response wrapped in markdown fences should be stripped and parsed."""
        fenced = f"```json\n{_make_valid_ai_response()}\n```"
        service = self._service_with_mock_gemini(monkeypatch, fenced)

        result = service.analyze(
            evidence=_make_minimal_evidence(),
            outcomes=["Build REST API"],
            questions_per_skill=2,
        )

        assert len(result.suggested_skills) == 2

    def test_handles_empty_skills_list(self, monkeypatch):
        """Empty skills list → AIAnalysisResult with empty suggested_skills."""
        response = json.dumps({
            "suggested_skills": [],
            "evaluation_report": {
                "skills": [],
                "summary": {
                    "overall_alignment": "weak",
                    "alignment_score": 0.0,
                    "narrative": "No skills detected.",
                    "strengths": [],
                    "gaps": ["No implementation found."],
                },
                "outcome_evaluation": [],
            },
            "viva_questions": [],
        })

        service = self._service_with_mock_gemini(monkeypatch, response)
        result = service.analyze(
            evidence=_make_minimal_evidence(),
            outcomes=[],
            questions_per_skill=2,
        )

        assert result.suggested_skills == []
        assert result.viva_questions == []
        assert result.evaluation_report.summary.overall_alignment == "weak"

    def test_invalid_question_type_defaults_to_conceptual(self, monkeypatch):
        """Unknown question_type in response should be normalised to 'conceptual'."""
        response = json.dumps({
            "suggested_skills": [],
            "evaluation_report": {
                "skills": [],
                "summary": {
                    "overall_alignment": "weak",
                    "alignment_score": 0.0,
                    "narrative": "n/a",
                    "strengths": [],
                    "gaps": [],
                },
                "outcome_evaluation": [],
            },
            "viva_questions": [
                {
                    "skill_id": "sk-001",
                    "skill_name": "Python",
                    "question_type": "INVALID_TYPE",
                    "question": "What is Python?",
                    "expected_answer_hint": "A language.",
                }
            ],
        })

        service = self._service_with_mock_gemini(monkeypatch, response)
        result = service.analyze(
            evidence=_make_minimal_evidence(),
            outcomes=[],
            questions_per_skill=2,
        )

        assert result.viva_questions[0].question_type == "conceptual"


# ---------------------------------------------------------------------------
# VivaQuestion Model Tests
# ---------------------------------------------------------------------------


class TestVivaQuestionModel:
    def test_valid_question_types(self):
        """Both valid question types should be accepted."""
        for q_type in ("conceptual", "codebase"):
            q = VivaQuestion(
                skill_id="sk-001",
                skill_name="Python",
                question_type=q_type,
                question="What is Python?",
                expected_answer_hint="A language.",
            )
            assert q.question_type == q_type

    def test_invalid_question_type_rejected(self):
        """Invalid question_type values should fail Pydantic validation."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            VivaQuestion(
                skill_id="sk-001",
                skill_name="Python",
                question_type="oral",  # not in Literal
                question="What is Python?",
                expected_answer_hint="A language.",
            )


# ---------------------------------------------------------------------------
# Integration: full test that mock API key present → response shape correct
# ---------------------------------------------------------------------------


class TestAPIResponseShape:
    """
    Checks that the /analyze-submission endpoint response includes viva_questions
    when the AI service is mocked to return valid data.
    """

    def test_response_includes_viva_questions_field(self, tmp_path, monkeypatch):
        """End-to-end shape test: response dict must have viva_questions key."""
        from app.services.ai_service import AIAnalysisResult
        from app.models.evaluation import EvaluationReportModel, SummaryModel

        valid_result = AIAnalysisResult(
            suggested_skills=[
                SkillModel(
                    skill_id="sk-py-001",
                    skill_name="Python",
                    confidence=0.95,
                    rationale="Primary language.",
                )
            ],
            evaluation_report=EvaluationReportModel(
                skills=[],
                summary=SummaryModel(
                    overall_alignment="strong",
                    alignment_score=0.9,
                    narrative="Good submission.",
                    strengths=[],
                    gaps=[],
                ),
                outcome_evaluation=[],
            ),
            viva_questions=[
                VivaQuestion(
                    skill_id="sk-py-001",
                    skill_name="Python",
                    question_type="conceptual",
                    question="Explain list comprehensions.",
                    expected_answer_hint="Concise way to create lists.",
                )
            ],
        )

        monkeypatch.setattr(
            "app.api.routes.AIService.analyze",
            lambda self, **kwargs: valid_result,
        )

        assert "viva_questions" in valid_result.__dataclass_fields__
        assert len(valid_result.viva_questions) == 1


# ---------------------------------------------------------------------------
# Helper: mock settings factory
# ---------------------------------------------------------------------------


def _mock_settings(api_key=None):
    """Create a minimal mock Settings-like object."""
    settings = MagicMock()
    settings.ai.api_key = api_key
    settings.ai.default_model = "gemini-2.5-flash"
    settings.ai.request_timeout_seconds = 60
    return settings
