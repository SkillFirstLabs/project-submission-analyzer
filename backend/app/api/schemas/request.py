from pydantic import BaseModel, Field
from typing import Optional

class ProjectAnalysisRequest(BaseModel):
    project_title: Optional[str] = Field(None, description="Title of the project")
    questions_per_skill: int = Field(5, description="Number of interview questions to generate per skill")
