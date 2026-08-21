"""
Text utilities: speaker label handling and language detection.
"""

from __future__ import annotations

import re


# ============================================================
# Speaker label handling
# ============================================================

SPEAKER_LABEL_PATTERN = re.compile(
    r"\[speaker\s*\d+\]\s*",
    re.IGNORECASE,
)


def strip_speaker_labels(text: str) -> str:
    """Remove all speaker labels from text."""
    return SPEAKER_LABEL_PATTERN.sub("", text).strip()


def get_leading_speaker_label(text: str) -> str | None:
    """Return the leading speaker label if text starts with one."""
    match = SPEAKER_LABEL_PATTERN.match(text)
    if match:
        return match.group().strip()
    return None


def starts_with_speaker_label(text: str) -> bool:
    """Check whether text starts with a speaker label."""
    return SPEAKER_LABEL_PATTERN.match(text.strip()) is not None


# ============================================================
# Language detection
# ============================================================

# Unicode ranges for Indic scripts
INDIC_SCRIPT_RANGES = [
    (0x0900, 0x097F),  # Devanagari (Hindi, Nepali, Marathi)
    (0x0980, 0x09FF),  # Bengali
    (0x0A00, 0x0A7F),  # Gurmukhi
    (0x0A80, 0x0AFF),  # Gujarati
    (0x0B00, 0x0B7F),  # Oriya
    (0x0B80, 0x0BFF),  # Tamil
    (0x0C00, 0x0C7F),  # Telugu
    (0x0C80, 0x0CFF),  # Kannada
    (0x0D00, 0x0D7F),  # Malayalam
]


def contains_indic_script(text: str) -> bool:
    """Check if text contains any Indic script characters."""
    for char in text:
        code = ord(char)
        for start, end in INDIC_SCRIPT_RANGES:
            if start <= code <= end:
                return True
    return False


def is_english_chunk(text: str) -> bool:
    """
    Determine if a chunk is English (no LLM needed) or mixed (needs LLM).
    
    Returns True if the chunk is purely English/Latin script.
    Returns False if it contains Indic script (Nepali/mixed).
    """
    if not text.strip():
        return True

    clean = strip_speaker_labels(text)
    if not clean.strip():
        return True

    return not contains_indic_script(clean)