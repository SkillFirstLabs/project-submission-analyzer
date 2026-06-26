from typing import List, Dict, Any

def build_report(
    suggested_skills: List[Dict[str, Any]],
    language_analysis: List[Dict[str, Any]],
    framework_analysis: List[Dict[str, Any]],
    interview_data: Dict[str, Any],
    summary_data: Dict[str, Any],
    metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Combines all outputs into one final structured response matching the API response schema and frontend expectations.
    """
    skills_report = []
    
    interview_skills = interview_data.get("skills", [])
    for iskill in interview_skills:
        s_name = iskill.get("skill_name", "")
        s_questions = []
        for q in iskill.get("questions", []):
            s_questions.append({
                "question_text": q.get("question_text") or q.get("question") or "",
                "expected_answer": q.get("expected_answer") or q.get("expected_answer_hint") or "",
                "topic": q.get("topic", ""),
                "difficulty": q.get("difficulty", "Medium")
            })
        skills_report.append({
            "skill_name": s_name,
            "questions": s_questions
        })
        
    evaluation_report = {
        "skills": skills_report,
        "strengths": summary_data.get("strengths", []),
        "gaps": summary_data.get("gaps", []),
        "summary": {
            "narrative": summary_data.get("narrative", ""),
            "strengths": summary_data.get("strengths", []),
            "gaps": summary_data.get("gaps", []),
            "alignment_score": float(summary_data.get("alignment_score", 75.0))
        }
    }
    
    overall_score = float(summary_data.get("alignment_score", 75.0))
    
    return {
        "overall_score": overall_score,
        "suggested_skills": suggested_skills,
        "language_analysis": language_analysis,
        "framework_analysis": framework_analysis,
        "evaluation_report": evaluation_report,
        "metadata": metadata
    }
