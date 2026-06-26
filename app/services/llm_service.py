import os
import json
import re
from typing import List, Optional
import anthropic
import httpx
from pydantic import BaseModel, Field
from app.models.project_context import ProjectContext


# Define LLM output schemas for structured response matching
class LlmSuggestedSkill(BaseModel):
    skill_name: str = Field(description="Name of the skill matching the catalog or a new skill name if not found in catalog")
    confidence: float = Field(description="Confidence score (0.0 to 1.0) for this skill suggestion")
    rationale: str = Field(description="Rationale for suggesting this skill based on file paths and code snippets in the project")
    proof_examples: List[str] = Field(default_factory=list, description="Concrete proof examples citing file paths, imports, symbols, or snippets")

class LlmQuestion(BaseModel):
    question_text: str = Field(description="The question text")
    question_focus: str = Field(description="The focus of the question: either 'conceptual' or 'codebase_specific'")
    expected_key_points: List[str] = Field(description="List of key points expected in the answer")

class LlmSkillEvaluation(BaseModel):
    skill_name: str = Field(description="Name of the skill")
    questions: List[LlmQuestion] = Field(description="At least 2 questions: 1 conceptual and 1 codebase-specific")

class LlmOutcomeEvaluation(BaseModel):
    stated_outcome: str = Field(description="Stated outcome from the user input")
    status: str = Field(description="Alignment status: met | partial | not_met | not_verifiable")
    evidence: Optional[str] = Field(description="Specific evidence from the codebase citing real files or patterns, or null")
    gap: Optional[str] = Field(description="Identified gap if status is partial or not_met, or null")

class LlmSummary(BaseModel):
    overall_alignment: str = Field(description="Overall alignment status: strong | partial | weak")
    alignment_score: float = Field(description="Alignment score from 0.0 to 1.0")
    narrative: str = Field(description="A 2-4 sentence narrative explanation in plain English for the mentor")
    outcome_evaluation: List[LlmOutcomeEvaluation] = Field(description="Evaluation of each stated outcome")
    strengths: List[str] = Field(description="List of strengths identified in the project")
    gaps: List[str] = Field(description="List of gaps identified in the project")

class LlmEvaluationOutput(BaseModel):
    suggested_skills: List[LlmSuggestedSkill]
    evaluation_report_skills: List[LlmSkillEvaluation]
    summary: LlmSummary


