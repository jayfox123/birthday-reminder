import email.utils
import os
import smtplib
import sys
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional
from data_store import Contact, get_days_until_birthday

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def format_countdown(days_remaining: int) -> str:
    """Format countdown days into human-readable string."""
    if days_remaining == 0:
        return "Today! 🎉"
    elif days_remaining == 1:
        return "Tomorrow (1 day left)"
    else:
        return f"In {days_remaining} days"


def clean_email(addr: Optional[str]) -> str:
    """
    Clean and extract pure email address.
    Strips leading/trailing whitespace, quotes, or display names,
    safely preserving plus-addressing like orogjay+reminders@gmail.com.
    """
    if not addr:
        return ""
    addr = addr.strip()
    _, parsed = email.utils.parseaddr(addr)
    return parsed.strip() if parsed else addr


def get_badge_info(c: Contact, target_date: date) -> tuple[str, str, str]:
    """Return (badge_text, bg_color, text_color) based on contact type."""
    years = c.age_on_date(target_date)
    if c.is_deceased:
        return "In Remembrance", "#f3f4f6", "#4b5563"
    elif c.is_anniversary:
        return f"{years}th Anniversary", "#fef3c7", "#92400e"
    else:
        return f"Turning {years}", "#e0e7ff", "#4338ca"


def generate_email_subject(contacts: List[Contact], target_date: date | None = None) -> str:
    """
    Generate email subject line with countdown status or event count.
    Examples:
      - 🎂 Birthday Alert: Alice in 5 days!
      - 🎂 Birthday Alert: Alice in 1 day (Tomorrow)!
      - 🎂 Birthday Alert: Alice is Today! 🎉
      - 🎂 Birthday Alert: 2 upcoming events (Alice in 3 days)!
    """
    if not contacts:
        return "🎂 Birthday Alert: No upcoming events"

    if target_date is None:
        target_date = date.today()

    if len(contacts) == 1:
        c = contacts[0]
        days = c.days_remaining
        if days is None:
            c_target = c.target_date or target_date
            days = (c_target - target_date).days

        if days == 0:
            return f"🎂 Birthday Alert: {c.name} is Today! 🎉"
        elif days == 1:
            return f"🎂 Birthday Alert: {c.name} in 1 day (Tomorrow)!"
        else:
            return f"🎂 Birthday Alert: {c.name} in {days} days!"
    else:
        count = len(contacts)
        first = contacts[0]
        days = first.days_remaining
        if days is None:
            f_target = first.target_date or target_date
            days = (f_target - target_date).days

        if days == 0:
            status = f"{first.name} is Today! 🎉"
        elif days == 1:
            status = f"{first.name} tomorrow"
        else:
            status = f"{first.name} in {days} days"

        return f"🎂 Birthday Alert: {count} upcoming events ({status})!"


