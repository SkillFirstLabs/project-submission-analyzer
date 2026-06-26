"""
app/services – Business logic and external service integrations.

Contents:
  ai_service.py – Gemini API caller: Evidence → EvaluationReport + VivaQuestions.
"""

from app.services.ai_service import AIAnalysisResult, AIService

__all__ = ["AIService", "AIAnalysisResult"]
