"""
LLM inference for Nepali/mixed chunk cleaning.

Handles:
- Single chunk inference
- Batch inference (multiple chunks in one LLM call)
- Output parsing and cleanup
"""

from __future__ import annotations

import re

from app.ai.ollama_client import ollama
from app.ai.prompts import (
    CLEANING_INFER_SYSTEM_PROMPT,
    CLEANING_INFER_USER_PROMPT,
    CLEANING_BATCH_SYSTEM_PROMPT,
    CLEANING_BATCH_USER_PROMPT,
)


# ============================================================
# LLM output cleaning
# ============================================================

def clean_llm_output(raw_output: str) -> str:
    """
    Strip any analysis, commentary, XML tags, or preamble the model adds.
    Returns only the actual transcript text.
    """
    text = raw_output.strip()

    # Remove XML tags
    text = re.sub(r"</?transcript>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"</?analysis>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)

    # Process line by line
    lines = text.split("\n")
    cleaned_lines = []
    skip_until_speaker = False

    for line in lines:
        stripped = line.strip()

        # Skip analysis sections
        if stripped.lower().startswith(("topic:", "key entities:", "entities:", "analysis:")):
            skip_until_speaker = True
            continue

        # If skipping, wait for speaker label
        if skip_until_speaker:
            if re.match(r"\[speaker\s*\d+\]", stripped, re.IGNORECASE):
                skip_until_speaker = False
                cleaned_lines.append(line)
            continue

        # Skip model commentary/preamble
        if stripped.lower().startswith((
            "here's", "here is", "okay,", "okay ", "sure,", "sure ",
            "the decoded", "the cleaned", "the transcript", "the corrected",
            "below is", "below:", "i've", "i have",
            "corrected transcript:", "clean transcript:", "fixed transcript:",
        )):
            continue

        # Skip empty lines at start
        if not cleaned_lines and not stripped:
            continue

        cleaned_lines.append(line)

    result = "\n".join(cleaned_lines).strip()
    return result if result else raw_output.strip()


# ============================================================
# Batch response parsing
# ============================================================

def parse_batch_response(response: str, expected_count: int) -> list[str]:
    """
    Parse the LLM's batched response into individual chunk texts.
    
    Expected format:
    [Chunk 1]
    <text>
    
    [Chunk 2]
    <text>
    """
    # Split by [Chunk N] markers
    chunks = re.split(r"\[Chunk\s*\d+\]", response, flags=re.IGNORECASE)

    # Remove empty strings
    chunks = [c.strip() for c in chunks if c.strip()]

    # Clean each chunk
    cleaned = [clean_llm_output(c) for c in chunks]

    # Pad with [unclear] if we got fewer than expected
    while len(cleaned) < expected_count:
        cleaned.append("[unclear]")

    # Truncate if we got more
    return cleaned[:expected_count]


# ============================================================
# Single chunk inference
# ============================================================

async def infer_single_chunk(raw_text: str) -> str:
    """
    Process a single Nepali/mixed chunk through the LLM.
    Returns cleaned English text.
    """
    prompt = CLEANING_INFER_USER_PROMPT.format(raw_text=raw_text)

    try:
        result = await ollama.generate(
            prompt,
            system_prompt=CLEANING_INFER_SYSTEM_PROMPT,
        )
        return clean_llm_output(result)
    except Exception as e:
        print(f"     ⚠️ Single chunk LLM inference failed: {e}")
        return raw_text


# ============================================================
# Batch inference
# ============================================================

async def infer_batch(batch: list[dict]) -> list[str]:
    """
    Process a batch of chunks in a single LLM call.
    
    Args:
        batch: List of dicts with 'chunk_id' and 'raw_text' keys.
        
    Returns:
        List of cleaned texts in the same order as input.
    """
    # Single chunk: use simple prompt
    if len(batch) == 1:
        return [await infer_single_chunk(batch[0]["raw_text"])]

    # Multiple chunks: build batch prompt
    batched_text = ""
    for i, chunk in enumerate(batch):
        batched_text += f"[Chunk {i + 1}]\n{chunk['raw_text']}\n\n"

    prompt = CLEANING_BATCH_USER_PROMPT.format(batched_chunks=batched_text.strip())

    try:
        result = await ollama.generate(
            prompt,
            system_prompt=CLEANING_BATCH_SYSTEM_PROMPT,
        )

        cleaned_texts = parse_batch_response(result, len(batch))
        return cleaned_texts

    except Exception as e:
        print(f"     ⚠️ Batch LLM inference failed: {e}")
        # Fallback: process individually
        results = []
        for chunk in batch:
            results.append(await infer_single_chunk(chunk["raw_text"]))
        return results