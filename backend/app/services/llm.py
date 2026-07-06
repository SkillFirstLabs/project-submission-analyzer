import json
import httpx
from typing import List, Dict, Any, Optional
from app.config import settings

class LLMServiceError(Exception):
    pass

async def call_gemini(prompt: str, system_instruction: Optional[str] = None, response_schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Call the Gemini API using httpx to ensure maximum stability and zero SDK dependency versioning issues.
    Uses the gemini-2.5-flash model (fallback to gemini-1.5-flash if needed).
    """
    api_key = settings.gemini_api_key
    if not api_key:
        # Dry run / fallback mock data if no key is configured
        print("WARNING: GEMINI_API_KEY is not set. Returning fallback mock response.")
        return {}

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    contents = {
        "parts": [{"text": prompt}]
    }
    
    generation_config = {
        "temperature": 0.2,
    }
    
    if response_schema:
        generation_config["responseMimeType"] = "application/json"
        generation_config["responseSchema"] = response_schema
    
    payload = {
        "contents": [contents],
        "generationConfig": generation_config
    }
    
    if system_instruction:
        payload["systemInstruction"] = {
            "parts": [{"text": system_instruction}]
        }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(url, json=payload)
            if response.status_code != 200:
                # Try fallback model if 2.5-flash has issues or is not in region
                if "gemini-2.5-flash" in url:
                    url_fallback = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
                    response = await client.post(url_fallback, json=payload)
                
                if response.status_code != 200:
                    raise LLMServiceError(f"Gemini API returned status {response.status_code}: {response.text}")
            
            data = response.json()
            # Extract text response
            candidates = data.get("candidates", [])
            if not candidates:
                raise LLMServiceError("No response candidates returned from Gemini API.")
            
            text_response = candidates[0]["content"]["parts"][0]["text"]
            
            # Record metadata tokens if available
            usage_metadata = data.get("usageMetadata", {})
            model_tokens_used = usage_metadata.get("totalTokenCount", 0)
            
            parsed_json = json.loads(text_response)
            return {
                "result": parsed_json,
                "tokens_used": model_tokens_used
            }
            
        except Exception as e:
            if isinstance(e, LLMServiceError):
                raise e
            raise LLMServiceError(f"Error calling Gemini API: {str(e)}")

async def analyze_project(
    project_title: str,
    project_description: str,
    project_outcomes: str,
    file_tree: List[Dict[str, Any]],
    dependencies: Dict[str, str],
    snippets: Dict[str, str],
    skill_catalog: List[Dict[str, str]],
    questions_per_skill: int = 2
) -> Dict[str, Any]:
    """
    Perform the complete project submission analysis by requesting Gemini to output:
    1. Suggested skills matching the catalog
    2. Questions per suggested skill (mix of conceptual & codebase-specific referencing real paths)
    3. Outcome evaluations (comparing evidence from snippets/file_tree against project_outcomes)
    4. Narrative summary
    """
    
    # Format inputs for LLM prompt
    catalog_str = json.dumps(skill_catalog, indent=2)
    file_tree_str = json.dumps(file_tree, indent=2)
    deps_str = json.dumps(dependencies, indent=2)
    snippets_str = ""
    for path, content in snippets.items():
        snippets_str += f"\n--- File: {path} ---\n{content}\n"

    # Define Pydantic-like Schema using OpenAPI Schema standard accepted by Gemini
    response_schema = {
        "type": "OBJECT",
        "properties": {
            "suggested_skills": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "skill_id": {"type": "STRING"},
                        "skill_name": {"type": "STRING"},
                        "confidence": {"type": "NUMBER"},
                        "rationale": {"type": "STRING"}
                    },
                    "required": ["skill_id", "skill_name", "confidence", "rationale"]
                }
            },
            "skills_questions": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "skill_name": {"type": "STRING"},
                        "questions": {
                            "type": "ARRAY",
                            "items": {
                                "type": "OBJECT",
                                "properties": {
                                    "skill_name": {"type": "STRING"},
                                    "type": {"type": "STRING", "enum": ["conceptual", "codebase_specific"]},
                                    "text": {"type": "STRING"},
                                    "referenced_file": {"type": "STRING"}
                                },
                                "required": ["skill_name", "type", "text"]
                            }
                        }
                    },
                    "required": ["skill_name", "questions"]
                }
            },
            "outcome_evaluation": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "outcome_text": {"type": "STRING"},
                        "status": {"type": "STRING", "enum": ["met", "partial", "not_met", "not_verifiable"]},
                        "evidence": {
                            "type": "ARRAY",
                            "items": {"type": "STRING"}
                        },
                        "gap": {"type": "STRING"}
                    },
                    "required": ["outcome_text", "status"]
                }
            },
            "summary": {
                "type": "OBJECT",
                "properties": {
                    "overall_alignment": {"type": "STRING", "enum": ["strong", "partial", "weak"]},
                    "alignment_score": {"type": "NUMBER"},
                    "narrative": {"type": "STRING"},
                    "strengths": {
                        "type": "ARRAY",
                        "items": {"type": "STRING"}
                    },
                    "gaps": {
                        "type": "ARRAY",
                        "items": {"type": "STRING"}
                    }
                },
                "required": ["overall_alignment", "alignment_score", "narrative", "strengths", "gaps"]
            }
        },
        "required": ["suggested_skills", "skills_questions", "outcome_evaluation", "summary"]
    }

    system_instruction = (
        "You are an expert AI code evaluator and senior mentor. Analyze the submitted project code, tree, "
        "and metadata, and map it strictly to the allowed skill catalog. Generate high-quality conceptual and "
        "codebase-specific questions, and evaluate the user's stated outcomes against codebase evidence."
    )

    prompt = f"""
    --- PROJECT METADATA ---
    Title: {project_title}
    Description: {project_description}
    Stated Outcomes (split on newlines or bullet points):
    {project_outcomes}

    --- ALLOWED SKILL CATALOG ---
    {catalog_str}

    --- FILE TREE ---
    {file_tree_str}

    --- DEPENDENCIES ---
    {deps_str}

    --- CODE SNIPPETS ---
    {snippets_str}

    --- INSTRUCTIONS ---
    1. SUGGEST SKILLS: Suggest relevant skills ONLY from the Allowed Skill Catalog. Do not invent new skills or IDs. For each skill, compute confidence (0.0 to 1.0) and include a detailed rationale referencing the code.
    2. GENERATE QUESTIONS: For each suggested skill, generate exactly {questions_per_skill} questions.
       - Ensure at least one is "conceptual" and one is "codebase_specific".
       - For "codebase_specific" questions, you MUST reference a real file from the Code Snippets or File Tree in the 'referenced_file' field and discuss actual code/logic present.
    3. OUTCOME EVALUATION: Review each item in the Stated Outcomes. Find evidence in the zip (files, imports, routes, logic) and label status: met | partial | not_met | not_verifiable. Cite specific files or modules in 'evidence'. If partial/not_met, note the gap in the 'gap' field.
    4. NARRATIVE SUMMARY: Write a 2-4 sentence overall narrative summary for the mentor. Give an overall alignment score (0.0 to 1.0). List key strengths and gaps.
    """

    # Call Gemini
    response_data = await call_gemini(prompt, system_instruction, response_schema)
    
    if not response_data:
        # Mock/Dummy fallback responses if key is missing or calls fail to allow offline work
        return get_mock_response(project_title, project_outcomes, skill_catalog)

    return response_data

def get_mock_response(project_title: str, project_outcomes: str, skill_catalog: List[Dict[str, str]]) -> Dict[str, Any]:
    # A realistic offline mock response matching the schemas
    outcomes_list = [o.strip() for o in project_outcomes.split("\n") if o.strip()]
    suggested = []
    if len(skill_catalog) > 0:
        suggested.append({
            "skill_id": skill_catalog[0]["skill_id"],
            "skill_name": skill_catalog[0]["skill_name"],
            "confidence": 0.95,
            "rationale": f"Found direct evidence of {skill_catalog[0]['skill_name']} usage in codebase imports and logic files."
        })
    if len(skill_catalog) > 1:
        suggested.append({
            "skill_id": skill_catalog[1]["skill_id"],
            "skill_name": skill_catalog[1]["skill_name"],
            "confidence": 0.85,
            "rationale": f"Identified {skill_catalog[1]['skill_name']} frameworks or dependency configurations."
        })

    skills_questions = []
    for s in suggested:
        skills_questions.append({
            "skill_name": s["skill_name"],
            "questions": [
                {
                    "skill_name": s["skill_name"],
                    "type": "conceptual",
                    "text": f"What are the core design patterns and architecture guidelines for implementing a robust app with {s['skill_name']}?"
                },
                {
                    "skill_name": s["skill_name"],
                    "type": "codebase_specific",
                    "text": f"Explain the implementation details and setup of {s['skill_name']} as observed in your entrypoint and config files.",
                    "referenced_file": "app/main.py"
                }
            ]
        })

    outcome_eval = []
    for out in outcomes_list:
        outcome_eval.append({
            "outcome_text": out,
            "status": "met",
            "evidence": ["app/main.py", "requirements.txt"],
            "gap": ""
        })

    return {
        "result": {
            "suggested_skills": suggested,
            "skills_questions": skills_questions,
            "outcome_evaluation": outcome_eval,
            "summary": {
                "overall_alignment": "strong",
                "alignment_score": 0.9,
                "narrative": f"The submission demonstrates solid alignment with the requirements of {project_title}.",
                "strengths": ["Clean structure", "Proper dependency setup"],
                "gaps": ["Lacks comprehensive unit tests"]
            }
        },
        "tokens_used": 1500
    }
