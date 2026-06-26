# Pydantic models
from pydantic import BaseModel
from typing import List


class Skill(BaseModel):
    skill_id: str
    skill_name: str
    confidence: int
    rationale: str


class Question(BaseModel):
    skill: str
    difficulty: str
    question: str


class AnalysisResponse(BaseModel):
    project_summary: dict
    skills: List[Skill]
    questions: dict
    project_statistics: dict