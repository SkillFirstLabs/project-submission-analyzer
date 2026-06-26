import os
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.api.analyze import parse_project_description_claims, parse_project_outcomes

client = TestClient(app)

def test_parse_project_outcomes_supports_multiple_values():
    assert parse_project_outcomes([
        "Build a REST API",
        "Implement authentication",
        "1. Deploy using Docker\n- Add tests",
        "React,Next.js,Javascript,MySql,Supabase"
    ]) == [
        "Build a REST API",
        "Implement authentication",
        "Deploy using Docker",
        "Add tests",
        "React",
        "Next.js",
        "Javascript",
        "MySql",
        "Supabase"
    ]

def test_parse_project_description_claims_extracts_expected_outcomes():
    assert parse_project_description_claims(
        "i implemented react and athentication and my own postgrease sql"
    ) == ["Authentication", "PostgreSQL"]

def test_analyze_submission_invalid_file_type():
    response = client.post(
        "/analyze-submission",
        data={
            "project_title": "Test Web Project",
            "project_description": "A sample description",
            "project_outcomes": "Build a REST API",
            "questions_per_skill": 2
        },
        files={"zip_file": ("test.txt", b"dummy content", "text/plain")}
    )
    
    assert response.status_code == 400
    assert "Only ZIP files are allowed" in response.json()["detail"]

def test_analyze_submission_empty_fields():
    zip_path = "sample_project.zip"
    assert os.path.exists(zip_path), "sample_project.zip must exist"
    
    with open(zip_path, "rb") as f:
        response = client.post(
            "/analyze-submission",
            data={
                # project_title is omitted to trigger validation error
                "project_outcomes": "Outcome 1",
                "questions_per_skill": 2
            },
            files={"zip_file": (zip_path, f, "application/zip")}
        )
    assert response.status_code == 422

def test_analyze_submission_path_traversal():
    zip_path = "path_traversal_project.zip"
    assert os.path.exists(zip_path), "path_traversal_project.zip must exist"
    
    with open(zip_path, "rb") as f:
        response = client.post(
            "/analyze-submission",
            data={
                "project_title": "Test Path Traversal",
                "project_outcomes": "Outcome 1",
                "questions_per_skill": 2
            },
            files={"zip_file": (zip_path, f, "application/zip")}
        )
        
    assert response.status_code == 400
    assert "Path traversal attempt detected" in response.json()["detail"]

def test_analyze_submission_empty_zip():
    zip_path = "empty_project.zip"
    assert os.path.exists(zip_path), "empty_project.zip must exist"
    
    with open(zip_path, "rb") as f:
        response = client.post(
            "/analyze-submission",
            data={
                "project_title": "Test Empty Zip",
                "project_outcomes": "Outcome 1",
                "questions_per_skill": 2
            },
            files={"zip_file": (zip_path, f, "application/zip")}
        )
        
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower() or "no files found" in response.json()["detail"].lower()

@patch("app.services.llm_service.os.getenv")
@patch("app.services.llm_service.httpx.Client")
def test_analyze_submission_success(mock_httpx_client_class, mock_getenv):
    def getenv_side_effect(key, default=None):
        if key == "LLM_PROVIDER":
            return "gemini"
        if key == "GEMINI_API_KEY":
            return "mock-gemini-key"
        if key == "GEMINI_MODEL":
            return "gemini-2.0-flash"
        return default
    mock_getenv.side_effect = getenv_side_effect

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "candidates": [{
            "content": {
                "parts": [{
                    "text": """
                    {
                      "suggested_skills": [
                        {
                          "skill_name": "Python",
                          "confidence": 0.95,
                          "rationale": "Uses python files main.py and api/routes/inventory.py"
                        },
                        {
                          "skill_name": "FastAPI",
                          "confidence": 0.90,
                          "rationale": "Imports FastAPI in main.py"
                        }
                      ],
                      "evaluation_report_skills": [
                        {
                          "skill_name": "Python",
                          "questions": [
                            {
                              "question_text": "What is Python list comprehension?",
                              "question_focus": "conceptual",
                              "expected_key_points": ["syntax", "expression"]
                            },
                            {
                              "question_text": "How do you define routes in main.py?",
                              "question_focus": "codebase_specific",
                              "expected_key_points": ["FastAPI", "main.py"]
                            }
                          ]
                        }
                      ],
                      "summary": {
                        "overall_alignment": "strong",
                        "alignment_score": 0.95,
                        "narrative": "The project is well aligned with outcomes.",
                        "outcome_evaluation": [
                          {
                            "stated_outcome": "Build a REST API",
                            "status": "met",
                            "evidence": "api/routes/inventory.py defines routes",
                            "gap": null
                          }
                        ],
                        "strengths": ["Clean separation of routes", "Proper use of FastAPI"],
                        "gaps": ["No unit tests", "No authentication middleware"]
                      }
                    }
                    """
                }]
            }
        }],
        "usageMetadata": {
            "promptTokenCount": 100,
            "candidatesTokenCount": 200,
            "totalTokenCount": 300
        }
    }

    mock_client = MagicMock()
    mock_client.post.return_value = mock_response
    mock_client.__enter__.return_value = mock_client
    mock_httpx_client_class.return_value = mock_client
    
    zip_path = "sample_project.zip"
    assert os.path.exists(zip_path), "sample_project.zip must exist"
    
    with open(zip_path, "rb") as f:
        response = client.post(
            "/analyze-submission",
            data={
                "project_title": "Test Successful API",
                "project_description": "A sample description",
                "project_outcomes": "Build a REST API",
                "questions_per_skill": 2
            },
            files={"zip_file": (zip_path, f, "application/zip")}
        )
            
    assert response.status_code == 200
    json_resp = response.json()
    assert json_resp["project_title"] == "Test Successful API"
    assert "project_summary" in json_resp
    assert "project_statistics" in json_resp
    assert len(json_resp["suggested_skills"]) == 2
    assert json_resp["suggested_skills"][0]["skill_name"] == "Python"
    assert "proof_examples" in json_resp["suggested_skills"][0]
    assert json_resp["evaluation_report"]["skills"][0]["skill_name"] == "Python"
    assert "proof_examples" in json_resp["evaluation_report"]["skills"][0]
    assert json_resp["evaluation_report"]["summary"]["overall_alignment"] == "strong"
    assert json_resp["processing_time_ms"] >= 0

