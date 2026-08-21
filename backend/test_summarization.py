"""
Test summarization pipeline on a cleaned meeting.

Usage:
    python test_summarization.py          # Interactive
    python test_summarization.py 14       # Direct
"""

import asyncio
import sys

sys.path.insert(0, ".")


async def main():
    if len(sys.argv) < 2:
        meeting_id = int(input("Enter meeting ID to summarize: "))
    else:
        meeting_id = int(sys.argv[1])

    print(f"\n{'=' * 70}")
    print(f"📝 SUMMARIZATION TEST — Meeting {meeting_id}")
    print(f"{'=' * 70}")

    from app.services.summarization import summarize_meeting
    await summarize_meeting(meeting_id)

    # Display results from DB
    await display_summary(meeting_id)


async def display_summary(meeting_id: int):
    """Print the stored summary."""
    from app.core.database import AsyncSessionLocal
    from app.models.summary import MeetingSummary
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        stmt = select(MeetingSummary).where(MeetingSummary.meeting_id == meeting_id)
        result = await db.execute(stmt)
        summary = result.scalar_one_or_none()

    if not summary:
        print("\n⚠️ No summary found.")
        return

    print(f"\n{'=' * 70}")
    print("RESULT")
    print(f"{'=' * 70}")
    print(f"\n  Type: {summary.meeting_type}")
    print(f"\n  Overview:")
    print(f"  {summary.overview}")
    print(f"\n  Key Topics:")
    for t in summary.key_topics:
        print(f"    • {t}")
    print(f"\n  Decisions:")
    for d in summary.decisions:
        print(f"    • {d}")
    print(f"\n  Action Items:")
    for a in summary.action_items:
        print(f"    • {a}")
    print(f"\n{'=' * 70}")


if __name__ == "__main__":
    asyncio.run(main())