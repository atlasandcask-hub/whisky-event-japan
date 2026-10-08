import json
import os
from pathlib import Path

import google.auth
from google.auth.transport.requests import AuthorizedSession

SHEET_ID = os.environ.get("GOOGLE_SHEET_ID", "").strip()
OUTPUT = Path("events.json")

COLUMNS = [
    "id", "publish", "status", "name", "category", "date",
    "start_time", "end_time", "prefecture", "venue", "price",
    "ticket_release", "deadline", "organizer", "official_url",
    "source_url", "verified_date", "confidence", "instagram",
    "x_post", "notes", "updated_at"
]

def main():
    if not SHEET_ID:
        raise RuntimeError("GOOGLE_SHEET_ID is not set. Check the GitHub Actions secret.")

    credentials, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
    )
    session = AuthorizedSession(credentials)
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/%E3%82%A4%E3%83%99%E3%83%B3%E3%83%88DB%21A2%3AV"
    response = session.get(url, timeout=30)
    response.raise_for_status()
    rows = response.json().get("values", [])

    events = []
    for row in rows:
        row = (row + [""] * len(COLUMNS))[:len(COLUMNS)]
        item = dict(zip(COLUMNS, row))
        if item["publish"].strip().lower() not in ("掲載", "掲載する", "公開", "yes", "true", "1", "○", "◯"):
            continue
        if not item["name"].strip():
            continue
        events.append(item)

    OUTPUT.write_text(
        json.dumps(events, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8"
    )
    print(f"Synced {len(events)} published events to {OUTPUT}")

if __name__ == "__main__":
    main()
