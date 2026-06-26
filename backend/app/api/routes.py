import json
import shutil
from pathlib import Path
from typing import List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel, Field
from app.config import settings
from app.core.extractor import SafeExtractor
from app.services.analysis_service import AnalysisService
from app.services.task_router import TaskRouter
from app.services.ai_service import AIService
from app.services.llm_service import LLMService
from app.models.response import ProjectAnalysisResponse

router = APIRouter()

@router.post("/analyze-submission", response_model=ProjectAnalysisResponse)
async def analyze_submission(
    title: str = Form(...),
    description: str = Form(...),
    outcomes: str = Form(...), # JSON serialized array of claimed outcomes
    questionsCount: int = Form(5),
    focusAreas: str = Form("[]"), # JSON serialized array of focus domains
    file: UploadFile = File(...)
):
    # 1. Parse outcomes and focus areas from form JSON strings
    try:
        outcomes_list = json.loads(outcomes)
        if not isinstance(outcomes_list, list):
            outcomes_list = [outcomes_list]
    except Exception:
        outcomes_list = [outcomes]

    try:
        focus_areas_list = json.loads(focusAreas)
    except Exception:
        focus_areas_list = []

    # Verify upload suffix is ZIP
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Only ZIP repositories are supported.")

    # Generate unique folder IDs for session isolation
    session_id = f"session_{Path(file.filename).stem}_{hash(title) % 10000}"
    temp_zip_path = settings.UPLOAD_DIR / f"{session_id}.zip"
    extract_path = settings.EXTRACT_DIR / session_id

    try:
        # 2. Write uploaded stream to temp zip file on filesystem
        with open(temp_zip_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 3. Safely extract files using Zip-Slip traversal blocker
        extracted_files = []
        try:
            extracted_files = SafeExtractor.extract_zip(temp_zip_path, extract_path)
        except ValueError as traversal_err:
            raise HTTPException(status_code=400, detail=str(traversal_err))
        except Exception as extract_err:
            # Fallback: ZIP is corrupted or empty/dummy file. 
            # Proceed with empty folder tree scanning to let text analysis run.
            print(f"ZIP Extraction skipped: {str(extract_err)}")

        # 4. Run the analysis service coordinator
        analysis_report = await AnalysisService.analyze_project(
            title=title,
            description=description,
            outcomes=outcomes_list,
            questions_count=questionsCount,
            focus_areas=focus_areas_list,
            extract_path=extract_path
        )
        return analysis_report

    except Exception as general_err:
        # Fallback debug logs
        raise HTTPException(status_code=500, detail=f"Diagnostic Pipeline Error: {str(general_err)}")

    finally:
        # 9. Clean up temporary files on server
        if temp_zip_path.exists():
            try:
                temp_zip_path.unlink()
            except Exception:
                pass
        
        # We preserve the extracted files directory to allow local debug/inspect
        # or it can be cleaned up. Let's clean it up to prevent server clutter:
        if extract_path.exists():
            try:
                shutil.rmtree(extract_path)
            except Exception:
                pass


class EvaluateAnswerRequest(BaseModel):
    question: str
    expectedPoints: List[str] = Field(default_factory=list)
    candidateAnswer: str

@router.post("/evaluate-answer")
async def evaluate_answer(request: EvaluateAnswerRequest):
    loaded_models = await AIService.get_loaded_models()
    phi_model = TaskRouter.get_model_for_task("viva_evaluation", loaded_models)
    
    if phi_model:
        try:
            evaluation = await LLMService.evaluate_viva_answer(
                model_name=phi_model,
                question=request.question,
                expected_points=request.expectedPoints,
                candidate_answer=request.candidateAnswer
            )
            return evaluation
        except Exception as err:
            raise HTTPException(status_code=500, detail=f"Viva answer evaluation failed: {str(err)}")
    else:
        # Fallback evaluation response
        return {
            "grade": "Partial",
            "points_met": [],
            "feedback": "Evaluation model fallback triggered (LM Studio offline)."
        }
