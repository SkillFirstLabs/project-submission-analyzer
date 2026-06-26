import json
from pathlib import Path
from typing import List, Dict, Any, Tuple
from groq import Groq
from app.config import settings
from app.models.schemas import SuggestedSkill, SkillWithQuestions, EvaluationQuestion

class QuestionGenerator:
    def __init__(self):
        pass

    def _select_key_files(self, extracted_files: List[Path], temp_dir: Path, max_files: int = 5) -> Dict[str, str]:
        """Selects key files (configs and entrypoints) to provide context for codebase-specific questions."""
        key_files = {}
        priority_keywords = ["main", "app", "index", "server", "router", "controller", "service", "config"]
        config_names = {"requirements.txt", "package.json", "pom.xml", "build.gradle", "Dockerfile", "docker-compose.yml"}
        
        scored_files = []
        for file_path in extracted_files:
            if not file_path.exists() or file_path.is_dir():
                continue
            
            rel_path = str(file_path.relative_to(temp_dir)).replace("\\", "/")
            score = 0
            
            # Prioritize configuration files
            if file_path.name in config_names:
                score += 15
            
            # Prioritize core logic keyword names
            for keyword in priority_keywords:
                if keyword in file_path.name.lower():
                    score += 8
                    break
                    
            # Prioritize source files
            if file_path.suffix in (".py", ".js", ".ts", ".java"):
                score += 3
                
            scored_files.append((score, file_path, rel_path))

        # Sort files by relevance score descending
        scored_files.sort(key=lambda x: x[0], reverse=True)

        for _, file_path, rel_path in scored_files[:max_files]:
            try:
                # Read up to first 120 lines to prevent context bloat
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = [f.readline() for _ in range(120)]
                    content = "".join(lines)
                    if len(content) > 8000:
                        content = content[:8000] + "\n... [content truncated]"
                    key_files[rel_path] = content
            except Exception:
                pass

        return key_files

    def generate_questions(
        self,
        suggested_skills: List[SuggestedSkill],
        extracted_files: List[Path],
        temp_dir: Path,
        file_tree: str,
        questions_per_skill: int = 2
    ) -> Tuple[List[SkillWithQuestions], int]:
        """
        Uses Groq API to generate interview questions for each suggested skill.
        Returns:
            Tuple[List[SkillWithQuestions], tokens_used]
        """
        if not suggested_skills:
            return [], 0

        # Retrieve api key; fail early if missing
        api_key = settings.GROQ_API_KEY
        if not api_key:
            raise ValueError("GROQ_API_KEY is not set. Please set it in your environment or .env file.")

        client = Groq(api_key=api_key)

        # Select relevant source file context
        key_file_contents = self._select_key_files(extracted_files, temp_dir)
        
        # Build codebase context block
        codebase_context = ""
        for rel_path, content in key_file_contents.items():
            codebase_context += f"--- File: {rel_path} ---\n{content}\n\n"

        # Map skills list to format for LLM prompt
        skills_formatted = "\n".join([
            f"- ID: {s.skill_id}, Name: {s.skill_name}"
            for s in suggested_skills
        ])

        # Define question distribution guidelines
        conceptual_count = max(1, questions_per_skill // 2)
        codebase_count = max(1, questions_per_skill - conceptual_count)

        prompt = f"""You are a senior mentor and code reviewer.
Analyze the following student project details and generate interview questions for each suggested skill.

### Project Directory Structure:
{file_tree}

### Codebase Contents (Key Files):
{codebase_context}

### Suggested Skills to Evaluate:
{skills_formatted}

### Task:
For each suggested skill, generate exactly {questions_per_skill} questions:
- {conceptual_count} conceptual question(s) (tests theoretical understanding of the skill/framework).
- {codebase_count} codebase-specific question(s) (tests knowledge of their own implementation. It MUST reference actual file names and code elements present in the codebase files listed above).

### Guidelines for Codebase-specific Questions:
- Reference actual files (e.g., "In `app/main.py`...").
- Probe design decisions or implementation details evident in the provided code.

### Output JSON Format:
Provide your response strictly in JSON format. The JSON must contain a root-level key "skills" which is an array of objects matching this schema:
{{
  "skills": [
    {{
      "skill_id": "fastapi",
      "skill_name": "FastAPI",
      "questions": [
        {{
          "question_text": "...",
          "question_focus": "conceptual",
          "expected_key_points": ["...", "..."]
        }},
        {{
          "question_text": "...",
          "question_focus": "codebase_specific",
          "expected_key_points": ["...", "..."]
        }}
      ]
    }}
  ]
}}
Ensure "question_focus" is either "conceptual" or "codebase_specific".
"""

        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional software engineering mentor. Always output responses in structured JSON matching the requested schema."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=settings.GROQ_MODEL,
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            
            response_content = chat_completion.choices[0].message.content
            tokens_used = chat_completion.usage.total_tokens if chat_completion.usage else 0
            
            parsed_data = json.loads(response_content)
            
            # Map parsed JSON objects back to SkillWithQuestions schemas
            skills_questions: List[SkillWithQuestions] = []
            skills_dict = {s.skill_id: s.skill_name for s in suggested_skills}
            
            for item in parsed_data.get("skills", []):
                skill_id = item.get("skill_id")
                # Only include if it's in our suggested skills
                if skill_id in skills_dict:
                    questions_list = []
                    for q in item.get("questions", []):
                        focus = q.get("question_focus")
                        if focus not in ("conceptual", "codebase_specific"):
                            focus = "conceptual"
                            
                        questions_list.append(
                            EvaluationQuestion(
                                question_text=q.get("question_text", "Explain your implementation choice."),
                                question_focus=focus,
                                expected_key_points=q.get("expected_key_points", [])
                            )
                        )
                    
                    skills_questions.append(
                        SkillWithQuestions(
                            skill_id=skill_id,
                            skill_name=skills_dict[skill_id],
                            questions=questions_list
                        )
                    )
            
            # Ensure all suggested skills are represented, even if LLM missed some
            matched_ids = {s.skill_id for s in skills_questions}
            for s in suggested_skills:
                if s.skill_id not in matched_ids:
                    # Generic fallback questions
                    skills_questions.append(
                        SkillWithQuestions(
                            skill_id=s.skill_id,
                            skill_name=s.skill_name,
                            questions=[
                                EvaluationQuestion(
                                    question_text=f"What are the core concepts of {s.skill_name} and how do you apply them?",
                                    question_focus="conceptual",
                                    expected_key_points=["Core architecture", "Best practices"]
                                ),
                                EvaluationQuestion(
                                    question_text=f"How is {s.skill_name} integrated into your codebase structure?",
                                    question_focus="codebase_specific",
                                    expected_key_points=["Configuration", "File organization"]
                                )
                            ][:questions_per_skill]
                        )
                    )

            return skills_questions, tokens_used

        except Exception as e:
            # Return fallback questions on failure
            skills_questions = []
            for s in suggested_skills:
                skills_questions.append(
                    SkillWithQuestions(
                        skill_id=s.skill_id,
                        skill_name=s.skill_name,
                        questions=[
                            EvaluationQuestion(
                                question_text=f"Describe the architecture of your implementation for {s.skill_name}.",
                                question_focus="conceptual",
                                expected_key_points=["Architecture patterns", "Components"]
                            ),
                            EvaluationQuestion(
                                question_text=f"Explain the design decisions made in your files regarding {s.skill_name}.",
                                question_focus="codebase_specific",
                                expected_key_points=["File layout", "Key logic"]
                            )
                        ][:questions_per_skill]
                    )
                )
            return skills_questions, 0
