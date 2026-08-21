"""
Transcript Cleaning Service — Single-Pass with Dynamic Batching.

English chunks:
    - Code-based overlap removal. No LLM.

Nepali/mixed chunks:
    - Dynamic batching: groups chunks to minimize LLM calls.
    - Single LLM pass per batch to infer clean English.
"""

from __future__ import annotations

import re

from sqlalchemy import select

from app.ai.ollama_client import ollama
from app.ai.prompts import (
    CLEANING_INFER_SYSTEM_PROMPT,
    CLEANING_INFER_USER_PROMPT,
    CLEANING_BATCH_SYSTEM_PROMPT,
    CLEANING_BATCH_USER_PROMPT,
)
from app.core.database import AsyncSessionLocal
from app.models.transcript import TranscriptChunk


# ============================================================
# Speaker label handling
# ============================================================

SPEAKER_LABEL_PATTERN = re.compile(
    r"\[speaker\s*\d+\]\s*",
    re.IGNORECASE,
)


def strip_speaker_labels(text: str) -> str:
    return SPEAKER_LABEL_PATTERN.sub("", text).strip()


def get_leading_speaker_label(text: str) -> str | None:
    match = SPEAKER_LABEL_PATTERN.match(text)
    if match:
        return match.group().strip()
    return None


def starts_with_speaker_label(text: str) -> bool:
    return SPEAKER_LABEL_PATTERN.match(text.strip()) is not None


# ============================================================
# Language detection
# ============================================================

def contains_indic_script(text: str) -> bool:
    for char in text:
        code = ord(char)
        if 0x0900 <= code <= 0x097F:
            return True
        if 0x0980 <= code <= 0x09FF:
            return True
        if 0x0A00 <= code <= 0x0A7F:
            return True
        if 0x0A80 <= code <= 0x0AFF:
            return True
        if 0x0B00 <= code <= 0x0B7F:
            return True
        if 0x0B80 <= code <= 0x0BFF:
            return True
        if 0x0C00 <= code <= 0x0C7F:
            return True
        if 0x0C80 <= code <= 0x0CFF:
            return True
        if 0x0D00 <= code <= 0x0D7F:
            return True
    return False


def is_english_chunk(text: str) -> bool:
    if not text.strip():
        return True
    clean = strip_speaker_labels(text)
    if not clean.strip():
        return True
    return not contains_indic_script(clean)


# ============================================================
# English overlap detection (code-based)
# ============================================================

def normalize_word(word: str) -> str:
    return word.lower().strip(".,!?;:…'\"""''()[]{}")


def find_word_overlap(
    prev_text: str,
    curr_text: str,
    min_words: int = 3,
    max_words: int = 30,
) -> int:
    if not prev_text or not curr_text:
        return 0

    clean_prev = strip_speaker_labels(prev_text)
    clean_curr = strip_speaker_labels(curr_text)

    prev_words = clean_prev.split()
    curr_words = clean_curr.split()

    if not prev_words or not curr_words:
        return 0

    max_window = min(len(prev_words), len(curr_words), max_words)

    for window in range(max_window, min_words - 1, -1):
        suffix = [normalize_word(w) for w in prev_words[-window:]]
        prefix = [normalize_word(w) for w in curr_words[:window]]
        if suffix == prefix:
            return window

    for window in range(max_window, min_words - 1, -1):
        suffix = [normalize_word(w) for w in prev_words[-window:]]
        prefix = [normalize_word(w) for w in curr_words[:window]]
        matches = sum(1 for a, b in zip(suffix, prefix) if a == b)
        if matches / window >= 0.75:
            return window

    return 0


def skip_words_in_raw(raw_text: str, words_to_skip: int) -> int:
    words_skipped = 0
    pos = 0

    while pos < len(raw_text) and words_skipped < words_to_skip:
        speaker_match = SPEAKER_LABEL_PATTERN.match(raw_text, pos)
        if speaker_match:
            pos = speaker_match.end()
            continue

        if raw_text[pos].isspace():
            pos += 1
            continue

        while pos < len(raw_text) and not raw_text[pos].isspace():
            if SPEAKER_LABEL_PATTERN.match(raw_text, pos):
                break
            pos += 1

        words_skipped += 1

    while pos < len(raw_text) and raw_text[pos].isspace():
        pos += 1

    return pos


