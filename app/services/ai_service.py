"""
AI Service: calls the Gemini API with the evaluation prompt and parses
the structured JSON response into typed Pydantic models.

Responsibilities:
  1. Validate that an API key is configured before making any call.
  2. Build the prompt via the evaluation_prompt module.
  3. Call the Gemini API with retry-aware timeout handling.
  4. Parse, validate, and return the AI response as an AIAnalysisResult.
  5. Map all Gemini/JSON errors to clean HTTP exceptions the route can return.

Error mapping:
  503 SERVICE_UNAVAILABLE  – GEMINI_API_KEY not configured
  504 AI_TIMEOUT           – Gemini request timed out
  502 AI_PARSE_ERROR       – Gemini returned malformed or invalid JSON
  502 AI_ERROR             – Gemini returned an unexpected error
"""

import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List

from fastapi import HTTPException, status

from app.config import get_logger, get_settings
from app.models.evaluation import EvaluationReportModel, OutcomeEvaluationModel, SummaryModel
from app.models.evidence import Evidence
from app.models.skill import SkillModel
from app.models.viva import VivaQuestion
from app.prompts.evaluation_prompt import build_prompt, load_skills_catalog

logger = get_logger("app.services.ai_service")


@dataclass
class AIAnalysisResult:
    """
    Typed container for all AI-generated output.
    Returned by AIService.analyze() and consumed by the API route.
    """
    suggested_skills: List[SkillModel] = field(default_factory=list)
    evaluation_report: EvaluationReportModel = field(default=None)  # type: ignore[assignment]
    viva_questions: List[VivaQuestion] = field(default_factory=list)


