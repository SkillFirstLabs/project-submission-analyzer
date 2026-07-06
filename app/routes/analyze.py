from fastapi import APIRouter, UploadFile, File
import shutil
import os
import zipfile

from app.services.skill_service import detect_skills
from app.services.ai_service import ask_gemini
from app.services.project_structure_service import analyze_project_structure
from app.services.readme_service import analyze_readme
from app.services.project_stats_service import analyze_project_stats
from app.services.scoring_service import calculate_project_score
from app.services.framework_service import detect_frameworks
from app.services.code_quality_service import analyze_code_quality
from app.services.pdf_service import generate_pdf_report
from app.services.database_service import save_analysis, get_all_analysis
from app.services.interview_service import generate_interview_questions
from app.data.interview_questions import latest_questions
import app.data.interview_questions as interview_data

router = APIRouter()


@router.post("/analyze-submission")
async def analyze_submission(file: UploadFile = File(...)):

    # -----------------------------
    # Upload ZIP
    # -----------------------------
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)

    zip_path = os.path.join(upload_dir, file.filename)

    with open(zip_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # -----------------------------
    # Extract ZIP
    # -----------------------------
    extract_folder = os.path.join(
        upload_dir,
        os.path.splitext(file.filename)[0]
    )

    if os.path.exists(extract_folder):
        shutil.rmtree(extract_folder)

    os.makedirs(extract_folder, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_folder)

    # -----------------------------
    # Read Project Files
    # -----------------------------
    project_text = ""

    supported_extensions = (
        ".py",
        ".java",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".html",
        ".css",
        ".cpp",
        ".c",
        ".cs",
        ".php",
        ".go",
        ".rs",
        ".md",
        ".txt"
    )

    for root, _, files in os.walk(extract_folder):

        for filename in files:

            if filename.endswith(supported_extensions):

                file_path = os.path.join(root, filename)

                try:
                    with open(
                        file_path,
                        "r",
                        encoding="utf-8",
                        errors="ignore"
                    ) as f:
                        project_text += f.read() + "\n"

                except Exception:
                    pass

    # -----------------------------
    # Analysis
    # -----------------------------
    detected_skills = detect_skills(project_text)

    detected_frameworks = detect_frameworks(extract_folder)

    structure_result = analyze_project_structure(extract_folder)

    readme_result = analyze_readme(extract_folder)

    stats_result = analyze_project_stats(extract_folder)

    code_quality = analyze_code_quality(extract_folder)

    score_result = calculate_project_score(
        structure_result,
        readme_result,
        detected_skills,
        stats_result
    )

    # -----------------------------
    # AI Analysis
    # -----------------------------
    prompt = f"""
Analyze the following software project.

Detected Frameworks:
{", ".join(detected_frameworks) if detected_frameworks else "None"}

Detected Skills:
{", ".join(skill["skill_name"] for skill in detected_skills)}

Project Content:

{project_text[:12000]}

Provide:

1. Short Project Summary
2. Strengths
3. Weaknesses
4. Suggestions
"""

    ai_feedback = ask_gemini(prompt)

    interview_questions = generate_interview_questions(
        project_text,
        detected_frameworks,
        detected_skills
    )

    interview_data.latest_questions = interview_questions

    # -----------------------------
    # Final Result
    # -----------------------------
    result = {
        "overall_score": score_result,
        "frameworks": detected_frameworks,
        "skills": detected_skills,
        "structure": structure_result,
        "readme": readme_result,
        "project_statistics": stats_result,
        "code_quality": code_quality,
        "ai_feedback": ai_feedback,
        "interview_questions": interview_questions
    }

    # -----------------------------
    # Generate PDF
    # -----------------------------
    pdf_path = os.path.join(
        extract_folder,
        "analysis_report.pdf"
    )

    generate_pdf_report(result, pdf_path)

    result["pdf_report"] = pdf_path.replace("\\", "/")

    # -----------------------------
    # Save to SQLite
    # -----------------------------
    save_analysis(
        project_name=file.filename,
        score=score_result,
        frameworks=detected_frameworks,
        skills=detected_skills
    )

    return result


# ==========================================
# Analysis History API
# ==========================================

@router.get("/analysis-history")
def analysis_history():

    history = get_all_analysis()

    result = []

    for row in history:
        result.append({
            "id": row[0],
            "project_name": row[1],
            "overall_score": row[2],
            "frameworks": row[3],
            "skills": row[4],
            "analysis_date": row[5]
        })

    return {
        "total_records": len(result),
        "history": result
    }