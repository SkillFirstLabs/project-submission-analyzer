"""
Orchestrator + Evaluator.

Runs the pipeline step by step:
  1. Safe ZIP extraction (deterministic, not an LLM call)
  2. Skill Extractor agent (RAG-grounded) + deterministic confidence floor
  3. Question Generator agent — once per suggested skill
  4. Comparator agent (description/outcomes vs code)
  5. Cross-Check agent — flags/drops skills contradicted by the comparator
  6. Report compilation (deterministic)

After every LLM step, the Evaluator checks the output is structurally
sound and non-empty. If a step fails validation, it retries that step
up to MAX_RETRIES times before raising, so a single bad agent call can't
silently corrupt the final report.
"""
from __future__ import annotations
import asyncio
import time
from typing import List
from openai import OpenAI

from schemas import (
    SuggestedSkill, SuggestedSkillList, SkillQuestionSet, InterviewQuestion,
    Summary, EvaluationReport, Metadata, AnalyzeResponse,
)
from utils.safe_zip import safe_extract_zip, ExtractionResult, UnsafeZipError, EmptyProjectError
from rag.catalog_index import get_skill_index
from pipeline_agents.skill_agent import extract_skills
from pipeline_agents.question_agent import generate_questions_for_skill
from pipeline_agents.comparator_agent import compare_description_to_code
from pipeline_agents.crosscheck_agent import run_crosscheck

MAX_RETRIES = 2
SKILL_CONFIDENCE_FLOOR = 0.3


class PipelineError(Exception):
    """Raised when a step fails validation after all retries."""


def _evaluate_skill_output(result: SuggestedSkillList) -> bool:
    if not result.suggested_skills:
        return False
    for s in result.suggested_skills:
        if not s.skill_id or not s.skill_name or not s.rationale.strip():
            return False
        if not (0.0 <= s.confidence <= 1.0):
            return False
    return True


def _evaluate_question_output(skill_name: str, questions: List[InterviewQuestion]) -> bool:
    if not questions:
        return False
    for q in questions:
        if not q.question_text.strip() or not q.expected_key_points:
            return False
    has_codebase = any(q.question_focus == "codebase_specific" for q in questions)
    has_conceptual = any(q.question_focus == "conceptual" for q in questions)
    return has_codebase and has_conceptual


def _evaluate_comparator_output(result) -> bool:
    if not result.outcome_evaluation:
        return False
    if not (0.0 <= result.alignment_score <= 1.0):
        return False
    if not result.narrative.strip():
        return False
    return True


async def _run_with_retries(coro_factory, evaluator, step_name: str, max_retries: int = MAX_RETRIES):
    last_err = None
    for attempt in range(max_retries + 1):
        try:
            output = await coro_factory()
        except Exception as e:
            last_err = e
            await asyncio.sleep(0.5)
            continue
        if evaluator(output):
            return output
        last_err = ValueError(f"{step_name} produced an invalid/empty output on attempt {attempt + 1}.")
    raise PipelineError(f"Step '{step_name}' failed after {max_retries + 1} attempts: {last_err}")


async def run_pipeline(
    zip_path: str,
    project_title: str,
    project_description: str,
    project_outcomes: str,
    questions_per_skill: int,
    model: str,
    client: OpenAI,
    max_file_size: int,
    max_total_files: int,
) -> AnalyzeResponse:
    start = time.time()

    # ---- Step 1: Safe extraction (deterministic) ----
    extract_start = time.time()
    extraction: ExtractionResult = safe_extract_zip(
        zip_path, max_file_size=max_file_size, max_total_files=max_total_files
    )
    extraction_time_ms = int((time.time() - extract_start) * 1000)

    # ---- Step 2: Skill extraction (RAG-grounded agent) ----
    catalog_index = get_skill_index(client)

    async def skill_step():
        return await extract_skills(extraction.files, catalog_index, model=model)

    skill_result: SuggestedSkillList = await _run_with_retries(
        skill_step, _evaluate_skill_output, "skill_extraction"
    )

    # Deterministic confidence floor: drop low-effort/speculative guesses
    # that slipped past the prompt's evidence requirement.
    skill_result.suggested_skills = [
        s for s in skill_result.suggested_skills if s.confidence >= SKILL_CONFIDENCE_FLOOR
    ]

    if not skill_result.suggested_skills:
        raise PipelineError(
            "No catalog skills could be confidently matched to this codebase. "
            "Try a project with more recognizable source files."
        )

    # ---- Step 3: Question generation per skill ----
    skill_question_sets: List[SkillQuestionSet] = []

    for skill in skill_result.suggested_skills:
        async def question_step(skill_name=skill.skill_name):
            return await generate_questions_for_skill(
                skill_name, extraction.files, model=model,
                questions_per_skill=questions_per_skill,
            )

        def question_eval(result, skill_name=skill.skill_name):
            return _evaluate_question_output(skill_name, result.questions)

        q_result = await _run_with_retries(
            question_step, question_eval, f"question_generation:{skill.skill_name}"
        )
        skill_question_sets.append(
            SkillQuestionSet(skill_name=skill.skill_name, questions=q_result.questions)
        )

    # ---- Step 4: Comparator (description/outcomes vs code) ----
    async def comparator_step():
        return await compare_description_to_code(
            project_description, project_outcomes, extraction, model=model
        )

    comparator_result = await _run_with_retries(
        comparator_step, _evaluate_comparator_output, "comparator"
    )

    # ---- Step 5: Cross-check — flag/drop skills contradicted by the comparator ----
    try:
        crosscheck_result = await run_crosscheck(skill_result.suggested_skills, comparator_result, model=model)
        flagged_names = {f.skill_name.lower() for f in crosscheck_result.flagged_skills}
    except Exception:
        # Cross-check is a quality safety net, not a hard requirement — if it
        # fails outright, don't let that take down an otherwise-good report.
        flagged_names = set()

    if flagged_names:
        skill_result.suggested_skills = [
            s for s in skill_result.suggested_skills if s.skill_name.lower() not in flagged_names
        ]
        skill_question_sets = [
            sq for sq in skill_question_sets if sq.skill_name.lower() not in flagged_names
        ]

    if not skill_result.suggested_skills:
        raise PipelineError(
            "All suggested skills were dropped by the confidence floor or cross-check step. "
            "The codebase may not provide strong enough evidence for catalog skills."
        )

    summary = Summary(
        overall_alignment=comparator_result.overall_alignment,
        alignment_score=comparator_result.alignment_score,
        narrative=comparator_result.narrative,
        outcome_evaluation=comparator_result.outcome_evaluation,
        strengths=comparator_result.strengths,
        gaps=comparator_result.gaps,
    )

    # ---- Step 6: Report compilation (deterministic) ----
    report = EvaluationReport(
        skills=skill_question_sets,
        summary=summary,
        metadata=Metadata(
            files_analyzed=extraction.files_analyzed,
            extraction_time_ms=extraction_time_ms,
            model_tokens_used=0,
        ),
    )

    response = AnalyzeResponse(
        project_title=project_title,
        suggested_skills=skill_result.suggested_skills,
        evaluation_report=report,
        processing_time_ms=int((time.time() - start) * 1000),
    )
    return response
