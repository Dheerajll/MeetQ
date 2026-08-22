"""
Email Service.

Sends notification emails when meeting processing completes.
Uses Gmail SMTP via Python's built-in smtplib.
The blocking SMTP call runs in a thread executor so it never
blocks the async processing pipeline.

Setup (one-time):
1. Enable 2FA on your Google account.
2. Create an App Password: https://myaccount.google.com/apppasswords
3. Set SMTP_USERNAME and SMTP_PASSWORD in .env
"""

from __future__ import annotations

import asyncio
import smtplib
from email.message import EmailMessage

from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.models.meeting import Meeting
from app.models.summary import MeetingSummary
from app.models.user import User

settings = get_settings()


async def send_meeting_completed_email(meeting_id: int) -> None:
    """
    Send a 'meeting processed' email to the meeting owner.

    Fetches the meeting + summary + user from DB, builds an HTML email,
    and sends it via SMTP. Fails gracefully (logs, never raises) so a
    failed email doesn't break the processing pipeline.
    """
    if not settings.smtp_enabled:
        print("📧 Email disabled (smtp_enabled=False). Skipping.")
        return

    if not settings.smtp_username or not settings.smtp_password:
        print("⚠️ SMTP credentials not configured. Skipping email.")
        return

    try:
        # ──────────────────────────────────────────────
        # 1. Fetch meeting, summary, and owner
        # ──────────────────────────────────────────────
        async with AsyncSessionLocal() as db:
            meeting_stmt = select(Meeting).where(Meeting.id == meeting_id)
            meeting = (await db.execute(meeting_stmt)).scalar_one_or_none()
            if meeting is None:
                print(f"⚠️ Meeting {meeting_id} not found. Skipping email.")
                return

            summary_stmt = select(MeetingSummary).where(
                MeetingSummary.meeting_id == meeting_id
            )
            summary = (await db.execute(summary_stmt)).scalar_one_or_none()

            user_stmt = select(User).where(User.id == meeting.user_id)
            user = (await db.execute(user_stmt)).scalar_one_or_none()
            if user is None:
                print(f"⚠️ User not found for meeting {meeting_id}. Skipping.")
                return

        # ──────────────────────────────────────────────
        # 2. Build the email
        # ──────────────────────────────────────────────
        msg = _build_email(user.name, meeting.title, summary)
        msg["To"] = user.email

        # ──────────────────────────────────────────────
        # 3. Send (blocking SMTP in a thread)
        # ──────────────────────────────────────────────
        await asyncio.to_thread(_send_sync, msg)
        print(f"📧 Sent completion email to {user.email} for meeting {meeting_id}")

    except Exception as e:
        # Never let an email failure crash the processing pipeline
        print(f"❌ Failed to send email for meeting {meeting_id}: {e}")


def _build_email(
    recipient_name: str,
    meeting_title: str,
    summary: MeetingSummary | None,
) -> EmailMessage:
    """Construct the EmailMessage with an HTML body."""
    msg = EmailMessage()
    msg["Subject"] = f"Your meeting summary is ready: {meeting_title}"
    msg["From"] = settings.email_from or settings.smtp_username

    html = _render_html(recipient_name, meeting_title, summary)
    msg.set_content("Your meeting has been processed. View your summary in MeetQ.")
    msg.add_alternative(html, subtype="html")

    return msg


def _render_html(
    recipient_name: str,
    meeting_title: str,
    summary: MeetingSummary | None,
) -> str:
    """Render the HTML email body."""
    if summary is None:
        return f"""
        <html><body style="font-family:Arial,sans-serif;color:#12141a;">
            <h2>Hi {recipient_name},</h2>
            <p>Your meeting <strong>{meeting_title}</strong> finished processing,
            but no summary was generated.</p>
        </body></html>
        """

    # Build list items safely
    topics = "".join(f"<li>{t}</li>" for t in summary.key_topics)
    decisions = "".join(f"<li>{d}</li>" for d in summary.decisions)
    actions = "".join(f"<li>{a}</li>" for a in summary.action_items)

    return f"""
    <html>
    <body style="font-family:Arial,sans-serif;color:#12141a;background:#f3f5f6;padding:24px;">
      <div style="max-width:600px;margin:0 auto;background:#ffffff;border-radius:12px;
                  border:1px solid #e1e4e8;overflow:hidden;">
        <!-- Header -->
        <div style="background:#0e9f82;padding:20px 28px;">
          <h1 style="color:#ffffff;margin:0;font-size:20px;">MeetQ</h1>
        </div>

        <div style="padding:28px;">
          <h2 style="margin-top:0;">Hi {recipient_name},</h2>
          <p>Your meeting <strong>{meeting_title}</strong> has been processed.
             Here's your summary:</p>

          <!-- Overview -->
          <h3 style="color:#0e9f82;border-bottom:1px solid #e1e4e8;padding-bottom:6px;">
            Overview
          </h3>
          <p style="line-height:1.6;">{summary.overview}</p>

          <!-- Key Topics -->
          {f'''
          <h3 style="color:#0e9f82;border-bottom:1px solid #e1e4e8;padding-bottom:6px;">
            Key Topics
          </h3>
          <ul style="line-height:1.7;">{topics}</ul>
          ''' if topics else ""}

          <!-- Decisions -->
          {f'''
          <h3 style="color:#0e9f82;border-bottom:1px solid #e1e4e8;padding-bottom:6px;">
            Decisions
          </h3>
          <ul style="line-height:1.7;">{decisions}</ul>
          ''' if decisions else ""}

          <!-- Action Items -->
          {f'''
          <h3 style="color:#0e9f82;border-bottom:1px solid #e1e4e8;padding-bottom:6px;">
            Action Items
          </h3>
          <ul style="line-height:1.7;">{actions}</ul>
          ''' if actions else ""}

          <p style="margin-top:24px;color:#6b7280;font-size:13px;">
            View the full transcript and ask questions in your MeetQ dashboard.
          </p>
        </div>
      </div>
    </body>
    </html>
    """


def _send_sync(msg: EmailMessage) -> None:
    """Blocking SMTP send. Runs inside asyncio.to_thread()."""
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.starttls()
        server.login(settings.smtp_username, settings.smtp_password)
        server.send_message(msg)