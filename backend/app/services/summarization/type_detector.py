"""
Step 0: Meeting type detection.
Classifies the meeting from its opening content.
"""

from __future__ import annotations

from app.ai.ollama_client import ollama
from app.services.summarization.prompts import (
    TYPE_DETECTION_SYSTEM,
    TYPE_DETECTION_USER,
)

VALID_TYPES = {"technical", "business", "educational", "standup", "general"}


async def detect_meeting_type(opening_chunks: list[str]) -> str:
    """
    Classify meeting type from the first 2-3 chunks.
    Returns: 'technical', 'business', 'educational', 'standup', or 'general'
    """
    opening_text = "\n\n".join(opening_chunks[:3])
    prompt = TYPE_DETECTION_USER.format(opening_chunks=opening_text)

    try:
        result = await ollama.generate(
            prompt,
            system_prompt=TYPE_DETECTION_SYSTEM,
        )

        type_word = result.strip().lower().strip('"\'')
        return type_word if type_word in VALID_TYPES else "general"

    except Exception as e:
        print(f"     ⚠️ Type detection failed: {e}")
        return "general"