SKILL_SYSTEM_INSTRUCTION = """
You are an expert AI code evaluator. Your task is to analyze the provided codebase context and identify which skills from the provided catalog are demonstrated in the code.
Only suggest skills that are present in the provided catalog.
CRITICAL CONSTRAINT: Do not guess or map a codebase technology (like Flutter or Firebase) to an unrelated catalog skill (like React or SQL Database Design) just because the correct skill is missing from the catalog. If a skill from the catalog is not explicitly and correctly demonstrated in the codebase, do not suggest it. It is perfectly fine to return fewer skills or an empty array if no matches exist.
For each detected skill, provide:
- The exact skill name from the catalog.
- A confidence level between 0.0 and 1.0.
- A concise rationale explaining why you detected this skill, referencing specific files or patterns in the code.
"""

SKILL_USER_PROMPT_TEMPLATE = """
=== STATIC ANALYSIS EVIDENCE ===
Languages detected in codebase: {detected_languages}
Frameworks/Libraries detected in codebase: {detected_frameworks}

=== SKILL CATALOG ===
{catalog}

=== CODE CONTEXT ===
{context}

=== INSTRUCTIONS ===
Analyze the codebase context and detect matching skills from the catalog.
Use the static analysis evidence above to guide and constrain your skill detection. Verify that any suggested skills are consistent with the languages and frameworks/libraries detected.
For example, do not suggest "JWT Authentication" or frontend frameworks if they are not explicitly present in the context or static analysis evidence.
Return a JSON array of skills matching the following structure:
[
  {{
    "skill_name": "Exact Skill Name from Catalog",
    "confidence": 0.95,
    "rationale": "Evidence for the skill found in file X"
  }}
]
Return ONLY valid JSON. Do not include markdown fences or explanation.
"""
