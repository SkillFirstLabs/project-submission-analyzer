from pydantic import BaseModel, Field
from typing import List, Dict, Any

from app.models.project_file import ProjectFile


class ProjectContext(BaseModel):
    """
    Shared context passed through every service.
    """

    # ------------------------
    # Project Information
    # ------------------------

    project_title: str
    project_description: str = ""
    project_outcomes: str
    questions_per_skill: int = 2

    # ------------------------
    # Upload
    # ------------------------

    zip_path: str = ""
    project_id: str = ""
    extract_path: str = ""

    # ------------------------
    # Pipeline
    # ------------------------

    scanned_files: List[ProjectFile] = Field(default_factory=list)

    ranked_files: List[ProjectFile] = Field(default_factory=list)

    selected_files: List[ProjectFile] = Field(default_factory=list)

    loaded_files: List[ProjectFile] = Field(default_factory=list)

    deeply_ranked_files: List[ProjectFile] = Field(default_factory=list)

    # ------------------------
    # Detection
    # ------------------------

    language: str = ""
    framework: str = ""
    dependencies: List[str] = Field(default_factory=list)

    # ------------------------
    # Gemini Output
    # ------------------------

    suggested_skills: List[Dict[str, Any]] = Field(default_factory=list)

    evaluation_report: Dict[str, Any] = Field(default_factory=dict)

    # ------------------------
    # Metadata
    # ------------------------

    metadata: Dict[str, Any] = Field(default_factory=dict)