import os
from pathlib import Path

class PromptService:
    """
    Handles dynamic loading and keyword formatting of prompt text files.
    """
    
    PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

    @classmethod
    def get_prompt(cls, template_name: str, **kwargs) -> str:
        """
        Loads prompt template by file name and formats it with keywords.
        """
        file_path = cls.PROMPTS_DIR / f"{template_name}.txt"
        
        if not file_path.exists():
            raise FileNotFoundError(f"Prompt template '{template_name}.txt' not found at {file_path}")
            
        with open(file_path, "r", encoding="utf-8") as f:
            template = f.read()
            
        # Format the template with provided keywords
        return template.format(**kwargs)
