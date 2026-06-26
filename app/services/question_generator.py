"""
Question generator: uses the LLM to produce conceptual and codebase-specific
viva questions for each detected skill.

Fallback: if the LLM fails, returns template-based questions.
All skills are processed in parallel via asyncio.gather.
"""

import json
import re
import asyncio

from app.models.schemas import DetectedSkill, Question, SkillWithQuestions
from app.llm.base import BaseLLMClient
from app.core.logging_config import get_logger

logger = get_logger(__name__)

_SYSTEM_PROMPT = (
    "You are an expert technical mentor reviewing an intern's project submission. "
    "Generate clear, specific viva questions that test both theoretical understanding "
    "and practical application of the skill as demonstrated in the submitted code."
)

_QUESTION_PROMPT_TEMPLATE = """\
Generate exactly {n} viva questions for the skill below.

SKILL: {skill_name}

EVIDENCE FROM CODE:
{evidence}

PROJECT CONTEXT (excerpt):
{context_excerpt}

Return ONLY a valid JSON array — no extra text, no markdown fences:
[
  {{"question_text": "...", "question_focus": "conceptual", "expected_key_points": ["point1", "point2"]}},
  {{"question_text": "...", "question_focus": "codebase",   "expected_key_points": ["point1", "point2"]}}
]

Rules:
- Mix conceptual (theory) and codebase (specific to this code) questions
- Each question needs 2-4 key points
- Return valid JSON only
"""

# Fallback template questions when LLM is unavailable
_FALLBACK_TEMPLATES: dict[str, list[dict]] = {
    "default": [
        {
            "question_text": "Explain the core concept behind {skill_name} and why you used it in this project.",
            "question_focus": "conceptual",
            "expected_key_points": [
                "Understanding of core concept",
                "Justification for using this technology",
                "Awareness of alternatives"
            ]
        },
        {
            "question_text": "Walk me through how you implemented {skill_name} in your code. What challenges did you face?",
            "question_focus": "codebase",
            "expected_key_points": [
                "Description of implementation",
                "Challenges encountered",
                "How challenges were resolved"
            ]
        },
        {
            "question_text": "What are the best practices for {skill_name} and how many did you follow in this project?",
            "question_focus": "conceptual",
            "expected_key_points": [
                "Knowledge of best practices",
                "Self-assessment of implementation quality",
                "Areas for improvement"
            ]
        },
    ]
}


def _parse_llm_questions(raw_text: str, skill_name: str) -> list[Question]:
    """
    Parse LLM JSON response into Question objects.
    Returns empty list (not raises) on any parse failure.
    """
    try:
        # Extract JSON array from response (LLM sometimes adds preamble text)
        match = re.search(r"\[.*\]", raw_text, re.DOTALL)
        if not match:
            logger.warning(f"No JSON array found in LLM response for {skill_name}")
            return []

        data = json.loads(match.group())
        questions = []
        for item in data:
            if not isinstance(item, dict):
                continue
            try:
                questions.append(Question(
                    question_text=str(item.get("question_text", "")).strip(),
                    question_focus=str(item.get("question_focus", "conceptual")).strip(),
                    expected_key_points=item.get("expected_key_points", []),
                ))
            except Exception as exc:
                logger.warning(f"Skipping malformed question: {exc}")
        return questions

    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning(f"Failed to parse LLM questions for {skill_name}: {exc}")
        return []


def _fallback_questions(skill_name: str, n: int) -> list[Question]:
    """Generate template-based questions when LLM is unavailable."""
    templates = _FALLBACK_TEMPLATES["default"][:n]
    return [
        Question(
            question_text=t["question_text"].replace("{skill_name}", skill_name),
            question_focus=t["question_focus"],
            expected_key_points=t["expected_key_points"],
        )
        for t in templates
    ]


async def _generate_for_one(
    skill: DetectedSkill,
    context: str,
    llm_client: BaseLLMClient,
    questions_per_skill: int,
) -> tuple[SkillWithQuestions, int]:
    """Generate questions for a single skill. Returns (result, tokens_used)."""
    evidence_text = "\n".join(
        f"  - {e.file_path}: {e.snippet}"
        for e in skill.evidence[:3]
    ) or "  No specific code evidence captured."

    prompt = (
        _QUESTION_PROMPT_TEMPLATE
        .replace("{n}", str(questions_per_skill))
        .replace("{skill_name}", skill.skill_name)
        .replace("{evidence}", evidence_text)
        .replace("{context_excerpt}", context[:3000])
    )

    questions: list[Question] = []
    tokens = 0
    try:
        if llm_client.is_available():
            response = await llm_client.generate(prompt=prompt, system_prompt=_SYSTEM_PROMPT)
            tokens = response.tokens_used
            questions = _parse_llm_questions(response.text, skill.skill_name)
        if not questions:
            logger.info(f"Using fallback questions for: {skill.skill_name}")
            questions = _fallback_questions(skill.skill_name, questions_per_skill)
    except Exception as exc:
        logger.error(f"LLM failed for '{skill.skill_name}': {exc} — using fallback")
        questions = _fallback_questions(skill.skill_name, questions_per_skill)

    return SkillWithQuestions(skill=skill, questions=questions), tokens


async def generate_questions_for_skills(
    skills: list[DetectedSkill],
    context: str,
    llm_client: BaseLLMClient,
    questions_per_skill: int = 3,
) -> tuple[list[SkillWithQuestions], int]:
    """
    Generate questions for all detected skills IN PARALLEL.
    Caps at top 5 skills. Returns empty list gracefully if no skills matched.
    """
    if not skills:
        logger.info("No skills to generate questions for — skipping LLM calls")
        return [], 0

    top_skills = skills[:5]
    tasks = [_generate_for_one(skill, context, llm_client, questions_per_skill) for skill in top_skills]
    results = await asyncio.gather(*tasks)

    skill_results = [r[0] for r in results]
    total_tokens = sum(r[1] for r in results)

    logger.info("Question generation complete", extra={
        "skills": len(skill_results),
        "total_tokens": total_tokens,
    })
    return skill_results, total_tokens
