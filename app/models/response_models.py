from pydantic import BaseModel, Field
from typing import List, Optional


class SuggestedSkill(BaseModel):
    skill_id: str
    skill_name: str
    confidence: float
    rationale: str
    proof_examples: List[str] = Field(default_factory=list)


class Question(BaseModel):
    question_text: str
    question_focus: str
    expected_key_points: List[str]


class SkillEvaluation(BaseModel):
    skill_name: str
    proof_examples: List[str] = Field(default_factory=list)
    questions: List[Question]


class OutcomeEvaluation(BaseModel):
    stated_outcome: str
    status: str
    evidence: Optional[str]
    gap: Optional[str]


class Summary(BaseModel):
    overall_alignment: str
    alignment_score: float
    narrative: str
    outcome_evaluation: List[OutcomeEvaluation]
    strengths: List[str]
    gaps: List[str]


class Metadata(BaseModel):
    files_analyzed: int
    extraction_time_ms: int
    model_tokens_used: int


class EvaluationReport(BaseModel):
    skills: List[SkillEvaluation]
    summary: Summary
    metadata: Metadata


class AnalyzeSubmissionResponse(BaseModel):
    project_title: str
    project_summary: dict = Field(default_factory=dict)
    suggested_skills: List[SuggestedSkill]
    evaluation_report: EvaluationReport
    project_statistics: dict = Field(default_factory=dict)
    processing_time_ms: int