def clean_english_chunk(
    raw_text: str,
    prev_english_raw: str | None,
) -> str:
    if prev_english_raw is None:
        return raw_text

    overlap_words = find_word_overlap(prev_english_raw, raw_text)

    if overlap_words <= 0:
        return raw_text

    skip_pos = skip_words_in_raw(raw_text, overlap_words)
    trimmed = raw_text[skip_pos:].strip()

    leading_speaker = get_leading_speaker_label(raw_text)
    if leading_speaker and trimmed and not starts_with_speaker_label(trimmed):
        trimmed = f"{leading_speaker} {trimmed}"

    return trimmed


# ============================================================
# LLM output cleaning
# ============================================================

def clean_llm_output(raw_output: str) -> str:
    """Strip any analysis, commentary, or tags the model adds."""
    text = raw_output.strip()

    text = re.sub(r"</?transcript>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"</?analysis>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)

    lines = text.split("\n")
    cleaned_lines = []
    skip_until_speaker = False

    for line in lines:
        stripped = line.strip()

        if stripped.lower().startswith(("topic:", "key entities:", "entities:", "analysis:")):
            skip_until_speaker = True
            continue

        if skip_until_speaker:
            if re.match(r"\[speaker\s*\d+\]", stripped, re.IGNORECASE):
                skip_until_speaker = False
                cleaned_lines.append(line)
            continue

        if stripped.lower().startswith((
            "here's", "here is", "okay,", "okay ", "sure,", "sure ",
            "the decoded", "the cleaned", "the transcript", "the corrected",
            "below is", "below:", "i've", "i have",
            "corrected transcript:", "clean transcript:", "fixed transcript:",
        )):
            continue

        if not cleaned_lines and not stripped:
            continue

        cleaned_lines.append(line)

    result = "\n".join(cleaned_lines).strip()
    return result if result else raw_output.strip()


# ============================================================
# Dynamic Batching for Nepali/Mixed Chunks
# ============================================================

# Maximum characters per batch (tune based on your model's context window)
MAX_BATCH_CHARS = 3000


