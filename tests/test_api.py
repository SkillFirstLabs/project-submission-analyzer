import io
import zipfile
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.llm.base import BaseLLMClient, LLMResponse
from app.api import routes

class MockLLMClient(BaseLLMClient):
    def is_available(self) -> bool:
        return True

    async def generate(self, prompt: str, system_prompt: str = "") -> LLMResponse:
        # Determine if it's evaluating outcomes or generating questions
        if "STATED OUTCOMES:" in prompt:
            # Outcome evaluation prompt
            return LLMResponse(
                text="""
                {
                  "strengths": ["Excellent styling and user experience", "Clean database separation"],
                  "gaps": ["No unit tests found for routes"],
                  "summary": "The student implemented the project well but lacks tests.",
                  "outcome_evaluations": [
                    {
                      "stated_outcome": "implement fast api",
                      "is_met": true,
                      "confidence": 0.9,
                      "evidence": "main.py has FastAPI instantiation",
                      "gaps": []
                    }
                  ]
                }
                """,
                tokens_used=100,
                provider="mock"
            )
        else:
            # Question generation prompt
            return LLMResponse(
                text="""
                [
                  {
                    "question_text": "How does dependency injection work in FastAPI?",
                    "question_focus": "conceptual",
                    "expected_key_points": ["Depends class", "Depends parameter injection"]
                  }
                ]
                """,
                tokens_used=50,
                provider="mock"
            )

@pytest.fixture
def mock_llm(monkeypatch):
    mock_client = MockLLMClient()
    monkeypatch.setattr(routes, "get_llm_client_for_provider", lambda provider: mock_client)
    return mock_client

def _make_zip(files: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return buf.getvalue()

def test_analyze_submission_with_mock_llm(mock_llm):
    client = TestClient(app)
    zip_bytes = _make_zip({
        "main.py": b"from fastapi import FastAPI\napp = FastAPI()",
        "requirements.txt": b"fastapi==0.115.0"
    })

    response = client.post(
        "/api/v1/analyze-submission",
        data={
            "project_title": "Test Title",
            "project_description": "A test FastAPI project built for testing the analyzer service.",
            "project_outcomes": "implement fast api",
            "questions_per_skill": 2,
            "llm_provider": "gemini"
        },
        files={
            "zip_file": ("project.zip", zip_bytes, "application/zip")
        }
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert "evaluation_report" in data
    eval_report = data["evaluation_report"]
    print("STRENGTHS:", eval_report["strengths"])
    print("GAPS:", eval_report["gaps"])
    assert eval_report["strengths"] == ["Excellent styling and user experience", "Clean database separation"]
    assert eval_report["gaps"] == ["No unit tests found for routes"]
