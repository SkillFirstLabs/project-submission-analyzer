from app.config import (
    PROJECT_SCORE_WEIGHT,
    VIVA_SCORE_WEIGHT,
    INTEGRITY_SCORE_WEIGHT
)


def generate_final_assessment(
    project_score,
    viva_score,
    integrity_score,
    risk_level,
    strengths,
    gaps
):
    overall_score = round(
        project_score * PROJECT_SCORE_WEIGHT
        + viva_score * VIVA_SCORE_WEIGHT
        + integrity_score * INTEGRITY_SCORE_WEIGHT,
        2
    )
    if overall_score >= 80:
        performance_level = "Excellent"
        recommendation = (
            "Strong project understanding "
            "and viva performance."
        )
    elif overall_score >= 60:
        performance_level = "Good"
        recommendation = (
            "Good overall performance with "
            "some areas for improvement."
        )
    elif overall_score >= 40:
        performance_level = "Average"
        recommendation = (
            "Basic understanding demonstrated. "
            "Further improvement is recommended."
        )
    else:
        performance_level = "Needs Improvement"
        recommendation = (
            "Significant improvement is required "
            "in project understanding and viva performance."
        )
    if risk_level == "high":
        recommendation += (
            " High integrity risk was detected "
            "during the viva session."
        )
    return {
        "project_score": round(project_score, 2),
        "viva_score": round(viva_score, 2),
        "integrity_score": round(integrity_score, 2),
        "overall_score": overall_score,
        "performance_level": performance_level,
        "risk_level": risk_level,
        "recommendation": recommendation,
        "strengths": strengths,
        "gaps": gaps
    }