class GeminiService:

    def __init__(self):
        self.client = None
        self.model = None
        self._initialized = False

    def _ensure_initialized(self):
        """Lazy initialization of the LLM client"""
        if self._initialized:
            return
        
        provider = os.getenv("LLM_PROVIDER", "gemini").lower()
        
        if provider == "gemini":
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY environment variable is not set. Please provide it in your .env file.")
            
            self.client = api_key
            self.model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        
        elif provider == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable is not set. Please provide it in your .env file.")
            
            self.client = anthropic.Anthropic(
                api_key=api_key,
                base_url=os.getenv("ANTHROPIC_API_BASE_URL", "https://api.anthropic.com"),
                http_client=httpx.Client(verify=self._verify_ssl(), timeout=60.0)
            )
            self.model = os.getenv("ANTHROPIC_MODEL", "claude-opus-4-1-20250805")
        
        elif provider == "openai":
            self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

        elif provider == "groq":
            self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        
        else:
            raise ValueError("LLM_PROVIDER must be one of: gemini, anthropic, openai, groq.")
        
        self._initialized = True

    def _verify_ssl(self) -> bool:
        return os.getenv("LLM_VERIFY_SSL", "true").strip().lower() not in {
            "0",
            "false",
            "no",
            "off",
        }

    def _has_negative_evidence(self, text: str) -> bool:
        lowered = (text or "").lower()
        negative_phrases = [
            "no evidence",
            "not used",
            "not found",
            "does not use",
            "is not used",
            "no indication",
            "not present",
            "absent",
        ]
        return any(phrase in lowered for phrase in negative_phrases)

    def _default_questions(self, skill_name: str, target_count: int = 2) -> list:
        questions = [
            {
                "question_text": f"What are the core concepts behind {skill_name}, and when would you choose it in a project?",
                "question_focus": "conceptual",
                "expected_key_points": ["Core concepts", "Appropriate use cases", "Trade-offs"]
            },
            {
                "question_text": f"Where is {skill_name} used in this codebase, and how would you improve that implementation?",
                "question_focus": "codebase_specific",
                "expected_key_points": ["Relevant files or imports", "Current implementation", "Possible improvements"]
            }
        ]
        while len(questions) < target_count:
            questions.append({
                "question_text": f"What risks or limitations should a developer consider when using {skill_name} in this project?",
                "question_focus": "conceptual" if len(questions) % 2 == 0 else "codebase_specific",
                "expected_key_points": ["Risks", "Limitations", "Practical improvements"]
            })
        return questions

    def _normalize_questions(self, skill_name: str, questions: list, target_count: int = 2) -> list:
        normalized = []
        for q in questions or []:
            question_text = (q.get("question_text") or "").strip()
            if not question_text:
                continue

            question_focus = (q.get("question_focus") or "").strip()
            if question_focus not in {"conceptual", "codebase_specific"}:
                question_focus = "conceptual" if not normalized else "codebase_specific"

            expected_key_points = q.get("expected_key_points") or []
            if not isinstance(expected_key_points, list):
                expected_key_points = [str(expected_key_points)]

            normalized.append({
                "question_text": question_text,
                "question_focus": question_focus,
                "expected_key_points": [str(point) for point in expected_key_points if str(point).strip()]
            })

        has_conceptual = any(q["question_focus"] == "conceptual" for q in normalized)
        has_codebase = any(q["question_focus"] == "codebase_specific" for q in normalized)

        defaults = self._default_questions(skill_name, target_count)
        if not has_conceptual:
            normalized.insert(0, defaults[0])
        if not has_codebase:
            normalized.append(defaults[1])
        while len(normalized) < target_count:
            normalized.append(defaults[len(normalized)])

        return normalized[: max(2, target_count)]

    def _canonical_skill_key(self, value: str) -> str:
        key = re.sub(r"[^a-z0-9]+", "", (value or "").lower())
        aliases = {
            "next": "nextjs",
            "nextjs": "nextjs",
            "javascript": "javascript",
            "js": "javascript",
            "mysql": "mysql",
            "postgres": "postgresql",
            "postgrease": "postgresql",
            "postgresql": "postgresql",
            "auth": "authentication",
            "login": "authentication",
        }
        return aliases.get(key, key)

    def _find_file_evidence(self, outcome: str, llm_context: dict) -> Optional[str]:
        terms = self._skill_search_terms(outcome)
        evidence = []

        for file_info in llm_context.get("files", []):
            path = file_info.get("path") or file_info.get("file_name") or ""
            content = file_info.get("content") or ""
            searchable = f"{path}\n{content}".lower()
            matched_term = next((term for term in terms if term.lower() in searchable), None)
            if matched_term:
                evidence.append(f"{path}: contains '{matched_term}' related to {outcome}.")
            if len(evidence) >= 3:
                break

        return "; ".join(evidence) if evidence else None

    def _find_outcome_evidence(self, outcome: str, suggested_skills: list, llm_context: dict) -> Optional[dict]:
        outcome_key = self._canonical_skill_key(outcome)
        if not outcome_key:
            return None

        for skill in suggested_skills:
            skill_name = skill.get("skill_name", "")
            if self._canonical_skill_key(skill_name) != outcome_key:
                continue

            proof_examples = skill.get("proof_examples", [])
            evidence = "; ".join(proof_examples) if proof_examples else skill.get("rationale")
            return {
                "status": "met" if evidence else "partial",
                "evidence": evidence or f"{skill_name} was detected as a suggested skill.",
                "gap": None if evidence else "The skill was detected, but concrete proof examples were limited."
            }

        if evidence := self._find_file_evidence(outcome, llm_context):
            return {
                "status": "met",
                "evidence": evidence,
                "gap": None
            }

        return None

    def _normalize_outcome_evaluation(self, raw_items: list, parsed_outcomes: List[str], suggested_skills: list, llm_context: dict) -> list:
        allowed_statuses = {"met", "partial", "not_met", "not_verifiable"}
        by_outcome = {}

        for item in raw_items or []:
            stated_outcome = (item.get("stated_outcome") or "").strip()
            if not stated_outcome:
                continue

            status = (item.get("status") or "not_verifiable").strip()
            if status not in allowed_statuses:
                status = "not_verifiable"

            by_outcome[stated_outcome] = {
                "stated_outcome": stated_outcome,
                "status": status,
                "evidence": item.get("evidence"),
                "gap": item.get("gap")
            }

        normalized = []
        for outcome in parsed_outcomes:
            if outcome in by_outcome:
                normalized.append(by_outcome[outcome])
            elif inferred := self._find_outcome_evidence(outcome, suggested_skills, llm_context):
                normalized.append({
                    "stated_outcome": outcome,
                    "status": inferred["status"],
                    "evidence": inferred["evidence"],
                    "gap": inferred["gap"]
                })
            else:
                normalized.append({
                    "stated_outcome": outcome,
                    "status": "not_verifiable",
                    "evidence": None,
                    "gap": "No code evidence was found for this stated outcome in the analyzed files."
                })

        return normalized

    def _skill_search_terms(self, skill_name: str) -> list:
        terms = {skill_name.lower()}
        aliases = {
            "jwt": ["jwt", "jsonwebtoken", "pyjwt", "jose"],
            "authentication": ["auth", "authentication", "login", "session", "jwt", "middleware"],
            "backend routes": ["route.ts", "routes", "router", "next/server", "api/"],
            "database": ["database", ".sql", "schema", "supabase", "postgres", "postgresql", "mysql", "prisma"],
            "next": ["next", "next/server", "next.config", "next.js"],
            "javascript": ["javascript", "js", "package.json"],
            "typescript": ["typescript", "tsconfig", ".ts", ".tsx"],
            "react": ["react", "jsx", "tsx"],
            "node.js": ["node", "node.js", "next/server", "express"],
            "fastapi": ["fastapi", "APIRouter"],
            "postgresql": ["postgres", "postgresql", "psycopg", "pg"],
            "mysql": ["mysql", "jdbc:mysql"],
            "supabase": ["supabase", "@supabase/supabase-js"],
            "java": ["java", "public class", ".java"],
            "spring boot": ["springboot", "spring boot", "@SpringBootApplication", "@RestController"],
            "rest api design": ["@app.", "APIRouter", "@RestController", "router.", "GET", "POST", "PUT", "DELETE"],
            "git": [".gitignore"],
        }
        terms.update(aliases.get(skill_name.lower(), []))
        return [term for term in terms if term]

    def _extract_proof_examples(self, skill_name: str, item: dict, llm_context: dict) -> list:
        proof_examples = []

        raw_proof = item.get("proof_examples") or item.get("evidence") or []
        if isinstance(raw_proof, str):
            raw_proof = [raw_proof]
        if isinstance(raw_proof, list):
            proof_examples.extend(str(proof).strip() for proof in raw_proof if str(proof).strip())

        rationale = item.get("rationale", "")
        for path in re.findall(r"[\w./\\-]+\.[A-Za-z0-9]+", rationale):
            proof_examples.append(f"{path}: cited in skill rationale.")

        terms = self._skill_search_terms(skill_name)
        for file_info in llm_context.get("files", []):
            path = file_info.get("path") or file_info.get("file_name") or ""
            content = file_info.get("content") or ""
            searchable = f"{path}\n{content}".lower()
            matched_term = next((term for term in terms if term.lower() in searchable), None)
            if matched_term:
                proof_examples.append(f"{path}: contains evidence for {skill_name} via '{matched_term}'.")
            if len(proof_examples) >= 3:
                break

        deduped = []
        seen = set()
        for proof in proof_examples:
            if proof and proof not in seen:
                seen.add(proof)
                deduped.append(proof)
        return deduped[:3]

    def _infer_project_summary(self, context: ProjectContext, suggested_skills: list, llm_context: dict) -> dict:
        file_paths = [file_info.get("path", "") for file_info in llm_context.get("files", [])]
        lower_paths = " ".join(file_paths).lower()
        technologies = [skill["skill_name"] for skill in suggested_skills]
        outcomes = context.metadata.get("parsed_outcomes", [])

        if any(part in lower_paths for part in ["controller", "service", "repository", "routes", "models"]):
            architecture_style = "Layered Architecture"
        elif any(part in lower_paths for part in ["pages", "app/", "components"]):
            architecture_style = "Component-Based Web Architecture"
        else:
            architecture_style = "Not clearly identifiable from selected files"

        file_count = len(context.scanned_files)
        if file_count <= 8:
            complexity = "Low"
        elif file_count <= 30:
            complexity = "Low to Medium"
        elif file_count <= 100:
            complexity = "Medium"
        else:
            complexity = "Medium to High"

        return {
            "project_purpose": context.project_title,
            "domain": self._infer_domain(context.project_title, context.project_description, outcomes),
            "description": context.project_description or "",
            "technologies_used": technologies,
            "complexity": complexity,
            "key_features": outcomes,
            "architecture_style": architecture_style
        }

    def _infer_domain(self, title: str, description: str, outcomes: List[str]) -> str:
        text = f"{title} {description} {' '.join(outcomes)}".lower()
        domain_keywords = [
            ("Education", ["student", "school", "college", "course", "learning", "education"]),
            ("E-commerce", ["shop", "cart", "order", "payment", "product", "inventory"]),
            ("Healthcare", ["health", "patient", "doctor", "medical", "hospital"]),
            ("Finance", ["bank", "payment", "invoice", "finance", "accounting"]),
            ("Developer Tools", ["api", "backend", "authentication", "database", "dashboard"]),
        ]
        for domain, keywords in domain_keywords:
            if any(keyword in text for keyword in keywords):
                return domain
        return "General Software"

    def _repair_summary_against_inputs(self, raw_summary: dict, outcome_evaluation: list) -> dict:
        met_or_partial = [item for item in outcome_evaluation if item["status"] in {"met", "partial"}]
        not_met = [item for item in outcome_evaluation if item["status"] in {"not_met", "not_verifiable"}]

        strengths = []
        for item in met_or_partial:
            if item.get("evidence"):
                strengths.append(f"{item['stated_outcome']} is {item['status']} with evidence: {item['evidence']}")

        gaps = []
        for item in not_met:
            gaps.append(f"{item['stated_outcome']} is not fully evidenced: {item.get('gap') or 'No matching code evidence found.'}")
        for item in met_or_partial:
            if item["status"] == "partial" and item.get("gap"):
                gaps.append(f"{item['stated_outcome']} is only partially met: {item['gap']}")

        if not strengths:
            strengths = raw_summary.get("strengths", [])[:3]
        if not gaps:
            gaps = raw_summary.get("gaps", [])[:3]

        if met_or_partial and not not_met:
            overall_alignment = "strong"
            alignment_score = 0.9
        elif met_or_partial:
            overall_alignment = "partial"
            alignment_score = 0.65
        else:
            overall_alignment = "weak"
            alignment_score = 0.25

        return {
            "overall_alignment": overall_alignment,
            "alignment_score": alignment_score,
            "narrative": (
                "The evaluation is based on the submitted project outcomes and description, "
                "with each judgment tied to evidence found in the analyzed files."
            ),
            "outcome_evaluation": outcome_evaluation,
            "strengths": strengths[:3],
            "gaps": gaps[:3]
        }

    def process(self, context: ProjectContext) -> ProjectContext:
        # Ensure client is initialized before processing
        self._ensure_initialized()
        
        llm_context = context.metadata.get("llm_context")
        if not llm_context:
            raise ValueError("LLM context not found. Build context first.")

        # Determine catalog path
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        catalog_path = os.path.join(base_dir, "catalog", "skills.json")

        # Load skill catalog
        if not os.path.exists(catalog_path):
            raise FileNotFoundError(f"Skill catalog not found at {catalog_path}")

        try:
            with open(catalog_path, "r", encoding="utf-8") as f:
                catalog = json.load(f)
        except Exception as e:
            raise ValueError(f"Invalid catalog JSON format: {str(e)}")

        catalog_map = {item["skill_name"].lower(): item for item in catalog}
        catalog_info = "\n".join([f"- {item['skill_name']} (ID: {item['skill_id']})" for item in catalog])

        parsed_outcomes = context.metadata.get("parsed_outcomes", [])
        if not parsed_outcomes:
            parsed_outcomes = [o.strip() for o in context.project_outcomes.split("\n") if o.strip()]
        target_questions = max(2, int(context.questions_per_skill or 2))

        prompt = self._build_prompt(llm_context, catalog_info, parsed_outcomes, target_questions)

        # Check LLM Provider
        provider = os.getenv("LLM_PROVIDER", "gemini").lower()

        try:
            if provider == "openai":
                result, tokens_used = self._call_openai(prompt)
            elif provider == "groq":
                result, tokens_used = self._call_groq(prompt)
            elif provider == "anthropic":
                result, tokens_used = self._call_anthropic(prompt)
            else:
                result, tokens_used = self._call_gemini(prompt)

            # Map responses and handle dynamic catalog additions
            suggested_skills = []
            catalog_updated = False

            for item in result.get("suggested_skills", []):
                skill_name = item.get("skill_name", "").strip()
                if not skill_name:
                    continue
                if self._has_negative_evidence(item.get("rationale", "")):
                    continue
                
                lower_name = skill_name.lower()
                if lower_name in catalog_map:
                    mapped_skill = catalog_map[lower_name]
                    skill_id = mapped_skill["skill_id"]
                    skill_name = mapped_skill["skill_name"]
                else:
                    # Dynamically add to catalog
                    max_num = 0
                    for cat_item in catalog:
                        id_str = cat_item.get("skill_id", "")
                        if id_str.startswith("sk-") and id_str[3:].isdigit():
                            max_num = max(max_num, int(id_str[3:]))
                    new_num = max_num + 1
                    new_id = f"sk-{new_num:03d}"
                    
                    new_skill = {
                        "skill_id": new_id,
                        "skill_name": skill_name,
                        "category": "Discovered"
                    }
                    catalog.append(new_skill)
                    catalog_map[lower_name] = new_skill
                    catalog_updated = True
                    skill_id = new_id

                proof_examples = self._extract_proof_examples(skill_name, item, llm_context)
                
                suggested_skills.append({
                    "skill_id": skill_id,
                    "skill_name": skill_name,
                    "confidence": max(0.0, min(1.0, float(item.get("confidence", 1.0)))),
                    "rationale": item.get("rationale", ""),
                    "proof_examples": proof_examples
                })

            if catalog_updated:
                try:
                    with open(catalog_path, "w", encoding="utf-8") as f:
                        json.dump(catalog, f, indent=2)
                except Exception as cat_err:
                    raise RuntimeError(f"Failed to write new skills to catalog: {str(cat_err)}")

            skills_eval = []
            suggested_skill_names = {item["skill_name"].lower() for item in suggested_skills}
            suggested_proof_examples = {
                item["skill_name"].lower(): item.get("proof_examples", [])
                for item in suggested_skills
            }
            for item in result.get("evaluation_report_skills", []):
                skill_name = item.get("skill_name", "").strip()
                if not skill_name:
                    continue
                if skill_name.lower() in catalog_map:
                    skill_name = catalog_map[skill_name.lower()]["skill_name"]
                if suggested_skill_names and skill_name.lower() not in suggested_skill_names:
                    continue

                questions = self._normalize_questions(skill_name, item.get("questions", []), target_questions)
                
                skills_eval.append({
                    "skill_name": skill_name,
                    "proof_examples": suggested_proof_examples.get(skill_name.lower(), []),
                    "questions": questions
                })

            existing_eval_names = {item["skill_name"].lower() for item in skills_eval}
            for suggested in suggested_skills:
                if suggested["skill_name"].lower() not in existing_eval_names:
                    skills_eval.append({
                        "skill_name": suggested["skill_name"],
                        "proof_examples": suggested.get("proof_examples", []),
                        "questions": self._default_questions(suggested["skill_name"], target_questions)
                    })

            raw_summary = result.get("summary", {})
            outcome_evaluation = self._normalize_outcome_evaluation(
                raw_summary.get("outcome_evaluation", []),
                parsed_outcomes,
                suggested_skills,
                llm_context
            )
            summary = self._repair_summary_against_inputs(raw_summary, outcome_evaluation)

            context.suggested_skills = suggested_skills
            context.metadata["project_summary"] = self._infer_project_summary(
                context,
                suggested_skills,
                llm_context
            )
            context.metadata["project_statistics"] = {
                "files_analyzed": len(context.deeply_ranked_files),
                "dependencies_found": len(context.dependencies),
                "code_samples_used": len(context.loaded_files)
            }
            context.evaluation_report = {
                "skills": skills_eval,
                "summary": summary,
                "metadata": {
                    "files_analyzed": len(context.deeply_ranked_files),
                    "extraction_time_ms": context.metadata.get("extraction_time_ms", 0),
                    "model_tokens_used": tokens_used
                }
            }

            context.metadata["llm_response"] = result

        except Exception as e:
            if isinstance(e, (FileNotFoundError, ValueError)):
                raise e
            raise RuntimeError(f"LLM API failed: {str(e)}")

        return context

    def _call_gemini(self, prompt: str) -> (dict, int):
        model = self.model
        if model.startswith("models/"):
            model = model.split("/", 1)[1]

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        json_prompt = f"""{prompt}

Return ONLY valid JSON that matches this exact top-level structure:
{{
  "suggested_skills": [],
  "evaluation_report_skills": [],
  "summary": {{
    "overall_alignment": "strong|partial|weak",
    "alignment_score": 0.0,
    "narrative": "",
    "outcome_evaluation": [],
    "strengths": [],
    "gaps": []
  }}
}}
"""
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": json_prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json"
            }
        }

        with httpx.Client(timeout=60.0, verify=self._verify_ssl()) as client:
            response = client.post(
                url,
                params={"key": self.client},
                json=payload
            )

        if response.status_code != 200:
            raise RuntimeError(f"Gemini API failed with status {response.status_code}: {response.text}")

        response_data = response.json()
        completion_text = response_data["candidates"][0]["content"]["parts"][0]["text"]
        result = json.loads(completion_text)
        usage_metadata = response_data.get("usageMetadata", {})
        tokens_used = usage_metadata.get("totalTokenCount") or (
            usage_metadata.get("promptTokenCount", 1000)
            + usage_metadata.get("candidatesTokenCount", 1000)
        )
        return result, tokens_used

    def _call_anthropic(self, prompt: str) -> (dict, int):
        """Call Claude Opus via Anthropic API with JSON response mode."""
        
        # Construct the system prompt for structured JSON output
        system_prompt = """You are an expert AI software engineering assessor and skill evaluator.
Your task is to return a valid JSON response that strictly conforms to this structure:
{
    "suggested_skills": [
        {
            "skill_name": "string",
            "confidence": number (0.0 to 1.0),
            "rationale": "string",
            "proof_examples": ["file path or code evidence string"]
        }
    ],
    "evaluation_report_skills": [
        {
            "skill_name": "string",
            "questions": [
                {
                    "question_text": "string",
                    "question_focus": "conceptual|codebase_specific",
                    "expected_key_points": ["string"]
                }
            ]
        }
    ],
    "summary": {
        "overall_alignment": "strong|partial|weak",
        "alignment_score": number (0.0 to 1.0),
        "narrative": "string",
        "outcome_evaluation": [
            {
                "stated_outcome": "string",
                "status": "met|partial|not_met|not_verifiable",
                "evidence": "string or null",
                "gap": "string or null"
            }
        ],
        "strengths": ["string"],
        "gaps": ["string"]
    }
}

IMPORTANT: Return ONLY valid JSON, no markdown formatting, no extra text."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.2,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # Parse the response
            response_text = response.content[0].text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            result = json.loads(response_text)
            
            # Calculate tokens used
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            
            return result, tokens_used
        
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse Anthropic API response as JSON: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Anthropic API failed: {str(e)}")

    def _call_openai(self, prompt: str) -> (dict, int):
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set. Please provide it in your .env file.")
        
        openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        
        headers = {
            "Authorization": f"Bearer {openai_key}",
            "Content-Type": "application/json"
        }
        
        openai_schema = {
            "type": "object",
            "properties": {
                "suggested_skills": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "skill_name": {"type": "string"},
                            "confidence": {"type": "number"},
                            "rationale": {"type": "string"},
                            "proof_examples": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["skill_name", "confidence", "rationale", "proof_examples"],
                        "additionalProperties": False
                    }
                },
                "evaluation_report_skills": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "skill_name": {"type": "string"},
                            "questions": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "question_text": {"type": "string"},
                                        "question_focus": {"type": "string"},
                                        "expected_key_points": {
                                            "type": "array",
                                            "items": {"type": "string"}
                                        }
                                    },
                                    "required": ["question_text", "question_focus", "expected_key_points"],
                                    "additionalProperties": False
                                }
                            }
                        },
                        "required": ["skill_name", "questions"],
                        "additionalProperties": False
                    }
                },
                "summary": {
                    "type": "object",
                    "properties": {
                        "overall_alignment": {"type": "string"},
                        "alignment_score": {"type": "number"},
                        "narrative": {"type": "string"},
                        "outcome_evaluation": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "stated_outcome": {"type": "string"},
                                    "status": {"type": "string"},
                                    "evidence": {"type": ["string", "null"]},
                                    "gap": {"type": ["string", "null"]}
                                },
                                "required": ["stated_outcome", "status", "evidence", "gap"],
                                "additionalProperties": False
                            }
                        },
                        "strengths": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "gaps": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    },
                    "required": ["overall_alignment", "alignment_score", "narrative", "outcome_evaluation", "strengths", "gaps"],
                    "additionalProperties": False
                }
            },
            "required": ["suggested_skills", "evaluation_report_skills", "summary"],
            "additionalProperties": False
        }
        
        payload = {
            "model": openai_model,
            "messages": [
                {"role": "system", "content": "You are a software engineering evaluator. You must return output strictly conforming to the JSON schema."},
                {"role": "user", "content": prompt}
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "LlmEvaluationOutput",
                    "strict": True,
                    "schema": openai_schema
                }
            },
            "temperature": 0.2
        }
        
        with httpx.Client(timeout=60.0, verify=self._verify_ssl()) as client:
            resp = client.post(
                "https://api.openai.com/v1/chat/completions",
                json=payload,
                headers=headers
            )
            
        if resp.status_code != 200:
            raise RuntimeError(f"OpenAI API failed with status {resp.status_code}: {resp.text}")
            
        resp_data = resp.json()
        completion_text = resp_data["choices"][0]["message"]["content"]
        result = json.loads(completion_text)
        
        prompt_tokens = resp_data.get("usage", {}).get("prompt_tokens", 1000)
        completion_tokens = resp_data.get("usage", {}).get("completion_tokens", 1000)
        tokens_used = prompt_tokens + completion_tokens
        
        return result, tokens_used

    def _call_groq(self, prompt: str) -> (dict, int):
        groq_key = os.getenv("GROQ_API_KEY")
        if not groq_key:
            raise ValueError("GROQ_API_KEY environment variable is not set. Please provide it in your .env file.")

        groq_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

        headers = {
            "Authorization": f"Bearer {groq_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": groq_model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a software engineering evaluator. "
                        "Return only valid JSON with keys: suggested_skills, "
                        "evaluation_report_skills, and summary. Do not suggest a skill "
                        "unless the provided files show positive evidence for it. "
                        "Every suggested skill must include proof_examples with real file paths, "
                        "imports, symbols, or snippets. Every suggested skill must have at least one conceptual question "
                        "and one codebase_specific question. Evaluate every stated outcome."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2
        }

        with httpx.Client(timeout=60.0, verify=self._verify_ssl()) as client:
            resp = client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                json=payload,
                headers=headers
            )

        if resp.status_code != 200:
            raise RuntimeError(f"Groq API failed with status {resp.status_code}: {resp.text}")

        resp_data = resp.json()
        completion_text = resp_data["choices"][0]["message"]["content"]
        result = json.loads(completion_text)

        prompt_tokens = resp_data.get("usage", {}).get("prompt_tokens", 1000)
        completion_tokens = resp_data.get("usage", {}).get("completion_tokens", 1000)
        tokens_used = prompt_tokens + completion_tokens

        return result, tokens_used

    def _build_prompt(self, llm_context: dict, catalog_info: str, parsed_outcomes: List[str], target_questions: int) -> str:
        return f"""
