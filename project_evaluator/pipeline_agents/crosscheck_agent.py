"""
Cross-Check Agent.

Runs after both the skill suggestions and the comparator's outcome
evaluation exist. Flags any suggested skill whose rationale is directly
contradicted by the comparator's findings (e.g. a skill claims a feature
is fully implemented, but the comparator's evidence/gap for the related
outcome says it's missing or broken). Flagged skills are dropped before
the final report is compiled.
"""
from __future__ import annotations
from typing import List
from agents import Agent, Runner

from schemas import SuggestedSkill, ComparatorResult, CrossCheckResult


def build_crosscheck_agent(model: str) -> Agent:
    return Agent(
        name="CrossCheckAgent",
        model=model,
        instructions=(
            "You are a consistency checker. You will be given a list of suggested skills with their "
            "rationales, and a list of outcome evaluations (status + evidence + gap) from a separate "
            "comparator review of the same codebase.\n"
            "Flag any suggested skill whose rationale is directly CONTRADICTED by the comparator's "
            "findings — for example, a skill rationale claims a feature is implemented but the "
            "comparator's gap/evidence for the related outcome says it is missing or broken.\n"
            "Only flag genuine contradictions, not minor differences in emphasis or scope. "
            "If nothing contradicts, return an empty flagged_skills list."
        ),
        output_type=CrossCheckResult,
    )


async def run_crosscheck(
    suggested_skills: List[SuggestedSkill],
    comparator_result: ComparatorResult,
    model: str,
) -> CrossCheckResult:
    skills_block = "\n".join(
        f"- {s.skill_name} (confidence {s.confidence:.2f}): {s.rationale}" for s in suggested_skills
    )
    outcomes_block = "\n".join(
        f"- outcome: {o.stated_outcome} | status: {o.status} | evidence: {o.evidence} | gap: {o.gap or 'none'}"
        for o in comparator_result.outcome_evaluation
    )

    prompt = (
        f"SUGGESTED SKILLS AND RATIONALES:\n{skills_block}\n\n"
        f"COMPARATOR OUTCOME EVALUATIONS:\n{outcomes_block}\n\n"
        "Identify any skill above whose rationale is contradicted by the comparator's findings."
    )

    agent = build_crosscheck_agent(model)
    result = await Runner.run(agent, prompt)
    return result.final_output