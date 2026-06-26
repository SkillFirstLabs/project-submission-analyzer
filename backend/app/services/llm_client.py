import os
import json
import re
import logging
import requests

logger = logging.getLogger("project_analyzer")

def get_llm_client():
    """Unused now that we use Cohere API directly."""
    return None

def llm_generate(system_instruction: str, user_prompt: str, temperature: float = 0.2) -> str:
    """
    Generates content using the Cohere command-r-08-2024 model.
    Returns the raw text response.
    """
    api_key = os.getenv("COHERE_API_KEY", "")
    url = "https://api.cohere.com/v2/chat"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "command-r-08-2024",
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": temperature,
        "max_tokens": 3000
    }
    
    response = requests.post(url, headers=headers, json=payload, timeout=180)
    response.raise_for_status()
    data = response.json()
    
    content_list = data["message"]["content"]
    text = "".join(item["text"] for item in content_list if item.get("type") == "text")
    return text

def parse_json_response(raw_text: str):
    """
    Robustly parses JSON from LLM response text.
    Handles markdown fences, extra text, and common LLM quirks.
    """
    if not raw_text:
        return None
    
    text = raw_text.strip()
    
    # Remove markdown code fences (```json ... ``` or ``` ... ```)
    fence_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?\s*```', text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1).strip()
    
    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Try to find JSON array or object in the text
    for pattern in [r'(\[.*\])', r'(\{.*\})']:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                continue
    
    logger.warning(f"Failed to parse JSON from LLM response: {text[:200]}...")
    return None
