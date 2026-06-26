# Groq Analysis Pipeline (FIXED + PRODUCTION SAFE)

import json
import os
import re
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

from app.prompts.project_prompt import PROJECT_ANALYSIS_PROMPT
from app.prompts.skill_prompt import SKILL_MATCH_PROMPT
from app.prompts.question_prompt import QUESTION_PROMPT


# -----------------------------
# ENV LOAD
# -----------------------------
BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise RuntimeError("GROQ_API_KEY missing in environment")

client = Groq(api_key=api_key)


# -----------------------------
# LLM CALL
# -----------------------------
def call_llm(prompt: str):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a STRICT JSON generator. "
                    "Return ONLY valid JSON. No explanation, no markdown."
                )
            },
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )
    return response.choices[0].message.content


# -----------------------------
# SAFE JSON PARSER (FIXED)
# -----------------------------
def extract_json(text: str):
    if not text:
        return {}

    text = text.strip()
    text = text.replace("```json", "").replace("```", "")

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        return {}

    json_str = text[start:end + 1]

    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        # safer fallback cleanup
        json_str = re.sub(r",\s*}", "}", json_str)
        json_str = re.sub(r",\s*]", "]", json_str)

        try:
            return json.loads(json_str)
        except:
            return {}


# -----------------------------
# SKILL CATALOG
# -----------------------------
def load_skill_catalog():
    path = Path("data/skill_catalog.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# -----------------------------
# EMPTY PROJECT CHECK (IMPORTANT FIX)
# -----------------------------
def is_empty_project(data):
    return (
        not data.get("file_tree") and
        not data.get("code_samples") and
        not data.get("imports") and
        not data.get("dependencies")
    )


# -----------------------------
# MAIN PIPELINE
# -----------------------------
def analyze_with_llm(project_data):

    enriched_project_data = {
        "file_tree": project_data.get("file_tree", []),
        "dependencies": project_data.get("dependencies", []),
        "imports": project_data.get("imports", []),
        "code_samples": project_data.get("code_samples", [])
    }

    # ==================================================
    # 🚨 EARLY EXIT FOR EMPTY / IMAGE PROJECTS
    # ==================================================
    if is_empty_project(enriched_project_data):
        return {
            "project_summary": {
                "project_purpose": "No code detected (empty or non-code files)",
                "domain": "Unknown",
                "technologies_used": [],
                "complexity": "None",
                "key_features": [],
                "architecture_style": "None"
            },
            "skills": {"skills": []},
            "questions": {"questions": []},
            "project_statistics": {
                "files_analyzed": len(enriched_project_data["file_tree"]),
                "dependencies_found": 0,
                "code_samples_used": 0
            }
        }

    # ==================================================
    # STEP 1: PROJECT ANALYSIS
    # ==================================================
    project_prompt = PROJECT_ANALYSIS_PROMPT.format(
        project_data=json.dumps(enriched_project_data)
    )

    project_analysis_raw = call_llm(project_prompt)
    project_summary = extract_json(project_analysis_raw)

    # ==================================================
    # STEP 2: SKILL MATCHING
    # ==================================================
    skill_catalog = load_skill_catalog()

    skill_prompt = SKILL_MATCH_PROMPT.format(
        project_summary=json.dumps(project_summary),
        file_tree=json.dumps(enriched_project_data["file_tree"]),
        code_samples=json.dumps(enriched_project_data["code_samples"]),
        skill_catalog=json.dumps(skill_catalog)
    )

    skill_analysis_raw = call_llm(skill_prompt)
    skills = extract_json(skill_analysis_raw)

    # FIX: handle empty skills safely
    if not skills.get("skills"):
        return {
            "project_summary": project_summary,
            "skills": skills,
            "questions": {"questions": []}
        }

    # ==================================================
    # STEP 3: QUESTION GENERATION
    # ==================================================
    question_prompt = QUESTION_PROMPT.format(
        skills=json.dumps(skills)
    )

    question_analysis_raw = call_llm(question_prompt)
    questions = extract_json(question_analysis_raw)

    if not questions.get("questions"):
        questions = {"questions": []}

    # ==================================================
    # FINAL OUTPUT
    # ==================================================
    return {
        "project_summary": project_summary,
        "skills": skills,
        "questions": questions,
        "project_statistics": {
            "files_analyzed": len(enriched_project_data["file_tree"]),
            "dependencies_found": len(enriched_project_data["dependencies"]),
            "code_samples_used": len(enriched_project_data["code_samples"])
        }
    }