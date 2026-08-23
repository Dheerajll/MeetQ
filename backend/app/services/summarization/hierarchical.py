"""
Steps 1-2: Hierarchical summarization.
Groups chunks, summarizes groups, progressively reduces.

Grouping uses a SLIDING WINDOW with a 1-item overlap so every group
carries the tail context of the previous group. This prevents the
Map LLM from seeing dangling references ("and because of that...")
at group boundaries. The REDUCE prompt removes the redundancy.
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
LEVEL1_STRIDE = 4       # Window step → 1-chunk overlap between groups
REDUCE_GROUP_SIZE = 4   # Summaries per group at higher levels
REDUCE_STRIDE = 3       # Window step → 1-summary overlap


def _sliding_groups(
    items: list,
    size: int,
    stride: int,
) -> list[list]:
    """
    Split items into overlapping groups (sliding window).

    Example (size=5, stride=4) over 13 chunks:
        Group 1: chunks[0:5]
        Group 2: chunks[4:9]    <- chunk 4 repeated as context
        Group 3: chunks[8:13]   <- chunk 8 repeated as context
    """
    stride = max(1, min(stride, size))  # safety bounds
    groups = []
    i = 0
    while i < len(items):
        groups.append(items[i:i + size])
        if i + size >= len(items):
            break
        i += stride
    return groups


async def summarize_chunk_group(chunk_texts: list[str]) -> str:
    """Summarize a single group of chunks."""
    combined = "\n".join(chunk_texts)
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
    combined = "\n---\n".join(summaries)
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
    Level 1: Group chunks (sliding window) → partial summaries
    Level 2+: Progressively reduce until one summary remains.
    Returns the final reduced summary text.
    """
    # Level 1: Summarize chunk groups with 1-chunk overlap
    groups = _sliding_groups(
        chunk_texts, LEVEL1_GROUP_SIZE, LEVEL1_STRIDE
    )
    print(
        f"     Level 1: {len(chunk_texts)} chunks → "
        f"{len(groups)} groups (sliding window)"
    )
    current_summaries = []
    for i, group in enumerate(groups):
        print(f"       Group {i + 1}/{len(groups)} ({len(group)} chunks)")
        summary = await summarize_chunk_group(group)
        current_summaries.append(summary)

    # Level 2+: Progressively reduce with 1-summary overlap
    level = 2
    while len(current_summaries) > 1:
        groups = _sliding_groups(
            current_summaries, REDUCE_GROUP_SIZE, REDUCE_STRIDE
        )
        print(
            f"     Level {level}: {len(current_summaries)} summaries → "
            f"{len(groups)} groups"
        )
        next_summaries = []
        for i, group in enumerate(groups):
            print(f"       Group {i + 1}/{len(groups)} ({len(group)} summaries)")
            reduced = await reduce_group(group)
            next_summaries.append(reduced)
        current_summaries = next_summaries
        level += 1

    return current_summaries[0]