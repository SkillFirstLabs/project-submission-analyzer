"""
Pydantic models for request, response, and all internal data structures.
"""

from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request
# ---------------------------------------------------------------------------

class AnalysisRequest(BaseModel):
    """
    Metadata submitted alongside the ZIP file via multipart form.
    The zip_file itself is handled as an UploadFile at the route level.
    """
    project_title: str = Field(..., min_length=1, max_length=200)
    project_description: str = Field(..., min_length=10, max_length=5000)
    project_outcomes: str = Field(..., min_length=10, max_length=5000)
    questions_per_skill: int = Field(default=3, ge=1, le=10)


# ---------------------------------------------------------------------------
# Internal data models
# ---------------------------------------------------------------------------

class ProjectMetadata(BaseModel):
    title: str
    description: str
    outcomes: str


class FileNode(BaseModel):
    path: str
    size_bytes: int
    language: Optional[str] = None
    is_skipped: bool = False
    skip_reason: Optional[str] = None


class ProjectTree(BaseModel):
    root_dir: str
    total_files: int
    analyzed_files: int
    skipped_files: int
    nodes: list[FileNode] = []


class TechDetectionResult(BaseModel):
    languages: list[str] = []
    frameworks: list[str] = []
    dependencies: list[str] = []
    dependency_files_found: list[str] = []


class SecurityFlag(BaseModel):
    file_path: str
    line_number: Optional[int] = None
    pattern: str
    severity: str = Field(..., pattern="^(low|medium|high)$")
    description: str


class SecurityScanResult(BaseModel):
    flags: list[SecurityFlag] = []
    has_high_severity: bool = False
    summary: str = ""


class SkillEvidence(BaseModel):
    file_path: str
    snippet: str


class DetectedSkill(BaseModel):
    skill_id: str
    skill_name: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    low_confidence: bool = False
    rationale: str
    evidence: list[SkillEvidence] = []


class Question(BaseModel):
    question_text: str
    question_focus: str  # "conceptual" or "codebase"
    expected_key_points: list[str] = []


class SkillWithQuestions(BaseModel):
    skill: DetectedSkill
    questions: list[Question] = []


class OutcomeEvaluation(BaseModel):
    stated_outcome: str
    is_met: bool
    confidence: float = Field(..., ge=0.0, le=1.0)
    evidence: str
    gaps: list[str] = []


class EvaluationReport(BaseModel):
    strengths: list[str] = []
    gaps: list[str] = []
    summary: str
    outcome_evaluations: list[OutcomeEvaluation] = []


class ReportMetadata(BaseModel):
    files_analyzed: int
    skipped_files: int
    extraction_time_ms: float
    analysis_time_ms: float
    model_tokens_used: int
    llm_provider: str


# ---------------------------------------------------------------------------
# Response
# ---------------------------------------------------------------------------

class AnalysisResponse(BaseModel):
    """Final JSON response returned to the client."""
    project_title: str
    suggested_skills: list[SkillWithQuestions] = []
    evaluation_report: EvaluationReport
    tech_detection: TechDetectionResult
    security_scan: SecurityScanResult
    metadata: ReportMetadata
    processing_time_ms: float
    analysis_note: Optional[str] = None


# ---------------------------------------------------------------------------
# Error responses
# ---------------------------------------------------------------------------

class ErrorDetail(BaseModel):
    code: str
    message: str
    detail: Optional[str] = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
