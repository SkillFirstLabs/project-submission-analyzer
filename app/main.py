from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
from fastapi import FastAPI, Form, File, UploadFile, HTTPException

from app.models import (
    ProctoringEventRequest,
    EndVivaRequest,
    ProjectAnalysisStoreRequest
)
from app.models import VivaEvaluationRequest
from app.models import FinalAssessmentRequest
from app.services.viva_evaluator import evaluate_viva_answers
from app.services.final_assessment import (
    generate_final_assessment
)

from app.services.zip_analyzer import analyze_zip
from app.services.skill_analyzer import suggest_skills
from app.services.question_generator import generate_questions
from app.services.outcome_evaluator import evaluate_outcomes
from app.services.session_store import (
    create_session,
    store_project_analysis,
    store_viva_evaluation,
    store_proctoring_report,
    store_final_assessment,
    get_session
)
from app.services.proctoring import (
    create_viva_session,
    add_proctoring_event,
    end_viva_session
)
from app.database import engine, Base
from app.config import MAX_ZIP_SIZE_BYTES
from app import database_models


# --------------------------------------------------
# CREATE DATABASE TABLES
# --------------------------------------------------
Base.metadata.create_all(
    bind=engine
)

# --------------------------------------------------
# CREATE FASTAPI APPLICATION
# --------------------------------------------------

app = FastAPI(
    title="Project Submission AI Analyzer",
    description="AI-powered project analysis and proctored viva system",
    version="1.0.0"
)
app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static"
)

templates = Jinja2Templates(
    directory="app/templates"
)


# --------------------------------------------------
# HOME ENDPOINT
# --------------------------------------------------

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )

# --------------------------------------------------
# HEALTH CHECK ENDPOINT
# --------------------------------------------------

@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


# --------------------------------------------------
# ANALYZE PROJECT SUBMISSION
# --------------------------------------------------

@app.post("/analyze-submission")
async def analyze_submission(
    project_title: str = Form(...),
    project_description: str = Form(""),
    project_outcomes: str = Form(...),
    questions_per_skill: int = Form(2),
    zip_file: UploadFile = File(...)
):

    # Validate project title
    if not project_title.strip():
        raise HTTPException(
            status_code=400,
            detail="Project title cannot be empty"
        )

    # Validate project outcomes
    if not project_outcomes.strip():
        raise HTTPException(
            status_code=400,
            detail="Project outcomes cannot be empty"
        )

    # Validate ZIP filename
    if (
        not zip_file.filename
        or not zip_file.filename.lower().endswith(".zip")
    ):
        raise HTTPException(
            status_code=400,
            detail="Only ZIP files are allowed"
        )

    # Validate question count
    if questions_per_skill < 2:
        raise HTTPException(
            status_code=400,
            detail="questions_per_skill must be at least 2"
        )

    # Read uploaded ZIP
    zip_content = await zip_file.read()

    # Validate empty upload
    if not zip_content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded ZIP file is empty"
        )

    # Validate uploaded ZIP size
    if len(zip_content) > MAX_ZIP_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail="ZIP file exceeds the maximum allowed size of 10 MB"
        )

    # Analyze ZIP files
    zip_analysis = analyze_zip(
        zip_content
    )

    # Suggest project skills
    suggested_skills = suggest_skills(
        zip_analysis
    )

    # Generate viva questions
    generated_questions = generate_questions(
        suggested_skills,
        zip_analysis,
        questions_per_skill
    )

    # Evaluate project outcomes
    evaluation_summary = evaluate_outcomes(
        project_outcomes,
        zip_analysis
    )

    # Return complete analysis
    return {
        "message": "Submission analyzed successfully",

        "project_title": project_title,

        "project_description": project_description,

        "project_outcomes": project_outcomes,

        "questions_per_skill": questions_per_skill,

        "zip_filename": zip_file.filename,

        "zip_analysis": zip_analysis,

        "suggested_skills": suggested_skills,

        "evaluation_report": {
            "skills": generated_questions,
            "summary": evaluation_summary
        }
    }


# --------------------------------------------------
# START VIVA SESSION
# --------------------------------------------------

@app.post("/viva-session/start")
def start_viva_session():

    session = create_viva_session()
    session_id = session["session_id"]

    # Create matching session in central session store
    create_session(session_id)

    return {
        "message": "Viva session started successfully",
        "session_id": session_id,
        "id_check": session["id_check"],
        "started_at": session["started_at"],
        "status": session["status"]
    }


# --------------------------------------------------
# RECEIVE PROCTORING EVENT
# --------------------------------------------------

@app.post("/viva-session/event")
def receive_proctoring_event(
    event_request: ProctoringEventRequest
):

    event, error = add_proctoring_event(

        session_id=event_request.session_id,

        event_type=event_request.event_type,

        duration_ms=event_request.duration_ms,

        confidence=event_request.confidence
    )

    if error:
        raise HTTPException(
            status_code=400,
            detail=error
        )

    return {
        "message": "Proctoring event recorded successfully",

        "event": event
    }


