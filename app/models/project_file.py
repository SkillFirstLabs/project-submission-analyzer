from pydantic import BaseModel
from typing import List, Optional


class ProjectFile(BaseModel):
    """
    Represents a single file inside the uploaded project.
    """

    # Basic Information
    name: str
    path: str
    extension: str
    size: int

    # Lightweight Ranking
    score: int = 0
    reasons: List[str] = []

    # Loader
    content: str = ""
    loaded: bool = False
    line_count: int = 0
    char_count: int = 0

    # Error Handling
    error: Optional[str] = None

    # Deep Ranking
    deep_score: int = 0
    deep_reasons: List[str] = []