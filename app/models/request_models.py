from pydantic import BaseModel, Field


class AnalyzeSubmissionRequest(BaseModel):
    """
    Request model for project analysis.

    Note:
    Multipart/form-data fields are received directly
    in the API endpoint. This model is mainly used
    for validation/documentation and future expansion.
    """

    project_title: str = Field(
        ...,
        min_length=3,
        max_length=200,
        description="Title of the submitted project"
    )

    project_description: str | None = Field(
        default=None,
        description="Optional project description"
    )

    project_outcomes: str = Field(
        ...,
        description="Expected project outcomes"
    )

    questions_per_skill: int = Field(
        default=2,
        ge=1,
        le=10,
        description="Number of questions per detected skill"
    )