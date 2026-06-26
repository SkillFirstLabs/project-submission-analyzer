"""
API routes: POST /analyze-submission
"""

import time

from fastapi import APIRouter, File, Form, UploadFile, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Optional

from app.models.schemas import AnalysisResponse, ErrorResponse, ErrorDetail
from app.core.config import get_settings
from app.core.logging_config import get_logger
from app.services.zip_extractor import extract_zip, ZipExtractionError
from app.services.project_scanner import scan_project
from app.services.code_sanitizer import scan_project as security_scan_project
from app.services.tech_detector import detect_technologies
from app.services.context_builder import build_context
from app.services.skill_matcher import match_skills
from app.services.question_generator import generate_questions_for_skills
from app.services.outcome_evaluator import evaluate_outcomes
from app.services.report_generator import build_report
from app.llm.llm_factory import get_llm_client_for_provider
from app.models.schemas import ProjectMetadata

router = APIRouter()
logger = get_logger(__name__)


@router.post(
    "/analyze-submission",
    response_model=AnalysisResponse,
    summary="Analyze a project submission ZIP",
    description=(
        "Accepts a project ZIP file and metadata, runs static analysis, "
        "skill detection, and LLM-based evaluation, then returns a "
        "mentor-ready JSON report."
    ),
    responses={
        400: {"model": ErrorResponse, "description": "Invalid ZIP or request"},
        413: {"model": ErrorResponse, "description": "File too large"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def analyze_submission(
    project_title: str = Form(..., min_length=1, max_length=200),
    project_description: str = Form(..., min_length=10, max_length=5000),
    project_outcomes: str = Form(..., min_length=10, max_length=5000),
    questions_per_skill: int = Form(default=3, ge=1, le=10),
    llm_provider: Optional[str] = Form(default=None, description="Override LLM provider: 'gemini' or 'local'"),
    zip_file: UploadFile = File(..., description="Project ZIP archive"),
) -> AnalysisResponse:
    """Main analysis endpoint."""

    request_start = time.time()
    settings = get_settings()
    extraction_result = None

    logger.info("Analysis request received", extra={
        "project_title": project_title,
        "zip_filename": zip_file.filename,   # 'filename' is reserved by LogRecord
    })

    try:
        # ------------------------------------------------------------------
        # Step 1: Validate content type and file size
        # ------------------------------------------------------------------
        if zip_file.content_type not in (
            "application/zip",
            "application/x-zip-compressed",
            "application/octet-stream",
            "multipart/form-data",
        ):
            # Be lenient — browsers sometimes send wrong content type
            # but still validate by reading magic bytes below
            pass

        zip_bytes = await zip_file.read()

        if len(zip_bytes) == 0:
            raise HTTPException(
                status_code=400,
                detail={"code": "EMPTY_FILE", "message": "Uploaded file is empty."}
            )

        if len(zip_bytes) > settings.max_zip_size_bytes:
            raise HTTPException(
                status_code=413,
                detail={
                    "code": "FILE_TOO_LARGE",
                    "message": (
                        f"ZIP file exceeds {settings.max_zip_size_mb}MB limit. "
                        f"Received: {len(zip_bytes) / (1024*1024):.1f}MB"
                    )
                }
            )

        # ------------------------------------------------------------------
        # Step 2: Secure ZIP extraction
        # ------------------------------------------------------------------
        extraction_start = time.time()
        try:
            extraction_result = extract_zip(zip_bytes)
        except ZipExtractionError as exc:
            status = 400 if exc.code != "FILE_TOO_LARGE" else 413
            raise HTTPException(
                status_code=status,
                detail={"code": exc.code, "message": str(exc)}
            )
        extraction_time_ms = (time.time() - extraction_start) * 1000

        # ------------------------------------------------------------------
        # Step 3: Scan project files
        # ------------------------------------------------------------------
        analysis_start = time.time()
        scan_result = scan_project(extraction_result.temp_dir)

        if not scan_result.file_contents:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "NO_SOURCE_FILES",
                    "message": (
                        "No readable source files found in the ZIP. "
                        "Ensure the archive contains source code files."
                    )
                }
            )

        # ------------------------------------------------------------------
        # Step 4: Security scan (static — never executes code)
        # ------------------------------------------------------------------
        security_result = security_scan_project(scan_result.file_contents)

        if security_result.has_high_severity:
            logger.warning("High-severity security patterns detected", extra={
                "project": project_title,
                "flags": len(security_result.flags),
            })

        # ------------------------------------------------------------------
        # Step 5: Technology detection
        # ------------------------------------------------------------------
        tech_result = detect_technologies(scan_result.file_contents)

        # ------------------------------------------------------------------
        # Step 6: Build CAG context
        # ------------------------------------------------------------------
        metadata = ProjectMetadata(
            title=project_title,
            description=project_description,
            outcomes=project_outcomes,
        )
        context = build_context(
            metadata=metadata,
            tree=scan_result.tree,
            file_contents=scan_result.file_contents,
            tech=tech_result,
        )

        # ------------------------------------------------------------------
        # Step 7: Skill matching (deterministic)
        # ------------------------------------------------------------------
        matched_skills, skill_note = match_skills(
            file_contents=scan_result.file_contents,
            detected_frameworks=tech_result.frameworks,
        )

        # ------------------------------------------------------------------
        # Step 8: LLM — question generation + outcome evaluation
        # ------------------------------------------------------------------
        # Use per-request override if provided, else fall back to config
        active_provider = (llm_provider or "").strip().lower() or settings.llm_provider
        llm_client = get_llm_client_for_provider(active_provider)
        total_tokens = 0

        skills_with_questions, q_tokens = await generate_questions_for_skills(
            skills=matched_skills,
            context=context,
            llm_client=llm_client,
            questions_per_skill=questions_per_skill,
        )
        total_tokens += q_tokens

        eval_report, e_tokens = await evaluate_outcomes(
            outcomes_text=project_outcomes,
            context=context,
            file_contents=scan_result.file_contents,
            llm_client=llm_client,
        )
        total_tokens += e_tokens

        analysis_time_ms = (time.time() - analysis_start) * 1000

        # ------------------------------------------------------------------
        # Step 9: Assemble report
        # ------------------------------------------------------------------
        settings = get_settings()
        report = build_report(
            project_title=project_title,
            skills_with_questions=skills_with_questions,
            evaluation_report=eval_report,
            tech_detection=tech_result,
            security_scan=security_result,
            tree=scan_result.tree,
            extraction_time_ms=extraction_time_ms,
            analysis_time_ms=analysis_time_ms,
            total_tokens=total_tokens,
            llm_provider=active_provider,
            request_start_time=request_start,
            analysis_note=skill_note,
        )

        return report

    except HTTPException:
        raise  # Let FastAPI handle these

    except Exception as exc:
        logger.error(f"Unhandled error during analysis: {exc}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred during analysis.",
                "detail": str(exc),
            }
        )

    finally:
        # Always clean up the temp directory
        if extraction_result is not None:
            extraction_result.cleanup()
