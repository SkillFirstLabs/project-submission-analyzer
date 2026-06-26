from pydantic import BaseModel
from typing import List

class ProjectMetadata(BaseModel):
    title: str
    description: str
    outcomes: List[str]
    questions_count: int = 5
    focus_areas: List[str] = []
