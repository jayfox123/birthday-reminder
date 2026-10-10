# 🎂 Birthday Reminder Agent

An automated Python agent that checks a contact list daily, identifies upcoming birthdays occurring in **exactly 5 days**, and sends HTML email notifications via SMTP.

---

## 🚀 Features

- **5-Day Advance Notice**: Detects contacts whose birthday is exactly 5 days away.
- **Leap Year Support**: Correctly handles Feb 29 birthdates on non-leap years.
- **Responsive HTML Emails**: Sends formatted emails with styled cards for each contact.
- **Simulated Dry Runs**: Allows testing without sending live emails (`--dry-run`).
- **GitHub Actions Integration**: Daily automated cron job to check and send alerts.

---

## 📁 Project Architecture

- `main.py`: CLI entry point and agent execution logic.
- `data_store.py`: Contact list loader and 5-day birthday detection filter.
- `email_service.py`: SMTP mail sender with HTML and plain-text templates.
- `contacts.json`: JSON data store containing contact details and birthdates (`YYYY-MM-DD`).
- `requirements.txt`: Python dependencies (`python-dotenv`).
- `.env.example`: Configuration template for SMTP credentials.
- `.github/workflows/daily_birthday_check.yml`: GitHub Actions daily automated workflow.
- `test_birthday_reminder.py`: Unit test suite.

---

## 🛠️ Quickstart & Local Setup

### 1. Initialize Virtual Environment & Install Dependencies
```bash
python -m venv .venv
# On Windows:
.venv\Scripts\pip install -r requirements.txt

# On macOS/Linux:
# source .venv/bin/activate
# pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your SMTP details:
```bash
cp .env.example .env
```

Example `.env`:
```ini
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
NOTIFICATION_RECIPIENT=recipient@example.com
DRY_RUN=false
```

---

## 💻 Running the Agent

### Dry Run (Simulate Email Output)
```bash
.venv\Scripts\python main.py --dry-run
```

### Test Specific Base Date
```bash
.venv\Scripts\python main.py --date 2026-10-10 --dry-run
```

### Run Unit Tests
```bash
.venv\Scripts\python -m unittest test_birthday_reminder.py
```

---

## 🤖 GitHub Actions Automated Daily Check

The included workflow (`.github/workflows/daily_birthday_check.yml`) runs automatically every day at 08:00 UTC.

### Repository Secrets to Configure:
In your GitHub Repository (`Settings > Secrets and variables > Actions > New repository secret`), add:
- `SMTP_SERVER`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `NOTIFICATION_RECIPIENT`
