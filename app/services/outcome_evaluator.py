import json
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple
from groq import Groq
from app.config import settings
from app.models.schemas import OutcomeEvaluationItem

class OutcomeEvaluator:
    def __init__(self):
        pass

    def parse_outcomes(self, outcomes_text: str) -> List[str]:
        """
        Splits outcomes by newlines, removing numbered list formatting, bullets,
        and leading/trailing whitespaces.
        """
        if not outcomes_text:
            return []
        
        lines = outcomes_text.splitlines()
        outcomes = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Clean up bullet list prefixes (e.g., "1.", "1)", "-", "*", "•")
            cleaned_line = re.sub(r"^([0-9]+[\.\)\-]\s*|[\*\-\•]\s*)", "", line).strip()
            if cleaned_line:
                outcomes.append(cleaned_line)
        return outcomes

    def _select_key_files(self, extracted_files: List[Path], temp_dir: Path, max_files: int = 5) -> Dict[str, str]:
        """Helper to get key file contents for codebase evidence matching."""
        key_files = {}
        priority_keywords = ["main", "app", "index", "server", "router", "controller", "service", "config"]
        config_names = {"requirements.txt", "package.json", "pom.xml", "build.gradle", "Dockerfile", "docker-compose.yml"}
        
        scored_files = []
        for file_path in extracted_files:
            if not file_path.exists() or file_path.is_dir():
                continue
            
            rel_path = str(file_path.relative_to(temp_dir)).replace("\\", "/")
            score = 0
            if file_path.name in config_names:
                score += 15
            for kw in priority_keywords:
                if kw in file_path.name.lower():
                    score += 8
                    break
            if file_path.suffix in (".py", ".js", ".ts", ".java"):
                score += 3
            scored_files.append((score, file_path, rel_path))

        scored_files.sort(key=lambda x: x[0], reverse=True)

        for _, file_path, rel_path in scored_files[:max_files]:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = [f.readline() for _ in range(120)]
                    content = "".join(lines)
                    if len(content) > 8000:
                        content = content[:8000] + "\n... [content truncated]"
                    key_files[rel_path] = content
            except Exception:
                pass

        return key_files

    def evaluate_outcomes(
        self,
        outcomes_text: str,
        extracted_files: List[Path],
        temp_dir: Path,
        file_tree: str
    ) -> Tuple[List[OutcomeEvaluationItem], int]:
        """
        Uses Groq API to compare student stated outcomes against codebase evidence.
        Returns:
            Tuple[List[OutcomeEvaluationItem], tokens_used]
        """
        parsed_outcomes = self.parse_outcomes(outcomes_text)
        if not parsed_outcomes:
            return [], 0

        api_key = settings.GROQ_API_KEY
        if not api_key:
            raise ValueError("GROQ_API_KEY is not set. Please set it in your environment or .env file.")

        client = Groq(api_key=api_key)

        key_file_contents = self._select_key_files(extracted_files, temp_dir)
        codebase_context = ""
        for rel_path, content in key_file_contents.items():
            codebase_context += f"--- File: {rel_path} ---\n{content}\n\n"

        outcomes_list_str = "\n".join([f"- {out}" for out in parsed_outcomes])

        prompt = f"""You are a professional software engineering auditor.
Your job is to cross-verify a student's stated project outcomes against the actual evidence in their codebase.

### Project Directory Structure:
{file_tree}

### Codebase Contents (Key Files):
{codebase_context}

### Stated Outcomes to Verify:
{outcomes_list_str}

### Instructions:
For each stated outcome, evaluate if the codebase matches or provides evidence of its implementation.
Determine the status for each outcome:
- 'met': The outcome is fully supported by clear code evidence.
- 'partial': The outcome is partially supported but has missing parts.
- 'not_met': The code is present but failed to implement the outcome, or the outcome was completely omitted.
- 'not_verifiable': There is no source code or configuration file related to this outcome in the ZIP, making it impossible to check.

Provide concrete details of files and patterns found for 'met' or 'partial' outcomes. Identify exactly what is missing for 'partial' or 'not_met' statuses.

### Output JSON Format:
Provide your response strictly in JSON format. The JSON must contain a root-level key "outcome_evaluation" which is an array of objects matching this schema:
{{
  "outcome_evaluation": [
    {{
      "stated_outcome": "Stated outcome string",
      "status": "met",
      "evidence": "Evidence details (e.g. app/routes/user.py contains CRUD endpoints)",
      "gap": null
    }}
  ]
}}
Ensure "status" is strictly one of: "met", "partial", "not_met", "not_verifiable".
If "gap" is not applicable, set it to null. If "evidence" is not applicable, set it to null.
"""

        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional technical auditor. Always output responses in structured JSON matching the requested schema."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=settings.GROQ_MODEL,
                response_format={"type": "json_object"},
                temperature=0.1,
            )

            response_content = chat_completion.choices[0].message.content
            tokens_used = chat_completion.usage.total_tokens if chat_completion.usage else 0

            parsed_data = json.loads(response_content)
            evaluations: List[OutcomeEvaluationItem] = []

            for item in parsed_data.get("outcome_evaluation", []):
                status = item.get("status")
                if status not in ("met", "partial", "not_met", "not_verifiable"):
                    status = "not_verifiable"

                evaluations.append(
                    OutcomeEvaluationItem(
                        stated_outcome=item.get("stated_outcome", ""),
                        status=status,
                        evidence=item.get("evidence"),
                        gap=item.get("gap")
                    )
                )

            # Reconcile outcomes to ensure every parsed outcome is returned, even if LLM missed it
            evaluated_outcomes = {item.stated_outcome.strip().lower() for item in evaluations}
            for original_out in parsed_outcomes:
                if original_out.strip().lower() not in evaluated_outcomes:
                    evaluations.append(
                        OutcomeEvaluationItem(
                            stated_outcome=original_out,
                            status="not_verifiable",
                            evidence=None,
                            gap="Missing evaluation from model."
                        )
                    )

            return evaluations, tokens_used

        except Exception as e:
            # Fallback evaluation on failure
            evaluations = [
                OutcomeEvaluationItem(
                    stated_outcome=out,
                    status="not_verifiable",
                    evidence=None,
                    gap=f"Failed to evaluate outcome: {str(e)}"
                )
                for out in parsed_outcomes
            ]
            return evaluations, 0
