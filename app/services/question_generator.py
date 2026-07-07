from pathlib import Path


CONCEPTUAL_QUESTIONS = {
    "Python": [
        "What are the main features of Python?",
        "Explain the difference between a list and a tuple in Python.",
        "What is exception handling in Python?"
    ],
    "FastAPI": [
        "What is FastAPI and what are its advantages?",
        "Explain the difference between GET and POST requests.",
        "What is asynchronous programming in FastAPI?"
    ],
    "PostgreSQL": [
        "What is PostgreSQL?",
        "Explain the difference between primary key and foreign key.",
        "What are SQL joins?"
    ],
    "JavaScript": [
        "What is JavaScript and where is it used?",
        "Explain the difference between let, const, and var.",
        "What is asynchronous programming in JavaScript?"
    ],
    "HTML": [
        "What is semantic HTML?",
        "Explain the basic structure of an HTML document.",
        "What is the difference between div and span elements?"
    ],
    "CSS": [
        "What is the CSS box model?",
        "Explain the difference between Flexbox and Grid.",
        "What is responsive web design?"
    ]
}


def find_relevant_file(skill_name, source_files):
    extension_map = {
        "Python": [".py"],
        "FastAPI": [".py"],
        "PostgreSQL": [".py", ".sql"],
        "JavaScript": [".js", ".jsx"],
        "HTML": [".html"],
        "CSS": [".css"]
    }

    allowed_extensions = extension_map.get(skill_name, [])

    for file_path in source_files:
        suffix = Path(file_path).suffix.lower()

        if suffix in allowed_extensions:
            return file_path

    return None


def generate_questions(
    suggested_skills,
    zip_analysis,
    questions_per_skill=2
):
    source_files = zip_analysis["source_files"]

    skill_questions = []

    for skill in suggested_skills:
        skill_name = skill["skill_name"]

        questions = []

        conceptual_list = CONCEPTUAL_QUESTIONS.get(
            skill_name,
            [f"Explain the core concepts of {skill_name}."]
        )

        # Always add one conceptual question
        questions.append(
            {
                "type": "conceptual",
                "question": conceptual_list[0]
            }
        )

        relevant_file = find_relevant_file(
            skill_name,
            source_files
        )

        # Always add one codebase-specific question
        if relevant_file:
            questions.append(
                {
                    "type": "codebase_specific",
                    "question": (
                        f"Explain how {skill_name} is used "
                        f"in the file '{relevant_file}'."
                    ),
                    "evidence_file": relevant_file
                }
            )
        else:
            questions.append(
                {
                    "type": "codebase_specific",
                    "question": (
                        f"Explain the implementation of "
                        f"{skill_name} in your project."
                    )
                }
            )

        # Add extra conceptual questions if requested
        question_index = 1

        while len(questions) < questions_per_skill:
            if question_index < len(conceptual_list):
                questions.append(
                    {
                        "type": "conceptual",
                        "question": conceptual_list[question_index]
                    }
                )

            question_index += 1

            if question_index >= len(conceptual_list):
                break

        skill_questions.append(
            {
                "skill_name": skill_name,
                "questions": questions
            }
        )

    return skill_questions