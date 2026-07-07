import io
import zipfile

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


# --------------------------------------------------
# HELPER: CREATE TEST PROJECT ZIP
# --------------------------------------------------

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


# --------------------------------------------------
# COMPLETE WORKFLOW TEST
# --------------------------------------------------

def test_complete_assessment_workflow():

    # --------------------------------------------------
    # STEP 1: ANALYZE PROJECT
    # --------------------------------------------------

    zip_content = create_project_zip()

    analysis_response = client.post(
        "/analyze-submission",
        data={
            "project_title":
                "Automated Test Project",

            "project_description":
                "Simple Python project for integration testing",

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

    assert analysis_response.status_code == 200

    analysis_data = analysis_response.json()

    assert (
        analysis_data["message"]
        ==
        "Submission analyzed successfully"
    )


    # --------------------------------------------------
    # STEP 2: START VIVA SESSION
    # --------------------------------------------------

    start_response = client.post(
        "/viva-session/start"
    )

    assert start_response.status_code == 200

    start_data = start_response.json()

    session_id = start_data["session_id"]

    assert session_id


    # --------------------------------------------------
    # STEP 3: STORE PROJECT ANALYSIS
    # --------------------------------------------------

    project_analysis_response = client.post(
        "/viva-session/project-analysis",
        json={
            "session_id":
                session_id,

            "project_analysis":
                analysis_data
        }
    )

    assert (
        project_analysis_response.status_code
        == 200
    )


    # --------------------------------------------------
    # STEP 4: SEND PROCTORING EVENT
    # --------------------------------------------------

    event_response = client.post(
        "/viva-session/event",
        json={
            "session_id":
                session_id,

            "event_type":
                "face_not_detected",

            "duration_ms":
                1000,

            "confidence":
                0.95
        }
    )

    assert event_response.status_code == 200


    # --------------------------------------------------
    # STEP 5: EVALUATE VIVA ANSWERS
    # --------------------------------------------------

    evaluation_response = client.post(
        "/viva-session/evaluate",
        json={
            "session_id":
                session_id,

            "answers": [
                {
                    "questionNumber":
                        1,

                    "skillName":
                        "Python",

                    "type":
                        "conceptual",

                    "question":
                        "What are the main features of Python?",

                    "answer":
                        (
                            "Python is a high-level interpreted "
                            "programming language with simple syntax "
                            "and extensive library support."
                        ),

                    "evidenceFile":
                        None
                },

                {
                    "questionNumber":
                        2,

                    "skillName":
                        "Python",

                    "type":
                        "codebase_specific",

                    "question":
                        (
                            "Explain how Python is used "
                            "in the project."
                        ),

                    "answer":
                        (
                            "Python is used to execute the main "
                            "application logic and display the "
                            "Hello World output."
                        ),

                    "evidenceFile":
                        "test_project/hello.py"
                }
            ]
        }
    )

    assert evaluation_response.status_code == 200

    evaluation_data = evaluation_response.json()

    assert (
        evaluation_data["evaluation"]["total_questions"]
        == 2
    )


    # --------------------------------------------------
    # STEP 6: END VIVA SESSION
    # --------------------------------------------------

    end_response = client.post(
        "/viva-session/end",
        json={
            "session_id":
                session_id
        }
    )

    assert end_response.status_code == 200

    end_data = end_response.json()

    assert (
        "proctoring_report"
        in end_data
    )


    # --------------------------------------------------
    # STEP 7: GENERATE FINAL ASSESSMENT
    # --------------------------------------------------

    final_response = client.post(
        "/final-assessment",
        json={
            "session_id":
                session_id
        }
    )

    assert final_response.status_code == 200

    final_data = final_response.json()

    # --------------------------------------------------
    # STEP 8: VERIFY FINAL ASSESSMENT RESPONSE
    # --------------------------------------------------
    final_assessment = final_data[
        "final_assessment"
    ]
    assert final_assessment is not None
    assert "project_score" in final_assessment
    assert "viva_score" in final_assessment
    assert "integrity_score" in final_assessment
    assert "overall_score" in final_assessment
    assert "performance_level" in final_assessment
    assert "risk_level" in final_assessment
    assert "recommendation" in final_assessment


    assert (
        final_data["session_id"]
        ==
        session_id
    )
