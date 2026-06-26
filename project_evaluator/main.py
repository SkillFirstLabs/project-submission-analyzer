"""
Project Submission AI Analyzer — FastAPI service.

Single endpoint: POST /analyze-submission
See README.md for setup and example calls.
"""
from __future__ import annotations
import os
import tempfile
import logging

from fastapi import FastAPI, UploadFile, Form, File, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from openai import OpenAI

from orchestrator import run_pipeline, PipelineError
from utils.safe_zip import UnsafeZipError, EmptyProjectError
from schemas import AnalyzeResponse

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("project_evaluator")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
QUESTIONS_PER_SKILL_DEFAULT = int(os.getenv("QUESTIONS_PER_SKILL_DEFAULT", "2"))
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE_BYTES", "200000"))
MAX_FILES_ANALYZED = int(os.getenv("MAX_FILES_ANALYZED", "20"))
MAX_ZIP_SIZE_BYTES = int(os.getenv("MAX_ZIP_SIZE_BYTES", "20000000"))

if not OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY is not set. The API will fail on real requests until it is.")

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

app = FastAPI(
    title="Project Submission AI Analyzer",
    description="Analyzes a student project ZIP and produces a mentor-ready viva evaluation report.",
    version="1.0.0",
)


@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL}


@app.post("/analyze-submission", response_model=AnalyzeResponse)
async def analyze_submission(
    project_title: str = Form(...),
    project_outcomes: str = Form(...),
    project_description: str = Form(None),
    questions_per_skill: int = Form(QUESTIONS_PER_SKILL_DEFAULT),
    zip_file: UploadFile = File(...),
):
    if client is None:
        raise HTTPException(
            status_code=500,
            detail="Server misconfiguration: OPENAI_API_KEY is not set. Check your .env file.",
        )

    if not project_title.strip():
        raise HTTPException(status_code=400, detail="project_title cannot be empty.")
    if not project_outcomes.strip():
        raise HTTPException(status_code=400, detail="project_outcomes cannot be empty.")
    if questions_per_skill < 1 or questions_per_skill > 6:
        raise HTTPException(status_code=400, detail="questions_per_skill must be between 1 and 6.")

    if not zip_file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="zip_file must be a .zip archive.")

    # Stream upload to a temp file, enforcing a max upload size
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
            tmp_path = tmp.name
            total = 0
            while True:
                chunk = await zip_file.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_ZIP_SIZE_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail=f"ZIP file exceeds the {MAX_ZIP_SIZE_BYTES // 1_000_000} MB limit.",
                    )
                tmp.write(chunk)

        response = await run_pipeline(
            zip_path=tmp_path,
            project_title=project_title,
            project_description=project_description or "",
            project_outcomes=project_outcomes,
            questions_per_skill=questions_per_skill,
            model=MODEL,
            client=client,
            max_file_size=MAX_FILE_SIZE,
            max_total_files=MAX_FILES_ANALYZED,
        )
        return response

    except UnsafeZipError as e:
        raise HTTPException(status_code=400, detail=f"Unsafe or invalid ZIP: {e}")
    except EmptyProjectError as e:
        raise HTTPException(status_code=422, detail=f"Empty project: {e}")
    except PipelineError as e:
        raise HTTPException(status_code=502, detail=f"Analysis pipeline failed: {e}")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unhandled error in analyze_submission")
        raise HTTPException(status_code=500, detail=f"Unexpected server error: {e}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    logger.exception("Unhandled exception")
    return JSONResponse(status_code=500, content={"detail": "Internal server error."})
