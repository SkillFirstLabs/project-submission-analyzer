

import json
from pathlib import Path
from typing import Any, Dict, List

from app.models.evidence import Evidence

# Path to the skills catalog relative to the project root
_CATALOG_PATH = Path("skills/skills_catalog.json")

# Maximum number of file entries included in the evidence block.
# Large catalogs inflate token count without adding reasoning value.
_MAX_FILES_IN_PROMPT = 30

# Maximum number of functions/classes sent to the AI.
# Routes are always included in full (they are the most evidence-rich signals).
_MAX_CODE_ITEMS = 20


def load_skills_catalog() -> List[Dict[str, Any]]:
    """
    Load and return the skills catalog from disk.

    Returns:
        List of skill dicts, each with skill_id, skill_name, category.

    Raises:
        FileNotFoundError: If skills_catalog.json is not found.
    """
    if not _CATALOG_PATH.exists():
        raise FileNotFoundError(
            f"Skills catalog not found at '{_CATALOG_PATH}'. "
            "Ensure skills/skills_catalog.json exists in the project root."
        )
    return json.loads(_CATALOG_PATH.read_text(encoding="utf-8"))


def build_prompt(
    evidence: Evidence,
    outcomes: List[str],
    questions_per_skill: int,
    skills_catalog: List[Dict[str, Any]],
) -> str:
    """
    Build the full structured prompt for the Gemini AI model.

    Args:
        evidence:            Fully populated Evidence object from ProjectScanner.
        outcomes:            List of stated project outcome strings.
        questions_per_skill: How many viva questions to generate per skill.
        skills_catalog:      Loaded skills catalog (from load_skills_catalog()).

    Returns:
        A formatted prompt string ready to be sent to the Gemini API.
    """
    evidence_block = _build_evidence_block(evidence)
    catalog_block = json.dumps(skills_catalog, indent=2)
    outcomes_block = _build_outcomes_block(outcomes)
    output_schema = _build_output_schema()

    prompt = f"""You are a technical evaluator for a university project assessment system.
Your job is to analyse the static evidence extracted from a student's code submission
and produce a structured JSON evaluation.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 1 — PROJECT EVIDENCE (Static Analysis Output)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This JSON was produced by a deterministic static analyser.
Treat it as ground truth. Do NOT invent evidence.

```json
{evidence_block}
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 2 — AVAILABLE SKILLS CATALOG
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

You MUST only suggest skills from this catalog.
Do NOT invent skill IDs or skill names outside this list.

```json
{catalog_block}
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 3 — PROJECT INFORMATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Project Title: {evidence.project.title}
Description: {evidence.project.description or "Not provided."}

Stated Outcomes (evaluate ALL of these):
{outcomes_block}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 4 — TASK INSTRUCTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Perform the following four tasks:
CRITICAL CONSTRAINT: Do NOT use emojis anywhere in your response (narrative, rationale, strengths, gaps, questions, expected answer hints). Keep all text professional, plain, and structured.

### TASK A — SKILL DETECTION
From the Available Skills Catalog, identify which skills are demonstrated
in the evidence. For each identified skill:
- Use ONLY skills from the catalog (exact skill_id and skill_name).
- Set confidence between 0.0 and 1.0 (higher = more evidence).
- Write a rationale that cites specific evidence (file names, import names,
  class names, route paths, or dependency names from the evidence block).
- Include a minimum of 2 and maximum of 8 skills.

### TASK B — OUTCOME EVALUATION
For each stated outcome, determine:
- status: "met" | "partial" | "not_met" | "not_verifiable"
  - "met": clear evidence the outcome was implemented.
  - "partial": some evidence but incomplete implementation.
  - "not_met": the stated outcome is missing from the codebase.
  - "not_verifiable": cannot be determined from static analysis alone.
- evidence: a 1–2 sentence explanation citing specific file/class/function names.
- gap: (only if status is "partial" or "not_met") explain what is missing.

### TASK C — SUMMARY
Write an overall evaluation summary:
- overall_alignment: "strong" | "partial" | "weak"
- alignment_score: float 0.0–1.0 (weighted average of outcome statuses)
  (met=1.0, partial=0.5, not_met=0.0, not_verifiable=0.3)
- narrative: 2–3 sentences summarising the submission quality.
- strengths: list of up to 4 specific strengths backed by evidence.
- gaps: list of up to 4 specific gaps or missing implementations.

### TASK D — VIVA QUESTIONS
For each detected skill (from Task A), generate exactly {questions_per_skill} viva question(s).
Each question must be one of:
- "conceptual": tests the student's theoretical understanding of the skill.
- "codebase": asks specifically about implementation choices in THIS submission
  (reference actual file names, class names, or patterns found in the evidence).

Write expected_answer_hint for the mentor (not shown to the student).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 5 — OUTPUT FORMAT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Return ONLY a valid JSON object. Do NOT include markdown fences, prose, or
any text outside the JSON. The JSON must exactly match this schema:

{output_schema}
"""
    return prompt


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _build_evidence_block(evidence: Evidence) -> str:
    """Serialize the Evidence object to a compact, prompt-friendly JSON block."""

    # Truncate large lists to control token usage
    files_sample = [
        {"path": f.path, "language": f.language, "size": f.size}
        for f in evidence.files[:_MAX_FILES_IN_PROMPT]
    ]

    classes_sample = [
        {"name": c.name, "file": c.file}
        for c in evidence.classes[:_MAX_CODE_ITEMS]
    ]

    functions_sample = [
        {"name": f.name, "file": f.file}
        for f in evidence.functions[:_MAX_CODE_ITEMS]
    ]

    evidence_dict = {
        "statistics": {
            "total_files": evidence.statistics.total_files,
            "source_files": evidence.statistics.source_files,
            "directories": evidence.statistics.directories,
            "lines_of_code": evidence.statistics.lines_of_code,
        },
        "languages": [
            {"name": l.name, "confidence": l.confidence}
            for l in evidence.languages
        ],
        "frameworks": [
            {"name": f.name, "evidence_files": f.evidence[:5]}
            for f in evidence.frameworks
        ],
        "dependencies": [
            {"name": d.name, "version": d.version}
            for d in evidence.dependencies[:50]
        ],
        "classes": classes_sample,
        "functions": functions_sample,
        "routes": [
            {"method": r.method, "path": r.path, "file": r.file}
            for r in evidence.routes
        ],
        "testing": [
            {"framework": t.framework, "files": t.files}
            for t in evidence.testing
        ],
        "databases": [
            {"type": d.type, "evidence_files": d.evidence[:3]}
            for d in evidence.databases
        ],
        "deployment": [
            {"type": d.type, "files": d.files[:3]}
            for d in evidence.deployment
        ],
        "documentation": [
            {"type": d.type, "file": d.file}
            for d in evidence.documentation
        ],
        "configuration": [
            {"file": c.file}
            for c in evidence.configuration
        ],
        "files_sample": files_sample,
    }

    return json.dumps(evidence_dict, indent=2)


