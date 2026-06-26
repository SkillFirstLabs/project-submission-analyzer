import os
import json
import logging
from app.services.llm_client import llm_generate, parse_json_response
from app.prompts.skill_prompt import SKILL_SYSTEM_INSTRUCTION, SKILL_USER_PROMPT_TEMPLATE

logger = logging.getLogger("project_analyzer")

def detect_skills(context: str) -> list:
    """
    Detects skills from catalog based on the code context.
    """
    catalog_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models", "skill_catalog.json")
    try:
        with open(catalog_path, "r") as f:
            catalog = json.load(f)
    except Exception:
        catalog = []
        
    catalog_str = json.dumps(catalog, indent=2)
    prompt = SKILL_USER_PROMPT_TEMPLATE.format(catalog=catalog_str, context=context)
    
    raw_text = llm_generate(
        system_instruction=SKILL_SYSTEM_INSTRUCTION,
        user_prompt=prompt,
        temperature=0.2,
    )
    
    
    skills = parse_json_response(raw_text)
    
    if not isinstance(skills, list):
        logger.warning(f"Skills detection returned non-list: {type(skills)}")
        return []
    
    try:
        catalog_names = {s["skill_name"].lower(): s["skill_name"] for s in catalog}
        valid_skills = []
        for s in skills:
            name_lower = s.get("skill_name", "").lower()
            if name_lower in catalog_names:
                s["skill_name"] = catalog_names[name_lower]
                valid_skills.append(s)
        return valid_skills
    except Exception as e:
        logger.error(f"Error processing skills: {e}")
        return []
