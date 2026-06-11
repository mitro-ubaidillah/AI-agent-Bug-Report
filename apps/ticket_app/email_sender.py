import json
from pathlib import Path
from datetime import datetime, timezone

EMAILS_FILE = Path(__file__).parent / "emails.json"


def send_simulated_email(to_team: str, subject: str, body: str, pdf_filename: str, pdf_path: str) -> dict:
    """
    Simulates sending an email by appending the message detail to emails.json
    """
    # 1. Ensure file exists and load it
    emails = []
    if EMAILS_FILE.exists():
        try:
            with open(EMAILS_FILE) as f:
                emails = json.load(f)
        except Exception:
            emails = []

    # 2. Map team names to appropriate internal email addresses
    team_email_map = {
        "FRD Team": "frd-alerts@bank.local",
        "Transfer Team": "transfer-ops@bank.local",
        "Middleware Team": "middleware-ops@bank.local"
    }
    recipient = team_email_map.get(to_team, "it-ops@bank.local")

    # 3. Create simulated email body and metadata
    email_id = f"MSG-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    email_record = {
        "email_id": email_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "from": "ai-agent-investigator@bank.local",
        "to": recipient,
        "subject": subject,
        "body": body,
        "pdf_filename": pdf_filename,
        "pdf_path": str(pdf_path)
    }

    # 4. Append and save
    emails.append(email_record)
    with open(EMAILS_FILE, "w") as f:
        json.dump(emails, f, indent=2)

    return email_record
