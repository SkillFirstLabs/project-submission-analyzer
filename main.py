from fastapi import FastAPI, UploadFile, File, Form
import os
import json

from utils.zip_handler import extract_zip, get_file_tree
from utils.skill_detector import detect_skills
from utils.question_generator import generate_questions
from utils.outcome_evaluator import evaluate_outcomes

app = FastAPI()

@app.get("/")
def home():
    return {
        "message": "Project Submission AI Analyzer API Running",
        "docs": "http://127.0.0.1:8000/docs"
    }


@app.post("/analyze-submission")
async def analyze_submission(
    project_title: str = Form(...),
    project_description: str = Form(""),
    project_outcomes: str = Form(...),
    questions_per_skill: int = Form(2),
    zip_file: UploadFile = File(...)
):
    try:
        os.makedirs("uploads", exist_ok=True)
        os.makedirs("extracted", exist_ok=True)

        zip_path = f"uploads/{zip_file.filename}"

        with open(zip_path, "wb") as f:
            f.write(await zip_file.read())

        extract_zip(zip_path, "extracted")

        files = get_file_tree("extracted")

        with open("skill_catalog.json", "r", encoding="utf-8") as f:
            catalog = json.load(f)

        skills = detect_skills(files, catalog)

        skill_report = []

        for skill in skills:
            skill_report.append({
                "skill_name": skill["skill_name"],
                "questions": generate_questions(skill["skill_name"])
            })

        outcomes = [
            x.strip()
            for x in project_outcomes.split("\n")
            if x.strip()
        ]

        return {
            "project_title": project_title,
            "suggested_skills": skills,
            "evaluation_report": {
                "skills": skill_report,
                "summary": {
                    "overall_alignment": "partial",
                    "alignment_score": 0.75,
                    "narrative":
                    "The submitted project partially supports the stated outcomes."
                },
                "outcome_evaluation":
                    evaluate_outcomes(outcomes)
            }
        }

    except Exception as e:
        return {"error": str(e)}
    
    