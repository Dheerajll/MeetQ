"""
English overlap detection and removal.

Uses code-based word matching (exact + fuzzy) to find and remove
overlapping content between consecutive English chunks.
No LLM involved.
"""

from __future__ import annotations

from app.services.cleaning.text_utils import (
    SPEAKER_LABEL_PATTERN,
    strip_speaker_labels,
    get_leading_speaker_label,
    starts_with_speaker_label,
)


# ============================================================
# Word normalization
# ============================================================

def normalize_word(word: str) -> str:
    """Normalize a word for comparison (lowercase, strip punctuation)."""
    return word.lower().strip(".,!?;:…'\"""''()[]{}")


# ============================================================
# Overlap detection
# ============================================================

def find_word_overlap(
    prev_text: str,
    curr_text: str,
    min_words: int = 3,
    max_words: int = 30,
) -> int:
    """
    Find overlapping words between end of prev_text and start of curr_text.
    
    Returns the number of overlapping words (0 if none found).
    
    Uses two passes:
    1. Exact suffix-prefix match
    2. Fuzzy match (75% threshold)
    """
    if not prev_text or not curr_text:
        return 0

    clean_prev = strip_speaker_labels(prev_text)
    clean_curr = strip_speaker_labels(curr_text)

    prev_words = clean_prev.split()
    curr_words = clean_curr.split()

    if not prev_words or not curr_words:
        return 0

    max_window = min(len(prev_words), len(curr_words), max_words)

    # Pass 1: Exact match
    for window in range(max_window, min_words - 1, -1):
        suffix = [normalize_word(w) for w in prev_words[-window:]]
        prefix = [normalize_word(w) for w in curr_words[:window]]
        if suffix == prefix:
            return window

    # Pass 2: Fuzzy match (75% threshold)
    for window in range(max_window, min_words - 1, -1):
        suffix = [normalize_word(w) for w in prev_words[-window:]]
        prefix = [normalize_word(w) for w in curr_words[:window]]
        matches = sum(1 for a, b in zip(suffix, prefix) if a == b)
        if matches / window >= 0.75:
            return window

    return 0


# ============================================================
# Overlap removal
# ============================================================

def skip_words_in_raw(raw_text: str, words_to_skip: int) -> int:
    """
    Find character position after skipping N actual words.
    Speaker labels are skipped but not counted as words.
    """
    words_skipped = 0
    pos = 0

    while pos < len(raw_text) and words_skipped < words_to_skip:
        # Skip speaker labels
        speaker_match = SPEAKER_LABEL_PATTERN.match(raw_text, pos)
        if speaker_match:
            pos = speaker_match.end()
            continue

        # Skip whitespace
        if raw_text[pos].isspace():
            pos += 1
            continue

        # Consume one word
        while pos < len(raw_text) and not raw_text[pos].isspace():
            if SPEAKER_LABEL_PATTERN.match(raw_text, pos):
                break
            pos += 1

        words_skipped += 1

    # Skip trailing whitespace
    while pos < len(raw_text) and raw_text[pos].isspace():
        pos += 1

    return pos


def clean_english_chunk(
    raw_text: str,
    prev_english_raw: str | None,
) -> str:
    """
    Clean an English chunk by removing overlap with the previous chunk.
    
    No LLM involved — pure code-based overlap detection and removal.
    """
    if prev_english_raw is None:
        return raw_text

    overlap_words = find_word_overlap(prev_english_raw, raw_text)

    if overlap_words <= 0:
        return raw_text

    # Skip the overlapping words
    skip_pos = skip_words_in_raw(raw_text, overlap_words)
    trimmed = raw_text[skip_pos:].strip()

    # Preserve speaker label if trimming removed it
    leading_speaker = get_leading_speaker_label(raw_text)
    if leading_speaker and trimmed and not starts_with_speaker_label(trimmed):
        trimmed = f"{leading_speaker} {trimmed}"

    return trimmed