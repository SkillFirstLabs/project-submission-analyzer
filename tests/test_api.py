import io
import zipfile
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def create_project_zip():
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(
        zip_buffer,
        "w",
        zipfile.ZIP_DEFLATED
    ) as zip_file:
        zip_file.writestr(
            "test_project/hello.py",
            'print("Hello World")'
        )
    return zip_buffer.getvalue()


def test_analyze_submission():
    zip_content = create_project_zip()
    response = client.post(
        "/analyze-submission",
        data={
            "project_title":
                "Test Python Project",
            "project_description":
                "Simple Python project",
            "project_outcomes":
                "Create a Python application",
            "questions_per_skill":
                "2"
        },
        files={
            "zip_file": (
                "test_project.zip",
                zip_content,
                "application/zip"
            )
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert (
        data["message"]
        ==
        "Submission analyzed successfully"
    )
    assert (
        data["project_title"]
        ==
        "Test Python Project"
    )
    assert (
        data["zip_analysis"]["files_analyzed"]
        == 1
    )
    assert (
        len(data["suggested_skills"])
        >= 1
    )
    assert (
        "evaluation_report"
        in data
    )
