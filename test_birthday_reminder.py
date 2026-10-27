import unittest
from datetime import date
from data_store import (
    Contact,
    is_birthday_on_date,
    get_days_until_birthday,
    get_upcoming_birthdays,
    load_contacts,
)
from email_service import (
    format_countdown,
    clean_email,
    generate_email_subject,
    render_html_email,
    render_text_email,
    send_birthday_reminder,
)
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
        leap_bday = date(1996, 2, 29)  # 1996 was a leap year
        non_leap_target = date(2025, 2, 28)  # 2025 non-leap
        self.assertTrue(is_birthday_on_date(leap_bday, non_leap_target))

    def test_get_days_until_birthday_and_year_transition(self):
        # Today: Dec 30, Birthday: Jan 2 -> 3 days remaining in next year
        base_date = date(2026, 12, 30)
        days, next_bday = get_days_until_birthday(date(1990, 1, 2), base_date)
        self.assertEqual(days, 3)
        self.assertEqual(next_bday, date(2027, 1, 2))

        # Birthday today: Oct 27
        today = date(2026, 10, 27)
        days, next_bday = get_days_until_birthday(date(1995, 10, 27), today)
        self.assertEqual(days, 0)
        self.assertEqual(next_bday, today)

        # Birthday yesterday: Oct 26 -> next year
        days, next_bday = get_days_until_birthday(date(1995, 10, 26), today)
        self.assertGreater(days, 300)

    def test_get_upcoming_birthdays_range_0_to_5(self):
        base_date = date(2026, 10, 10)
        contacts = [
            Contact(name="Today Contact", birthdate=date(1995, 10, 10)),   # 0 days (Oct 10)
            Contact(name="Tomorrow Contact", birthdate=date(1992, 10, 11)), # 1 day (Oct 11)
            Contact(name="In 5 Days", birthdate=date(1990, 10, 15)),        # 5 days (Oct 15)
            Contact(name="In 6 Days (Excluded)", birthdate=date(1988, 10, 16)), # 6 days (Oct 16)
            Contact(name="Yesterday (Excluded)", birthdate=date(1985, 10, 9)),  # Passed
        ]
        upcoming = get_upcoming_birthdays(contacts, from_date=base_date, days_ahead=5)
        names = [c.name for c in upcoming]

        self.assertEqual(len(upcoming), 3)
        self.assertIn("Today Contact", names)
        self.assertIn("Tomorrow Contact", names)
        self.assertIn("In 5 Days", names)
        self.assertNotIn("In 6 Days (Excluded)", names)
        self.assertNotIn("Yesterday (Excluded)", names)

        # Verify sorted by days_remaining ascending
        self.assertEqual(upcoming[0].days_remaining, 0)
        self.assertEqual(upcoming[1].days_remaining, 1)
        self.assertEqual(upcoming[2].days_remaining, 5)

    def test_format_countdown(self):
        self.assertEqual(format_countdown(0), "Today! 🎉")
        self.assertEqual(format_countdown(1), "Tomorrow (1 day left)")
        self.assertEqual(format_countdown(2), "In 2 days")
        self.assertEqual(format_countdown(5), "In 5 days")

    def test_clean_email_and_plus_addressing(self):
        self.assertEqual(clean_email("orogjay+reminders@gmail.com"), "orogjay+reminders@gmail.com")
        self.assertEqual(clean_email("  orogjay+reminders@gmail.com \n"), "orogjay+reminders@gmail.com")
        self.assertEqual(clean_email("Jay Orog <orogjay+reminders@gmail.com>"), "orogjay+reminders@gmail.com")
        self.assertEqual(clean_email(None), "")
        self.assertEqual(clean_email(""), "")

    def test_email_subject_countdown(self):
        c_today = Contact(name="Alice", birthdate=date(1995, 10, 10), days_remaining=0)
        self.assertIn("Alice is Today! 🎉", generate_email_subject([c_today]))

        c_tomorrow = Contact(name="Bob", birthdate=date(1992, 10, 11), days_remaining=1)
        self.assertIn("Bob in 1 day (Tomorrow)!", generate_email_subject([c_tomorrow]))

        c_in_4 = Contact(name="Charlie", birthdate=date(1990, 10, 14), days_remaining=4)
        self.assertIn("Charlie in 4 days!", generate_email_subject([c_in_4]))

        # Multiple events
        subject_multi = generate_email_subject([c_today, c_tomorrow])
        self.assertIn("2 upcoming events", subject_multi)
        self.assertIn("Alice is Today! 🎉", subject_multi)

    def test_email_rendering_with_countdown(self):
        contacts = [
            Contact(name="Alice", birthdate=date(1995, 10, 10), days_remaining=0, email="alice@example.com"),
            Contact(name="Bob", birthdate=date(1992, 10, 11), days_remaining=1),
        ]
        target_date = date(2026, 10, 10)
        html = render_html_email(contacts, target_date)
        text = render_text_email(contacts, target_date)

        self.assertIn("Today! 🎉", html)
        self.assertIn("Tomorrow (1 day left)", html)
        self.assertIn("Today! 🎉", text)
        self.assertIn("Tomorrow (1 day left)", text)

    def test_dry_run_sending(self):
        contacts = [Contact(name="Bob", birthdate=date(1990, 10, 15), days_remaining=3)]
        target_date = date(2026, 10, 12)
        res = send_birthday_reminder(
            contacts, target_date, recipient_email="orogjay+reminders@gmail.com"
        )
        self.assertTrue(res)

    def test_run_agent_simulation(self):
        # Base date 2026-10-27: Nychel's birthday is 1983-10-28 (tomorrow, 1 day away)
        exit_code = run_agent(
            contacts_file="contacts.json",
            days_ahead=5,
            base_date=date(2026, 10, 27),
            dry_run=True,
        )
        self.assertEqual(exit_code, 0)


if __name__ == "__main__":
    unittest.main()
