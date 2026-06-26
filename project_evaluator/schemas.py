"""
Pydantic models for the Project Submission AI Analyzer.
These mirror the exact output JSON shape required by the spec.
"""
from __future__ import annotations
from typing import List, Optional, Literal
from pydantic import BaseModel, Field


# ---------- Catalog ----------

class SkillCatalogItem(BaseModel):
    skill_id: str
    skill_name: str
    category: Optional[str] = None


# ---------- Skill suggestion (step 2) ----------

class SuggestedSkill(BaseModel):
    skill_id: str
    skill_name: str
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str


class SuggestedSkillList(BaseModel):
    """Structured output type the LLM agent must return."""
    suggested_skills: List[SuggestedSkill]


# ---------- Interview questions (step 3) ----------

QuestionFocus = Literal["conceptual", "codebase_specific"]


class InterviewQuestion(BaseModel):
    question_text: str
    question_focus: QuestionFocus
    expected_key_points: List[str]


class SkillQuestionSet(BaseModel):
    skill_name: str
    questions: List[InterviewQuestion]


class QuestionGenResult(BaseModel):
    """Structured output type the question-generator agent must return."""
    skill_name: str
    questions: List[InterviewQuestion]


# ---------- Outcome comparison / summary (step 4) ----------

OutcomeStatus = Literal["met", "partial", "not_met", "not_verifiable"]
AlignmentLevel = Literal["strong", "partial", "weak"]


class OutcomeEvaluation(BaseModel):
    stated_outcome: str
    status: OutcomeStatus
    evidence: str
    gap: Optional[str] = None


class Summary(BaseModel):
    overall_alignment: AlignmentLevel
    alignment_score: float = Field(ge=0.0, le=1.0)
    narrative: str
    outcome_evaluation: List[OutcomeEvaluation]
    strengths: List[str]
    gaps: List[str]


class ComparatorResult(BaseModel):
    """Structured output type the comparator agent must return."""
    overall_alignment: AlignmentLevel
    alignment_score: float = Field(ge=0.0, le=1.0)
    narrative: str
    outcome_evaluation: List[OutcomeEvaluation]
    strengths: List[str]
    gaps: List[str]


# ---------- Final report ----------

class Metadata(BaseModel):
    files_analyzed: int
    extraction_time_ms: int
    model_tokens_used: int = 0


class EvaluationReport(BaseModel):
    skills: List[SkillQuestionSet]
    summary: Summary
    metadata: Metadata


class AnalyzeResponse(BaseModel):
    project_title: str
    suggested_skills: List[SuggestedSkill]
    evaluation_report: EvaluationReport
    processing_time_ms: int

class CrossCheckFlag(BaseModel):
    skill_name: str
    reason: str


class CrossCheckResult(BaseModel):
    """Structured output type for the cross-check agent."""
    flagged_skills: List[CrossCheckFlag]
