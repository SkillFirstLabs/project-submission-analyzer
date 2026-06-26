"""
app/prompts – Prompt construction for AI model calls.

Contents:
  evaluation_prompt.py – Builds the structured Gemini prompt from Evidence.
"""

from app.prompts.evaluation_prompt import build_prompt, load_skills_catalog

__all__ = ["build_prompt", "load_skills_catalog"]
