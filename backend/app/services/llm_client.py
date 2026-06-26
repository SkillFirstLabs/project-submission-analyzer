import os
import json
import re
import logging
from openai import OpenAI

logger = logging.getLogger("project_analyzer")

def get_llm_client():
    """Returns an OpenAI client configured for NVIDIA API."""
    api_key = os.getenv("NVIDIA_API_KEY", "")
    return OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=api_key,
    )

def llm_generate(system_instruction: str, user_prompt: str, temperature: float = 0.2) -> str:
    """
    Generates content using the NVIDIA-hosted DeepSeek model.
    Returns the raw text response.
    """
    client = get_llm_client()
    
    completion = client.chat.completions.create(
        model="deepseek-ai/deepseek-v4-flash",
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        top_p=0.95,
        max_tokens=16384,
        stream=False,
    )
    
    return completion.choices[0].message.content

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
