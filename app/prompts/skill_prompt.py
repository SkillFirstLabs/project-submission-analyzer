SKILL_MATCH_PROMPT = """
You are a strict technical evaluator.

CRITICAL RULES:
- ONLY select skills explicitly visible in project data.
- DO NOT guess programming language or frameworks.
- DO NOT infer missing technologies.
- DO NOT assume database, cloud, or backend stack.

If NO explicit evidence exists, return: {{ "skills": [] }}

PROJECT SUMMARY:
{project_summary}

PROJECT FILE TREE:
{file_tree}

CODE SAMPLES:
{code_samples}

SKILL CATALOG:
{skill_catalog}

TASK:
Return ONLY TOP 5 skills with strong evidence from project.

IMPORTANT:
- Evidence must come directly from code or file names.
- No hallucination allowed.

FORMAT (STRICT JSON ONLY),example only :
{{
  "skills": [
    {{
      "skill_id": "SK001",
      "skill_name": "Python",
      "confidence": 95,
      "evidence": "main.py uses FastAPI import",
      "rationale": "Backend built using Python FastAPI"
    }}
  ]
}}
"""