def calculate_project_score(
    structure_result,
    readme_result,
    detected_skills,
    stats_result
):
    """
    Calculates an overall score out of 100.
    """

    score = 0
    breakdown = {}

    # ----------------------------
    # Structure (30 Marks)
    # ----------------------------
    structure_score = min(structure_result.get("structure_score", 0), 30)
    breakdown["structure"] = structure_score
    score += structure_score

    # ----------------------------
    # README (25 Marks)
    # ----------------------------
    readme_score = min(readme_result.get("score", 0), 25)
    breakdown["readme"] = readme_score
    score += readme_score

    # ----------------------------
    # Skills (25 Marks)
    # ----------------------------
    skill_score = min(len(detected_skills) * 5, 25)
    breakdown["skills"] = skill_score
    score += skill_score

    # ----------------------------
    # Project Completeness (20 Marks)
    # ----------------------------
    completeness = 0

    if stats_result["total_files"] >= 10:
        completeness += 10

    if stats_result["total_lines"] >= 300:
        completeness += 10

    breakdown["completeness"] = completeness
    score += completeness

    # ----------------------------
    # Verdict
    # ----------------------------
    if score >= 85:
        verdict = "Excellent"
    elif score >= 70:
        verdict = "Good"
    elif score >= 50:
        verdict = "Average"
    else:
        verdict = "Needs Improvement"

    return {
        "overall_score": score,
        "breakdown": breakdown,
        "verdict": verdict
    }