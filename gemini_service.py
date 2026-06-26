import asyncio
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv

try:
    import google.generativeai as genai  # type: ignore
except Exception:  # pragma: no cover - optional dependency during demo mode
    genai = None

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_MODEL_NAME = "gemini-2.0-flash"
DEMO_MODE = True


def get_api_key(env_path: Path | None = None) -> str | None:
    """Resolve the Gemini API key from the project .env file or environment variables."""
    if env_path is None:
        env_path = BASE_DIR / ".env"

    load_dotenv(env_path, override=True)

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None
    return api_key.strip().strip('"').strip("'")


def get_model_name(env_path: Path | None = None) -> str:
    """Resolve the Gemini model name from the project .env file or environment variables."""
    if env_path is None:
        env_path = BASE_DIR / ".env"

    load_dotenv(env_path, override=True)

    model_name = (
        os.getenv("GEMINI_MODEL")
        or os.getenv("GOOGLE_MODEL")
        or os.getenv("GEMINI_MODEL_NAME")
        or DEFAULT_MODEL_NAME
    )
    return model_name.strip().strip('"').strip("'") if model_name else DEFAULT_MODEL_NAME


def _extract_technologies(file_info: Dict[str, Any], skill_info: Dict[str, Any]) -> List[str]:
    extensions = file_info.get("extensions", {}) or {}
    source_code = file_info.get("source_code", "")
    framework_names = [str(item) for item in skill_info.get("frameworks", []) or []]
    language_names = [str(item) for item in skill_info.get("languages", {}).keys()]

    detected: List[str] = []
    if ".py" in extensions:
        detected.append("Python")
    if ".js" in extensions or ".ts" in extensions:
        detected.append("JavaScript/TypeScript")
    if ".html" in extensions:
        detected.append("HTML")
    if ".css" in extensions:
        detected.append("CSS")
    if ".java" in extensions:
        detected.append("Java")
    if ".cpp" in extensions:
        detected.append("C++")

    lowered = source_code.lower()
    if "fastapi" in lowered or "flask" in lowered or "django" in lowered:
        detected.append("Backend Framework")
    if "react" in lowered or "vue" in lowered or "next" in lowered:
        detected.append("Frontend Framework")
    if "sqlite" in lowered or "postgres" in lowered or "mysql" in lowered:
        detected.append("Database")

    detected.extend(language_names)
    detected.extend(framework_names)

    # De-duplicate while preserving order
    seen = set()
    ordered: List[str] = []
    for item in detected:
        if item and item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def _build_demo_report(
    project_name: str,
    description: str,
    file_info: Dict[str, Any],
    skill_info: Dict[str, Any],
) -> Dict[str, Any]:
    project_title = (project_name or "Untitled Project").strip() or "Untitled Project"
    description_text = (description or "No project description provided.").strip() or "No project description provided."
    all_files = file_info.get("all_files", []) or []
    total_files = len(all_files)
    source_code = file_info.get("source_code", "")
    has_readme = bool(file_info.get("has_readme", False))
    extensions = file_info.get("extensions", {}) or {}
    technologies = _extract_technologies(file_info, skill_info)
    tech_summary = ", ".join(technologies) if technologies else "a modern web stack"

    file_factor = min(20, max(0, total_files - 2) * 2)
    readme_boost = 8 if has_readme else 0
    tech_boost = min(20, len(technologies) * 3)
    source_boost = min(15, max(0, len(source_code) // 700))
    overall_score = min(95, 65 + file_factor + readme_boost + tech_boost + source_boost)

    innovation_score = min(95, overall_score + (4 if len(technologies) >= 3 else 1))
    technical_complexity = "Moderate"
    if len(technologies) >= 4 or total_files >= 10:
        technical_complexity = "High"
    elif len(technologies) <= 1:
        technical_complexity = "Low"

    if overall_score >= 85:
        code_quality = "Excellent"
        documentation_score = "Strong"
        ui_ux_score = "Strong"
    elif overall_score >= 75:
        code_quality = "Good"
        documentation_score = "Solid"
        ui_ux_score = "Good"
    else:
        code_quality = "Developing"
        documentation_score = "Needs improvement"
        ui_ux_score = "Needs refinement"

    strengths = [
        f"The submission presents a clear objective around {project_title}.",
        f"The project includes {total_files} discovered files and demonstrates a practical use of {tech_summary}.",
        "The structure indicates thoughtful organization and a good foundation for iterative development.",
    ]
    weaknesses = []
    if not has_readme:
        weaknesses.append("README documentation is missing or not clearly discoverable.")
    if total_files < 5:
        weaknesses.append("The project would benefit from more modular components and clearer separation of concerns.")
    if not source_code.strip():
        weaknesses.append("The uploaded archive did not contain substantial source content for deeper analysis.")
    if not weaknesses:
        weaknesses.append("The project would benefit from a few additional refinements in maintainability and extensibility.")

    improvement_suggestions = [
        "Add a concise README with setup steps, architecture notes, and known limitations.",
        "Introduce clearer component boundaries and reusable modules for future growth.",
        "Add lightweight tests for critical workflows to improve confidence and maintainability.",
    ]
    security_observations = [
        "Sensitive configuration values should remain externalized from source files.",
        "Input validation and error handling should be strengthened for production readiness.",
        "Dependencies should be reviewed regularly for security updates.",
    ]

    architecture_review = (
        f"{project_title} appears to follow a practical, approachable architecture with a clear focus on {tech_summary}. "
        f"The project structure and identified files suggest a foundation that is suitable for expansion, but additional "
        f"modularization and documentation would make it easier to maintain and scale."
    )
    scalability_analysis = (
        "The current solution shows a solid base for incremental growth. If the project expands, introducing service boundaries, "
        "clear data flows, and automated testing will improve long-term maintainability and resilience."
    )
    project_summary = (
        f"{project_title} is a promising submission that aligns well with the provided description: {description_text}. "
        f"The discovered files, folder structure, and selected technologies suggest a project with meaningful potential and a credible implementation path."
    )
    verdict = (
        f"{project_title} demonstrates solid initiative, a practical implementation approach, and a clear understanding of the "
        f"chosen technology stack. With a bit more polish in documentation, testing, and architecture refinement, this project "
        f"could become a strong showcase piece for the hackathon."
    )

    conceptual_question = (
        f"How would you explain the role of {technologies[0] if technologies else 'the chosen technology'} in the architecture of this project?"
    )
    coding_question = (
        "If this project needed to handle twice the current load, what would be the first performance or scalability improvement you would implement?"
    )

    return {
        "demo_mode": True,
        "description_vs_code": {
            "claims": [description_text],
            "found": [f"Discovered {total_files} files", f"Detected technologies: {tech_summary}"],
            "mismatches": [],
            "match_score": min(95, 70 + (4 if has_readme else 0) + (3 if total_files >= 5 else 0)),
        },
        "conceptual_questions": [conceptual_question],
        "code_questions": [coding_question],
        "evaluation": {
            "score": overall_score,
            "overall_score": overall_score,
            "innovation_score": innovation_score,
            "technical_complexity": technical_complexity,
            "code_quality": code_quality,
            "documentation_score": documentation_score,
            "ui_ux_score": ui_ux_score,
            "architecture_review": architecture_review,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "improvement_suggestions": improvement_suggestions,
            "security_observations": security_observations,
            "scalability_analysis": scalability_analysis,
            "project_summary": project_summary,
            "verdict": verdict,
            "final_verdict": verdict,
        },
    }


async def analyze_project(
    description: str,
    file_info: Dict[str, Any],
    skill_info: Dict[str, Any],
    project_name: str | None = None,
) -> Dict[str, Any]:
    """Run either the demo evaluation path or the real Gemini path without changing the API contract."""
    if DEMO_MODE:
        await asyncio.sleep(4)
        return _build_demo_report(project_name or "", description, file_info, skill_info)

    api_key = get_api_key()
    print("API key configured:", bool(api_key))
    print("API key length:", len(api_key) if api_key else 0)
    if not api_key:
        return {
            "error": "AI analysis failed",
            "detail": "GEMINI_API_KEY is not configured.",
            "description_vs_code": {
                "claims": [],
                "found": [],
                "mismatches": ["Missing GEMINI_API_KEY environment variable"],
                "match_score": 0,
            },
            "conceptual_questions": ["Key not set"],
            "code_questions": ["Key not set"],
            "evaluation": {
                "score": 0,
                "overall_score": 0,
                "strengths": [],
                "weaknesses": ["API Key not configured"],
                "verdict": "Could not execute Gemini API call because the API Key is missing.",
                "final_verdict": "Could not execute Gemini API call because the API Key is missing.",
            },
        }

    if genai is None:
        return {
            "error": "AI analysis failed",
            "detail": "Gemini SDK is not available.",
            "description_vs_code": {
                "claims": [],
                "found": [],
                "mismatches": ["Gemini SDK not available"],
                "match_score": 0,
            },
            "conceptual_questions": ["SDK not available"],
            "code_questions": ["SDK not available"],
            "evaluation": {
                "score": 0,
                "overall_score": 0,
                "strengths": [],
                "weaknesses": ["Gemini SDK not available"],
                "verdict": "Gemini SDK is not available for this execution.",
                "final_verdict": "Gemini SDK is not available for this execution.",
            },
        }

    genai.configure(api_key=api_key)
    file_list = file_info.get("all_files", [])
    source_code = file_info.get("source_code", "")
    languages = skill_info.get("languages", {})
    frameworks = skill_info.get("frameworks", [])

    prompt = f"""You are a project evaluator for a university submission system.

Analyze this student project submission and return ONLY a valid JSON object. No markdown wrapping. No backticks. No explanation.

PROJECT DESCRIPTION (what student claims):
{description}

FILES FOUND IN ZIP:
{json.dumps(file_list, indent=2)}

SOURCE CODE EXTRACTED:
{source_code}

DETECTED SKILLS:
Languages: {json.dumps(languages, indent=2)}
Frameworks: {json.dumps(frameworks, indent=2)}

Return ONLY this JSON structure:
{{
  "description_vs_code": {{
    "claims": ["list of things student claimed in description"],
    "found": ["list of things actually found in code"],
    "mismatches": ["list of mismatches found"],
    "match_score": 75
  }},
  "conceptual_questions": [
    "Question 1 about concepts used",
    "Question 2",
    "Question 3",
    "Question 4",
    "Question 5"
  ],
  "code_questions": [
    "Specific question about something in their actual code",
    "Question 2",
    "Question 3",
    "Question 4",
    "Question 5"
  ],
  "evaluation": {{
    "score": 72,
    "strengths": ["strength 1", "strength 2", "strength 3"],
    "weaknesses": ["weakness 1", "weakness 2"],
    "verdict": "One paragraph summary of the project quality and student understanding"
  }}
}}

Rules:
- mismatches should catch things like: claimed backend but only HTML found, claimed AI/ML but no ML libraries found, claimed database but no DB code found
- code_questions must be specific to the actual code found, not generic (reference actual files, functions, variables, style rules, or structure)
- score should be honest: basic static HTML project = 30-40, good full stack = 70-85
- If description is very different from code, reduce match_score heavily
"""

    try:
        model_name = get_model_name()
        print("Using Gemini model:", model_name)
        model = genai.GenerativeModel(model_name)

        try:
            response = await asyncio.to_thread(
                model.generate_content,
                prompt,
                generation_config={"response_mime_type": "application/json"},
            )
        except Exception:
            response = await asyncio.to_thread(model.generate_content, prompt)

        raw_text = response.text.strip()
        try:
            result = json.loads(raw_text)
        except json.JSONDecodeError:
            cleaned_text = raw_text
            if cleaned_text.startswith("```"):
                cleaned_text = re.sub(r"^```(?:json)?\n", "", cleaned_text)
                cleaned_text = re.sub(r"\n```$", "", cleaned_text)
            result = json.loads(cleaned_text.strip())

        return result

    except Exception as e:
        message = str(e)
        lower_message = message.lower()
        if "quota" in lower_message or "resource_exhausted" in lower_message or "429" in lower_message:
            detail = "Gemini API quota exceeded. The current API key has reached its free-tier request limit. Please try again later or use a different API key with billing enabled."
        elif "api key" in lower_message or "api_key" in lower_message or "invalid" in lower_message:
            detail = "Gemini API key is invalid or not authorized for this request."
        else:
            detail = message

        return {
            "error": "AI analysis failed",
            "detail": detail,
            "description_vs_code": {
                "claims": ["Could not parse claims due to API error"],
                "found": ["Could not parse code due to API error"],
                "mismatches": ["API Connection Error"],
                "match_score": 0,
            },
            "conceptual_questions": ["Could not generate questions: API connection failed."],
            "code_questions": ["Could not generate questions: API connection failed."],
            "evaluation": {
                "score": 0,
                "overall_score": 0,
                "strengths": ["None (API Call Failed)"],
                "weaknesses": ["AI Evaluation Service Error"],
                "verdict": f"The Gemini AI model failed to evaluate this submission. Details: {detail}",
                "final_verdict": f"The Gemini AI model failed to evaluate this submission. Details: {detail}",
            },
        }
