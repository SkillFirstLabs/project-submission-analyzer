import json
from typing import List, Tuple
from groq import Groq
from app.config import settings
from app.models.schemas import (
    SuggestedSkill, SkillWithQuestions, OutcomeEvaluationItem,
    ReportSummary, EvaluationReport, AnalysisResponse, ReportMetadata
)

class ReportBuilder:
    def __init__(self):
        pass

    def build_report(
        self,
        project_title: str,
        project_description: str,
        suggested_skills: List[SuggestedSkill],
        skills_questions: List[SkillWithQuestions],
        outcome_evaluations: List[OutcomeEvaluationItem],
        files_analyzed: int,
        extraction_time_ms: int,
        processing_start_time: float,
        tokens_accumulated: int
    ) -> Tuple[AnalysisResponse, int]:
        """
        Synthesizes the evaluations and queries Groq to generate strengths, gaps,
        overall alignment, alignment score, and narrative summary.
        Returns:
            Tuple[AnalysisResponse, tokens_used]
        """
        api_key = settings.GROQ_API_KEY
        if not api_key:
            raise ValueError("GROQ_API_KEY is not set. Please set it in your environment or .env file.")

        client = Groq(api_key=api_key)

        # Format inputs for LLM synthesis
        skills_str = "\n".join([f"- {s.skill_name} (Confidence: {s.confidence})" for s in suggested_skills])
        
        outcomes_str = "\n".join([
            f"- Outcome: {item.stated_outcome}\n  Status: {item.status}\n  Evidence: {item.evidence or 'None'}\n  Gap: {item.gap or 'None'}"
            for item in outcome_evaluations
        ])

        prompt = f"""You are an elite senior technical architect. Your job is to compile a final mentor-ready evaluation report of a student project.
You have the following evaluation elements:

### Project Title:
{project_title}

### Project Description:
{project_description or "No description provided."}

### Detected Skills:
{skills_str}

### Outcome Evaluations:
{outcomes_str}

### Task:
Synthesize this information and output a JSON response containing:
1. `overall_alignment`: String representing how well the codebase matches stated outcomes. Must be one of: "strong", "partial", "weak".
2. `alignment_score`: A float from 0.0 to 1.0 representing completeness.
3. `narrative`: A detailed summary (2-3 paragraphs) assessing the overall quality of the code, how well the student implemented their goals, and their usage of frameworks.
4. `strengths`: A list of strings identifying key strengths of their implementation (technologies used correctly, clean architecture, security checks, etc.).
5. `gaps`: A list of strings identifying areas of improvement, missing parts, or poor practices.

### Scoring Guidelines:
- If almost all outcomes are 'met', alignment_score should be 0.8 to 1.0, and overall_alignment should be 'strong'.
- If there are 'partial' or a mix of 'met' and 'not_met' outcomes, alignment_score should be 0.4 to 0.79, and overall_alignment should be 'partial'.
- If most outcomes are 'not_met' or 'not_verifiable', alignment_score should be 0.0 to 0.39, and overall_alignment should be 'weak'.

### Output JSON Format:
Provide your response strictly in JSON format matching this schema:
{{
  "overall_alignment": "strong",
  "alignment_score": 0.9,
  "narrative": "...",
  "strengths": ["...", "..."],
  "gaps": ["...", "..."]
}}
"""

        tokens_used = tokens_accumulated

        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional software architect. Always output responses in structured JSON matching the requested schema."
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
            tokens_used += chat_completion.usage.total_tokens if chat_completion.usage else 0

            parsed_data = json.loads(response_content)

            # Extract and validate fields
            alignment_score = parsed_data.get("alignment_score", 0.0)
            # Guarantee score ranges between 0.0 and 1.0
            alignment_score = max(0.0, min(1.0, float(alignment_score)))

            overall_alignment = parsed_data.get("overall_alignment", "partial")
            if overall_alignment not in ("strong", "partial", "weak"):
                # Programmatic calculation fallback if LLM gave an invalid value
                if alignment_score >= 0.8:
                    overall_alignment = "strong"
                elif alignment_score >= 0.4:
                    overall_alignment = "partial"
                else:
                    overall_alignment = "weak"

            summary = ReportSummary(
                overall_alignment=overall_alignment,
                alignment_score=round(alignment_score, 2),
                narrative=parsed_data.get("narrative", "Analysis complete."),
            )

            strengths = parsed_data.get("strengths", ["Code logic implemented successfully."])
            gaps = parsed_data.get("gaps", ["No specific gaps detected."])

        except Exception as e:
            # Programmatic fallback summary in case of error
            met_count = sum(1 for item in outcome_evaluations if item.status == "met")
            total_outcomes = len(outcome_evaluations)
            score = (met_count / total_outcomes) if total_outcomes > 0 else 0.0
            
            if score >= 0.8:
                align = "strong"
            elif score >= 0.4:
                align = "partial"
            else:
                align = "weak"

            summary = ReportSummary(
                overall_alignment=align,
                alignment_score=round(score, 2),
                narrative=f"Successfully analyzed project and completed evaluation. (Fallback summary due to: {str(e)})"
            )
            strengths = ["Detected project structure matching catalog patterns."]
            gaps = ["Unable to complete detailed AI analysis summary."]

        # Calculate processing time
        import time
        processing_time_ms = int((time.perf_counter() - processing_start_time) * 1000)

        report = EvaluationReport(
            skills=skills_questions,
            summary=summary,
            outcome_evaluation=outcome_evaluations,
            strengths=strengths,
            gaps=gaps
        )

        metadata = ReportMetadata(
            files_analyzed=files_analyzed,
            extraction_time_ms=extraction_time_ms,
            model_tokens_used=tokens_used
        )

        response = AnalysisResponse(
            project_title=project_title,
            suggested_skills=suggested_skills,
            evaluation_report=report,
            metadata=metadata,
            processing_time_ms=processing_time_ms
        )

        return response, tokens_used
