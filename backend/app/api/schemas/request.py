from pydantic import BaseModel, Field
from typing import List, Optional

class ProjectAnalysisRequest(BaseModel):
    project_title: Optional[str] = Field(None, description="Title of the project")
    project_description: Optional[str] = Field(None, description="Description of the project")
    project_outcomes: Optional[List[str]] = Field(default_factory=list, description="Target outcomes to evaluate against")
    questions_per_skill: int = Field(5, description="Number of interview questions to generate per skill")
