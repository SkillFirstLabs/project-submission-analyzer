"""
Pydantic data model for individual viva (oral exam) questions.

Viva questions are generated per demonstrated skill and are the
primary deliverable of this system — they give mentors structured,
evidence-backed questions to use during project oral examinations.
"""

from typing import Literal
from pydantic import BaseModel, Field


class VivaQuestion(BaseModel):
    """A single viva question generated for a demonstrated skill."""

    skill_id: str = Field(
        ...,
        description="ID of the skill this question tests (matches skills catalog).",
    )
    skill_name: str = Field(
        ...,
        description="Human-readable name of the skill being tested.",
    )
    question_type: Literal["conceptual", "codebase"] = Field(
        ...,
        description=(
            "Type of question: 'conceptual' tests theoretical understanding; "
            "'codebase' asks about specific implementation choices in the submission."
        ),
    )
    question: str = Field(
        ...,
        description="The full viva question text, phrased for the student.",
    )
    expected_answer_hint: str = Field(
        ...,
        description=(
            "A concise hint for the mentor describing what a good answer covers. "
            "Not shown to the student."
        ),
    )
