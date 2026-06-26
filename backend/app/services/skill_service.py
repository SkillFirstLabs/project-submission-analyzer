import os
import json
import logging
from app.services.llm_client import llm_generate, parse_json_response
from app.prompts.skill_prompt import SKILL_SYSTEM_INSTRUCTION, SKILL_USER_PROMPT_TEMPLATE

logger = logging.getLogger("project_analyzer")

def detect_skills(context: str, detected_languages: list = None, detected_frameworks: list = None) -> list:
    """
    Detects skills from catalog based on the code context, guided by static analysis evidence.
    """
    catalog_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models", "skill_catalog.json")
    try:
        with open(catalog_path, "r") as f:
            catalog = json.load(f)
    except Exception:
        catalog = []
        
    langs_str = ", ".join(detected_languages) if detected_languages else "None detected"
    fws_str = ", ".join(detected_frameworks) if detected_frameworks else "None detected"
    
    catalog_str = json.dumps(catalog, indent=2)
    prompt = SKILL_USER_PROMPT_TEMPLATE.format(
        catalog=catalog_str,
        context=context,
        detected_languages=langs_str,
        detected_frameworks=fws_str
    )
    
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
        catalog_map = {s["skill_name"].lower(): s for s in catalog}
        valid_skills = []
        for s in skills:
            name_lower = s.get("skill_name", "").lower()
            if name_lower in catalog_map:
                catalog_item = catalog_map[name_lower]
                s["skill_name"] = catalog_item["skill_name"]
                s["skill_id"] = catalog_item.get("skill_id", "")
                s["category"] = catalog_item.get("category", "")
                valid_skills.append(s)
        
        # Post-filter skills based on static analysis sanity checks to avoid LLM hallucinations
        filtered_skills = []
        detected_languages_lower = [l.lower() for l in detected_languages] if detected_languages else []
        
        SKILL_LANGUAGE_MAPPING = {
            "flutter": ["dart"],
            "react native": ["javascript", "typescript"],
            "ios development": ["swift"],
            "android development": ["kotlin", "java", "dart", "javascript", "typescript"],
            "c++": ["c++"],
            "c": ["c"],
            "rust": ["rust"],
            "go": ["go"],
            "java": ["java"],
            "typescript": ["typescript"],
            "javascript": ["javascript"],
            "python": ["python"],
            "pytest": ["python"],
            "django": ["python"],
            "flask": ["python"],
            "fastapi": ["python"],
            "pandas": ["python"],
            "numpy": ["python"],
            "pytorch": ["python"],
            "tensorflow": ["python"],
            "scikit-learn": ["python"],
            "opencv": ["python", "c++", "java"],
            "spring boot": ["java"],
            "nestjs": ["typescript", "javascript"],
            "react": ["typescript", "javascript"],
            "next.js": ["typescript", "javascript"],
            "vue.js": ["typescript", "javascript"],
            "angular": ["typescript", "javascript"],
            "express.js": ["typescript", "javascript"],
            "jest": ["typescript", "javascript"],
        }

        for s in valid_skills:
            name_lower = s["skill_name"].lower()
            category = s["category"]
            
            # 1. If it's a Programming Language skill, it MUST be in the detected languages
            if category == "Programming Language":
                if name_lower not in detected_languages_lower:
                    logger.info(f"Filtering out language skill '{s['skill_name']}' because it wasn't detected in static analysis.")
                    continue
            
            # 2. Check if the required language is present
            req_langs = SKILL_LANGUAGE_MAPPING.get(name_lower)
            if req_langs:
                # check if at least one required language was detected
                has_req = any(rl in detected_languages_lower for rl in req_langs)
                if not has_req:
                    logger.info(f"Filtering out skill '{s['skill_name']}' because required languages {req_langs} were not detected.")
                    continue
            
            filtered_skills.append(s)
            
        valid_skills = filtered_skills
        

        if not valid_skills:
            if detected_languages:
                for lang in detected_languages:
                    lang_lower = lang.lower()
                    if lang_lower in catalog_map:
                        item = catalog_map[lang_lower]
                        valid_skills.append({
                            "skill_name": item["skill_name"],
                            "skill_id": item.get("skill_id", f"lang-{lang_lower}"),
                            "category": item.get("category", "Programming Language"),
                            "confidence": 1.0,
                            "rationale": f"Primary programming language detected in static analysis: {lang}."
                        })
                    else:
                        valid_skills.append({
                            "skill_name": lang,
                            "skill_id": f"lang-{lang_lower}",
                            "category": "Programming Language",
                            "confidence": 1.0,
                            "rationale": f"Programming language detected in static analysis: {lang}."
                        })
            else:
                valid_skills.append({
                    "skill_name": "Software Architecture",
                    "skill_id": "general-arch",
                    "category": "General",
                    "confidence": 0.8,
                    "rationale": "Fallback general software engineering assessment when no specific catalog skills are detected."
                })
                
        return valid_skills
    except Exception as e:
        logger.error(f"Error processing skills: {e}")
        return []
