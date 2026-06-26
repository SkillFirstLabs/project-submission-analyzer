import sys
import zipfile
import io
import json
from fastapi.testclient import TestClient

# Ensure backend directory is in python path
from app.main import app

client = TestClient(app)

def generate_dummy_zip():
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        zip_file.writestr("model/attention.py", "import torch\nimport numpy as np\nprint('attention mechanism')\n")
        zip_file.writestr("model/optimizer.py", "import torch\n# CUDA optimization routines\n")
        zip_file.writestr("package.json", '{"dependencies": {"react": "18.2.0"}}')
        zip_file.writestr("README.md", "# Deep attention model\nThis project implements attention.")
    zip_buffer.seek(0)
    return zip_buffer.getvalue()

def run_tests():
    print("========================================")
    print("Starting AIPSA Backend Verification Tests")
    print("========================================")
    
    # 1. Test Health Check Endpoint
    print("\n[Test 1] Health check endpoint...")
    response = client.get("/")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    print("Health check response:", data)
    assert data["status"] == "healthy"
    
    # 2. Test Submission Analysis Endpoint
    print("\n[Test 2] ZIP Submission analysis endpoint...")
    zip_data = generate_dummy_zip()
    response = client.post(
        "/api/analyze-submission",
        data={
            "title": "Attention Model Project",
            "description": "Deep neural attention matrix multiplication optimization",
            "outcomes": json.dumps(["Implement custom attention layers", "Optimize tensor operations"]),
            "questionsCount": 3,
            "focusAreas": json.dumps(["PyTorch", "Performance"])
        },
        files={"file": ("project.zip", zip_data, "application/zip")}
    )
    
    if response.status_code != 200:
        print(f"Error details: {response.text}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    report = response.json()
    print("Analysis success! Summary findings:")
    print(f"- Title: {report['title']}")
    print(f"- Files Count: {report['files_count']}")
    print(f"- Languages: {report['languages']}")
    print(f"- Confidence: {report['confidence_score']}% ({report['confidence_label']})")
    print(f"- Authenticity Score: {report['authenticity']['score']}% ({report['authenticity']['classification']})")
    print(f"- Suggested Skills Count: {len(report['suggested_skills'])}")
    print(f"- Viva Questions Count: {len(report['viva_questions'])}")
    print(f"- Audit Strengths Count: {len(report['audit']['strengths'])}")
    
    # Assert fields structure
    assert report["title"] == "Attention Model Project"
    assert report["files_count"] > 0
    assert "Python" in report["languages"]
    assert len(report["viva_questions"]) == 3
    
    # 3. Test Viva Evaluation Endpoint
    print("\n[Test 3] Viva evaluation endpoint...")
    viva_req = {
        "question": "Describe the mathematical formulation of your custom attention mechanism, and why it cuts down visual latency.",
        "expectedPoints": [
            "Calculates Query, Key, and Value matrices from input visual tensors.",
            "Applies Scaled Dot-Product Attention: Softmax(QK^T / sqrt(d_k))V."
        ],
        "candidateAnswer": "It calculates Q, K, and V matrices and then calculates the dot product scaled by Softmax to yield attention weights."
    }
    
    response = client.post(
        "/api/evaluate-answer",
        json=viva_req
    )
    
    if response.status_code != 200:
        print(f"Error details: {response.text}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    eval_result = response.json()
    print("Viva Evaluation response:", eval_result)
    assert "grade" in eval_result
    assert "feedback" in eval_result
    
    print("\n========================================")
    print("All tests completed successfully!")
    print("========================================")

if __name__ == "__main__":
    try:
        run_tests()
        sys.exit(0)
    except AssertionError as e:
        print(f"\n[FAIL] Assertion failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] Unexpected error: {e}")
        sys.exit(1)
