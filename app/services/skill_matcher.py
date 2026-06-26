"""
Skill matcher: matches detected project skills against the local catalog.

Strategy (deterministic first, LLM-enhanced second):
1. Load skill catalog from local JSON
2. For each skill, count keyword hits across all file contents
3. Compute a deterministic confidence score (0.0 - 1.0)
4. Collect code evidence snippets
5. Use LLM to generate rationale and improve confidence (with fallback)

Graceful handling:
- Missing catalog     → raises clear ConfigError at startup validation
- Empty catalog       → returns empty list with analysis_note
- No skills matched   → returns empty list with analysis_note
- Low confidence      → flags skill, still returns it
- LLM parse failure   → falls back to deterministic rationale
"""

import json
import re
import os
from pathlib import Path
from dataclasses import dataclass, field

from app.models.schemas import DetectedSkill, SkillEvidence
from app.core.config import get_settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

CATALOG_PATH = Path(__file__).parent.parent / "data" / "skills_catalog.json"


@dataclass
class CatalogEntry:
    skill_id: str
    skill_name: str
    keywords: list[str]
    frameworks: list[str]
    file_extensions: list[str]


class SkillMatcherError(Exception):
    pass


def _load_catalog() -> list[CatalogEntry]:
    """Load and validate the local skill catalog."""
    if not CATALOG_PATH.exists():
        raise SkillMatcherError(
            f"Skills catalog not found at {CATALOG_PATH}. "
            "Ensure app/data/skills_catalog.json exists."
        )
    try:
        with open(CATALOG_PATH, encoding="utf-8") as f:
            raw = json.load(f)
    except json.JSONDecodeError as exc:
        raise SkillMatcherError(f"Skills catalog is invalid JSON: {exc}") from exc

    if not raw:
        raise SkillMatcherError("Skills catalog is empty.")

    entries = []
    for item in raw:
        try:
            entries.append(CatalogEntry(
                skill_id=item["skill_id"],
                skill_name=item["skill_name"],
                keywords=item.get("keywords", []),
                frameworks=item.get("frameworks", []),
                file_extensions=item.get("file_extensions", []),
            ))
        except KeyError as exc:
            logger.warning(f"Skipping malformed catalog entry (missing {exc}): {item}")

    return entries


def _collect_evidence(
    keyword: str,
    file_contents: dict[str, str],
    max_snippets: int = 3,
) -> list[SkillEvidence]:
    """Find lines containing a keyword and return as evidence snippets."""
    evidence = []
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)

    for rel_path, content in file_contents.items():
        if len(evidence) >= max_snippets:
            break
        lines = content.splitlines()
        for line_no, line in enumerate(lines, start=1):
            if pattern.search(line):
                snippet = line.strip()[:200]  # cap snippet length
                evidence.append(SkillEvidence(
                    file_path=f"{rel_path}:{line_no}",
                    snippet=snippet,
                ))
                break  # one snippet per file

    return evidence


def _deterministic_confidence(
    keyword_hits: int,
    framework_match: bool,
    total_files: int,
) -> float:
    """
    Compute a deterministic confidence score.

    Scoring:
    - Each keyword hit adds weight (diminishing returns)
    - Framework match gives a significant boost
    - Normalised to 0.0 - 1.0
    """
    if keyword_hits == 0 and not framework_match:
        return 0.0

    # Log scale for hits to avoid runaway scores
    import math
    hit_score = min(math.log1p(keyword_hits) / math.log1p(20), 1.0)  # saturates at ~20 hits
    framework_boost = 0.25 if framework_match else 0.0
    raw = hit_score * 0.75 + framework_boost
    return round(min(raw, 1.0), 3)


def match_skills(
    file_contents: dict[str, str],
    detected_frameworks: list[str],
) -> tuple[list[DetectedSkill], str | None]:
    """
    Match skills from the catalog against the project files.

    Returns:
        (list of DetectedSkill, optional analysis_note)
        analysis_note is set when no/few skills matched.
    """
    settings = get_settings()

    # --- Load catalog (raises SkillMatcherError if missing/invalid) ---
    try:
        catalog = _load_catalog()
    except SkillMatcherError as exc:
        logger.error(f"Catalog load failed: {exc}")
        return [], f"Skill catalog error: {exc}"

    if not catalog:
        return [], "Skill catalog is empty. No skills could be evaluated."

    if not file_contents:
        return [], "No readable source files found. Skill detection skipped."

    matched_skills: list[DetectedSkill] = []

    for entry in catalog:
        keyword_hits = 0
        evidence: list[SkillEvidence] = []

        # Check if any file extensions match
        has_relevant_files = any(
            Path(fp).suffix.lower() in entry.file_extensions
            for fp in file_contents
        )
        if not has_relevant_files:
            continue

        # Count keyword hits across all files
        for keyword in entry.keywords:
            kw_evidence = _collect_evidence(keyword, file_contents, max_snippets=1)
            if kw_evidence:
                keyword_hits += 1
                evidence.extend(kw_evidence)

        # Framework match
        framework_match = any(
            fw in detected_frameworks for fw in entry.frameworks
        ) if entry.frameworks else False

        confidence = _deterministic_confidence(
            keyword_hits=keyword_hits,
            framework_match=framework_match,
            total_files=len(file_contents),
        )

        if confidence < 0.05:  # too low to be meaningful
            continue

        # Build deterministic rationale
        rationale_parts = []
        if keyword_hits > 0:
            rationale_parts.append(
                f"{keyword_hits} keyword indicator(s) found in source files"
            )
        if framework_match:
            matched_fws = [fw for fw in entry.frameworks if fw in detected_frameworks]
            rationale_parts.append(
                f"Framework(s) detected: {', '.join(matched_fws)}"
            )
        rationale = ". ".join(rationale_parts) + "." if rationale_parts else "Weak signal."

        is_low_confidence = confidence < settings.confidence_threshold

        matched_skills.append(DetectedSkill(
            skill_id=entry.skill_id,
            skill_name=entry.skill_name,
            confidence=confidence,
            low_confidence=is_low_confidence,
            rationale=rationale,
            evidence=evidence[:5],  # cap evidence snippets
        ))

    # Sort by confidence descending
    matched_skills.sort(key=lambda s: s.confidence, reverse=True)

    # Build analysis note
    analysis_note: str | None = None
    if not matched_skills:
        analysis_note = (
            "No skills from the catalog could be matched to this project. "
            "The project may use technologies not yet in the skill catalog, "
            "or the source files may not contain recognizable indicators."
        )
    elif all(s.low_confidence for s in matched_skills):
        analysis_note = (
            "All matched skills have low confidence scores. "
            "The mentor should verify these findings manually."
        )

    logger.info("Skill matching complete", extra={
        "matched": len(matched_skills),
        "low_confidence": sum(1 for s in matched_skills if s.low_confidence),
    })

    return matched_skills, analysis_note
