import time
import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, File, Form, UploadFile, HTTPException, status
from app.models.schemas import AnalysisResponse
from app.services.zip_extractor import SafeZipExtractor
from app.services.skill_detector import SkillDetector
from app.services.question_generator import QuestionGenerator
from app.services.outcome_evaluator import OutcomeEvaluator
from app.services.report_builder import ReportBuilder

router = APIRouter()

@router.post("/analyze-submission", response_model=AnalysisResponse)
async def analyze_submission(
    project_title: str = Form(...),
    project_description: Optional[str] = Form(None),
    project_outcomes: str = Form(...),
    zip_file: UploadFile = File(...),
    questions_per_skill: int = Form(2)
):
    processing_start_time = time.perf_counter()

    # Create temporary zip storage
    temp_zip_file = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    temp_zip_path = Path(temp_zip_file.name)

    extractor = None
    try:
        # Copy the uploaded stream to the local temp file
        shutil.copyfileobj(zip_file.file, temp_zip_file)
        temp_zip_file.close()  # Close writing channel so extraction library can read it
        
        # 1. Safely extract files and audit zip integrity
        extractor = SafeZipExtractor(temp_zip_path)
        temp_dir, extracted_files, extraction_time_ms, file_tree = extractor.extract()

        # 2. Detect project catalog skills
        detector = SkillDetector()
        try:
            suggested_skills = detector.detect_skills(temp_dir, extracted_files)
        except ValueError as catalog_error:
            # Catalog errors are system configuration issues
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Catalog Configuration Error: {str(catalog_error)}"
            )

        # 3. Generate interview questions via Groq API
        generator = QuestionGenerator()
        try:
            skills_questions, gen_tokens = generator.generate_questions(
                suggested_skills=suggested_skills,
                extracted_files=extracted_files,
                temp_dir=temp_dir,
                file_tree=file_tree,
                questions_per_skill=questions_per_skill
            )
        except ValueError as api_key_error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(api_key_error)
            )

        # 4. Evaluate stated outcomes against codebase evidence
        evaluator = OutcomeEvaluator()
        try:
            outcome_evaluations, eval_tokens = evaluator.evaluate_outcomes(
                outcomes_text=project_outcomes,
                extracted_files=extracted_files,
                temp_dir=temp_dir,
                file_tree=file_tree
            )
        except ValueError as api_key_error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(api_key_error)
            )

        # 5. Build and synthesize the final report
        builder = ReportBuilder()
        try:
            response, _ = builder.build_report(
                project_title=project_title,
                project_description=project_description,
                suggested_skills=suggested_skills,
                skills_questions=skills_questions,
                outcome_evaluations=outcome_evaluations,
                files_analyzed=extractor.files_analyzed_count,
                extraction_time_ms=extraction_time_ms,
                processing_start_time=processing_start_time,
                tokens_accumulated=gen_tokens + eval_tokens
            )
        except ValueError as api_key_error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(api_key_error)
            )

        return response

    except ValueError as ve:
        # Catch expected client validations (invalid zip, path traversal, zip bombs)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except HTTPException as he:
        # Re-raise HTTP exceptions
        raise he
    except Exception as e:
        # Internal server errors
        err_msg = str(e)
        # Check for authentication errors from Groq
        if "api_key" in err_msg.lower() or "authentication" in err_msg.lower() or "unauthorized" in err_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Groq API authentication failure: {err_msg}"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during submission analysis: {err_msg}"
        )
    finally:
        # Guarantee cleanup of temporary uploaded zip
        if temp_zip_path.exists():
            try:
                os.unlink(temp_zip_path)
            except Exception:
                pass
        # Guarantee cleanup of extracted directory contents
        if extractor:
            extractor.cleanup()
