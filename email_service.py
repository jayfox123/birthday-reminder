import os
import smtplib
import sys
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional
from data_store import Contact

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def get_badge_info(c: Contact, target_date: date) -> tuple[str, str, str]:
    """Return (badge_text, bg_color, text_color) based on contact type."""
    years = c.age_on_date(target_date)
    if c.is_deceased:
        return "In Remembrance", "#f3f4f6", "#4b5563"
    elif c.is_anniversary:
        return f"{years}th Anniversary", "#fef3c7", "#92400e"
    else:
        return f"Turning {years}", "#e0e7ff", "#4338ca"


def render_html_email(contacts: List[Contact], target_date: date) -> str:
    """Render a clean, responsive HTML email template for upcoming birthdays & events."""
    date_formatted = target_date.strftime("%B %d, %Y")
    count = len(contacts)

    cards_html = ""
    for c in contacts:
        badge_text, bg_color, text_color = get_badge_info(c, target_date)

        email_row = ""
        if c.email:
            email_row = f'<p style="margin: 4px 0;">✉️ <strong>Email:</strong> <a href="mailto:{c.email}" style="color: #4f46e5; text-decoration: none;">{c.email}</a></p>'

        notes_row = ""
        if c.notes:
            notes_row = f'<p style="margin: 4px 0; color: #6b7280; font-style: italic;">📝 <strong>Notes:</strong> {c.notes}</p>'

        cards_html += f"""
        <div style="background-color: #ffffff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 20px; margin-bottom: 16px; box-shadow: 0 2px 4px rgba(0,0,0,0.04);">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h3 style="margin: 0; color: #1f2937; font-size: 18px; font-weight: 600;">{c.name}</h3>
                <span style="background-color: {bg_color}; color: {text_color}; padding: 4px 12px; border-radius: 9999px; font-size: 13px; font-weight: 600;">
                    {badge_text}
                </span>
            </div>
            <div style="margin-top: 12px; color: #4b5563; font-size: 14px; line-height: 1.5;">
                <p style="margin: 4px 0;">📅 <strong>Date:</strong> {c.birthdate.strftime('%B %d, %Y')}</p>
                {email_row}
                {notes_row}
            </div>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Upcoming Birthday & Event Reminder</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f3f4f6; margin: 0; padding: 24px;">
    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);">
        <!-- Header Banner -->
        <div style="background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); padding: 32px 24px; text-align: center; color: #ffffff;">
            <div style="font-size: 48px; margin-bottom: 8px;">🎈</div>
            <h1 style="margin: 0; font-size: 24px; font-weight: 700; letter-spacing: -0.025em;">Birthday & Event Alert!</h1>
            <p style="margin-top: 8px; margin-bottom: 0; font-size: 15px; color: #e0e7ff;">
                {count} event{'s' if count > 1 else ''} coming up in <strong>5 days</strong> on {date_formatted}
            </p>
        </div>

        <!-- Body Content -->
        <div style="padding: 24px; background-color: #f9fafb;">
            <p style="margin-top: 0; margin-bottom: 20px; color: #374151; font-size: 15px; line-height: 1.6;">
                Here are the upcoming birthdays and events occurring in exactly 5 days:
            </p>
            {cards_html}
        </div>

        <!-- Footer -->
        <div style="padding: 20px; background-color: #ffffff; border-top: 1px solid #f3f4f6; text-align: center; color: #9ca3af; font-size: 12px;">
            <p style="margin: 0;">Automated Birthday Reminder Agent • Running daily check</p>
        </div>
    </div>
</body>
</html>
"""
    return html


def render_text_email(contacts: List[Contact], target_date: date) -> str:
    """Render plain-text version of email for fallback."""
    date_formatted = target_date.strftime("%B %d, %Y")
    lines = [
        f"BIRTHDAY & EVENT REMINDER - {len(contacts)} upcoming event(s) on {date_formatted} (in 5 days):",
        "=" * 60,
    ]
    for c in contacts:
        badge_text, _, _ = get_badge_info(c, target_date)
        lines.append(f"- {c.name} ({badge_text})")
        lines.append(f"  Date: {c.birthdate.strftime('%B %d, %Y')}")
        if c.email:
            lines.append(f"  Email: {c.email}")
        if c.notes:
            lines.append(f"  Notes: {c.notes}")
        lines.append("")
    lines.append("Don't forget to prepare your wishes or gifts!")
    return "\n".join(lines)


def send_birthday_reminder(
    contacts: List[Contact],
    target_date: date,
    recipient_email: Optional[str] = None
) -> bool:
    """
    Send HTML birthday reminder email via SMTP.
    Returns True if sent or simulated successfully, False on error.
    """
    if not contacts:
        print("ℹ️ No upcoming birthdays/events to send notification for.")
        return True

    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    sender_email = os.getenv("SENDER_EMAIL") or os.getenv("SMTP_USERNAME")
    sender_password = os.getenv("SENDER_PASSWORD") or os.getenv("SMTP_PASSWORD")
    recipient = recipient_email or os.getenv("RECIPIENT_EMAIL") or os.getenv("NOTIFICATION_RECIPIENT") or sender_email


    dry_run = os.getenv("DRY_RUN", "false").lower() in ("true", "1", "yes")

    subject = f"🎂 Birthday Alert: {len(contacts)} upcoming event{'s' if len(contacts) > 1 else ''} on {target_date.strftime('%b %d')}!"
    html_body = render_html_email(contacts, target_date)
    text_body = render_text_email(contacts, target_date)

    if dry_run or not sender_email or not sender_password or not recipient:
        print("\n--- [SIMULATED EMAIL NOTIFICATION] ---")
        print(f"To: {recipient or '[RECIPIENT_NOT_SET]'}")
        print(f"From: {sender_email or '[SENDER_NOT_SET]'}")
        print(f"Subject: {subject}")
        print("\n" + text_body)
        print("--------------------------------------\n")
        if not dry_run:
            print("⚠️ SMTP credentials not configured (SMTP_USERNAME/SMTP_PASSWORD). Skipped actual SMTP send.")
        return True

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = recipient

        msg.attach(MIMEText(text_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        if int(smtp_port) == 465:
            print(f"Connecting to {smtp_server}:{smtp_port} using SSL...")
            with smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=15) as server:
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, [recipient], msg.as_string())
        else:
            with smtplib.SMTP(smtp_server, smtp_port, timeout=15) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, [recipient], msg.as_string())

        print(f"✅ Birthday reminder email successfully sent to {recipient}")
        return True
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ Failed to send SMTP email: {e}")
        return False