class AIService:
    """
    Orchestrates the AI reasoning pipeline:
      Evidence → Prompt → Gemini API → Parsed EvaluationReportModel + VivaQuestions
    """

    def __init__(self) -> None:
        self._settings = get_settings()

    def analyze(
        self,
        evidence: Evidence,
        outcomes: List[str],
        questions_per_skill: int,
    ) -> AIAnalysisResult:
        """
        Run the full AI analysis pipeline.

        Args:
            evidence:            Evidence object from ProjectScanner.
            outcomes:            Parsed list of stated project outcomes.
            questions_per_skill: Number of viva questions to generate per skill.

        Returns:
            AIAnalysisResult with suggested_skills, evaluation_report, viva_questions.

        Raises:
            HTTPException 503: GEMINI_API_KEY not configured.
            HTTPException 504: Gemini request timed out.
            HTTPException 502: Gemini returned bad/unparseable JSON.
        """
        self._validate_api_key()

        # Load skills catalog
        try:
            skills_catalog = load_skills_catalog()
        except FileNotFoundError as e:
            logger.error("Skills catalog not found: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": {
                        "code": "CATALOG_MISSING",
                        "message": "Skills catalog file is missing. Contact the system administrator.",
                        "details": None,
                    }
                },
            ) from e

        # Build prompt
        prompt = build_prompt(
            evidence=evidence,
            outcomes=outcomes,
            questions_per_skill=questions_per_skill,
            skills_catalog=skills_catalog,
        )

        logger.info(
            "Sending evaluation prompt to Gemini (model=%s, prompt_chars=%d)",
            self._settings.ai.default_model,
            len(prompt),
        )

        # Call Gemini
        start_ns = time.monotonic_ns()
        raw_response = self._call_gemini(prompt)
        elapsed_ms = (time.monotonic_ns() - start_ns) // 1_000_000

        logger.info("Gemini responded in %d ms", elapsed_ms)

        # Parse and return
        return self._parse_response(raw_response)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _validate_api_key(self) -> None:
        """Raise 503 if no Gemini API key is configured."""
        if not self._settings.ai.api_key:
            logger.error(
                "GEMINI_API_KEY is not set. AI analysis cannot proceed."
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": {
                        "code": "SERVICE_UNAVAILABLE",
                        "message": (
                            "AI analysis service is unavailable: GEMINI_API_KEY is not configured. "
                            "Set GEMINI_API_KEY in your .env.local file."
                        ),
                        "details": None,
                    }
                },
            )

    def _call_gemini(self, prompt: str) -> str:
        """
        Call the Gemini API and return the raw text response.

        Uses the google-genai SDK with a configured timeout.
        Wraps all SDK errors into clean HTTP exceptions.

        Args:
            prompt: The full evaluation prompt string.

        Returns:
            Raw text response from the model.

        Raises:
            HTTPException 504: On timeout.
            HTTPException 502: On any other Gemini error.
        """
        try:
            from google import genai  # type: ignore[import]
            from google.genai import types as genai_types  # type: ignore[import]
        except ImportError as e:
            logger.error("google-genai SDK not installed: %s", e)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": {
                        "code": "SERVICE_UNAVAILABLE",
                        "message": "AI SDK not installed. Run: pip install google-genai",
                        "details": None,
                    }
                },
            ) from e

        try:
            client = genai.Client(api_key=self._settings.ai.api_key)

            response = client.models.generate_content(
                model=self._settings.ai.default_model,
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    temperature=0.2,       # Low temperature → deterministic output
                    max_output_tokens=8192,
                    response_mime_type="application/json",
                ),
            )

            return response.text

        except Exception as exc:
            exc_name = type(exc).__name__.lower()

            # Detect timeout-like exceptions by name
            if "timeout" in exc_name or "deadline" in exc_name:
                logger.error(
                    "Gemini request timed out after %d seconds: %s",
                    self._settings.ai.request_timeout_seconds,
                    exc,
                )
                raise HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail={
                        "error": {
                            "code": "AI_TIMEOUT",
                            "message": (
                                f"AI model request timed out after "
                                f"{self._settings.ai.request_timeout_seconds} seconds."
                            ),
                            "details": None,
                        }
                    },
                ) from exc

            logger.error("Gemini API error (%s): %s", type(exc).__name__, exc)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={
                    "error": {
                        "code": "AI_ERROR",
                        "message": f"AI model returned an unexpected error: {type(exc).__name__}",
                        "details": None,
                    }
                },
            ) from exc

    def _parse_response(self, raw_text: str) -> AIAnalysisResult:
        """
        Parse the raw Gemini text response into typed Pydantic models.

        Expects the response to be a valid JSON object matching the schema
        defined in evaluation_prompt.py.

        Args:
            raw_text: Raw string from Gemini (should be valid JSON).

        Returns:
            AIAnalysisResult with all fields populated.

        Raises:
            HTTPException 502: If JSON is invalid or schema is missing fields.
        """
        # Strip markdown fences if the model ignored response_mime_type
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            cleaned = "\n".join(
                line for line in lines
                if not line.strip().startswith("```")
            ).strip()

        try:
            data: Dict[str, Any] = json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(
                "Gemini returned non-JSON response (first 500 chars): %s",
                raw_text[:500],
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={
                    "error": {
                        "code": "AI_PARSE_ERROR",
                        "message": "AI model returned a response that could not be parsed as JSON.",
                        "details": None,
                    }
                },
            ) from e

        try:
            suggested_skills = self._parse_skills(data.get("suggested_skills", []))
            evaluation_report = self._parse_evaluation_report(
                data.get("evaluation_report", {})
            )
            viva_questions = self._parse_viva_questions(data.get("viva_questions", []))
        except (KeyError, TypeError, ValueError) as e:
            logger.error(
                "Gemini response schema validation failed: %s. Raw data: %s",
                e,
                str(data)[:500],
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={
                    "error": {
                        "code": "AI_PARSE_ERROR",
                        "message": (
                            "AI model response did not match the expected schema. "
                            "The analysis could not be completed."
                        ),
                        "details": None,
                    }
                },
            ) from e

        logger.info(
            "Parsed AI response: %d skills, %d outcomes, %d viva questions",
            len(suggested_skills),
            len(evaluation_report.outcome_evaluation),
            len(viva_questions),
        )

        return AIAnalysisResult(
            suggested_skills=suggested_skills,
            evaluation_report=evaluation_report,
            viva_questions=viva_questions,
        )

    # ------------------------------------------------------------------
    # Schema parsers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_skills(skills_data: List[Dict]) -> List[SkillModel]:
        """Parse a list of skill dicts into SkillModel instances."""
        skills = []
        for s in skills_data:
            try:
                skills.append(
                    SkillModel(
                        skill_id=str(s.get("skill_id", "")),
                        skill_name=str(s.get("skill_name", "")),
                        confidence=float(s.get("confidence", 0.0)),
                        rationale=str(s.get("rationale", "")),
                    )
                )
            except (TypeError, ValueError) as e:
                logger.warning("Skipping malformed skill entry: %s — %s", s, e)
        return skills

    @staticmethod
    def _parse_evaluation_report(report_data: Dict) -> EvaluationReportModel:
        """Parse the evaluation_report dict into EvaluationReportModel."""
        # Skills inside the report (same structure as suggested_skills)
        skills = []
        for s in report_data.get("skills", []):
            try:
                skills.append(
                    SkillModel(
                        skill_id=str(s.get("skill_id", "")),
                        skill_name=str(s.get("skill_name", "")),
                        confidence=float(s.get("confidence", 0.0)),
                        rationale=str(s.get("rationale", "")),
                    )
                )
            except (TypeError, ValueError):
                pass

        # Summary
        summary_data = report_data.get("summary", {})
        summary = SummaryModel(
            overall_alignment=str(summary_data.get("overall_alignment", "weak")),
            alignment_score=float(summary_data.get("alignment_score", 0.0)),
            narrative=str(summary_data.get("narrative", "")),
            strengths=[str(s) for s in summary_data.get("strengths", [])],
            gaps=[str(g) for g in summary_data.get("gaps", [])],
        )

        # Outcome evaluations
        outcome_evaluations = []
        for oe in report_data.get("outcome_evaluation", []):
            try:
                outcome_evaluations.append(
                    OutcomeEvaluationModel(
                        stated_outcome=str(oe.get("stated_outcome", "")),
                        status=str(oe.get("status", "not_verifiable")),
                        evidence=str(oe.get("evidence", "")),
                        gap=oe.get("gap") or None,
                    )
                )
            except (TypeError, ValueError) as e:
                logger.warning("Skipping malformed outcome entry: %s — %s", oe, e)

        return EvaluationReportModel(
            skills=skills,
            summary=summary,
            outcome_evaluation=outcome_evaluations,
        )

    @staticmethod
    def _parse_viva_questions(questions_data: List[Dict]) -> List[VivaQuestion]:
        """Parse viva question dicts into VivaQuestion instances."""
        questions = []
        valid_types = {"conceptual", "codebase"}

        for q in questions_data:
            try:
                q_type = str(q.get("question_type", "conceptual")).lower()
                if q_type not in valid_types:
                    q_type = "conceptual"

                questions.append(
                    VivaQuestion(
                        skill_id=str(q.get("skill_id", "")),
                        skill_name=str(q.get("skill_name", "")),
                        question_type=q_type,  # type: ignore[arg-type]
                        question=str(q.get("question", "")),
                        expected_answer_hint=str(q.get("expected_answer_hint", "")),
                    )
                )
            except (TypeError, ValueError) as e:
                logger.warning("Skipping malformed viva question: %s — %s", q, e)

        return questions
