from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class OutcomeStatus(str, Enum):
    MET = "met"
    PARTIAL = "partial"
    NOT_MET = "not_met"
    NOT_VERIFIABLE = "not_verifiable"

class SuggestedSkill(BaseModel):
    skill_id: str
    skill_name: str
    confidence: float
    rationale: str

class QuestionType(str, Enum):
    CONCEPTUAL = "conceptual"
    CODEBASE_SPECIFIC = "codebase_specific"

class Question(BaseModel):
    skill_name: str
    type: QuestionType
    text: str
    referenced_file: Optional[str] = None

class SkillQuestionGroup(BaseModel):
    skill_name: str
    questions: List[Question]

class OutcomeEvaluation(BaseModel):
    outcome_text: str
    status: OutcomeStatus
    evidence: List[str] = []
    gap: Optional[str] = None

class EvaluationSummary(BaseModel):
    overall_alignment: str
    alignment_score: float
    narrative: str
    outcome_evaluation: List[OutcomeEvaluation] = []
    strengths: List[str] = []
    gaps: List[str] = []

class EvaluationReport(BaseModel):
    skills: List[SkillQuestionGroup]
    summary: EvaluationSummary

class ProctoringEvent(BaseModel):
    session_id: str
    event_type: str
    timestamp: str
    duration_ms: Optional[float] = None
    confidence: Optional[float] = None

class Flag(BaseModel):
    type: str
    timestamp: str
    severity: Severity
    duration_ms: Optional[float] = None

class ProctoringReport(BaseModel):
    session_id: str
    id_check: str
    integrity_score: float
    risk_level: RiskLevel
    flag_summary: Dict[str, int]
    flags: List[Flag]
    narrative: str

class AnalyzeSubmissionResponse(BaseModel):
    project_title: str
    suggested_skills: List[SuggestedSkill]
    evaluation_report: EvaluationReport
    proctoring_report: Optional[ProctoringReport] = None
    metadata: Dict[str, Any]
    processing_time_ms: float