def _build_outcomes_block(outcomes: List[str]) -> str:
    """Format the outcomes list as a numbered text block."""
    if not outcomes:
        return "  (No outcomes stated)"
    return "\n".join(f"  {i + 1}. {outcome}" for i, outcome in enumerate(outcomes))


def _build_output_schema() -> str:
    """Return the strict JSON output schema as a formatted string."""
    schema = {
        "suggested_skills": [
            {
                "skill_id": "<string: from catalog>",
                "skill_name": "<string: from catalog>",
                "confidence": "<float: 0.0–1.0>",
                "rationale": "<string: cite evidence>"
            }
        ],
        "evaluation_report": {
            "skills": [
                {
                    "skill_id": "<string>",
                    "skill_name": "<string>",
                    "confidence": "<float>",
                    "rationale": "<string>"
                }
            ],
            "summary": {
                "overall_alignment": "<string: strong|partial|weak>",
                "alignment_score": "<float: 0.0–1.0>",
                "narrative": "<string: 2-3 sentences>",
                "strengths": ["<string>"],
                "gaps": ["<string>"]
            },
            "outcome_evaluation": [
                {
                    "stated_outcome": "<string: exact outcome text>",
                    "status": "<string: met|partial|not_met|not_verifiable>",
                    "evidence": "<string: cite specific evidence>",
                    "gap": "<string|null>"
                }
            ]
        },
        "viva_questions": [
            {
                "skill_id": "<string: from catalog>",
                "skill_name": "<string>",
                "question_type": "<string: conceptual|codebase>",
                "question": "<string: full question text>",
                "expected_answer_hint": "<string: mentor hint>"
            }
        ]
    }
    return json.dumps(schema, indent=2)
