"""
Transcript Cleaning Service — v3 (Word-level overlap detection).

Key insight: The overlap between chunks is the SAME AUDIO transcribed twice.
So the overlapping words will be EXACTLY identical. We use exact word matching,
not fuzzy character matching.
"""
import re
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.transcript import TranscriptChunk
from app.ai.ollama_client import ollama
from app.ai.prompts import (
    TRANSLATE_SYSTEM_PROMPT,
    TRANSLATE_FIRST_CHUNK_PROMPT,
    TRANSLATE_WITH_CONTEXT_PROMPT,
)


# ============================================================
# WORD-LEVEL OVERLAP DETECTION
# ============================================================

def strip_speaker_labels(text: str) -> str:
    """Remove all [Speaker N] labels from text."""
    return re.sub(r'\[Speaker \d+\]\s*', '', text).strip()


def find_word_overlap(raw_prev: str, raw_curr: str, min_words: int = 3) -> int:
    """
    Find overlapping WORDS between end of raw_prev and start of raw_curr.
    
    Uses exact word matching since the overlap is the same audio
    transcribed twice by Whisper.
    
    Returns:
        Number of overlapping words (0 if none found).
    """
    if not raw_prev or not raw_curr:
        return 0
    
    # Strip speaker labels and split into words
    clean_prev = strip_speaker_labels(raw_prev)
    clean_curr = strip_speaker_labels(raw_curr)
    
    words_prev = clean_prev.split()
    words_curr = clean_curr.split()
    
    if not words_prev or not words_curr:
        return 0
    
    # Try from largest possible overlap down to minimum
    max_words = min(len(words_prev), len(words_curr), 30)
    
    for window in range(max_words, min_words - 1, -1):
        suffix = words_prev[-window:]
        prefix = words_curr[:window]
        
        # Exact word match (case-insensitive)
        suffix_lower = [w.lower().strip('.,!?;:') for w in suffix]
        prefix_lower = [w.lower().strip('.,!?;:') for w in prefix]
        
        if suffix_lower == prefix_lower:
            return window
    
    return 0


def skip_words_in_raw(raw_text: str, words_to_skip: int) -> int:
    """
    Find the character position in raw_text after skipping N words.
    Accounts for speaker labels (skips them without counting as words).
    
    Returns:
        Character position to start reading from.
    """
    words_skipped = 0
    pos = 0
    
    while pos < len(raw_text) and words_skipped < words_to_skip:
        # Skip speaker labels
        speaker_match = re.match(r'\[Speaker \d+\]\s*', raw_text[pos:])
        if speaker_match:
            pos += speaker_match.end()
            continue
        
        # Skip whitespace
        if raw_text[pos].isspace():
            pos += 1
            continue
        
        # We're at a word — consume it
        while pos < len(raw_text) and not raw_text[pos].isspace():
            # Stop if we hit a speaker label mid-word
            if raw_text[pos:].startswith('[Speaker'):
                break
            pos += 1
        
        words_skipped += 1
    
    # Skip trailing whitespace
    while pos < len(raw_text) and raw_text[pos].isspace():
        pos += 1
    
    return pos


# ============================================================
# TRANSLATION
# ============================================================

async def translate_chunk_with_context(
    raw_text: str,
    prev_translated: str | None = None,
) -> str:
    """Translate a chunk, using previous translation as context."""
    if not raw_text.strip():
        return ""
    
    if prev_translated is None:
        prompt = TRANSLATE_FIRST_CHUNK_PROMPT.format(raw_text=raw_text)
    else:
        # Give generous context (last 300 chars)
        prev_ending = prev_translated[-300:] if len(prev_translated) > 300 else prev_translated
        prompt = TRANSLATE_WITH_CONTEXT_PROMPT.format(
            prev_chunk_ending=prev_ending,
            raw_text=raw_text,
        )
    
    try:
        result = await ollama.generate(prompt, system_prompt=TRANSLATE_SYSTEM_PROMPT)
        return result.strip()
    except Exception as e:
        print(f"     ⚠️ Translation failed: {e}")
        return raw_text


# ============================================================
# IN-MEMORY CLEANING (for testing)
# ============================================================

async def clean_chunks_in_memory(chunks_data: list[dict]) -> list[str]:
    """Clean chunks without database (for testing)."""
    print(f"\n🧹 Cleaning {len(chunks_data)} chunks...")
    print(f"   Strategy: Exact word overlap → Trim → Translate with context\n")
    
    cleaned_results = []
    prev_raw = None
    prev_translated = None
    
    for chunk in chunks_data:
        chunk_id = chunk["chunk_id"]
        raw_text = chunk["raw_text"]
        
        print(f"  --- Chunk {chunk_id} ---")
        print(f"  RAW: {raw_text[:90]}...")
        
        # Step 1: Detect word-level overlap
        overlap_words = 0
        if prev_raw is not None:
            overlap_words = find_word_overlap(prev_raw, raw_text)
        
        # Step 2: Trim overlap from raw text
        if overlap_words > 0:
            skip_pos = skip_words_in_raw(raw_text, overlap_words)
            trimmed_raw = raw_text[skip_pos:].strip()
            
            # Show what was trimmed
            trimmed_portion = raw_text[:skip_pos].strip()
            print(f"  OVERLAP: {overlap_words} words → \"{trimmed_portion[:60]}\"")
            print(f"  TRIMMED: \"{trimmed_raw[:70]}...\"")
        else:
            trimmed_raw = raw_text
            print(f"  OVERLAP: None detected")
        
        # Step 3: Translate
        if not trimmed_raw.strip():
            print(f"  RESULT: (empty — entire chunk was overlap)\n")
            cleaned_results.append("")
            prev_raw = raw_text
            continue
        
        cleaned = await translate_chunk_with_context(
            raw_text=trimmed_raw,
            prev_translated=prev_translated,
        )
        
        cleaned_results.append(cleaned)
        prev_raw = raw_text
        prev_translated = cleaned
        
        print(f"  RESULT: {cleaned}\n")
    
    return cleaned_results


# ============================================================
# DATABASE CLEANING (for production)
# ============================================================

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
            print(f"⚠️ No transcript chunks found for meeting {meeting_id}")
            return
        
        print(f"📝 Found {len(chunks)} chunks to clean")
        
        chunks_data = [
            {"chunk_id": c.chunk_id, "raw_text": c.raw_text}
            for c in chunks
        ]
        
        cleaned_results = await clean_chunks_in_memory(chunks_data)
        
        for i, chunk in enumerate(chunks):
            chunk.cleaned_text = cleaned_results[i]
        
        await db.commit()
        print(f"✓ Saved {len(chunks)} cleaned chunks to database")