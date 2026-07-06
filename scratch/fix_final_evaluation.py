import re
import os

# 1. Update app/schemas.py
with open("app/schemas.py", "r", encoding="utf-8") as f:
    schemas = f.read()

if "class VivaEndRequest" not in schemas:
    new_schemas = """
class AnsweredQuestion(BaseModel):
    question: str
    answer: str = ""
    skill_name: Optional[str] = None

class VivaEndRequest(BaseModel):
    session_id: str
    answers: List[AnsweredQuestion] = []
"""
    schemas = schemas.replace("class VivaStartResponse(BaseModel):", new_schemas + "\nclass VivaStartResponse(BaseModel):")
    
    # Add Optional to imports if not there
    if "from typing import " in schemas and "Optional" not in schemas:
        schemas = schemas.replace("from typing import ", "from typing import Optional, ")
    
    with open("app/schemas.py", "w", encoding="utf-8") as f:
        f.write(schemas)


# 2. Update app/skill_engine.py
with open("app/skill_engine.py", "r", encoding="utf-8") as f:
    skill_engine = f.read()

if "def evaluate_answers" not in skill_engine:
    eval_func = """
def evaluate_answers(project_title: str, answers: List[dict]) -> EvaluationSummary:
    if not answers:
        return EvaluationSummary(
            overall_alignment="weak",
            alignment_score=0.0,
            narrative="No answers were provided during the Viva session.",
            outcome_evaluation=[]
        )
        
    system_prompt = (
        "You are an expert technical assessor grading a student's live viva session.\\n"
        "The student has uploaded a project and was asked several questions about it.\\n"
        "Evaluate their answers based on correctness, technical depth, and alignment with the project.\\n"
        "Respond strictly with a JSON object matching this schema:\\n"
        "{\\n"
        '  "overall_alignment": "strong" | "partial" | "weak",\\n'
        '  "alignment_score": float (0.0 to 1.0),\\n'
        '  "narrative": "A professional 3-5 sentence summary of their verbal performance...",\\n'
        '  "outcome_evaluation": [\\n'
        '    {\\n'
        '      "outcome": "Question or Skill assessed",\\n'
        '      "status": "met" | "partial" | "not_met",\\n'
        '      "rationale": "Short explanation"\\n'
        '    }\\n'
        '  ]\\n'
        "}\\n"
    )
    
    user_prompt = f"Project: {project_title}\\n\\nStudent Answers:\\n"
    for idx, ans in enumerate(answers):
        user_prompt += f"Q{idx+1}: {ans.get('question', '')}\\n"
        user_prompt += f"A{idx+1}: {ans.get('answer', 'No answer provided')}\\n\\n"
        
    try:
        model = genai.GenerativeModel('gemini-2.5-flash-8b', system_instruction=system_prompt)
        resp = model.generate_content(
            user_prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
            )
        )
        result = json.loads(resp.text)
        
        return EvaluationSummary(
            overall_alignment=result.get("overall_alignment", "weak"),
            alignment_score=result.get("alignment_score", 0.0),
            narrative=result.get("narrative", "Evaluation completed."),
            outcome_evaluation=[
                OutcomeEvaluation(**out) for out in result.get("outcome_evaluation", [])
            ]
        )
    except Exception as e:
        print(f"Viva evaluation failed: {e}")
        return EvaluationSummary(
            overall_alignment="partial",
            alignment_score=0.5,
            narrative="Viva evaluation failed due to a processing error.",
            outcome_evaluation=[]
        )
"""
    skill_engine += eval_func
    with open("app/skill_engine.py", "w", encoding="utf-8") as f:
        f.write(skill_engine)


# 3. Update app/main.py
with open("app/main.py", "r", encoding="utf-8") as f:
    main_py = f.read()

# Add VivaEndRequest to schemas import
if "VivaEndRequest" not in main_py:
    main_py = main_py.replace("VivaEventAck,", "VivaEventAck, VivaEndRequest, AnsweredQuestion,")

if "evaluate_answers" not in main_py:
    main_py = main_py.replace("evaluate_outcomes", "evaluate_outcomes, evaluate_answers")

# Replace viva_end
old_viva_end = """@app.post("/viva-session/end")
async def viva_end(session_id: str):
    session = get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Unknown or expired session_id.")
    if session.ended:
        raise HTTPException(status_code=400, detail="This session has already ended.")

    proctoring_report = end_session(session)
    submission = _submissions.get(session.submission_id, {})

    combined = CombinedReport(
        project_title=submission.get("project_title", "Unknown"),
        suggested_skills=submission.get("suggested_skills", []),
        evaluation_report=submission.get("evaluation_report"),
        proctoring_report=proctoring_report,
        metadata=submission.get("metadata"),
        processing_time_ms=0,
    )
    return JSONResponse(content=json.loads(combined.model_dump_json()))"""

new_viva_end = """@app.post("/viva-session/end")
async def viva_end(request: VivaEndRequest):
    session = get_session(request.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Unknown or expired session_id.")
    if session.ended:
        raise HTTPException(status_code=400, detail="This session has already ended.")

    proctoring_report = end_session(session)
    submission = _submissions.get(session.submission_id, {})

    # Evaluate the real-time viva answers
    answers_dicts = [ans.model_dump() for ans in request.answers]
    viva_summary = evaluate_answers(submission.get("project_title", "Unknown"), answers_dicts)
    
    # Update the submission's evaluation report with the new viva summary
    if "evaluation_report" in submission and submission["evaluation_report"]:
        submission["evaluation_report"].summary = viva_summary

    combined = CombinedReport(
        project_title=submission.get("project_title", "Unknown"),
        suggested_skills=submission.get("suggested_skills", []),
        evaluation_report=submission.get("evaluation_report"),
        proctoring_report=proctoring_report,
        metadata=submission.get("metadata"),
        processing_time_ms=0,
    )
    return JSONResponse(content=json.loads(combined.model_dump_json()))"""

main_py = main_py.replace(old_viva_end, new_viva_end)

with open("app/main.py", "w", encoding="utf-8") as f:
    f.write(main_py)


# 4. Update app.js
with open("static/app.js", "r", encoding="utf-8") as f:
    app_js = f.read()

old_fetch = """      const res = await fetch("/viva-session/end?session_id=" + encodeURIComponent(state.sessionId), {
        method: "POST"
      });"""

new_fetch = """      const res = await fetch("/viva-session/end", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: state.sessionId,
          answers: state.questions
        })
      });"""

app_js = app_js.replace(old_fetch, new_fetch)
app_js = app_js.replace('src="/static/app.js?v=4"', 'src="/static/app.js?v=5"') # in case we need to bump index.html, wait I already did. Let's just bump it again.

with open("static/app.js", "w", encoding="utf-8") as f:
    f.write(app_js)

with open("static/index.html", "r", encoding="utf-8") as f:
    idx = f.read()
idx = idx.replace('src="/static/app.js?v=4"', 'src="/static/app.js?v=5"')
with open("static/index.html", "w", encoding="utf-8") as f:
    f.write(idx)

print("Done updating backend and frontend for real-time viva evaluation")
