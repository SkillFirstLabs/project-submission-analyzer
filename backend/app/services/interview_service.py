import json
import logging
from app.services.llm_client import llm_generate, parse_json_response
from app.prompts.interview_prompt import INTERVIEW_SYSTEM_INSTRUCTION, INTERVIEW_USER_PROMPT_TEMPLATE

logger = logging.getLogger("project_analyzer")

def generate_interview_questions(skills: list, context: str, questions_per_skill: int = 5) -> dict:
    """
    Generates conceptual and codebase-specific questions for each skill.
    """
    if not skills:
        return {"skills": []}
        
    skills_str = json.dumps(skills, indent=2)
    prompt = INTERVIEW_USER_PROMPT_TEMPLATE.format(skills=skills_str, context=context, questions_per_skill=questions_per_skill)
    
    raw_text = llm_generate(
        system_instruction=INTERVIEW_SYSTEM_INSTRUCTION,
        user_prompt=prompt,
        temperature=0.3,
    )
    
    result = parse_json_response(raw_text)
    
    if isinstance(result, dict) and "skills" in result:
        return result
    
    logger.warning(f"Interview questions returned unexpected format: {type(result)}")
    return {"skills": []}
