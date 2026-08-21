"""
Step 4: Structured extraction.
Extracts key topics, decisions, and action items from the overview.
"""

from __future__ import annotations

import json
import re

from app.ai.ollama_client import ollama
from app.services.summarization.prompts import (
    EXTRACTION_SYSTEM,
    EXTRACTION_USER,
)


async def extract_structured_info(overview: str) -> dict:
    """
    Extract key_topics, decisions, and action_items from the overview.
    Returns dict with these three fields.
    """
    prompt = EXTRACTION_USER.format(overview=overview)

    try:
        result = await ollama.generate(prompt, system_prompt=EXTRACTION_SYSTEM)
        return _parse_json(result)
    except Exception as e:
        print(f"     ⚠️ Extraction failed: {e}")
        return {"key_topics": [], "decisions": [], "action_items": []}


def _parse_json(response: str) -> dict:
    """Parse JSON from LLM response, handling edge cases."""
    text = response.strip()

    # Remove markdown code blocks if present
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*", "", text)

    try:
        parsed = json.loads(text)
        return {
            "key_topics": parsed.get("key_topics", []),
            "decisions": parsed.get("decisions", []),
            "action_items": parsed.get("action_items", []),
        }
    except json.JSONDecodeError:
        print(f"     ⚠️ JSON parse failed: {text[:100]}...")
        return {"key_topics": [], "decisions": [], "action_items": []}