"""
Dynamic batching logic for Nepali/mixed chunks.

Groups chunks into batches based on total character count
to minimize LLM calls while respecting context window limits.
"""

from __future__ import annotations


# Maximum characters per batch (tune based on model's context window)
MAX_BATCH_CHARS = 3000


def group_chunks_into_batches(
    mixed_chunks: list[dict],
    max_batch_chars: int = MAX_BATCH_CHARS,
) -> list[list[dict]]:
    """
    Group mixed chunks into batches based on total character count.
    
    Each batch stays under max_batch_chars to avoid overwhelming the model.
    
    Args:
        mixed_chunks: List of dicts with 'chunk_id' and 'raw_text' keys.
        max_batch_chars: Maximum total characters per batch.
        
    Returns:
        List of batches, where each batch is a list of chunk dicts.
    """
    batches = []
    current_batch = []
    current_chars = 0

    for chunk in mixed_chunks:
        chunk_chars = len(chunk["raw_text"])

        # If adding this chunk would exceed the limit, start a new batch
        if current_chars + chunk_chars > max_batch_chars and current_batch:
            batches.append(current_batch)
            current_batch = []
            current_chars = 0

        current_batch.append(chunk)
        current_chars += chunk_chars

    # Don't forget the last batch
    if current_batch:
        batches.append(current_batch)

    return batches


def estimate_batch_count(total_chunks: int, avg_chars_per_chunk: int = 500) -> int:
    """
    Estimate how many batches will be created.
    Useful for logging/progress indicators.
    """
    total_chars = total_chunks * avg_chars_per_chunk
    return max(1, total_chars // MAX_BATCH_CHARS + (1 if total_chars % MAX_BATCH_CHARS else 0))