import json
import re
import asyncio
import httpx
from typing import Dict, Any, List, Optional
from app.config import settings

class AIService:
    """
    Low-level client for interacting with LM Studio's OpenAI compatible API.
    Handles pings, model listings, raw prompt posting, exponential retries,
    timeouts, and robust JSON parsing/extraction.
    """

    @classmethod
    async def get_loaded_models(cls) -> List[str]:
        """
        Queries LM Studio's /v1/models endpoint to identify currently active models.
        """
        url = f"{settings.LM_STUDIO_BASE_URL}/models"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    models = [m.get("id") for m in data.get("data", []) if m.get("id")]
                    return models
        except Exception as err:
            print(f"[Warning] Failed to fetch loaded models from {url}: {err}")
        return []

    @classmethod
    async def post_prompt(
        cls, 
        model: str, 
        system_instruction: str, 
        user_prompt: str, 
        response_format: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
        backoff_factor: float = 2.0
    ) -> str:
        """
        Posts system and user prompt commands to the chat/completions endpoint.
        Implements linear-to-exponential backoff retries on connectivity or timeout events.
        """
        url = f"{settings.LM_STUDIO_BASE_URL}/chat/completions"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.2
        }
        
        if response_format:
            payload["response_format"] = response_format

        delay = 1.0
        last_exception = None

        for attempt in range(1, max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=float(settings.REQUEST_TIMEOUT)) as client:
                    response = await client.post(url, json=payload)
                    
                    if response.status_code == 200:
                        data = response.json()
                        content = data["choices"][0]["message"]["content"]
                        return content
                    else:
                        raise httpx.HTTPStatusError(
                            f"LM Studio returned status {response.status_code}",
                            request=response.request,
                            response=response
                        )
            except (httpx.RequestError, httpx.TimeoutException, httpx.HTTPStatusError) as exc:
                last_exception = exc
                print(f"[Warning] LM Studio call attempt {attempt}/{max_retries} failed: {exc}")
                if attempt < max_retries:
                    await asyncio.sleep(delay)
                    delay *= backoff_factor
                else:
                    break

        raise last_exception or RuntimeError(f"Failed to call model {model} after {max_retries} retries")

    @classmethod
    def extract_and_parse_json(cls, text: str) -> Any:
        """
        Cleans and parses raw text output into valid Python objects (dicts/lists).
        Extracts content from markdown code fences or matching brackets if needed.
        """
        text = text.strip()
        
        # 1. Try simple loads directly
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # 2. Try to extract content wrapped in ```json ... ``` or ``` ... ```
        fence_match = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL)
        if fence_match:
            try:
                return json.loads(fence_match.group(1).strip())
            except json.JSONDecodeError:
                pass

        # 3. Find boundaries of matching braces or brackets as a last ditch effort
        brace_match = re.search(r'(\{.*\}|\[.*\])', text, re.DOTALL)
        if brace_match:
            try:
                return json.loads(brace_match.group(1).strip())
            except json.JSONDecodeError:
                pass

        raise ValueError(f"Could not parse valid JSON from output:\n{text}")
