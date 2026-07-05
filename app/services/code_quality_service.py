import os


def analyze_code_quality(project_path: str):
    """
    Analyze basic code quality of the uploaded project.
    """

    total_files = 0
    empty_files = 0
    large_files = 0
    todo_count = 0

    supported_extensions = (
        ".py",
        ".java",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".cpp",
        ".c",
        ".cs",
        ".php",
        ".go",
        ".rs",
        ".html",
        ".css"
    )

    for root, _, files in os.walk(project_path):

        for file in files:

            if not file.endswith(supported_extensions):
                continue

            total_files += 1

            file_path = os.path.join(root, file)

            try:
                with open(
                    file_path,
                    "r",
                    encoding="utf-8",
                    errors="ignore"
                ) as f:

                    lines = f.readlines()

            except Exception:
                continue

            # Empty file
            if len(lines) == 0:
                empty_files += 1

            # Large file (>500 lines)
            if len(lines) > 500:
                large_files += 1

            # TODO / FIXME
            for line in lines:

                text = line.lower()

                if "todo" in text or "fixme" in text:
                    todo_count += 1

    score = 100

    score -= empty_files * 5
    score -= large_files * 3
    score -= todo_count * 2

    score = max(score, 0)

    feedback = []

    if empty_files:
        feedback.append(f"{empty_files} empty file(s) found.")

    if large_files:
        feedback.append(f"{large_files} large file(s) (>500 lines).")

    if todo_count:
        feedback.append(f"{todo_count} TODO/FIXME comment(s) found.")

    if not feedback:
        feedback.append("Good code quality.")

    return {
        "score": score,
        "total_files": total_files,
        "empty_files": empty_files,
        "large_files": large_files,
        "todo_comments": todo_count,
        "feedback": feedback
    }