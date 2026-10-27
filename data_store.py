import json
from dataclasses import dataclass
from datetime import datetime, date
from pathlib import Path
from typing import List, Union, Tuple


@dataclass
class Contact:
    name: str
    birthdate: date
    email: str = ""
    notes: str = ""
    days_remaining: int | None = None
    target_date: date | None = None

    @property
    def birthdate_str(self) -> str:
        return self.birthdate.strftime("%Y-%m-%d")

    @property
    def is_deceased(self) -> bool:
        return "passed away" in self.notes.lower()

    @property
    def is_anniversary(self) -> bool:
        return "anniversary" in self.notes.lower() or "anniversary" in self.name.lower()

    def age_on_date(self, target_date: date | None = None) -> int:
        """Calculate the age or years turned on target_date."""
        if target_date is None:
            target_date = self.target_date or date.today()
        age = target_date.year - self.birthdate.year
        if (target_date.month, target_date.day) < (self.birthdate.month, self.birthdate.day):
            age -= 1
        return age


def load_contacts(filepath: Union[str, Path] = "contacts.json") -> List[Contact]:
    """Load contact list from a JSON file."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Contacts file not found at {path.resolve()}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    contacts = []
    for item in data:
        name = item.get("name", "").strip()
        email = item.get("email", "").strip()
        notes = item.get("notes", "").strip()

        raw_bday = item.get("birth_date") or item.get("birthdate") or ""
        raw_bday = str(raw_bday).strip()

        if not name or not raw_bday:
            continue

        # Parse date (YYYY-MM-DD)
        bday = datetime.strptime(raw_bday, "%Y-%m-%d").date()
        contacts.append(Contact(name=name, email=email, birthdate=bday, notes=notes))

    return contacts


def is_birthday_on_date(birthdate: date, target_date: date) -> bool:
    """
    Check if a birthdate matches target_date's month and day.
    Handles leap year (Feb 29) when target year is not a leap year.
    """
    if birthdate.month == 2 and birthdate.day == 29:
        is_leap = (target_date.year % 4 == 0 and target_date.year % 100 != 0) or (target_date.year % 400 == 0)
        if not is_leap:
            return target_date.month == 2 and target_date.day == 28
    return birthdate.month == target_date.month and birthdate.day == target_date.day


def get_days_until_birthday(birthdate: date, from_date: date) -> Tuple[int, date]:
    """
    Calculate (days_remaining, next_birthday_date) from from_date.
    - Handles leap year (Feb 29) on non-leap years by celebrating on Feb 28.
    - Handles year transitions (e.g. from_date in late December, birthday in early January).
    """
    def bday_in_year(year: int) -> date:
        if birthdate.month == 2 and birthdate.day == 29:
            is_leap = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
            if not is_leap:
                return date(year, 2, 28)
        return date(year, birthdate.month, birthdate.day)

    this_year_bday = bday_in_year(from_date.year)
    if this_year_bday >= from_date:
        next_bday = this_year_bday
    else:
        next_bday = bday_in_year(from_date.year + 1)

    days_remaining = (next_bday - from_date).days
    return days_remaining, next_bday


def get_upcoming_birthdays(
    contacts: List[Contact],
    from_date: date | None = None,
    days_ahead: int = 5
) -> List[Contact]:
    """
    Filter contacts whose birthday occurs within the next `days_ahead` days
    (from 0 to days_ahead inclusive).
    Each returned Contact has `days_remaining` and `target_date` populated.
    """
    if from_date is None:
        from_date = date.today()

    upcoming: List[Contact] = []
    for contact in contacts:
        days_remaining, target_date = get_days_until_birthday(contact.birthdate, from_date)
        if 0 <= days_remaining <= days_ahead:
            upcoming.append(
                Contact(
                    name=contact.name,
                    birthdate=contact.birthdate,
                    email=contact.email,
                    notes=contact.notes,
                    days_remaining=days_remaining,
                    target_date=target_date,
                )
            )

    # Sort upcoming events by days_remaining ascending, then name
    upcoming.sort(key=lambda c: (c.days_remaining if c.days_remaining is not None else 999, c.name))
    return upcoming
