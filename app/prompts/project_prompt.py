# Project prompt templates

PROJECT_ANALYSIS_PROMPT = """
You are a senior software architect.

Analyze the project.

Determine:

1. Project purpose
2. Domain
3. Technologies used
4. Complexity
5. Key features
6. Architecture style

Return JSON ONLY.

PROJECT DATA:

{project_data}
"""