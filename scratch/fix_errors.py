import re

# 1. Update app/main.py
with open("app/main.py", "r", encoding="utf-8") as f:
    main_py = f.read()

# Add empty project check
empty_proj_check = """        extracted_files = safe_extract(zip_path, workdir)
        evidence = build_evidence(workdir, extracted_files)
        
        if evidence.files_analyzed == 0:
            raise HTTPException(status_code=400, detail="Empty project: No valid source code files found in the ZIP archive.")
"""
main_py = main_py.replace("""        extracted_files = safe_extract(zip_path, workdir)\n        evidence = build_evidence(workdir, extracted_files)""", empty_proj_check)


# Add LLM Failure wrapping
llm_try = """        try:
            suggested, tokens = suggest_skills(evidence, catalog)
            total_tokens += tokens
            if not suggested:
                raise HTTPException(
                    status_code=422,
                    detail="No skills from the catalog could be matched to this codebase. "
                           "Ensure your ZIP contains relevant source code files."
                )

            questions_per_skill = 5 if len(suggested) == 1 else 2
            questions, tokens = generate_questions(evidence, suggested, questions_per_skill)
            total_tokens += tokens

            summary, tokens = evaluate_outcomes(evidence, project_title, project_description, project_outcomes)
            total_tokens += tokens
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            raise HTTPException(status_code=502, detail="LLM service failure. Please try again later.")
"""
main_py = re.sub(r'        suggested, tokens = suggest_skills\(evidence, catalog\).*?total_tokens \+= tokens\s+', llm_try, main_py, flags=re.DOTALL)

# Modify viva_event to reject dropped connections
dropped_conn = """    if session.connection_lost_flagged:
        raise HTTPException(status_code=408, detail="Proctoring connection dropped due to inactivity. Session terminated.")"""

main_py = main_py.replace("""    if session.ended:
        raise HTTPException(status_code=400, detail="This session has already ended.")""", 
"""    if session.ended:
        raise HTTPException(status_code=400, detail="This session has already ended.")
""" + dropped_conn)

with open("app/main.py", "w", encoding="utf-8") as f:
    f.write(main_py)

# 2. Update app/skill_engine.py for strict JSON / Question generation
with open("app/skill_engine.py", "r", encoding="utf-8") as f:
    skill_py = f.read()

# Enforce strict prompt
old_user = """        f"QUESTIONS PER SKILL: {questions_per_skill} minimum "
        f"(at least 1 must be type 'conceptual' and at least 1 must be type 'codebase_specific').\\n\\n"
        f"CODEBASE EVIDENCE:\\n{_evidence_prompt(evidence)}\\n\\n"
        "Return a JSON array where each item has:\\n"
        '  "skill_name" (must exactly match one of the SKILLS TO COVER),\\n'
        '  "questions": array of objects each with:\\n'
        '      "type": "conceptual" or "codebase_specific",\\n'
        '      "question": string,\\n'
        '      "references": array of file paths / symbol names the question cites '
        '(empty array for pure "conceptual" questions with no direct citation).'"""

new_user = """        f"QUESTIONS PER SKILL: {questions_per_skill} minimum "
        f"(YOU MUST GENERATE AT LEAST 1 'conceptual' AND AT LEAST 1 'codebase_specific' question per skill). "
        f"Codebase-specific questions MUST cite real file paths or symbols from the evidence.\\n\\n"
        f"CODEBASE EVIDENCE:\\n{_evidence_prompt(evidence)}\\n\\n"
        "Return a strictly valid JSON array where each item has:\\n"
        '  "skill_name" (must exactly match one of the SKILLS TO COVER),\\n'
        '  "questions": array of objects each with:\\n'
        '      "type": "conceptual" or "codebase_specific",\\n'
        '      "question": string,\\n'
        '      "references": array of file paths / symbol names the question cites '
        '(MUST NOT BE EMPTY for "codebase_specific" questions, empty for pure "conceptual" questions).'"""

skill_py = skill_py.replace(old_user, new_user)

with open("app/skill_engine.py", "w", encoding="utf-8") as f:
    f.write(skill_py)

print("Updated prompt instructions and error handling.")