def render_html_email(contacts: List[Contact], target_date: date | None = None) -> str:
    """Render a clean, responsive HTML email template for upcoming birthdays & events."""
    if target_date is None:
        target_date = date.today()

    date_formatted = target_date.strftime("%B %d, %Y")
    count = len(contacts)

    cards_html = ""
    for c in contacts:
        c_target_date = c.target_date or target_date
        c_days = c.days_remaining
        if c_days is None:
            c_days = (c_target_date - target_date).days

        countdown_text = format_countdown(c_days)
        badge_text, bg_color, text_color = get_badge_info(c, c_target_date)

        if c_days == 0:
            countdown_bg = "#fee2e2"
            countdown_color = "#991b1b"
        elif c_days == 1:
            countdown_bg = "#fef3c7"
            countdown_color = "#92400e"
        else:
            countdown_bg = "#e0e7ff"
            countdown_color = "#3730a3"

        email_row = ""
        if c.email:
            email_row = f'<p style="margin: 4px 0;">✉️ <strong>Email:</strong> <a href="mailto:{c.email}" style="color: #4f46e5; text-decoration: none;">{c.email}</a></p>'

        notes_row = ""
        if c.notes:
            notes_row = f'<p style="margin: 4px 0; color: #6b7280; font-style: italic;">📝 <strong>Notes:</strong> {c.notes}</p>'

        cards_html += f"""
        <div style="background-color: #ffffff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 20px; margin-bottom: 16px; box-shadow: 0 2px 4px rgba(0,0,0,0.04);">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                <h3 style="margin: 0; color: #1f2937; font-size: 18px; font-weight: 600;">{c.name}</h3>
                <div style="display: flex; gap: 6px; align-items: center;">
                    <span style="background-color: {countdown_bg}; color: {countdown_color}; padding: 4px 12px; border-radius: 9999px; font-size: 12px; font-weight: 700;">
                        {countdown_text}
                    </span>
                    <span style="background-color: {bg_color}; color: {text_color}; padding: 4px 12px; border-radius: 9999px; font-size: 13px; font-weight: 600;">
                        {badge_text}
                    </span>
                </div>
            </div>
            <div style="margin-top: 12px; color: #4b5563; font-size: 14px; line-height: 1.5;">
                <p style="margin: 4px 0;">⏰ <strong>Status:</strong> <strong style="color: {countdown_color};">{countdown_text}</strong> ({c_target_date.strftime('%B %d, %Y')})</p>
                <p style="margin: 4px 0;">📅 <strong>Birthdate:</strong> {c.birthdate.strftime('%B %d, %Y')}</p>
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
                {count} upcoming event{'s' if count > 1 else ''} in the next 5 days (as of {date_formatted})
            </p>
        </div>

        <!-- Body Content -->
        <div style="padding: 24px; background-color: #f9fafb;">
            <p style="margin-top: 0; margin-bottom: 20px; color: #374151; font-size: 15px; line-height: 1.6;">
                Here are the birthdays and events happening today and over the next 5 days:
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


def render_text_email(contacts: List[Contact], target_date: date | None = None) -> str:
    """Render plain-text version of email for fallback."""
    if target_date is None:
        target_date = date.today()

    date_formatted = target_date.strftime("%B %d, %Y")
    lines = [
        f"BIRTHDAY & EVENT REMINDER - {len(contacts)} upcoming event(s) in the next 5 days (as of {date_formatted}):",
        "=" * 60,
    ]
    for c in contacts:
        c_target_date = c.target_date or target_date
        c_days = c.days_remaining
        if c_days is None:
            c_days = (c_target_date - target_date).days

        countdown_text = format_countdown(c_days)
        badge_text, _, _ = get_badge_info(c, c_target_date)
        lines.append(f"- {c.name} ({badge_text}) — {countdown_text}")
        lines.append(f"  Event Date: {c_target_date.strftime('%B %d, %Y')}")
        lines.append(f"  Birthdate: {c.birthdate.strftime('%B %d, %Y')}")
        if c.email:
            lines.append(f"  Email: {c.email}")
        if c.notes:
            lines.append(f"  Notes: {c.notes}")
        lines.append("")
    lines.append("Don't forget to prepare your wishes or gifts!")
    return "\n".join(lines)


def send_birthday_reminder(
    contacts: List[Contact],
    target_date: date | None = None,
    recipient_email: Optional[str] = None
) -> bool:
    """
    Send HTML birthday reminder email via SMTP.
    Returns True if sent or simulated successfully, False on error.
    """
    if not contacts:
        print("ℹ️ No upcoming birthdays/events to send notification for.")
        return True

    if target_date is None:
        target_date = date.today()

    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    sender_email = os.getenv("SENDER_EMAIL") or os.getenv("SMTP_USERNAME")
    sender_password = os.getenv("SENDER_PASSWORD") or os.getenv("SMTP_PASSWORD")
    recipient = recipient_email or os.getenv("RECIPIENT_EMAIL") or os.getenv("NOTIFICATION_RECIPIENT") or sender_email

    clean_sender = clean_email(sender_email)
    clean_recipient = clean_email(recipient)

    dry_run = os.getenv("DRY_RUN", "false").lower() in ("true", "1", "yes")

    subject = generate_email_subject(contacts, target_date)
    html_body = render_html_email(contacts, target_date)
    text_body = render_text_email(contacts, target_date)

    if dry_run or not clean_sender or not sender_password or not clean_recipient:
        print("\n--- [SIMULATED EMAIL NOTIFICATION] ---")
        print(f"To: {clean_recipient or '[RECIPIENT_NOT_SET]'}")
        print(f"From: {clean_sender or '[SENDER_NOT_SET]'}")
        print(f"Subject: {subject}")
        print("\n" + text_body)
        print("--------------------------------------\n")
        if not dry_run:
            print("⚠️ SMTP credentials not configured (SMTP_USERNAME/SMTP_PASSWORD). Skipped actual SMTP send.")
        return True

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = clean_sender
        msg["To"] = clean_recipient

        msg.attach(MIMEText(text_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        if int(smtp_port) == 465:
            print(f"Connecting to {smtp_server}:{smtp_port} using SSL...")
            with smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=20) as server:
                server.ehlo()
                server.login(clean_sender, sender_password)
                server.sendmail(clean_sender, [clean_recipient], msg.as_string())
        else:
            with smtplib.SMTP(smtp_server, smtp_port, timeout=15) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(clean_sender, sender_password)
                server.sendmail(clean_sender, [clean_recipient], msg.as_string())

        print(f"✅ Birthday reminder email successfully sent to {clean_recipient}")
        return True
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ Failed to send SMTP email: {e}")
        return False
