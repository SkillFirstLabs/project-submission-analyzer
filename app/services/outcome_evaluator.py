import re
from pathlib import Path


def split_outcomes(project_outcomes):
    """
    Splits numbered, bulleted, or newline-separated project outcomes.
    """

    normalized_text = re.sub(
        r"\s+(?=\d+[\.\)])",
        "\n",
        project_outcomes.strip()
    )

    lines = normalized_text.splitlines()

    outcomes = []

    for line in lines:
        cleaned_line = re.sub(
            r"^\s*(\d+[\.\)]|[-*•])\s*",
            "",
            line
        ).strip()

        if cleaned_line:
            outcomes.append(cleaned_line)

    return outcomes

def find_evidence(outcome, zip_analysis):
    """
    Searches for simple evidence related to
    the project outcome inside the ZIP.
    """

    file_tree = zip_analysis["file_tree"]
    source_files = zip_analysis["source_files"]

    outcome_lower = outcome.lower()

    evidence = []

    # Python evidence
    if "python" in outcome_lower:
        python_files = [
            file
            for file in file_tree
            if file.lower().endswith(".py")
        ]

        if python_files:
            evidence.extend(python_files[:3])

    # FastAPI / API evidence
    if (
        "fastapi" in outcome_lower
        or "api" in outcome_lower
        or "rest" in outcome_lower
    ):
        for file_path, content in source_files.items():
            content_lower = content.lower()

            if (
                "from fastapi" in content_lower
                or "import fastapi" in content_lower
                or "@app.get" in content_lower
                or "@app.post" in content_lower
                or "@app.put" in content_lower
                or "@app.delete" in content_lower
            ):
                evidence.append(file_path)

    # CRUD evidence
    if "crud" in outcome_lower:
        crud_patterns = [
            "@app.get",
            "@app.post",
            "@app.put",
            "@app.delete",
            "create",
            "read",
            "update",
            "delete"
        ]

        for file_path, content in source_files.items():
            content_lower = content.lower()

            if any(
                pattern in content_lower
                for pattern in crud_patterns
            ):
                evidence.append(file_path)

    # Database evidence
    if (
        "database" in outcome_lower
        or "postgresql" in outcome_lower
        or "sql" in outcome_lower
    ):
        database_patterns = [
            "postgresql",
            "psycopg",
            "asyncpg",
            "sqlalchemy",
            "sqlite",
            "mysql"
        ]

        for file_path, content in source_files.items():
            content_lower = content.lower()

            if any(
                pattern in content_lower
                for pattern in database_patterns
            ):
                evidence.append(file_path)

    # HTML evidence
    if "html" in outcome_lower:
        html_files = [
            file
            for file in file_tree
            if file.lower().endswith(".html")
        ]

        evidence.extend(html_files[:3])

    # CSS evidence
    if "css" in outcome_lower:
        css_files = [
            file
            for file in file_tree
            if file.lower().endswith(".css")
        ]

        evidence.extend(css_files[:3])

    # JavaScript evidence
    if "javascript" in outcome_lower:
        js_files = [
            file
            for file in file_tree
            if file.lower().endswith((".js", ".jsx"))
        ]

        evidence.extend(js_files[:3])

    # Hello World evidence for current test project
    if (
        "hello world" in outcome_lower
        or "display hello world" in outcome_lower
    ):
        for file_path, content in source_files.items():
            if "hello world" in content.lower():
                evidence.append(file_path)

    # Remove duplicate evidence
    evidence = list(dict.fromkeys(evidence))

    return evidence


def evaluate_outcomes(project_outcomes, zip_analysis):
    outcomes = split_outcomes(project_outcomes)

    outcome_evaluation = []

    met_count = 0

    strengths = []

    gaps = []

    for outcome in outcomes:
        evidence = find_evidence(
            outcome,
            zip_analysis
        )

        if evidence:
            status = "met"
            met_count += 1

            gap = None

            strengths.append(
                f"Evidence found for outcome: {outcome}"
            )

        else:
            status = "not_verifiable"

            gap = (
                "No clear supporting evidence was found "
                "in the analyzed source files."
            )

            gaps.append(
                f"No evidence found for outcome: {outcome}"
            )

        outcome_evaluation.append(
            {
                "outcome": outcome,
                "status": status,
                "evidence": evidence,
                "gap": gap
            }
        )

    total_outcomes = len(outcomes)

    if total_outcomes == 0:
        alignment_score = 0.0
    else:
        alignment_score = round(
            met_count / total_outcomes,
            2
        )

    if alignment_score >= 0.8:
        overall_alignment = "strong"

    elif alignment_score >= 0.5:
        overall_alignment = "partial"

    else:
        overall_alignment = "weak"

    if overall_alignment == "strong":
        narrative = (
            "The analyzed project shows strong alignment "
            "with the stated project outcomes. Clear source "
            "code evidence was found for most of the expected "
            "features and technologies."
        )

    elif overall_alignment == "partial":
        narrative = (
            "The analyzed project partially aligns with the "
            "stated project outcomes. Some outcomes are supported "
            "by source code evidence, while others require further "
            "implementation or mentor verification."
        )

    else:
        narrative = (
            "The analyzed project shows weak alignment with the "
            "stated project outcomes. Limited source code evidence "
            "was found, and several outcomes require further "
            "implementation or mentor verification."
        )

    return {
        "overall_alignment": overall_alignment,
        "alignment_score": alignment_score,
        "narrative": narrative,
        "outcome_evaluation": outcome_evaluation,
        "strengths": strengths,
        "gaps": gaps
    }