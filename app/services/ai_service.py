from google import genai
from app.config import GEMINI_API_KEY, MODEL_NAME

client = genai.Client(api_key=GEMINI_API_KEY)


def ask_gemini(prompt: str):
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
        )

        if response.text:
            return response.text

        return "No response generated."

    except Exception as e:
        print("Gemini Error:", e)
        return "Gemini service is temporarily unavailable. Project analysis continued without AI feedback."