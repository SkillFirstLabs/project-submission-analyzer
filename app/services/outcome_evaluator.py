"""
Outcome evaluator: evaluates whether stated project outcomes are met.

Fixes:
- Uses .replace() not .format() — safe against { } in source code
- Sends file list + tech stack as concrete evidence for the LLM
- Detailed fallback builds per-outcome analysis from the codebase directly
- Graceful no-skills handling
"""

import json
import re
from pathlib import Path

from app.models.schemas import OutcomeEvaluation, EvaluationReport
from app.llm.base import BaseLLMClient
from app.core.logging_config import get_logger

logger = get_logger(__name__)

_SYSTEM_PROMPT = (
    "You are a senior technical mentor doing a detailed evaluation of an intern's project. "
    "Be specific, fair, and evidence-based. Reference actual file names and code patterns."
)

# Use a plain string — substituted with .replace() to avoid { } collision with source code
_EVAL_PROMPT = """\
Evaluate this student project submission in detail.

STATED OUTCOMES:
OUTCOMES_PLACEHOLDER

PROJECT FILES:
FILES_PLACEHOLDER

TECHNOLOGY DETECTED:
TECH_PLACEHOLDER

CODE SAMPLES (first 4000 chars of context):
CONTEXT_PLACEHOLDER

Identify overall project:
- strengths: 2-4 key technical strengths of the project implementation (e.g. good architecture, robust security, clean style)
- gaps: 2-4 key technical gaps or areas for improvement (e.g. missing error handling, lack of tests, security vulnerabilities)

For each stated outcome, evaluate:
- is_met: true or false
- confidence: 0.0 to 1.0
- evidence: exact file name or code pattern that proves it
- gaps: what is missing or incomplete

IMPORTANT: Output ONLY the raw JSON object below. No preamble, no explanation, no markdown fences.
{
  "strengths": ["specific strength with file/code reference", ...],
  "gaps": ["specific gap with explanation", ...],
  "summary": "3-4 sentence honest overall assessment mentioning key files",
  "outcome_evaluations": [
    {
      "stated_outcome": "exact outcome text",
      "is_met": true,
      "confidence": 0.8,
      "evidence": "found in routes.py line 45 — POST /items endpoint implemented",
      "gaps": []
    }
  ]
}
"""


def _build_file_summary(file_contents: dict[str, str]) -> str:
    """Build a compact file listing with sizes for the LLM."""
    lines = []
    for path, content in list(file_contents.items())[:30]:
        lines.append(f"  {path} ({len(content)} chars)")
    if len(file_contents) > 30:
        lines.append(f"  ... and {len(file_contents) - 30} more files")
    return "\n".join(lines) if lines else "  No source files found"


def _parse_eval_response(raw_text: str) -> dict | None:
    """Extract JSON object from LLM response — handles preamble/postamble text."""
    data = None
    # Try direct parse first
    try:
        data = json.loads(raw_text.strip())
    except (json.JSONDecodeError, ValueError):
        pass

    if not data:
        # Find outermost { ... }
        match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        if not match:
            return None
        try:
            data = json.loads(match.group())
        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning(f"Failed to parse evaluation JSON: {exc}")
            return None

    # Normalize key variants (handling case-insensitive search and common singular/plural names)
    if isinstance(data, dict):
        normalized = {}
        for k, v in data.items():
            normalized[k.lower().strip()] = v

        # Resolve strengths
        strengths = []
        for k in ("strengths", "strength", "key_strengths", "key_strength", "strengths_list"):
            if k in normalized:
                val = normalized[k]
                if isinstance(val, list):
                    strengths = val
                elif isinstance(val, str):
                    strengths = [val]
                break
        data["strengths"] = strengths

        # Resolve gaps
        gaps = []
        for k in ("gaps", "gap", "weaknesses", "weakness", "gaps_list", "areas_for_improvement", "areas_of_improvement"):
            if k in normalized:
                val = normalized[k]
                if isinstance(val, list):
                    gaps = val
                elif isinstance(val, str):
                    gaps = [val]
                break
        data["gaps"] = gaps

        return data
    return None


