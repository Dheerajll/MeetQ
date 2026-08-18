"""
Transcript Cleaning Service — v4 with debug output.
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
# SPEAKER LABEL HANDLING (case-insensitive!)
# ============================================================

SPEAKER_LABEL_PATTERN = re.compile(r'\[speaker\s*\d+\]\s*', re.IGNORECASE)


def strip_speaker_labels(text: str) -> str:
    """Remove all [Speaker N] / [speaker N] labels from text."""
    return SPEAKER_LABEL_PATTERN.sub('', text).strip()


# ============================================================
# WORD-LEVEL OVERLAP DETECTION
# ============================================================

def find_word_overlap(raw_prev: str, raw_curr: str, min_words: int = 3) -> int:
    """
    Find overlapping WORDS between end of raw_prev and start of raw_curr.
    
    Pass 1: Exact word matching
    Pass 2: Fuzzy matching (allows 1 word difference per 5 words)
    
    Returns: Number of overlapping words (0 if none).
    """
    if not raw_prev or not raw_curr:
        return 0
    
    clean_prev = strip_speaker_labels(raw_prev)
    clean_curr = strip_speaker_labels(raw_curr)
    
    words_prev = clean_prev.split()
    words_curr = clean_curr.split()
    
    if not words_prev or not words_curr:
        return 0
    
    max_words = min(len(words_prev), len(words_curr), 30)
    
    # Pass 1: Exact matching (from largest to smallest)
    for window in range(max_words, min_words - 1, -1):
        suffix = [w.lower().strip('.,!?;:…\'"') for w in words_prev[-window:]]
        prefix = [w.lower().strip('.,!?;:…\'"') for w in words_curr[:window]]
        
        if suffix == prefix:
            print(f"    [DEBUG] Exact match found at window={window}")
            print(f"    [DEBUG] Suffix: {' '.join(words_prev[-window:])}")
            return window
    
    # Pass 2: Fuzzy matching (handles Whisper inconsistencies like "on" vs "in")
    for window in range(max_words, min_words - 1, -1):
        suffix = [w.lower().strip('.,!?;:…\'"') for w in words_prev[-window:]]
        prefix = [w.lower().strip('.,!?;:…\'"') for w in words_curr[:window]]
        
        matches = sum(1 for a, b in zip(suffix, prefix) if a == b)
        match_ratio = matches / window if window > 0 else 0
        
        # Allow 75% match (handles minor Whisper differences)
        if match_ratio >= 0.75:
            print(f"    [DEBUG] Fuzzy match at window={window}, ratio={match_ratio:.2f}")
            print(f"    [DEBUG] Suffix: {' '.join(words_prev[-window:])}")
            print(f"    [DEBUG] Prefix: {' '.join(words_curr[:window])}")
            return window
    
    return 0


def skip_words_in_raw(raw_text: str, words_to_skip: int) -> int:
    """
    Find the character position after skipping N words in raw text.
    Properly handles speaker labels (case-insensitive).
    
    Returns: Character position to start reading from.
    """
    words_skipped = 0
    pos = 0
    
    while pos < len(raw_text) and words_skipped < words_to_skip:
        # Skip speaker labels (case-insensitive)
        speaker_match = SPEAKER_LABEL_PATTERN.match(raw_text, pos)
        if speaker_match:
            pos = speaker_match.end()
            continue
        
        # Skip whitespace
        if raw_text[pos].isspace():
            pos += 1
            continue
        
        # Consume one word (until whitespace or speaker label)
        while pos < len(raw_text) and not raw_text[pos].isspace():
            # Check if we hit a speaker label
            if SPEAKER_LABEL_PATTERN.match(raw_text, pos):
                break
            pos += 1
        
        words_skipped += 1
    
    # Skip trailing whitespace
    while pos < len(raw_text) and raw_text[pos].isspace():
        pos += 1
    
    return pos


# ============================================================
# ENGLISH DETECTION
# ============================================================

def is_mostly_english(text: str) -> bool:
    """Detect if text is already English (skip LLM if True)."""
    if not text.strip():
        return True
    
    clean = strip_speaker_labels(text)
    if not clean.strip():
        return True
    
    # Check for Devanagari characters
    for char in clean:
        if '\u0900' <= char <= '\u097F':
            return False
    
    # Check for common Roman Nepali indicators
    roman_nepali_words = {
        'huncha', 'parcha', 'garna', 'garnu', 'garchu', 'garnechu',
        'cha', 'chha', 'chaina', 'haina', 'tara', 'ani', 'bhane',
        'maile', 'hamile', 'timile', 'tapai', 'bholi', 'aaja', 'hijo',
        'samma', 'thik', 'hajur', 'kura', 'baare', 'lagcha', 'sakincha',
        'rakhnu', 'jane', 'janu', 'herchu', 'pathaune', 'pathaunu',
        'bhannu', 'sunnu', 'kasari', 'kasto', 'kati', 'kaile',
        'chahi', 'chahincha', 'tespachi', 'dherai',
    }
    
    words = clean.lower().split()
    if not words:
        return True
    
    nepali_count = sum(1 for w in words if w.strip('.,!?;:') in roman_nepali_words)
    
    if len(words) > 0 and nepali_count / len(words) > 0.10:
        return False
    
    return True


# ============================================================
# TRANSLATION
# ============================================================

async def translate_chunk_with_context(
    raw_text: str,
    prev_translated: str | None = None,
) -> str:
    """Translate a chunk with context."""
    if not raw_text.strip():
        return ""
    
    if prev_translated is None:
        prompt = TRANSLATE_FIRST_CHUNK_PROMPT.format(raw_text=raw_text)
    else:
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
# MAIN CLEANING PIPELINE
# ============================================================

async def clean_chunks_in_memory(chunks_data: list[dict]) -> list[str]:
    """Clean chunks without database (for testing)."""
    print(f"\n🧹 Cleaning {len(chunks_data)} chunks...")
    
    cleaned_results = []
    prev_raw = None
    prev_translated = None
    
    for chunk in chunks_data:
        chunk_id = chunk["chunk_id"]
        raw_text = chunk["raw_text"]
        
        print(f"\n  --- Chunk {chunk_id} ---")
        print(f"  RAW: {raw_text[:80]}...")
        
        # Step 1: Detect overlap
        overlap_words = 0
        if prev_raw is not None:
            overlap_words = find_word_overlap(prev_raw, raw_text)
        
        # Step 2: Trim overlap
        if overlap_words > 0:
            skip_pos = skip_words_in_raw(raw_text, overlap_words)
            trimmed_raw = raw_text[skip_pos:].strip()
            overlap_shown = raw_text[:skip_pos].strip()
            print(f"  OVERLAP: {overlap_words} words → \"{overlap_shown[:60]}\"")
            print(f"  TRIMMED: \"{trimmed_raw[:70]}...\"")
        else:
            trimmed_raw = raw_text
            print(f"  OVERLAP: None detected")
        
        # Step 3: Translate or keep as-is
        if not trimmed_raw.strip():
            print(f"  RESULT: (empty)")
            cleaned_results.append("")
            prev_raw = raw_text
            continue
        
        if is_mostly_english(trimmed_raw):
            print(f"  LANG: English → keeping as-is")
            cleaned = trimmed_raw
        else:
            print(f"  LANG: Nepali/mixed → translating")
            cleaned = await translate_chunk_with_context(
                raw_text=trimmed_raw,
                prev_translated=prev_translated,
            )
        
        cleaned_results.append(cleaned)
        prev_raw = raw_text
        prev_translated = cleaned
        
        print(f"  RESULT: {cleaned[:100]}...")
    
    return cleaned_results


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
            {"chunk_id": c.chunk_id, "raw_text": c.raw_text}
            for c in chunks
        ]
        
        cleaned_results = await clean_chunks_in_memory(chunks_data)
        
        for i, chunk in enumerate(chunks):
            chunk.cleaned_text = cleaned_results[i]
        
        await db.commit()
        print(f"✓ Saved {len(chunks)} cleaned chunks")