"""
Pydantic data models for qualitative summaries and evaluations.
"""

from typing import List, Optional
from pydantic import BaseModel, Field

from app.models.skill import SkillModel


class SummaryModel(BaseModel):
    """Mentor-friendly summary of the project implementation."""
    overall_alignment: str = Field(..., description="Overall project alignment with expectations (strong, partial, weak).")
    alignment_score: float = Field(..., description="Numerical alignment score between 0.0 and 1.0.")
    narrative: str = Field(..., description="Concise qualitative summary of the submission.")
    strengths: List[str] = Field(default_factory=list, description="Key strengths identified in the project.")
    gaps: List[str] = Field(default_factory=list, description="Identified implementation gaps or areas for improvement.")


class OutcomeEvaluationModel(BaseModel):
    """Detailed evaluation of a single project outcome."""
    stated_outcome: str = Field(..., description="Stated objective/outcome of the project.")
    status: str = Field(..., description="Evaluation status (met, partial, not_met, not_verifiable).")
    evidence: str = Field(..., description="Supporting evidence extracted from the codebase.")
    gap: Optional[str] = Field(None, description="Detailed gap description if the status is not fully met.")


class EvaluationReportModel(BaseModel):
    """Structured project evaluation report containing skills, summary, and outcomes."""
    skills: List[SkillModel] = Field(default_factory=list, description="List of suggested skills.")
    summary: SummaryModel = Field(..., description="Qualitative summary of the evaluation.")
    outcome_evaluation: List[OutcomeEvaluationModel] = Field(default_factory=list, description="Detailed status of expected outcomes.")
