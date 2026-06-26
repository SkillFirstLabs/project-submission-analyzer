from app.models.project_context import ProjectContext


class ContextBuilderService:

    def process(self, context: ProjectContext) -> ProjectContext:

        if not context.deeply_ranked_files:
            raise ValueError("No deeply ranked files found for context building.")

        structured_files = []

        for file in context.deeply_ranked_files:

            structured_files.append({
                "file_name": file.name,
                "path": file.path,
                "score": file.deep_score,
                "reasons": file.deep_reasons,
                "content": file.content
            })

        # -----------------------------
        # Build LLM-ready context
        # -----------------------------

        llm_context = {
            "project_title": context.project_title,
            "project_description": context.project_description,
            "project_outcomes": context.project_outcomes,

            "files": structured_files,

            "summary_instructions": {
                "task": "Analyze the project and extract skills, evaluation report, strengths, and gaps.",
                "rules": [
                    "Use only provided files",
                    "Do not assume missing files",
                    "Base reasoning on actual code",
                    "Extract real frameworks and technologies"
                ]
            }
        }

        # -----------------------------
        # Store in metadata for Gemini
        # -----------------------------
        context.metadata["llm_context"] = llm_context

        context.metadata["files_for_llm"] = len(structured_files)

        return context