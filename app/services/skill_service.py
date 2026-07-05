import json
from pathlib import Path


SKILLS_FILE = Path("app/data/skills.json")


def load_skills():
    """
    Load the skill catalog.
    """
    with open(SKILLS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def detect_skills(all_code):
    """
    Detect skills using simple keyword matching.
    Returns only skills present in skills.json.
    """

    all_code = all_code.lower()

    catalog = load_skills()

    detected = []

    keyword_map = {
        "Python": [
            "import ",
            "def ",
            "print(",
            ".py"
        ],

        "FastAPI": [
            "fastapi",
            "apirouter",
            "uploadfile",
            "@app.",
            "@router."
        ],

        "PostgreSQL": [
            "postgres",
            "psycopg2",
            "postgresql"
        ]
    }

    for skill in catalog:

        skill_name = skill["skill_name"]

        keywords = keyword_map.get(skill_name, [])

        matches = 0

        for keyword in keywords:

            if keyword.lower() in all_code:
                matches += 1

        if matches > 0:

            confidence = round(matches / len(keywords), 2)

            detected.append({
                "skill_id": skill["skill_id"],
                "skill_name": skill_name,
                "confidence": confidence,
                "rationale": f"Detected {matches} matching keyword(s)."
            })

    return detected