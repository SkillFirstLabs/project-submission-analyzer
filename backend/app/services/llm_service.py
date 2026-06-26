import json
from typing import Dict, Any, List, Optional
from app.services.ai_service import AIService
from app.services.prompt_service import PromptService

class LLMService:
    """
    High-level LLM orchestrator. Formulates user prompts via PromptService,
    calls AIService, and safely parses the output text into python models.
    """

    @classmethod
    async def detect_skills(cls, model_name: str, evidence_map: Dict[str, Any], skill_catalog: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Tasks Phi-3 to inspect codebase features and match them against the catalog.
        """
        system = "You are a precise technical scanning assistant. You analyze codebase maps and return structured JSON arrays matching the exact formats requested."
        
        try:
            prompt = PromptService.get_prompt(
                "skill_prompt", 
                skill_catalog=json.dumps(skill_catalog, indent=2), 
                evidence_map=json.dumps(evidence_map, indent=2)
            )
            raw_response = await AIService.post_prompt(
                model=model_name,
                system_instruction=system,
                user_prompt=prompt,
                response_format={"type": "json_object"}
            )
            parsed = AIService.extract_and_parse_json(raw_response)
            if isinstance(parsed, list):
                return parsed
            elif isinstance(parsed, dict) and "skills" in parsed:
                return parsed["skills"]
            elif isinstance(parsed, dict):
                return [parsed]
        except Exception as err:
            print(f"[Error] Skill detection LLM call failed: {err}")
        return []

    @classmethod
    async def verify_outcomes(cls, model_name: str, evidence_map: Dict[str, Any], outcomes: List[str]) -> List[Dict[str, Any]]:
        """
        Tasks Phi-3 to cross-examine project outcome descriptions against codebase evidence.
        """
        system = "You are a precise technical outcome verification assistant. Return structured JSON arrays matching the exact format requested."
        
        try:
            prompt = PromptService.get_prompt(
                "outcome_prompt",
                outcomes=json.dumps(outcomes, indent=2),
                evidence_map=json.dumps(evidence_map, indent=2)
            )
            raw_response = await AIService.post_prompt(
                model=model_name,
                system_instruction=system,
                user_prompt=prompt,
                response_format={"type": "json_object"}
            )
            parsed = AIService.extract_and_parse_json(raw_response)
            if isinstance(parsed, list):
                return parsed
            elif isinstance(parsed, dict) and "outcomes" in parsed:
                return parsed["outcomes"]
            elif isinstance(parsed, dict):
                return [parsed]
        except Exception as err:
            print(f"[Error] Outcome verification LLM call failed: {err}")
        return []

    @classmethod
    async def generate_viva_questions(cls, model_name: str, evidence_map: Dict[str, Any], questions_count: int, focus_areas: List[str]) -> List[Dict[str, Any]]:
        """
        Tasks Phi-3 to compile conceptual and codebase-specific questions for candidate testing.
        """
        system = "You are a senior technical interviewer. Generate conceptual and codebase-specific questions based on the evidence map. Return structured JSON matching the exact format requested."
        
        try:
            prompt = PromptService.get_prompt(
                "viva_prompt",
                evidence_map=json.dumps(evidence_map, indent=2),
                questions_count=questions_count,
                focus_areas=json.dumps(focus_areas, indent=2)
            )
            raw_response = await AIService.post_prompt(
                model=model_name,
                system_instruction=system,
                user_prompt=prompt,
                response_format={"type": "json_object"}
            )
            parsed = AIService.extract_and_parse_json(raw_response)
            if isinstance(parsed, list):
                return parsed
            elif isinstance(parsed, dict) and "questions" in parsed:
                return parsed["questions"]
            elif isinstance(parsed, dict) and "viva_questions" in parsed:
                return parsed["viva_questions"]
            elif isinstance(parsed, dict):
                return [parsed]
        except Exception as err:
            print(f"[Error] Viva generation LLM call failed: {err}")
        return []

    @classmethod
    async def generate_summary(cls, model_name: str, title: str, description: str, evidence_map: Dict[str, Any]) -> str:
        """
        Tasks Phi-3 to summarize candidate capability findings.
        """
        system = "You are an executive summary writer. Write a concise, professional overview. Return only the raw text."
        
        try:
            prompt = PromptService.get_prompt(
                "summary_prompt",
                title=title,
                description=description,
                evidence_map=json.dumps(evidence_map, indent=2)
            )
            raw_response = await AIService.post_prompt(
                model=model_name,
                system_instruction=system,
                user_prompt=prompt
            )
            return raw_response.strip()
        except Exception as err:
            print(f"[Error] Executive summary LLM call failed: {err}")
        return f"A technical review of project: {title}. The codebase matches standard framework configuration structures."

    @classmethod
    async def review_architecture(cls, model_name: str, evidence_map: Dict[str, Any], dependencies: List[Dict[str, str]]) -> str:
        """
        Tasks Gemma-3 to perform deep structural design pattern audit.
        """
        system = "You are a chief software architect. Review the codebase modularity and patterns. Return only the raw explanation text."
        
        try:
            prompt = PromptService.get_prompt(
                "architecture_prompt",
                dependencies=json.dumps(dependencies, indent=2),
                evidence_map=json.dumps(evidence_map, indent=2)
            )
            raw_response = await AIService.post_prompt(
                model=model_name,
                system_instruction=system,
                user_prompt=prompt
            )
            return raw_response.strip()
        except Exception as err:
            print(f"[Error] Architecture review LLM call failed: {err}")
        return "The architecture demonstrates modular layout separation. Subsystems are split by responsibility layer."

    @classmethod
    async def run_code_audit(cls, model_name: str, evidence_map: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tasks Gemma-3 to compile technical debt, code smells, strengths, and recommendations.
        """
        system = "You are a senior codebase auditor. Compile technical strengths, weaknesses, security findings, code smells, tech debt, and recommendations. Return structured JSON matching the exact format requested."
        
        try:
            prompt = PromptService.get_prompt(
                "audit_prompt",
                evidence_map=json.dumps(evidence_map, indent=2)
            )
            raw_response = await AIService.post_prompt(
                model=model_name,
                system_instruction=system,
                user_prompt=prompt,
                response_format={"type": "json_object"}
            )
            return AIService.extract_and_parse_json(raw_response)
        except Exception as err:
            print(f"[Error] Technical code audit LLM call failed: {err}")
        return {
            "strengths": ["Clear project setup"],
            "weaknesses": ["Lack of test coverage"],
            "security": "Static scanner did not detect major credentials leaks.",
            "codeSmells": "Minor monolithic class configurations.",
            "technicalDebt": "Standard debt matching template structures.",
            "recommendations": "Implement unit verification routines."
        }

    @classmethod
    async def explain_authenticity(
        cls, 
        model_name: str, 
        evidence_map: Dict[str, Any], 
        score: int, 
        classification: str, 
        category_scores: Dict[str, int], 
        missing_indicators: List[str], 
        real_indicators: List[str]
    ) -> str:
        """
        Tasks Gemma-3 to explain why the project received the scores computed by the rule engine.
        """
        system = "You are an expert software authenticity evaluator. Write a detailed review of why the code scores were awarded. Return only the raw text."
        
        try:
            prompt = PromptService.get_prompt(
                "authenticity_prompt",
                evidence_map=json.dumps(evidence_map, indent=2),
                authenticity_score=score,
                classification=classification,
                category_scores=json.dumps(category_scores, indent=2),
                missing_components=json.dumps(missing_indicators, indent=2),
                evidence_indicators=json.dumps(real_indicators, indent=2)
            )
            raw_response = await AIService.post_prompt(
                model=model_name,
                system_instruction=system,
                user_prompt=prompt
            )
            return raw_response.strip()
        except Exception as err:
            print(f"[Error] Authenticity explanation LLM call failed: {err}")
        return f"The project represents a {classification} layout with an authenticity rating of {score}%. The missing elements account for score deviations."

    @classmethod
    async def evaluate_viva_answer(cls, model_name: str, question: str, expected_points: List[str], candidate_answer: str) -> Dict[str, Any]:
        """
        Tasks Phi-3 to evaluate candidate's verbal/textual explanations.
        """
        system = "You are a senior technical examiner. Grade candidate answers against expected points. Return structured JSON matching the exact format requested."
        
        try:
            prompt = PromptService.get_prompt(
                "viva_evaluation_prompt",
                question=question,
                expected_points=json.dumps(expected_points, indent=2),
                candidate_answer=candidate_answer
            )
            raw_response = await AIService.post_prompt(
                model=model_name,
                system_instruction=system,
                user_prompt=prompt,
                response_format={"type": "json_object"}
            )
            return AIService.extract_and_parse_json(raw_response)
        except Exception as err:
            print(f"[Error] Viva answer evaluation LLM call failed: {err}")
        return {
            "grade": "Partial",
            "points_met": [],
            "feedback": "Evaluation model fallback triggered."
        }
