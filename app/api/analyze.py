from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Form,
    HTTPException
)

import os
import shutil
import time
import re
from typing import List

from app.models.project_context import ProjectContext
from app.models.response_models import AnalyzeSubmissionResponse

from app.services.zip_service import ZipService
from app.services.scanner_service import ScannerService
from app.services.lightweight_ranking_service import LightweightRankingService
from app.services.loader_service import LoaderService
from app.services.deep_ranking_service import DeepRankingService
from app.services.context_builder_service import ContextBuilderService
from app.services.llm_service import GeminiService


router = APIRouter(
    prefix="",
    tags=["Project Analysis"]
)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# -----------------------
# Initialize services
# -----------------------
zip_service = ZipService()
scanner_service = ScannerService()
ranking_service = LightweightRankingService()
loader_service = LoaderService()
deep_ranking_service = DeepRankingService()
context_builder_service = ContextBuilderService()
gemini_service = GeminiService()


def parse_project_outcomes(project_outcomes: str | List[str]) -> List[str]:
    raw_values = project_outcomes if isinstance(project_outcomes, list) else [project_outcomes]
    parsed_outcomes = []

    for raw_value in raw_values:
        for line in re.split(r'\r?\n', raw_value or ""):
            line = line.strip()
            if not line:
                continue
            # Strip leading bullets like "* ", "- ", or numbering like "1. "
            line = re.sub(r'^(?:\d+\.|\*|-)\s*', '', line).strip()
            # Also support comma/semicolon separated outcomes, e.g. React,Next.js,MySQL.
            for outcome in re.split(r'\s*[,;]\s*', line):
                outcome = outcome.strip()
                if outcome:
                    parsed_outcomes.append(outcome)

    return parsed_outcomes


def parse_project_description_claims(project_description: str) -> List[str]:
    description = (project_description or "").lower()
    claims = []

    if any(term in description for term in ["auth", "authentication", "athentication", "login", "jwt", "session"]):
        claims.append("Authentication")

    if any(term in description for term in ["postgres", "postgrease", "postgresql"]):
        claims.append("PostgreSQL")
    elif "mysql" in description:
        claims.append("MySQL")
    elif any(term in description for term in ["own database", "database", "sql"]):
        claims.append("Database")

    if any(term in description for term in ["backend route", "backend routes", "routing", "route in backend", "rout in backend"]):
        claims.append("Backend Routes")

    return claims


def merge_outcomes(*outcome_groups: List[str]) -> List[str]:
    merged = []
    seen = set()
    for outcomes in outcome_groups:
        for outcome in outcomes:
            key = re.sub(r"[^a-z0-9]+", "", outcome.lower())
            if key and key not in seen:
                seen.add(key)
                merged.append(outcome)
    return merged


@router.post("/analyze-submission", response_model=AnalyzeSubmissionResponse)
async def analyze_submission(
    project_title: str = Form(...),
    project_description: str = Form(""),
    project_outcomes: List[str] = Form(...),
    questions_per_skill: int = Form(2),
    zip_file: UploadFile = File(...)
):
    start_time = time.time()

    if not zip_file.filename.lower().endswith(".zip"):
        raise HTTPException(
            status_code=400,
            detail="Only ZIP files are allowed."
        )

    # Parse outcomes into a clean list of strings.
    # Supports both a single textarea value and repeated form fields.
    parsed_outcomes = merge_outcomes(
        parse_project_outcomes(project_outcomes),
        parse_project_description_claims(project_description)
    )
    if not parsed_outcomes:
        raise ValueError("Stated outcomes must not be empty.")

    # Save uploaded ZIP
    file_path = os.path.join(
        UPLOAD_FOLDER,
        zip_file.filename
    )

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(zip_file.file, buffer)

    # Create ProjectContext
    context = ProjectContext(
        project_title=project_title,
        project_description=project_description,
        project_outcomes="\n".join(parsed_outcomes),
        questions_per_skill=questions_per_skill,
        zip_path=file_path
    )
    context.metadata["parsed_outcomes"] = parsed_outcomes

    # =================================
    # PIPELINE STAGE 1: File Processing
    # =================================
    start_extract = time.time()
    context = zip_service.process(context)
    context.metadata["extraction_time_ms"] = int((time.time() - start_extract) * 1000)

    context = scanner_service.process(context)
    context = ranking_service.process(context)
    context = loader_service.process(context)

    # =================================
    # PIPELINE STAGE 2: Deep Analysis
    # =================================
    context = deep_ranking_service.process(context)

    # =================================
    # PIPELINE STAGE 3: LLM Context
    # =================================
    context = context_builder_service.process(context)

    # =================================
    # PIPELINE STAGE 4: GEMINI AI
    # =================================
    context = gemini_service.process(context)

    # =================================
    # FINAL RESPONSE
    # =================================
    processing_time_ms = int((time.time() - start_time) * 1000)

    return {
        "project_title": context.project_title,
        "project_summary": context.metadata.get("project_summary", {}),
        "suggested_skills": context.suggested_skills,
        "evaluation_report": context.evaluation_report,
        "project_statistics": context.metadata.get("project_statistics", {}),
        "processing_time_ms": processing_time_ms
    }
