"""
Pydantic response models for the Project Submission AI Analyzer API.
"""

from typing import List
from pydantic import BaseModel, Field

from app.models.evaluation import EvaluationReportModel
from app.models.skill import SkillModel
from app.models.viva import VivaQuestion


class MetadataModel(BaseModel):
    """Processing metadata returned with every successful analysis response."""
    files_analyzed: int = Field(..., description="Total count of files analyzed in the ZIP archive.")
    source_files: int = Field(..., description="Count of parsed source files.")
    processing_time_ms: int = Field(..., description="Time taken by the scanner to analyze project files.")
    parser_version: str = Field(..., description="Parser engine version used.")
    model: str = Field(..., description="AI model name used for reasoning.")


class AnalyzeSubmissionResponse(BaseModel):
    """Full successful response for the analyze-submission endpoint."""
    project_title: str = Field(..., description="Stated project title.")
    suggested_skills: List[SkillModel] = Field(
        default_factory=list,
        description="Skills detected in the codebase, ordered by confidence.",
    )
    evaluation_report: EvaluationReportModel = Field(
        ...,
        description="Detailed evaluation report: skill alignment, outcome status, and summary.",
    )
    viva_questions: List[VivaQuestion] = Field(
        default_factory=list,
        description="AI-generated viva questions per demonstrated skill, for use in oral examinations.",
    )
    metadata: MetadataModel = Field(..., description="Processing metadata.")
    processing_time_ms: int = Field(..., description="Total HTTP request processing time in milliseconds.")
