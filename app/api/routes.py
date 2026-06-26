"""
API routes for the Project Submission AI Analyzer.

Processing pipeline for POST /api/v1/analyze-submission:
  1. Validate file extension (ZIP only).
  2. Create a unique temporary workspace directory.
  3. Securely extract the ZIP (Zip Slip protection, size limits).
  4. Run ProjectScanner → Evidence (deterministic static analysis).
  5. Run AIService → AIAnalysisResult (Gemini-powered reasoning).
  6. Assemble and return the structured AnalyzeSubmissionResponse.
  7. Delete the temporary workspace (guaranteed via try/finally).
"""

import re
import time

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.config import get_logger, get_settings
from app.core import constants
from app.models import AnalyzeSubmissionRequest, AnalyzeSubmissionResponse
from app.models.evidence import ProjectInfo
from app.scanner import ProjectScanner, ZipExtractor
from app.services import AIService
from app.utils.filesystem import create_temp_directory, safe_delete_directory

router = APIRouter(prefix="/api/v1")
logger = get_logger("app.api.routes")


@router.post(
    "/analyze-submission",
    response_model=AnalyzeSubmissionResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze project submission",
    description=(
        "Accepts a student project ZIP file and returns a structured evaluation report: "
        "detected skills, outcome alignment, and AI-generated viva questions."
    ),
)
async def analyze_submission(
    request: AnalyzeSubmissionRequest = Depends(AnalyzeSubmissionRequest),
    zip_file: UploadFile = File(
        ...,
        description="ZIP archive of the student project submission.",
    ),
) -> dict:
    """
    Full analysis pipeline: ZIP → Evidence → AI Evaluation → Response.
    """
    logger.info(
        "Analysis request received — project: '%s'", request.project_title
    )
    request_start = time.monotonic_ns()

    # ── Step 1: Validate archive format ──────────────────────────────────────
    filename = zip_file.filename or ""
    if not any(filename.lower().endswith(ext) for ext in constants.SUPPORTED_ARCHIVE_EXTENSIONS):
        logger.warning("Rejected unsupported file type: '%s'", filename)
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail={
                "error": {
                    "code": "UNSUPPORTED_ARCHIVE",
                    "message": "Only ZIP archives (.zip) are supported.",
                    "details": None,
                }
            },
        )

    # ── Step 2: Parse outcomes from the form field ───────────────────────────
    outcomes = [
        o.strip()
        for o in re.split(r"[\n,]", request.project_outcomes)
        if o.strip()
    ]

    # ── Step 3: Create isolated workspace ────────────────────────────────────
    workspace_dir = create_temp_directory(prefix="workspace_")

    try:
        # ── Step 4: Secure extraction ─────────────────────────────────────────
        ZipExtractor().extract_zip(zip_file, workspace_dir)

        # ── Step 5: Static analysis ───────────────────────────────────────────
        project_info = ProjectInfo(
            title=request.project_title,
            description=request.project_description,
            outcomes=outcomes,
        )

        evidence = ProjectScanner().scan(workspace_dir, project_info)

        logger.info(
            "Scanner complete — %d files, %d source files, %d languages",
            evidence.statistics.total_files,
            evidence.statistics.source_files,
            len(evidence.languages),
        )

        # ── Step 6: AI reasoning ──────────────────────────────────────────────
        ai_result = AIService().analyze(
            evidence=evidence,
            outcomes=outcomes,
            questions_per_skill=request.questions_per_skill,
        )

        # ── Step 7: Assemble response ─────────────────────────────────────────
        total_time_ms = int((time.monotonic_ns() - request_start) // 1_000_000)
        settings = get_settings()

        response = {
            "project_title": request.project_title,
            "suggested_skills": [s.model_dump() for s in ai_result.suggested_skills],
            "evaluation_report": ai_result.evaluation_report.model_dump(),
            "viva_questions": [q.model_dump() for q in ai_result.viva_questions],
            "metadata": {
                "files_analyzed": evidence.statistics.total_files,
                "source_files": evidence.statistics.source_files,
                "processing_time_ms": evidence.metadata.processing_time_ms,
                "parser_version": evidence.metadata.parser_version,
                "model": settings.ai.default_model,
            },
            "processing_time_ms": total_time_ms,
        }

        logger.info(
            "Analysis complete — '%s': %d skills, %d outcomes, %d questions, %d ms total",
            request.project_title,
            len(ai_result.suggested_skills),
            len(ai_result.evaluation_report.outcome_evaluation),
            len(ai_result.viva_questions),
            total_time_ms,
        )

        return response

    finally:
        # ── Step 8: Guaranteed workspace cleanup ──────────────────────────────
        safe_delete_directory(workspace_dir)