@patch("app.services.llm_service.os.getenv")
@patch("app.services.llm_service.httpx.Client")
def test_analyze_submission_repairs_incomplete_llm_output(mock_httpx_client_class, mock_getenv):
    def getenv_side_effect(key, default=None):
        if key == "LLM_PROVIDER":
            return "gemini"
        if key == "GEMINI_API_KEY":
            return "mock-gemini-key"
        if key == "GEMINI_MODEL":
            return "gemini-2.0-flash"
        return default
    mock_getenv.side_effect = getenv_side_effect

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "candidates": [{
            "content": {
                "parts": [{
                    "text": """
                    {
                      "suggested_skills": [
                        {
                          "skill_name": "JavaScript",
                          "confidence": 1,
                          "rationale": "The project uses JavaScript in package.json."
                        },
                        {
                          "skill_name": "FastAPI",
                          "confidence": 1,
                          "rationale": "There is no evidence of FastAPI being used in the project."
                        }
                      ],
                      "evaluation_report_skills": [
                        {
                          "skill_name": "",
                          "questions": []
                        }
                      ],
                      "summary": {
                        "overall_alignment": "partial",
                        "alignment_score": 0.8,
                        "narrative": "The project is partially aligned.",
                        "outcome_evaluation": [],
                        "strengths": ["Uses JavaScript"],
                        "gaps": ["Needs more evidence"]
                      }
                    }
                    """
                }]
            }
        }],
        "usageMetadata": {
            "totalTokenCount": 300
        }
    }

    mock_client = MagicMock()
    mock_client.post.return_value = mock_response
    mock_client.__enter__.return_value = mock_client
    mock_httpx_client_class.return_value = mock_client

    zip_path = "sample_project.zip"
    assert os.path.exists(zip_path), "sample_project.zip must exist"

    with open(zip_path, "rb") as f:
        response = client.post(
            "/analyze-submission",
            data={
                "project_title": "Test Repaired API",
                "project_description": "A description",
                "project_outcomes": "Build a REST API",
                "questions_per_skill": 2
            },
            files={"zip_file": (zip_path, f, "application/zip")}
        )

    assert response.status_code == 200
    json_resp = response.json()
    skill_names = [item["skill_name"] for item in json_resp["suggested_skills"]]
    assert "JavaScript" in skill_names
    assert "FastAPI" not in skill_names
    assert json_resp["suggested_skills"][0]["proof_examples"]

    report_skills = json_resp["evaluation_report"]["skills"]
    assert report_skills
    assert all(item["skill_name"] for item in report_skills)
    assert all(len(item["questions"]) >= 2 for item in report_skills)
    assert all(
        {"conceptual", "codebase_specific"}.issubset(
            {question["question_focus"] for question in item["questions"]}
        )
        for item in report_skills
    )

    outcomes = json_resp["evaluation_report"]["summary"]["outcome_evaluation"]
    assert outcomes == [{
        "stated_outcome": "Build a REST API",
        "status": "not_verifiable",
        "evidence": None,
        "gap": "No code evidence was found for this stated outcome in the analyzed files."
    }]

