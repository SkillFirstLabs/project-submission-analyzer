"""
FastAPI form dependency for analyzing project submissions.
"""

from typing import Optional
from fastapi import Form, HTTPException, status

from app.core import constants


class AnalyzeSubmissionRequest:
    """
    Dependency class to handle multipart form data validation for project submissions.
    """

    def __init__(
        self,
        project_title: str = Form(
            ...,
            max_length=200,
            description="The title of the submitted project.",
        ),
        project_description: Optional[str] = Form(
            None,
            max_length=5000,
            description="An optional brief description of the project.",
        ),
        project_outcomes: str = Form(
            ...,
            description="Stated project outcomes or objectives (e.g. newline or comma separated).",
        ),
        questions_per_skill: int = Form(
            default=constants.DEFAULT_QUESTIONS_PER_SKILL,
            ge=1,
            le=5,
            description="Number of conceptual and codebase questions to generate per skill.",
        ),
    ) -> None:
        self.project_title = project_title.strip()
        self.project_description = (
            project_description.strip() if project_description else None
        )
        self.project_outcomes = project_outcomes.strip()
        self.questions_per_skill = questions_per_skill

        # Manual validations for blank fields
        if not self.project_title:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Project title cannot be empty.",
                        "details": None,
                    }
                },
            )

        if not self.project_outcomes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Project outcomes cannot be empty.",
                        "details": None,
                    }
                },
            )
