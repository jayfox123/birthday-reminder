import unittest
from datetime import date
from data_store import Contact, is_birthday_on_date, get_upcoming_birthdays, load_contacts
from email_service import render_html_email, render_text_email, send_birthday_reminder
from main import run_agent


class TestBirthdayReminder(unittest.TestCase):

    def test_contact_age_calculation(self):
        contact = Contact(name="Test User", birthdate=date(1995, 10, 15), email="test@example.com")
        target_date = date(2026, 10, 15)
        self.assertEqual(contact.age_on_date(target_date), 31)

    def test_birthday_on_date_match(self):
        bday = date(1990, 5, 20)
        target = date(2026, 5, 20)
        self.assertTrue(is_birthday_on_date(bday, target))

        other_day = date(2026, 5, 21)
        self.assertFalse(is_birthday_on_date(bday, other_day))

    def test_leap_year_birthday(self):
        leap_bday = date(1996, 2, 29) # 1996 was a leap year
        non_leap_target = date(2025, 2, 28) # 2025 non-leap
        self.assertTrue(is_birthday_on_date(leap_bday, non_leap_target))

    def test_get_upcoming_birthdays_in_5_days(self):
        base_date = date(2026, 10, 10)
        # Target date is 2026-10-15
        contacts = [
            Contact(name="Match User", birthdate=date(1995, 10, 15)),
            Contact(name="No Match", birthdate=date(1990, 10, 16)),
        ]
        upcoming = get_upcoming_birthdays(contacts, from_date=base_date, days_ahead=5)
        self.assertEqual(len(upcoming), 1)
        self.assertEqual(upcoming[0].name, "Match User")

    def test_email_rendering(self):
        contacts = [Contact(name="Alice", birthdate=date(1995, 10, 15), email="alice@example.com")]
        target_date = date(2026, 10, 15)
        html = render_html_email(contacts, target_date)
        text = render_text_email(contacts, target_date)

        self.assertIn("Alice", html)
        self.assertIn("Turning 31", html)
        self.assertIn("Alice", text)

    def test_dry_run_sending(self):
        contacts = [Contact(name="Bob", birthdate=date(1990, 10, 15), email="bob@example.com")]
        target_date = date(2026, 10, 15)
        res = send_birthday_reminder(contacts, target_date, recipient_email="dry@example.com")
        self.assertTrue(res)

    def test_run_agent_with_user_contacts(self):
        # Base date 2026-10-06 -> target 2026-10-11 (Merlita & Emay birthdays)
        exit_code = run_agent(
            contacts_file="contacts.json",
            days_ahead=5,
            base_date=date(2026, 10, 6),
            dry_run=True
        )
        self.assertEqual(exit_code, 0)


if __name__ == "__main__":
    unittest.main()
