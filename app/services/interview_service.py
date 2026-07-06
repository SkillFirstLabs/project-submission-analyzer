from app.services.ai_service import ask_gemini


def generate_interview_questions(project_text, frameworks, skills):

    framework_text = ", ".join(frameworks) if frameworks else "None"

    skill_text = ", ".join(
        [skill["skill_name"] for skill in skills]
    )

    prompt = f"""
You are an AI interviewer.

Based on this software project, generate interview questions.

Frameworks:
{framework_text}

Skills:
{skill_text}

Project Code:
{project_text[:8000]}

Generate:

1. Five Technical Questions
2. Two Project-Based Questions
3. Two HR Questions

Return only the questions as a numbered list.
"""

    return ask_gemini(prompt)