from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class SkillSuggestion(BaseModel):
    skill_name: str
    confidence: float
    rationale: str

class LanguageMetric(BaseModel):
    language: str
    loc: int
    percentage: float

class FrameworkDetection(BaseModel):
    framework: str
    confidence: float
    evidence: List[str]

class QuestionSchema(BaseModel):
    question_text: str
    expected_answer: str
    topic: str
    difficulty: str

class SkillReport(BaseModel):
    skill_name: str
    questions: List[QuestionSchema]

class ProjectSummarySchema(BaseModel):
    narrative: str
    strengths: List[str]
    gaps: List[str]
    alignment_score: float

class EvaluationReportSchema(BaseModel):
    skills: List[SkillReport]
    strengths: List[str]
    gaps: List[str]
    summary: ProjectSummarySchema

class MetadataSchema(BaseModel):
    total_files: int
    total_chunks: int
    files_analyzed: int

class ProjectAnalysisResponse(BaseModel):
    overall_score: float
    suggested_skills: List[SkillSuggestion]
    language_analysis: List[LanguageMetric]
    framework_analysis: List[FrameworkDetection]
    evaluation_report: EvaluationReportSchema
    metadata: MetadataSchema
