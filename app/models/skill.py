"""
Pydantic data models for skills.
"""

from pydantic import BaseModel, Field


class SkillModel(BaseModel):
    """Suggested technical skill details."""
    skill_id: str = Field(..., description="Unique ID of the skill in the catalog.")
    skill_name: str = Field(..., description="Name of the suggested skill.")
    confidence: float = Field(..., description="Confidence score between 0.0 and 1.0.")
    rationale: str = Field(..., description="Rationale for suggesting the skill based on codebase evidence.")
