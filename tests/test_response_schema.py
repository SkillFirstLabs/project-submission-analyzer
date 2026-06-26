import io
import zipfile
from fastapi.testclient import TestClient
import pytest
from app.main import app
from app.models.schemas import AnalysisResponse
from app.services.question_generator import QuestionGenerator
from app.services.outcome_evaluator import OutcomeEvaluator
from app.services.report_builder import ReportBuilder
from app.models.schemas import (
    SuggestedSkill, SkillWithQuestions, EvaluationQuestion,
    OutcomeEvaluationItem, ReportSummary, EvaluationReport, ReportMetadata
)

client = TestClient(app)

@pytest.fixture
def dummy_zip():
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as z:
        z.writestr("main.py", "from fastapi import FastAPI\napp = FastAPI()")
        z.writestr("requirements.txt", "fastapi==0.100.0\n")
    zip_buffer.seek(0)
    return zip_buffer

def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert "ProjectIQ" in response.text

def test_analyze_submission_endpoint(dummy_zip, monkeypatch):
    # Mock services to prevent actual Groq API calls
    
    def mock_generate_questions(self, suggested_skills, extracted_files, temp_dir, file_tree, questions_per_skill):
        return [
            SkillWithQuestions(
                skill_id="fastapi",
                skill_name="FastAPI",
                questions=[
                    EvaluationQuestion(
                        question_text="What is dependency injection in FastAPI?",
                        question_focus="conceptual",
                        expected_key_points=["Depends", "di", "dependency injection"]
                    ),
                    EvaluationQuestion(
                        question_text="In main.py, explain why app = FastAPI() was used.",
                        question_focus="codebase_specific",
                        expected_key_points=["initialization", "instance"]
                    )
                ]
            )
        ], 100

    def mock_evaluate_outcomes(self, outcomes_text, extracted_files, temp_dir, file_tree):
        return [
            OutcomeEvaluationItem(
                stated_outcome="Build a REST API",
                status="met",
                evidence="main.py contains FastAPI application",
                gap=None
            )
        ], 150

    def mock_build_report(
        self,
        project_title,
        project_description,
        suggested_skills,
        skills_questions,
        outcome_evaluations,
        files_analyzed,
        extraction_time_ms,
        processing_start_time,
        tokens_accumulated
    ):
        summary = ReportSummary(
            overall_alignment="strong",
            alignment_score=0.9,
            narrative="Perfect score."
        )
        report = EvaluationReport(
            skills=skills_questions,
            summary=summary,
            outcome_evaluation=outcome_evaluations,
            strengths=["Mock strength"],
            gaps=["Mock gap"]
        )
        metadata = ReportMetadata(
            files_analyzed=files_analyzed,
            extraction_time_ms=extraction_time_ms,
            model_tokens_used=tokens_accumulated
        )
        response = AnalysisResponse(
            project_title=project_title,
            suggested_skills=suggested_skills,
            evaluation_report=report,
            metadata=metadata,
            processing_time_ms=500
        )
        return response, tokens_accumulated

    # Apply mocks
    monkeypatch.setattr(QuestionGenerator, "generate_questions", mock_generate_questions)
    monkeypatch.setattr(OutcomeEvaluator, "evaluate_outcomes", mock_evaluate_outcomes)
    monkeypatch.setattr(ReportBuilder, "build_report", mock_build_report)

    # Make the HTTP request
    response = client.post(
        "/analyze-submission",
        data={
            "project_title": "My Awesome Project",
            "project_description": "A web API project",
            "project_outcomes": "Build a REST API",
            "questions_per_skill": 2
        },
        files={
            "zip_file": ("project.zip", dummy_zip, "application/zip")
        }
    )

    assert response.status_code == 200
    json_data = response.json()
    
    # Validate structure using Pydantic model validation
    validated_response = AnalysisResponse.model_validate(json_data)
    
    # Assert specific responses
    assert validated_response.project_title == "My Awesome Project"
    assert len(validated_response.suggested_skills) >= 1
    assert validated_response.suggested_skills[0].skill_id == "fastapi"
    assert validated_response.suggested_skills[0].confidence >= 0.9
    
    assert len(validated_response.evaluation_report.skills) == 1
    assert validated_response.evaluation_report.skills[0].skill_id == "fastapi"
    assert len(validated_response.evaluation_report.skills[0].questions) == 2
    
    assert validated_response.evaluation_report.outcome_evaluation[0].stated_outcome == "Build a REST API"
    assert validated_response.evaluation_report.outcome_evaluation[0].status == "met"
    
    assert validated_response.metadata.files_analyzed == 2
    assert validated_response.metadata.model_tokens_used == 250
    assert validated_response.processing_time_ms > 0

def test_missing_required_fields():
    response = client.post(
        "/analyze-submission",
        data={
            # missing project_title and project_outcomes
            "project_description": "Missing fields"
        }
    )
    assert response.status_code == 422  # FastAPI validation error
