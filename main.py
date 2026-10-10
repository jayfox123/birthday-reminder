import argparse
import sys
from datetime import datetime, date
from pathlib import Path
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from data_store import load_contacts, get_upcoming_birthdays
from email_service import send_birthday_reminder



def parse_args():
    parser = argparse.ArgumentParser(
        description="Birthday Reminder Agent - Detect birthdays in X days and send email alerts."
    )
    parser.add_argument(
        "--contacts",
        type=str,
        default="contacts.json",
        help="Path to contacts JSON data file (default: contacts.json)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=5,
        help="Days ahead to check for upcoming birthdays (default: 5)",
    )
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Base date for check in YYYY-MM-DD format (default: today)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate email sending without connecting to SMTP server",
    )
    return parser.parse_parse_args() if hasattr(parser, "parse_parse_args") else parser.parse_args()


def run_agent(
    contacts_file: str = "contacts.json",
    days_ahead: int = 5,
    base_date: date | None = None,
    dry_run: bool = False
) -> int:
    """Run the birthday reminder detection and notification workflow."""
    load_dotenv()

    if base_date is None:
        base_date = date.today()

    contacts_path = Path(contacts_file)
    if not contacts_path.exists():
        print(f"❌ Error: Contacts file '{contacts_path}' not found.")
        return 1

    try:
        contacts = load_contacts(contacts_path)
    except Exception as e:
        print(f"❌ Error loading contacts: {e}")
        return 1

    print(f"🔍 Loaded {len(contacts)} contacts from '{contacts_path}'")
    print(f"📅 Checking for birthdays occurring in exactly {days_ahead} days from {base_date.strftime('%Y-%m-%d')}...")

    upcoming = get_upcoming_birthdays(contacts, from_date=base_date, days_ahead=days_ahead)

    from datetime import timedelta
    target_date = base_date + timedelta(days=days_ahead)

    if not upcoming:
        print(f"✨ No birthdays found on {target_date.strftime('%Y-%m-%d')} (in {days_ahead} days).")
        return 0

    print(f"🎉 Found {len(upcoming)} birthday(s) on {target_date.strftime('%Y-%m-%d')}:")
    for contact in upcoming:
        age = contact.age_on_date(target_date)
        print(f"   • {contact.name} ({contact.email}) - Turning {age}")

    if dry_run:
        import os
        os.environ["DRY_RUN"] = "true"

    success = send_birthday_reminder(upcoming, target_date)
    return 0 if success else 1


def main():
    args = parse_args()

    base_date = None
    if args.date:
        try:
            base_date = datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            print(f"❌ Invalid date format '{args.date}'. Expected YYYY-MM-DD.")
            sys.exit(1)

    exit_code = run_agent(
        contacts_file=args.contacts,
        days_ahead=args.days,
        base_date=base_date,
        dry_run=args.dry_run
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
