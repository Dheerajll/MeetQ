"""
Query Parser Service.

Analyzes natural language queries to extract time-based filters
before performing vector search.

Handles:
- "yesterday" → full day range (00:00 to 23:59)
- "last week" → previous Monday to Sunday
- "this week" → current Monday to now
- "today" → current day
- "last Sunday", "last Friday" → specific day via dateparser
- "2 days ago", "3 weeks ago" → relative dates via dateparser

Uses the `dateparser` library for flexible natural language date parsing.
No LLM call needed — instant and deterministic.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from dataclasses import dataclass

import dateparser


@dataclass
class ParsedQuery:
    """The result of parsing a user query."""
    original_query: str
    search_query: str
    start_date: datetime | None
    end_date: datetime | None


def parse_query(raw_query: str) -> ParsedQuery:
    """
    Parse a natural language query into time filters.

    Returns a ParsedQuery with:
    - search_query: The text to embed for semantic search
    - start_date / end_date: Time range filters (None if no time reference found)
    """
    query_lower = raw_query.lower()

    start_date = None
    end_date = None

    # ──────────────────────────────────────────────
    # 1. Check for explicit relative ranges (Regex)
    #    These are handled better by logic than dateparser
    # ──────────────────────────────────────────────

    # "last week" → Previous Monday 00:00 to Sunday 23:59
    if "last week" in query_lower:
        today = datetime.now(timezone.utc)
        last_monday = today - timedelta(days=today.weekday() + 7)
        last_sunday = last_monday + timedelta(days=6)
        start_date = last_monday.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = last_sunday.replace(hour=23, minute=59, second=59, microsecond=999999)

    # "this week" → Current Monday 00:00 to now
    elif "this week" in query_lower:
        today = datetime.now(timezone.utc)
        this_monday = today - timedelta(days=today.weekday())
        start_date = this_monday.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = today

    # "yesterday" → Full day range
    elif "yesterday" in query_lower:
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        start_date = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)

    # "today" → From midnight to now
    elif "today" in query_lower:
        today = datetime.now(timezone.utc)
        start_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = today

    # ──────────────────────────────────────────────
    # 2. Fallback to dateparser for specific dates
    #    Handles: "last Sunday", "last Friday", "Aug 12th", "2 days ago"
    # ──────────────────────────────────────────────
    else:
        parsed_date = dateparser.parse(
            raw_query,
            settings={
                "RELATIVE_BASE": datetime.now(timezone.utc),
                "PREFER_DAY_OF_MONTH": "first",
            },
        )

        if parsed_date:
            # Ensure timezone-aware
            if parsed_date.tzinfo is None:
                parsed_date = parsed_date.replace(tzinfo=timezone.utc)

            # Set range to the full day of the parsed date
            start_date = parsed_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = parsed_date.replace(hour=23, minute=59, second=59, microsecond=999999)

    return ParsedQuery(
        original_query=raw_query,
        search_query=raw_query,  # We still embed the full query for semantic matching
        start_date=start_date,
        end_date=end_date,
    )