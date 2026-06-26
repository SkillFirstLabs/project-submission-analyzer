QUESTION_PROMPT = """
You are a senior technical interviewer.

SKILLS:

{skills}
IF skill is empty in the skills list, DO NOT generate questions for it return an empty list.
or else
Generate:

- 2 conceptual Questions
- 2 codebase_specific Questions

For each skill.

Also provide:

- expected_answer_points
- evaluation_criteria

Return JSON ONLY.

Expected Format(example only):

{{
  "questions": [
    {{
      "skill": "Python",
      "difficulty": "Easy",
      "question": "What is a list comprehension?",
      "expected_answer_points": [
        "Creates list in one line",
        "Uses loops internally"
      ],
      "evaluation_criteria": [
        "Concept clarity",
        "Example provided"
      ]
    }}
  ]
}}
"""