def group_chunks_into_batches(
    mixed_chunks: list[dict],
    max_batch_chars: int = MAX_BATCH_CHARS,
) -> list[list[dict]]:
    """
    Group mixed chunks into batches based on total character count.
    
    Each batch stays under max_batch_chars to avoid overwhelming the model.
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


async def infer_batch(batch: list[dict]) -> list[str]:
    """
    Process a batch of chunks in a single LLM call.
    Returns list of cleaned texts in the same order as input.
    """
    if len(batch) == 1:
        # Single chunk: use the simple prompt
        return [await infer_single_chunk(batch[0]["raw_text"])]

    # Multiple chunks: use batch prompt
    batched_text = ""
    for i, chunk in enumerate(batch):
        batched_text += f"[Chunk {i + 1}]\n{chunk['raw_text']}\n\n"

    prompt = CLEANING_BATCH_USER_PROMPT.format(batched_chunks=batched_text.strip())

    try:
        result = await ollama.generate(
            prompt,
            system_prompt=CLEANING_BATCH_SYSTEM_PROMPT,
        )

        # Parse the batched response
        cleaned_texts = parse_batch_response(result, len(batch))
        return cleaned_texts

    except Exception as e:
        print(f"     ⚠️ Batch LLM inference failed: {e}")
        # Fallback: process individually
        results = []
        for chunk in batch:
            results.append(await infer_single_chunk(chunk["raw_text"]))
        return results


async def infer_single_chunk(raw_text: str) -> str:
    """Single LLM pass for one chunk (fallback)."""
    prompt = CLEANING_INFER_USER_PROMPT.format(raw_text=raw_text)

    try:
        result = await ollama.generate(
            prompt,
            system_prompt=CLEANING_INFER_SYSTEM_PROMPT,
        )
        return clean_llm_output(result)
    except Exception as e:
        print(f"     ⚠️ LLM inference failed: {e}")
        return raw_text


def parse_batch_response(response: str, expected_count: int) -> list[str]:
    """
    Parse the LLM's batched response into individual chunk texts.
    
    Expected format:
    [Chunk 1]
    <text>
    
    [Chunk 2]
    <text>
    """
    # Try to split by [Chunk N] markers
    chunks = re.split(r"\[Chunk\s*\d+\]", response, flags=re.IGNORECASE)

    # Remove empty strings from split
    chunks = [c.strip() for c in chunks if c.strip()]

    # Clean each chunk
    cleaned = [clean_llm_output(c) for c in chunks]

    # If we got the expected number, great
    if len(cleaned) == expected_count:
        return cleaned

    # If we got fewer, pad with [unclear]
    while len(cleaned) < expected_count:
        cleaned.append("[unclear]")

    # If we got more, truncate
    return cleaned[:expected_count]


# ============================================================
# Main pipeline
# ============================================================

async def clean_chunks_in_memory(chunks_data: list[dict]) -> list[str]:
    """
    Clean chunks without database.

    English: code-based overlap removal (sequential, no LLM).
    Nepali/mixed: dynamic batching for LLM inference.
    """
    print(f"\n🧹 Cleaning {len(chunks_data)} chunks...")

    # Separate English and mixed chunks while preserving order
    results = [None] * len(chunks_data)
    mixed_indices = []
    prev_english_raw: str | None = None

    for idx, chunk in enumerate(chunks_data):
        chunk_id = chunk["chunk_id"]
        raw_text = chunk["raw_text"]

        if is_english_chunk(raw_text):
            print(f"  Chunk {chunk_id}: English → code overlap removal")
            cleaned = clean_english_chunk(
                raw_text=raw_text,
                prev_english_raw=prev_english_raw,
            )
            results[idx] = cleaned
            prev_english_raw = raw_text
        else:
            mixed_indices.append(idx)
            prev_english_raw = None  # Reset English chain

    # Process all mixed chunks with dynamic batching
    if mixed_indices:
        mixed_chunks = [chunks_data[i] for i in mixed_indices]
        print(f"\n  📦 {len(mixed_chunks)} Nepali/mixed chunks → dynamic batching")

        # Group into batches
        batches = group_chunks_into_batches(mixed_chunks)
        print(f"  📦 Grouped into {len(batches)} batch(es)")

        # Process each batch
        batch_offset = 0
        for batch_idx, batch in enumerate(batches):
            print(f"\n  --- Batch {batch_idx + 1}/{len(batches)} ({len(batch)} chunks) ---")

            cleaned_texts = await infer_batch(batch)

            for i, cleaned in enumerate(cleaned_texts):
                results[mixed_indices[batch_offset + i]] = cleaned

            batch_offset += len(batch)

    return results


async def clean_meeting_transcripts(meeting_id: int) -> None:
    """Main cleaning pipeline for a meeting."""
    print(f"\n🧹 Starting transcript cleaning for meeting {meeting_id}...")

    async with AsyncSessionLocal() as db:
        stmt = (
            select(TranscriptChunk)
            .where(TranscriptChunk.meeting_id == meeting_id)
            .order_by(TranscriptChunk.chunk_id)
        )
        result = await db.execute(stmt)
        chunks = result.scalars().all()

        if not chunks:
            print(f"⚠️ No chunks found for meeting {meeting_id}")
            return

        print(f"📝 Found {len(chunks)} chunks")

        chunks_data = [
            {"chunk_id": c.chunk_id, "raw_text": c.raw_text or ""}
            for c in chunks
        ]

        cleaned_results = await clean_chunks_in_memory(chunks_data)

        for i, chunk in enumerate(chunks):
            chunk.cleaned_text = cleaned_results[i]

        await db.commit()
        print(f"✓ Saved {len(chunks)} cleaned chunks")