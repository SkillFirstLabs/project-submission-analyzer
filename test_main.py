from unittest.mock import patch, AsyncMock
import io
import json
import os
import zipfile
import time
from pathlib import Path
from fastapi.testclient import TestClient
from main import app, BASE_DIR

client = TestClient(app)

def test_path_traversal_zip_rejected():
    """
    Test 1: Submit a ZIP containing path traversal paths and verify rejection.
    """
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("../evil.py", "print('evil')")
    zip_bytes = zip_buffer.getvalue()
    
    response = client.post(
        "/submit",
        data={
            "project_name": "Test Path Traversal",
            "description": "Testing path traversal"
        },
        files={"zip_file": ("traversal.zip", zip_bytes, "application/zip")}
    )
    
    # In background tasks, if error happens during extraction, the job status becomes "error"
    # Or, if validation happens before background task?
    # In main.py, submit validates if it's empty, but the extract validation happens inside process_submission background task.
    # So we get 200 from /submit, and then status becomes "error" with detail!
    assert response.status_code == 200
    job_id = response.json()["job_id"]
    
    # Poll status to ensure it caught the traversal error
    # We poll for up to 3 seconds
    status = "extracting"
    for _ in range(15):
        res = client.get(f"/status/{job_id}")
        data = res.json()
        status = data["status"]
        if status == "error":
            assert "path traversal" in data["error"].lower()
            break
        time.sleep(0.1)
    assert status == "error"


def test_save_report_writes_json_file():
    """
    Test 2: Submit a report payload and verify it is written to disk in the project folder.
    """
    payload = {
        "project_name": "Saved Report Test",
        "skills": {"python": 1},
        "file_count": 3,
        "gemini": {"evaluation": {"score": 92, "verdict": "Great"}},
        "answers": {
            "conceptual_question": "Answered",
            "coding_question": "Answered"
        }
    }

    response = client.post("/save-report", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "saved_path" in data

    saved_path = BASE_DIR / data["saved_path"]
    assert saved_path.exists()

    with open(saved_path, "r", encoding="utf-8") as fh:
        saved_data = json.load(fh)

    assert saved_data["project_name"] == "Saved Report Test"
    assert saved_data["answers"]["conceptual_question"] == "Answered"

    os.remove(saved_path)


def test_empty_zip_rejected():
    """
    Test 3: Submit an empty upload or empty zip and verify rejection.
    """
    # 0-byte upload file (caught synchronously in main.py)
    response = client.post(
        "/submit",
        data={
            "project_name": "Test Empty",
            "description": "Testing empty zip"
        },
        files={"zip_file": ("empty.zip", b"", "application/zip")}
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


@patch("services.gemini_service.analyze_project", new_callable=AsyncMock)
def test_valid_response_schema(mock_analyze):
    """
    Test 4: Submit a valid project and check status transitions and result schema.
    """
    # Mock Gemini evaluation output
    mock_analyze.return_value = {
        "description_vs_code": {
            "claims": ["Build API"],
            "found": ["main.py initializes FastAPI"],
            "mismatches": [],
            "match_score": 100
        },
        "conceptual_questions": [f"Conceptual Q{i}" for i in range(1, 6)],
        "code_questions": [f"Code Q{i}" for i in range(1, 6)],
        "evaluation": {
            "score": 90,
            "strengths": ["Clean structure"],
            "weaknesses": [],
            "verdict": "Great FastAPI codebase."
        }
    }
    
    # Create valid ZIP
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("main.py", "from fastapi import FastAPI\napp = FastAPI()")
        zip_file.writestr("requirements.txt", "fastapi\nuvicorn\n")
    zip_bytes = zip_buffer.getvalue()
    
    response = client.post(
        "/submit",
        data={
            "project_name": "FastAPI App Test",
            "description": "Building a FastAPI web application"
        },
        files={"zip_file": ("project.zip", zip_bytes, "application/zip")}
    )
    
    assert response.status_code == 200
    job_id = response.json()["job_id"]
    
    # Poll status until done
    status = "extracting"
    for _ in range(20):
        res = client.get(f"/status/{job_id}")
        status = res.json()["status"]
        if status in ["done", "error"]:
            break
        time.sleep(0.1)
        
    assert status == "done"
    
    # Retrieve result
    res_result = client.get(f"/result/{job_id}")
    assert res_result.status_code == 200
    res_data = res_result.json()
    
    assert res_data["project_name"] == "FastAPI App Test"
    assert "skills" in res_data
    assert res_data["file_count"] == 2
    
    gemini = res_data["gemini"]
    assert "description_vs_code" in gemini
    assert gemini["description_vs_code"]["match_score"] == 100
    assert len(gemini["conceptual_questions"]) == 5
    assert len(gemini["code_questions"]) == 5
    assert gemini["evaluation"]["score"] == 90
