import os


def analyze_readme(project_path: str):
    """
    Analyze the README.md file in the uploaded project.
    """

    readme_path = None

    # Search for README.md
    for root, _, files in os.walk(project_path):
        for file in files:
            if file.lower() == "readme.md":
                readme_path = os.path.join(root, file)
                break

    # README not found
    if readme_path is None:
        return {
            "exists": False,
            "score": 0,
            "feedback": [
                "README.md file is missing."
            ]
        }

    # Read README
    try:
        with open(readme_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception:
        return {
            "exists": True,
            "score": 0,
            "feedback": [
                "Unable to read README.md."
            ]
        }

    score = 0
    feedback = []

    length = len(content.strip())

    if length >= 100:
        score += 5
    else:
        feedback.append("README is too short.")

    lower = content.lower()

    if "installation" in lower:
        score += 5
    else:
        feedback.append("Installation section missing.")

    if "usage" in lower:
        score += 5
    else:
        feedback.append("Usage section missing.")

    if "features" in lower:
        score += 5
    else:
        feedback.append("Features section missing.")

    if "author" in lower or "license" in lower:
        score += 5
    else:
        feedback.append("Author or License section missing.")

    return {
        "exists": True,
        "score": score,
        "feedback": feedback
    }