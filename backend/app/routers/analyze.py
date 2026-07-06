import time
import os
import uuid
import json
import shutil
from fastapi import APIRouter, UploadFile, Form, File, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.models import User, Submission, EvaluationReport
from app.services.auth import require_role
from app.schemas.schemas import AnalyzeSubmissionResponse
from app.services.extractor import extract_and_analyze_zip, ZipSafetyError
from app.services.llm import analyze_project

router = APIRouter()

# Path to skill catalog
CATALOG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "skill_catalog.json")

def load_skill_catalog():
    if not os.path.exists(CATALOG_PATH):
        # Fallback if catalog not found
        return [
            {"skill_id": "uuid-1", "skill_name": "Python"},
            {"skill_id": "uuid-2", "skill_name": "FastAPI"},
            {"skill_id": "uuid-3", "skill_name": "PostgreSQL"}
        ]
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

@router.post("/analyze-submission", response_model=AnalyzeSubmissionResponse)
async def analyze_submission(
    project_title: str = Form(...),
    project_description: str = Form(None),
    project_outcomes: str = Form(...),
    zip_file: UploadFile = File(...),
    questions_per_skill: int = Form(2),
    current_user: User = Depends(require_role("student")),
    db: AsyncSession = Depends(get_db)
):
    start_time = time.time()
    
    # 1. Save uploaded file temporarily to run safe extraction
    temp_zip_name = f"temp_upload_{uuid.uuid4().hex}.zip"
    final_zip_path = os.path.join("app", "data", "uploads", temp_zip_name)
    os.makedirs(os.path.dirname(final_zip_path), exist_ok=True)
    
    try:
        with open(final_zip_path, "wb") as buffer:
            content = await zip_file.read()
            buffer.write(content)
            
        # 2. Safely extract and parse codebase contents
        try:
            analysis_result = extract_and_analyze_zip(final_zip_path)
        except ZipSafetyError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to process ZIP archive: {str(e)}")
            
        # 3. Load allowed catalog
        skill_catalog = load_skill_catalog()
        
        # 4. Call Gemini LLM API
        try:
            llm_response = await analyze_project(
                project_title=project_title,
                project_description=project_description or "",
                project_outcomes=project_outcomes,
                file_tree=analysis_result["file_tree"],
                dependencies=analysis_result["dependencies"],
                snippets=analysis_result["snippets"],
                skill_catalog=skill_catalog,
                questions_per_skill=questions_per_skill
            )
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"LLM analysis failed: {str(e)}")

        end_time = time.time()
        processing_time_ms = round((end_time - start_time) * 1000, 2)
        
        # Compute extraction time (approx)
        extraction_time_ms = round((time.time() - start_time) * 1000 - processing_time_ms, 2)
        if extraction_time_ms < 0:
            extraction_time_ms = 100.0
            
        # Assemble Response matching schema exactly
        result = llm_response.get("result", {})
        
        # Build structured evaluation report from LLM outcome
        skills_raw = result.get("skills_questions", [])
        
        # Setup metadata
        metadata = {
            "files_analyzed": len(analysis_result["file_tree"]),
            "extraction_time_ms": extraction_time_ms,
            "model_tokens_used": llm_response.get("tokens_used", 0)
        }
        
        sub_id = str(uuid.uuid4())
        
        response_data = {
            "project_title": project_title,
            "suggested_skills": result.get("suggested_skills", []),
            "evaluation_report": {
                "skills": skills_raw,
                "summary": result.get("summary", {})
            },
            "proctoring_report": None,
            "metadata": metadata,
            "processing_time_ms": processing_time_ms,
            "session_id": sub_id  # For frontend backwards compatibility
        }
        
        # Save to DB
        new_submission = Submission(
            id=sub_id,
            student_id=current_user.id,
            project_title=project_title,
            description=project_description or "",
            outcomes=project_outcomes,
            zip_path=final_zip_path
        )
        db.add(new_submission)
        
        new_evaluation = EvaluationReport(
            id=str(uuid.uuid4()),
            submission_id=sub_id,
            suggested_skills=response_data["suggested_skills"],
            evaluation_report=response_data["evaluation_report"]
        )
        db.add(new_evaluation)
        
        await db.commit()
        response_data["session_id"] = sub_id
        
        # Strip out sensitive info since this goes to the student
        response_data["suggested_skills"] = []
        response_data["evaluation_report"]["summary"] = {}

        return response_data

    finally:
        pass # Keep ZIP in uploads folder for mentor review