@patch("app.services.llm_service.os.getenv")
@patch("app.services.llm_service.httpx.Client")
def test_analyze_submission_infers_outcome_from_detected_skill(mock_httpx_client_class, mock_getenv):
    def getenv_side_effect(key, default=None):
        if key == "LLM_PROVIDER":
            return "gemini"
        if key == "GEMINI_API_KEY":
            return "mock-gemini-key"
        if key == "GEMINI_MODEL":
            return "gemini-2.0-flash"
        return default
    mock_getenv.side_effect = getenv_side_effect

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "candidates": [{
            "content": {
                "parts": [{
                    "text": """
                    {
                      "suggested_skills": [
                        {
                          "skill_name": "React",
                          "confidence": 0.95,
                          "rationale": "React is used in package.json and app/page.tsx.",
                          "proof_examples": [
                            "package.json includes react and react-dom",
                            "app/page.tsx contains React component code"
                          ]
                        },
                        {
                          "skill_name": "JavaScript",
                          "confidence": 0.9,
                          "rationale": "JavaScript is used in package.json.",
                          "proof_examples": [
                            "package.json defines JavaScript dependencies"
                          ]
                        },
                        {
                          "skill_name": "MySQL",
                          "confidence": 0.8,
                          "rationale": "MySQL is used for database storage.",
                          "proof_examples": [
                            "db/schema.sql contains MySQL table definitions"
                          ]
                        }
                      ],
                      "evaluation_report_skills": [
                        {
                          "skill_name": "React",
                          "questions": [
                            {
                              "question_text": "What are React components?",
                              "question_focus": "conceptual",
                              "expected_key_points": ["components"]
                            },
                            {
                              "question_text": "Where is React used in app/page.tsx?",
                              "question_focus": "codebase_specific",
                              "expected_key_points": ["app/page.tsx"]
                            }
                          ]
                        }
                      ],
                      "summary": {
                        "overall_alignment": "partial",
                        "alignment_score": 0.5,
                        "narrative": "Generic response",
                        "outcome_evaluation": [],
                        "strengths": ["Uses React"],
                        "gaps": ["Needs docs"]
                      }
                    }
                    """
                }]
            }
        }],
        "usageMetadata": {
            "totalTokenCount": 300
        }
    }

    mock_client = MagicMock()
    mock_client.post.return_value = mock_response
    mock_client.__enter__.return_value = mock_client
    mock_httpx_client_class.return_value = mock_client

    zip_path = "sample_project.zip"
    assert os.path.exists(zip_path), "sample_project.zip must exist"

    with open(zip_path, "rb") as f:
        response = client.post(
            "/analyze-submission",
            data={
                "project_title": "GFG",
                "project_description": "in react i implemented rout in backend i implemented authentication and i use my own postgrease sql",
                "project_outcomes": "React,Javascript,MySql,Supabase",
                "questions_per_skill": 2
            },
            files={"zip_file": (zip_path, f, "application/zip")}
        )

    assert response.status_code == 200
    json_resp = response.json()
    assert json_resp["project_summary"]["domain"] != json_resp["project_summary"]["description"]
    outcomes = json_resp["evaluation_report"]["summary"]["outcome_evaluation"]
    assert [outcome["stated_outcome"] for outcome in outcomes] == [
        "React",
        "Javascript",
        "MySql",
        "Supabase",
        "Authentication",
        "PostgreSQL",
        "Backend Routes"
    ]
    assert outcomes[0]["status"] == "met"
    assert "package.json includes react and react-dom" in outcomes[0]["evidence"]
    assert "app/page.tsx contains React component code" in outcomes[0]["evidence"]
    assert outcomes[0]["gap"] is None
    assert outcomes[1]["status"] == "met"
    assert "JavaScript dependencies" in outcomes[1]["evidence"]
    assert outcomes[2]["status"] == "met"
    assert "MySQL table definitions" in outcomes[2]["evidence"]
    assert outcomes[3]["status"] == "not_verifiable"
    assert outcomes[4]["status"] in {"met", "not_verifiable"}
    assert outcomes[5]["status"] in {"met", "not_verifiable"}
    assert "React is met with evidence" in json_resp["evaluation_report"]["summary"]["strengths"][0]

