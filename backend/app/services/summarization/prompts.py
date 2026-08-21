"""
All prompts for the summarization pipeline.
Generic — no domain-specific assumptions.
"""

# ============================================================
# STEP 0: Meeting Type Detection
# ============================================================

TYPE_DETECTION_SYSTEM = """You are classifying a meeting based on its opening content.

Possible types:
- technical: Software development, architecture, code review, sprint planning
- business: Strategy, sales, partnerships, revenue, clients
- educational: Lectures, training, workshops, learning sessions
- standup: Status updates, blockers, quick check-ins
- general: Anything that doesn't fit the above categories

Output ONLY the type as a single word. No explanation."""

TYPE_DETECTION_USER = """Classify this meeting based on its opening content:

{opening_chunks}

Meeting type:"""


# ============================================================
# STEP 1: Level 1 — Chunk Group Summarization
# ============================================================

LEVEL1_SYSTEM = """You are summarizing a portion of a meeting transcript.

RULES:
- Write a concise summary of what was discussed.
- Preserve all key facts: numbers, dates, names, decisions, action items.
- Do NOT add information not present in the text.
- Do NOT include speaker labels or speaker attribution.
- Write in clear, factual English.
- Output ONLY the summary. No headings, no formatting."""

LEVEL1_USER = """Summarize the following meeting transcript segment:

{chunk_group}"""


# ============================================================
# STEP 2: Higher Level Reduction
# ============================================================

REDUCE_SYSTEM = """You are combining multiple meeting summaries into one coherent summary.

RULES:
- Merge the information into a single flowing summary.
- Remove redundancy — if the same point appears multiple times, mention it once.
- Preserve all unique facts, decisions, and action items.
- Do NOT add information not present in the input.
- Do NOT include speaker labels or attribution.
- Write in clear, factual English.
- Output ONLY the combined summary. No headings, no formatting."""

REDUCE_USER = """Combine these meeting segment summaries into one coherent summary:

{summaries}"""


# ============================================================
# STEP 3: Overview Generation
# ============================================================

OVERVIEW_SYSTEM = """You are writing a final meeting overview paragraph.

RULES:
- Write ONE paragraph (4-7 sentences) that covers the meeting from start to end.
- Focus on the main purpose and flow of the meeting.
- Mention what was discussed, what was decided, and what comes next.
- Do NOT include speaker labels or attribution.
- Do NOT add information not in the source text.
- Keep it concise but comprehensive. Not too long, not too short.
- Write in natural, professional English.
- Output ONLY the paragraph. No headings, no bullet points."""

OVERVIEW_USER = """Write a meeting overview paragraph from this summarized content:

{reduced_summary}"""


# ============================================================
# STEP 4: Structured Extraction
# ============================================================

EXTRACTION_SYSTEM = """You are extracting structured information from a meeting summary.

Output a JSON object with exactly these fields:
{
    "key_topics": ["topic 1", "topic 2"],
    "decisions": ["decision 1", "decision 2"],
    "action_items": ["action 1", "action 2"]
}

RULES:
- key_topics: Main subjects discussed (3-7 items)
- decisions: Concrete decisions made (0-5 items)
- action_items: Tasks or next steps mentioned (0-7 items)
- Each item is a short, clear sentence.
- Do NOT include speaker names or attribution.
- Do NOT invent items not in the text.
- If a category has no items, use an empty list [].
- Output ONLY valid JSON. No markdown, no explanation."""

EXTRACTION_USER = """Extract structured information from this meeting summary:

{overview}

JSON output:"""