You are an expert AI software engineering assessor and skill evaluator.
Your goal is to analyze the provided project source code and produce a detailed evaluation report.

TECHNICAL SKILL CATALOG:
{catalog_info}

PROJECT DATA:
{json.dumps(llm_context, indent=2)}

STRICT RULES:
1. ONLY suggest skills that are clearly demonstrated in the source code files.
2. NEVER suggest a skill when the evidence says it is missing, absent, not used, or has "no evidence".
3. Prioritize suggesting skills from the TECHNICAL SKILL CATALOG above.
4. If a highly relevant technology or framework is used in the project but is NOT in the catalog (e.g. a specific library or tool not listed), you may suggest it using its real name. We will add it to our catalog.
5. For EACH suggested skill:
   - Provide a confidence score between 0.0 and 1.0.
   - Provide a clear rationale citing specific file paths and import statements/patterns.
   - Provide 1-3 proof_examples. Each proof example MUST cite a real file path and concrete evidence, e.g. "app/auth.py imports jwt and decodes JWT tokens", "package.json includes @supabase/supabase-js", or "migrations/001_init.sql creates students table".
   - Generate EXACTLY {target_questions} interview questions:
     - 1 Conceptual: focusing on general knowledge/theory of the technology.
     - 1 Codebase-specific: MUST cite real file paths (e.g., 'app/api/analyze.py') or symbol names (e.g. functions, classes) from the ZIP.
6. The evaluation_report_skills array must contain one entry for every suggested skill, and skill_name must never be blank.
7. Evaluate each of the following stated outcomes individually:
{json.dumps(parsed_outcomes, indent=2)}
   For each outcome:
   - Stated outcome must match the outcome string exactly.
   - Status MUST be one of: 'met', 'partial', 'not_met', 'not_verifiable'.
   - Cite specific evidence (file paths, configurations, modules) from the codebase.
   - Identify gaps if the status is 'partial' or 'not_met'.
8. Provide an overall alignment status ('strong', 'partial', 'weak'), an alignment score (0.0 to 1.0), and a narrative (2-4 sentences in plain English for the mentor summarizing the evaluation).
9. List the project's strengths and gaps (at least 2-3 of each).
"""
