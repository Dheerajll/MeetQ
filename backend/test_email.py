import asyncio
import sys
sys.path.insert(0, ".")

async def main():
    meeting_id = int(sys.argv[1]) if len(sys.argv) > 1 else int(input("Meeting ID: "))
    from app.services.email_service import send_meeting_completed_email
    await send_meeting_completed_email(meeting_id)

asyncio.run(main())