@patch("app.services.llm_service.os.getenv")
@patch("httpx.Client")
def test_analyze_submission_openai_success(mock_httpx_client_class, mock_getenv):
    def getenv_side_effect(key, default=None):
        if key == "LLM_PROVIDER":
            return "openai"
        if key == "OPENAI_API_KEY":
            return "sk-mock-key"
        if key == "OPENAI_MODEL":
            return "gpt-4o-mini"
        return default
    mock_getenv.side_effect = getenv_side_effect
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{
            "message": {
                "content": """
                {
                  "suggested_skills": [
                    {
                      "skill_name": "Python",
                      "confidence": 0.95,
                      "rationale": "Uses Python"
                    }
                  ],
                  "evaluation_report_skills": [
                    {
                      "skill_name": "Python",
                      "questions": [
                        {
                          "question_text": "What is Python?",
                          "question_focus": "conceptual",
                          "expected_key_points": ["language"]
                        },
                        {
                          "question_text": "What is main.py?",
                          "question_focus": "codebase_specific",
                          "expected_key_points": ["file"]
                        }
                      ]
                    }
                  ],
                  "summary": {
                    "overall_alignment": "strong",
                    "alignment_score": 0.95,
                    "narrative": "Aligned",
                    "outcome_evaluation": [
                      {
                        "stated_outcome": "Build a REST API",
                        "status": "met",
                        "evidence": "api/routes/inventory.py",
                        "gap": null
                      }
                    ],
                    "strengths": ["Clean code"],
                    "gaps": ["No tests"]
                  }
                }
                """
            }
        }],
        "usage": {
            "prompt_tokens": 150,
            "completion_tokens": 250
        }
    }
    
    mock_client = MagicMock()
    mock_client.post.return_value = mock_response
    mock_client.__enter__.return_value = mock_client
    mock_httpx_client_class.return_value = mock_client
    
    zip_path = "sample_project.zip"
    assert os.path.exists(zip_path), "sample_project.zip must exist"
    
    with open(zip_path, "rb") as f:
        response = client.post(
            "/analyze-submission",
            data={
                "project_title": "Test OpenAI API",
                "project_description": "A description",
                "project_outcomes": "Build a REST API",
                "questions_per_skill": 2
            },
            files={"zip_file": (zip_path, f, "application/zip")}
        )
        
    assert response.status_code == 200
    json_resp = response.json()
    assert json_resp["project_title"] == "Test OpenAI API"
    assert json_resp["suggested_skills"][0]["skill_name"] == "Python"

@patch("app.services.llm_service.os.getenv")
@patch("httpx.Client")
def test_analyze_submission_groq_success(mock_httpx_client_class, mock_getenv):
    def getenv_side_effect(key, default=None):
        if key == "LLM_PROVIDER":
            return "groq"
        if key == "GROQ_API_KEY":
            return "gsk-mock-key"
        if key == "GROQ_MODEL":
            return "llama-3.3-70b-versatile"
        return default
    mock_getenv.side_effect = getenv_side_effect

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{
            "message": {
                "content": """
                {
                  "suggested_skills": [
                    {
                      "skill_name": "Python",
                      "confidence": 0.95,
                      "rationale": "Uses Python files"
                    }
                  ],
                  "evaluation_report_skills": [
                    {
                      "skill_name": "Python",
                      "questions": [
                        {
                          "question_text": "What is Python?",
                          "question_focus": "conceptual",
                          "expected_key_points": ["language"]
                        },
                        {
                          "question_text": "Where is Python used in main.py?",
                          "question_focus": "codebase_specific",
                          "expected_key_points": ["main.py"]
                        }
                      ]
                    }
                  ],
                  "summary": {
                    "overall_alignment": "strong",
                    "alignment_score": 0.9,
                    "narrative": "Aligned",
                    "outcome_evaluation": [
                      {
                        "stated_outcome": "Build a REST API",
                        "status": "met",
                        "evidence": "main.py",
                        "gap": null
                      }
                    ],
                    "strengths": ["Clear API structure"],
                    "gaps": ["Limited tests"]
                  }
                }
                """
            }
        }],
        "usage": {
            "prompt_tokens": 120,
            "completion_tokens": 180
        }
    }

    mock_client = MagicMock()
    mock_client.post.return_value = mock_response
    mock_client.__enter__.return_value = mock_client
    mock_httpx_client_class.return_value = mock_client

    zip_path = "sample_project.zip"
    assert os.path.exists(zip_path), "sample_project.zip must exist"

    with open(zip_path, "rb") as f:
        response = client.post(
            "/analyze-submission",
            data={
                "project_title": "Test Groq API",
                "project_description": "A description",
                "project_outcomes": "Build a REST API",
                "questions_per_skill": 2
            },
            files={"zip_file": (zip_path, f, "application/zip")}
        )

    assert response.status_code == 200
    json_resp = response.json()
    assert json_resp["project_title"] == "Test Groq API"
    assert json_resp["suggested_skills"][0]["skill_name"] == "Python"
