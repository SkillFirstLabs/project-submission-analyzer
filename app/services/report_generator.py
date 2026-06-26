"""
Report generator: assembles all analysis results into the final
AnalysisResponse returned to the client.
"""

import time

from app.models.schemas import (
    AnalysisResponse,
    EvaluationReport,
    ReportMetadata,
    SecurityScanResult,
    SkillWithQuestions,
    TechDetectionResult,
    ProjectTree,
)
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def build_report(
    project_title: str,
    skills_with_questions: list[SkillWithQuestions],
    evaluation_report: EvaluationReport,
    tech_detection: TechDetectionResult,
    security_scan: SecurityScanResult,
    tree: ProjectTree,
    extraction_time_ms: float,
    analysis_time_ms: float,
    total_tokens: int,
    llm_provider: str,
    request_start_time: float,
    analysis_note: str | None = None,
) -> AnalysisResponse:
    """
    Assemble the final AnalysisResponse.

    Args:
        project_title: submitted project title
        skills_with_questions: matched skills + generated questions
        evaluation_report: outcome evaluation result
        tech_detection: detected languages/frameworks/deps
        security_scan: security flag scan result
        tree: project file tree
        extraction_time_ms: ZIP extraction duration
        analysis_time_ms: full analysis pipeline duration
        total_tokens: total LLM tokens used
        llm_provider: name of LLM provider used
        request_start_time: float from time.time() at request start
        analysis_note: optional note for mentor (e.g. no skills matched)

    Returns:
        AnalysisResponse ready to serialise to JSON
    """
    processing_time_ms = round((time.time() - request_start_time) * 1000, 2)

    metadata = ReportMetadata(
        files_analyzed=tree.analyzed_files,
        skipped_files=tree.skipped_files,
        extraction_time_ms=round(extraction_time_ms, 2),
        analysis_time_ms=round(analysis_time_ms, 2),
        model_tokens_used=total_tokens,
        llm_provider=llm_provider,
    )

    # Compose analysis note — combine skill matcher note + security warning
    notes: list[str] = []
    if analysis_note:
        notes.append(analysis_note)
    if security_scan.has_high_severity:
        notes.append(
            "⚠️ High-severity security patterns were detected in the submitted code. "
            "Review the security_scan section before proceeding."
        )

    combined_note = " | ".join(notes) if notes else None

    response = AnalysisResponse(
        project_title=project_title,
        suggested_skills=skills_with_questions,
        evaluation_report=evaluation_report,
        tech_detection=tech_detection,
        security_scan=security_scan,
        metadata=metadata,
        processing_time_ms=processing_time_ms,
        analysis_note=combined_note,
    )

    logger.info("Report assembled", extra={
        "skills": len(skills_with_questions),
        "processing_time_ms": processing_time_ms,
        "tokens": total_tokens,
    })

    return response