def _detailed_fallback_eval(
    outcomes_text: str,
    file_contents: dict[str, str],
) -> EvaluationReport:
    """
    Deterministic fallback when LLM is unavailable.
    Does real keyword + file analysis per outcome — not just a generic message.
    """
    from app.services.code_sanitizer import scan_project as security_scan
    from app.services.tech_detector import detect_technologies
    outcome_lines = [
        line.strip().lstrip("-•*0123456789.) ").strip()
        for line in re.split(r"[\n]", outcomes_text)
        if line.strip() and len(line.strip()) > 5
    ]

    all_content_lower = " ".join(file_contents.values()).lower()
    file_names = [Path(p).name.lower() for p in file_contents]

    # Tech keyword → indicator mappings
    TECH_INDICATORS = {
        "api": ["@app.", "router", "endpoint", "fastapi", "flask", "express", "route"],
        "database": ["sqlalchemy", "sqlite", "mongodb", "pymongo", "psycopg", "mysql", "db."],
        "authentication": ["jwt", "bcrypt", "auth", "login", "token", "password"],
        "crud": ["create", "read", "update", "delete", "post", "put", "patch", "get"],
        "test": ["pytest", "unittest", "test_", "def test", "assert "],
        "docker": ["dockerfile", "docker-compose", "from ubuntu", "from python"],
        "frontend": ["react", "vue", "angular", "html", "css", "jsx", "tsx"],
        "ml": ["model.fit", "train_test_split", "sklearn", "tensorflow", "torch", "predict"],
        "rest": ["status_code", "json()", "response", "request", "http"],
    }

    evaluations: list[OutcomeEvaluation] = []
    strengths: list[str] = []
    gaps: list[str] = []

    # Run static security scan and tech detector
    security_res = security_scan(file_contents)
    tech_res = detect_technologies(file_contents)

    for outcome in outcome_lines[:10]:
        if not outcome:
            continue

        outcome_lower = outcome.lower()
        words = [w for w in re.findall(r'\w+', outcome_lower) if len(w) > 3]

        # Find matching files
        matching_files = []
        for fpath, content in file_contents.items():
            content_lower = content.lower()
            if sum(1 for w in words if w in content_lower) >= max(1, len(words) // 3):
                matching_files.append(Path(fpath).name)

        # Find matching tech indicators
        found_indicators = []
        for tech, indicators in TECH_INDICATORS.items():
            if any(kw in outcome_lower for kw in [tech] + indicators[:2]):
                if any(ind in all_content_lower for ind in indicators):
                    found_indicators.append(tech)

        # Score
        keyword_hits = sum(1 for w in words if w in all_content_lower)
        confidence = round(min((keyword_hits / max(len(words), 1)) * 0.7 + (0.3 if found_indicators else 0), 1.0), 2)
        is_met = confidence >= 0.35

        if matching_files:
            evidence = f"Related code found in: {', '.join(matching_files[:3])}"
        elif found_indicators:
            evidence = f"Indicators of {', '.join(found_indicators)} detected in codebase"
        else:
            evidence = "No direct code evidence found for this outcome"

        if is_met:
            strengths.append(f"{outcome[:60]} — evidence in {matching_files[0] if matching_files else 'codebase'}")
        else:
            gaps.append(f"{outcome[:60]} — insufficient code evidence")

        evaluations.append(OutcomeEvaluation(
            stated_outcome=outcome,
            is_met=is_met,
            confidence=confidence,
            evidence=evidence,
            gaps=[] if is_met else ["Implementation not clearly evidenced in source files"],
        ))

    # Add general strengths/gaps based on static analysis
    
    # 1. Security Check
    if not security_res.has_high_severity:
        strengths.append("Security: No high-severity security vulnerabilities or dangerous functions (such as eval, exec, or subprocess) detected.")
    else:
        for flag in security_res.flags:
            if flag.severity == "high":
                gaps.append(f"Security: High-severity issue in {flag.file_path} - {flag.description}")

    # 2. Testing Check
    has_tests = False
    test_deps = ["pytest", "unittest", "mocha", "jest", "cypress", "junit"]
    if any(dep in "".join(tech_res.dependencies).lower() for dep in test_deps):
        has_tests = True
    if any("test" in fname for fname in file_names):
        has_tests = True
    if any(keyword in all_content_lower for keyword in ["import pytest", "import unittest", "from unittest", "describe(", " it("]):
        has_tests = True

    if has_tests:
        strengths.append("Testing: Automated tests or test frameworks detected in the codebase.")
    else:
        gaps.append("Testing: No automated unit tests or test directories detected in the codebase. Adding tests is recommended.")

    # 3. Configuration Check
    if tech_res.dependency_files_found:
        strengths.append(f"Configuration: Standard dependency configuration file (e.g. {', '.join(tech_res.dependency_files_found[:3])}) present.")
    else:
        gaps.append("Configuration: Missing standard dependency configuration file (such as requirements.txt or package.json).")

    # (No LLM-offline filler gap — static analysis already produced real gaps above)

    met = sum(1 for e in evaluations if e.is_met)
    total = len(evaluations)
    file_count = len(file_contents)

    summary = (
        f"Static analysis of {file_count} source files found evidence for {met}/{total} stated outcomes. "
        f"{'The project appears substantially complete.' if met >= total * 0.7 else 'Several outcomes lack clear implementation evidence.'} "
        "Results are based on static keyword and file analysis."
    )

    return EvaluationReport(
        strengths=strengths or ["Project ZIP submitted and parsed successfully"],
        gaps=gaps or ["Detailed evaluation unavailable — LLM not configured"],
        summary=summary,
        outcome_evaluations=evaluations,
    )


async def evaluate_outcomes(
    outcomes_text: str,
    context: str,
    file_contents: dict[str, str],
    llm_client: BaseLLMClient,
) -> tuple[EvaluationReport, int]:
    """Evaluate project outcomes. Falls back to deterministic analysis if LLM unavailable."""
    tokens_used = 0

    # Graceful no-files case
    if not file_contents:
        return EvaluationReport(
            strengths=[],
            gaps=["No source files could be read from the submission"],
            summary="Cannot evaluate outcomes — no readable source files found in the ZIP.",
            outcome_evaluations=[],
        ), 0

    try:
        if not llm_client.is_available():
            logger.info("LLM unavailable — using detailed fallback evaluation")
            return _detailed_fallback_eval(outcomes_text, file_contents), 0

        # Truncate context for local LLMs to avoid payload size errors
        try:
            from app.llm.local_llm_client import LocalLLMClient
        except ImportError:
            LocalLLMClient = None
        if LocalLLMClient and isinstance(llm_client, LocalLLMClient) and len(context) > 8000:
            logger.info("Truncating context to 8000 chars for local LLM")
            context = context[:8000]

        file_summary = _build_file_summary(file_contents)

        # Safe substitution — no .format(), avoids KeyError from { } in source code
        prompt = (
            _EVAL_PROMPT
            .replace("OUTCOMES_PLACEHOLDER", outcomes_text)
            .replace("FILES_PLACEHOLDER", file_summary)
            .replace("TECH_PLACEHOLDER", "See files above")
            .replace("CONTEXT_PLACEHOLDER", context)
        )

        response = await llm_client.generate(prompt=prompt, system_prompt=_SYSTEM_PROMPT)
        tokens_used = response.tokens_used
        data = _parse_eval_response(response.text)

        if not data:
            logger.warning("LLM eval parse failed — using detailed fallback")
            return _detailed_fallback_eval(outcomes_text, file_contents), tokens_used

        outcome_evals = []
        for item in data.get("outcome_evaluations", []):
            try:
                outcome_evals.append(OutcomeEvaluation(
                    stated_outcome=str(item.get("stated_outcome", "")),
                    is_met=bool(item.get("is_met", False)),
                    confidence=float(item.get("confidence", 0.5)),
                    evidence=str(item.get("evidence", "")),
                    gaps=item.get("gaps", []),
                ))
            except Exception as exc:
                logger.warning(f"Skipping malformed outcome: {exc}")

        # If LLM returned empty evaluations, fall back
        if not outcome_evals:
            logger.warning("LLM returned no outcome evaluations — using fallback")
            return _detailed_fallback_eval(outcomes_text, file_contents), tokens_used

        report = EvaluationReport(
            strengths=data.get("strengths", []),
            gaps=data.get("gaps", []),
            summary=str(data.get("summary", "Evaluation complete.")),
            outcome_evaluations=outcome_evals,
        )

        logger.info("Outcome evaluation complete", extra={
            "outcomes_evaluated": len(outcome_evals),
            "tokens_used": tokens_used,
        })
        return report, tokens_used

    except Exception as exc:
        logger.error(f"Outcome evaluation failed: {exc} — using detailed fallback")
        return _detailed_fallback_eval(outcomes_text, file_contents), tokens_used
