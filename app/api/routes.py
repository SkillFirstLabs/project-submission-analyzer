# Upload endpoint
import shutil
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException

from app.services.zip_service import extract_zip
from app.services.project_analyzer import analyze_project
from app.services.llm_analyzer import analyze_with_llm
from app.services.report_builder import build_report

router = APIRouter()

UPLOAD_DIR = Path("temp/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/analyze")
async def analyze_submission(
    file: UploadFile = File(...)
):
    if not file.filename.endswith(".zip"):
        raise HTTPException(
            status_code=400,
            detail="Only ZIP files are allowed."
        )

    zip_path = UPLOAD_DIR / file.filename

    with open(zip_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    project_path = extract_zip(zip_path)

    project_data = analyze_project(project_path)

    llm_result = analyze_with_llm(project_data)

    report = build_report(
        project_data,
        llm_result
    )

    return report