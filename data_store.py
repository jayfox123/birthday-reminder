import json
from dataclasses import dataclass
from datetime import datetime, date
from pathlib import Path
from typing import List, Union


@dataclass
class Contact:
    name: str
    birthdate: date
    email: str = ""
    notes: str = ""

    @property
    def birthdate_str(self) -> str:
        return self.birthdate.strftime("%Y-%m-%d")

    @property
    def is_deceased(self) -> bool:
        return "passed away" in self.notes.lower()

    @property
    def is_anniversary(self) -> bool:
        return "anniversary" in self.notes.lower() or "anniversary" in self.name.lower()

    def age_on_date(self, target_date: date) -> int:
        """Calculate the age or years turned on target_date."""
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


def get_upcoming_birthdays(
    contacts: List[Contact],
    from_date: date | None = None,
    days_ahead: int = 5
) -> List[Contact]:
    """
    Filter contacts whose birthday occurs in exactly `days_ahead` days.
    """
    if from_date is None:
        from_date = date.today()

    from datetime import timedelta
    target_date = from_date + timedelta(days=days_ahead)

    return [
        contact for contact in contacts
        if is_birthday_on_date(contact.birthdate, target_date)
    ]
