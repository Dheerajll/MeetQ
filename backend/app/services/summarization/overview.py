"""
Step 3: Overview paragraph generation.
Shapes the reduced summary into a proper meeting overview.
"""

from __future__ import annotations

from app.ai.ollama_client import ollama
from app.services.summarization.prompts import (
    OVERVIEW_SYSTEM,
    OVERVIEW_USER,
)


async def generate_overview(reduced_summary: str) -> str:
    """
    Generate a final overview paragraph from the reduced summary.
    
    The overview should be:
    - One paragraph (4-7 sentences)
    - Covers the meeting from start to end
    - Focuses on main purpose and flow
    - Professional, natural English
    """
    prompt = OVERVIEW_USER.format(reduced_summary=reduced_summary)

    try:
        result = await ollama.generate(prompt, system_prompt=OVERVIEW_SYSTEM)
        return result.strip()
    except Exception as e:
        print(f"     ⚠️ Overview generation failed: {e}")
        # Fallback: use the reduced summary as-is
        return reduced_summary