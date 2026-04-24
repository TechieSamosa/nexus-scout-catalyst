"""
llm_engine.py — Google Gemini API wrapper with retry logic and JSON parsing.
"""

import json
import re
import time
from typing import Any, Dict, Optional
from google import genai
from google.genai import types


def get_client(api_key: str) -> genai.Client:
    """Create a Gemini client with the given API key."""
    return genai.Client(api_key=api_key)


def call_gemini(
    client: genai.Client,
    prompt: str,
    system_instruction: str = "",
    max_retries: int = 3,
    model: str = "gemini-2.0-flash",
) -> str:
    """Call Gemini API with retry logic. Returns raw text response."""
    for attempt in range(max_retries):
        try:
            config = types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=2048,
            )
            if system_instruction:
                config.system_instruction = system_instruction

            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=config,
            )
            return response.text
        except Exception as e:
            if attempt < max_retries - 1:
                wait = 2 ** attempt
                time.sleep(wait)
            else:
                raise RuntimeError(f"Gemini API failed after {max_retries} attempts: {e}")
    return ""


def parse_json_response(text: str) -> Dict[str, Any]:
    """Extract and parse JSON from LLM response text."""
    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting from markdown code block
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Try finding first { ... } block
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not parse JSON from response: {text[:300]}")
