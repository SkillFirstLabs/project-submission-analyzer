from typing import Optional, List

from pydantic import BaseModel, Field


class ProctoringEventRequest(BaseModel):
    session_id: str
    event_type: str

    duration_ms: Optional[int] = Field(
        default=None,
        ge=0
    )

    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0
    )


class EndVivaRequest(BaseModel):
    session_id: str


class ProjectAnalysisStoreRequest(BaseModel):
    session_id: str
    project_analysis: dict


class VivaAnswer(BaseModel):
    questionNumber: int
    skillName: str
    type: str
    question: str
    answer: str
    evidenceFile: Optional[str] = None


class VivaEvaluationRequest(BaseModel):
    session_id: str
    answers: List[VivaAnswer]


class FinalAssessmentRequest(BaseModel):
    session_id: str