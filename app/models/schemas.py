from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class SuggestedSkill(BaseModel):
    skill_id: str
    skill_name: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    rationale: str

class EvaluationQuestion(BaseModel):
    question_text: str
    question_focus: Literal["conceptual", "codebase_specific"]
    expected_key_points: List[str]

class SkillWithQuestions(BaseModel):
    skill_id: str
    skill_name: str
    questions: List[EvaluationQuestion]

class OutcomeEvaluationItem(BaseModel):
    stated_outcome: str
    status: Literal["met", "partial", "not_met", "not_verifiable"]
    evidence: Optional[str] = None
    gap: Optional[str] = None

class ReportSummary(BaseModel):
    overall_alignment: Literal["strong", "partial", "weak"]
    alignment_score: float = Field(..., ge=0.0, le=1.0)
    narrative: str

class EvaluationReport(BaseModel):
    skills: List[SkillWithQuestions]
    summary: ReportSummary
    outcome_evaluation: List[OutcomeEvaluationItem]
    strengths: List[str]
    gaps: List[str]

class ReportMetadata(BaseModel):
    files_analyzed: int
    extraction_time_ms: int
    model_tokens_used: int

class AnalysisResponse(BaseModel):
    project_title: str
    suggested_skills: List[SuggestedSkill]
    evaluation_report: EvaluationReport
    metadata: ReportMetadata
    processing_time_ms: int
