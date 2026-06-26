import json
import logging
from app.services.llm_client import llm_generate, parse_json_response
from app.prompts.outcome_prompt import OUTCOME_SYSTEM_INSTRUCTION, OUTCOME_USER_PROMPT_TEMPLATE

logger = logging.getLogger("project_analyzer")

def evaluate_outcomes(outcomes: list, context: str) -> list:
    """
    Evaluates project outcomes against implementation.
    """
    if not outcomes:
        return []
        
    outcomes_str = json.dumps(outcomes, indent=2)
    prompt = OUTCOME_USER_PROMPT_TEMPLATE.format(outcomes=outcomes_str, context=context)
    
    raw_text = llm_generate(
        system_instruction=OUTCOME_SYSTEM_INSTRUCTION,
        user_prompt=prompt,
        temperature=0.2,
    )
    
    result = parse_json_response(raw_text)
    
    if isinstance(result, list):
        return result
    
    logger.warning(f"Outcome evaluation returned non-list: {type(result)}")
    return []