# --------------------------------------------------
# END VIVA SESSION
# --------------------------------------------------

@app.post("/viva-session/end")
def finish_viva_session(
    end_request: EndVivaRequest
):
    session, error = end_viva_session(
        end_request.session_id
    )

    if error:
        raise HTTPException(
            status_code=400,
            detail=error
        )

    # Get generated proctoring report
    proctoring_report = session[
        "proctoring_report"
    ]

    # Store report in central session store
    store_proctoring_report(
        end_request.session_id,
        proctoring_report
    )

    return {
        "message": "Viva session ended successfully",
        "session_id": session["session_id"],
        "status": session["status"],
        "started_at": session["started_at"],
        "ended_at": session["ended_at"],
        "proctoring_report": proctoring_report
    }


# --------------------------------------------------
# EVALUATE VIVA ANSWERS
# --------------------------------------------------


@app.post("/viva-session/evaluate")
def evaluate_viva(
    request: VivaEvaluationRequest):
    # Check whether session exists
    session_data = get_session(
        request.session_id
    )
    if session_data is None:
        raise HTTPException(
            status_code=404,
            detail="Viva session not found"
        )

    # Evaluate submitted answers
    evaluation_result = evaluate_viva_answers(
        request.answers
    )

    # Store evaluation in central session store
    store_viva_evaluation(
        request.session_id,
        evaluation_result
    )
    return {
        "message": "Viva answers evaluated successfully",
        "session_id": request.session_id,
        "evaluation": evaluation_result
    }


@app.post("/viva-session/project-analysis")
def attach_project_analysis(
    request: ProjectAnalysisStoreRequest):
    session_data = get_session(
        request.session_id
    )
    if session_data is None:
        raise HTTPException(
            status_code=404,
            detail="Viva session not found"
        )
    store_project_analysis(
        request.session_id,
        request.project_analysis
    )
    return {
        "message": "Project analysis stored successfully",
        "session_id": request.session_id
    }


# --------------------------------------------------
# FINAL ASSESSMENT ENDPOINT
# --------------------------------------------------


@app.post("/final-assessment")
def create_final_assessment(request: FinalAssessmentRequest):
    # -----------------------------------------------
    # GET SESSION DATA
    # -----------------------------------------------
    session_data = get_session(
        request.session_id
    )
    if session_data is None:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )

    # -----------------------------------------------
    # GET STORED RESULTS
    # -----------------------------------------------
    project_analysis = session_data.get(
        "project_analysis"
    )
    viva_evaluation = session_data.get(
        "viva_evaluation"
    )
    proctoring_report = session_data.get(
        "proctoring_report"
    )

    # -----------------------------------------------
    # VALIDATE REQUIRED DATA
    # -----------------------------------------------
    if project_analysis is None:
        raise HTTPException(
            status_code=400,
            detail="Project analysis not found"
        )
    if viva_evaluation is None:
        raise HTTPException(
            status_code=400,
            detail="Viva evaluation not found"
        )
    if proctoring_report is None:
        raise HTTPException(
            status_code=400,
            detail="Proctoring report not found"
        )

    # -----------------------------------------------
    # EXTRACT PROJECT DATA
    # -----------------------------------------------
    project_summary = (
        project_analysis
        ["evaluation_report"]
        ["summary"]
    )
    project_score = (
        project_summary["alignment_score"]
        * 100
    )
    strengths = (
        project_summary.get(
            "strengths",
            []
        )
    )
    gaps = (
        project_summary.get(
            "gaps",
            []
        )
    )

    # -----------------------------------------------
    # EXTRACT VIVA DATA
    # -----------------------------------------------
    viva_score = viva_evaluation[
        "average_score"
    ]

    # -----------------------------------------------
    # EXTRACT PROCTORING DATA
    # -----------------------------------------------
    integrity_score = (
        proctoring_report[
            "integrity_score"
        ]
        * 100
    )
    risk_level = proctoring_report[
        "risk_level"
    ]

    # -----------------------------------------------
    # GENERATE FINAL ASSESSMENT
    # -----------------------------------------------
    result = generate_final_assessment(
        project_score=project_score,
        viva_score=viva_score,
        integrity_score=integrity_score,
        risk_level=risk_level,
        strengths=strengths,
        gaps=gaps
    )

    # -----------------------------------------------
    # STORE FINAL ASSESSMENT
    # -----------------------------------------------
    store_final_assessment(
        request.session_id,
        result
    )

    # -----------------------------------------------
    # RETURN RESULT
    # -----------------------------------------------
    return {
        "message": "Final assessment generated successfully",
        "session_id": request.session_id,
        "final_assessment": result
    }


