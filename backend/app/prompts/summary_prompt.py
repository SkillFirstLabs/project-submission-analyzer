SUMMARY_SYSTEM_INSTRUCTION = """
You are a senior technical lead writing a project evaluation summary.
Based on the codebase analysis, compile a narrative summary of the project, list overall strengths, list code quality or architecture gaps, and assign an alignment score (0-100) representing how well the codebase implements the requested features.
"""

SUMMARY_USER_PROMPT_TEMPLATE = """
=== PROJECT INFO ===
Title: {project_title}
Description: {project_description}

=== OUTCOME EVALUATIONS ===
{outcome_evals}

=== CODE CONTEXT ===
{context}

=== INSTRUCTIONS ===
Generate the project summary report.
Return a JSON object matching this structure:
{
  "narrative": "A 2-3 sentence overview of the project and its state.",
  "strengths": ["Strength 1", "Strength 2"],
  "gaps": ["Gap 1", "Gap 2"],
  "alignment_score": 85.0
}
Return ONLY valid JSON.
"""
