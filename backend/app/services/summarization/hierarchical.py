"""
Steps 1-2: Hierarchical summarization.
Groups chunks, summarizes groups, progressively reduces.
"""

from __future__ import annotations

from app.ai.ollama_client import ollama
from app.services.summarization.prompts import (
    LEVEL1_SYSTEM,
    LEVEL1_USER,
    REDUCE_SYSTEM,
    REDUCE_USER,
)

# Tuning constants
LEVEL1_GROUP_SIZE = 5   # Chunks per group at Level 1
REDUCE_GROUP_SIZE = 4   # Summaries per group at higher levels


async def summarize_chunk_group(chunk_texts: list[str]) -> str:
    """Summarize a single group of chunks."""
    combined = "\n\n".join(chunk_texts)
    prompt = LEVEL1_USER.format(chunk_group=combined)

    try:
        result = await ollama.generate(prompt, system_prompt=LEVEL1_SYSTEM)
        return result.strip()
    except Exception as e:
        print(f"     ⚠️ Chunk group summarization failed: {e}")
        return combined[:500]


async def reduce_group(summaries: list[str]) -> str:
    """Reduce a group of summaries into one."""
    if len(summaries) == 1:
        return summaries[0]

    combined = "\n\n---\n\n".join(summaries)
    prompt = REDUCE_USER.format(summaries=combined)

    try:
        result = await ollama.generate(prompt, system_prompt=REDUCE_SYSTEM)
        return result.strip()
    except Exception as e:
        print(f"     ⚠️ Reduction failed: {e}")
        return combined[:1000]


async def run_hierarchical(chunk_texts: list[str]) -> str:
    """
    Full hierarchical summarization.
    
    Level 1: Group chunks → partial summaries
    Level 2+: Progressively reduce until one summary remains.
    
    Returns the final reduced summary text.
    """
    # Level 1: Summarize chunk groups
    groups = [
        chunk_texts[i:i + LEVEL1_GROUP_SIZE]
        for i in range(0, len(chunk_texts), LEVEL1_GROUP_SIZE)
    ]

    print(f"     Level 1: {len(chunk_texts)} chunks → {len(groups)} groups")

    current_summaries = []
    for i, group in enumerate(groups):
        print(f"       Group {i + 1}/{len(groups)} ({len(group)} chunks)")
        summary = await summarize_chunk_group(group)
        current_summaries.append(summary)

    # Level 2+: Progressively reduce
    level = 2
    while len(current_summaries) > 1:
        groups = [
            current_summaries[i:i + REDUCE_GROUP_SIZE]
            for i in range(0, len(current_summaries), REDUCE_GROUP_SIZE)
        ]

        print(f"     Level {level}: {len(current_summaries)} summaries → {len(groups)} groups")

        next_summaries = []
        for i, group in enumerate(groups):
            print(f"       Group {i + 1}/{len(groups)} ({len(group)} summaries)")
            reduced = await reduce_group(group)
            next_summaries.append(reduced)

        current_summaries = next_summaries
        level += 1

    return current_summaries[0]