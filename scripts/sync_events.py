import csv
import io
import json
import re
import urllib.request
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

SHEET_ID = "1_A0aQ2elKC4Rs_SET6WIHqwHbgAUZSnaB6A2TfvEzhs"
SHEET_GID = "1399683849"
CSV_URL = (
    f"https://docs.google.com/spreadsheets/d/{SHEET_ID}"
    f"/export?format=csv&gid={SHEET_GID}"
)
OUTPUT = Path("events.json")
MIN_EVENTS = 8

REQUIRED = {
    "ID", "掲載判定", "イベント名", "開催日",
    "カテゴリ", "都道府県", "会場", "公式URL"
}


def main():
    request = urllib.request.Request(
        CSV_URL,
        headers={"User-Agent": "WEJ-Event-Sync/1.0"}
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        raw = response.read(2_000_001)

    if len(raw) > 2_000_000:
        raise ValueError("CSV too large. Existing data preserved.")

    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))

    if not reader.fieldnames or not REQUIRED.issubset(reader.fieldnames):
        raise ValueError("Invalid CSV headers. Existing data preserved.")

    existing = {}
    if OUTPUT.exists():
        for item in json.loads(OUTPUT.read_text(encoding="utf-8")):
            existing[(item.get("title"), item.get("date"))] = item

    events = []
    seen_ids = set()

    for row in reader:
        if (row.get("掲載判定") or "").strip() != "掲載":
            continue

        event_id = (row.get("ID") or "").strip()
        name = (row.get("イベント名") or "").strip()
        raw_date = (row.get("開催日") or "").strip()
        url = (row.get("公式URL") or "").strip()

        match = re.search(
            r"(20\d{2})/(\d{1,2})(?:/(\d{1,2}))?",
            raw_date
        )

        if not event_id or not name or not match or event_id in seen_ids:
            raise ValueError("Invalid event data. Existing data preserved.")

        event_date = date(
            int(match.group(1)),
            int(match.group(2)),
            int(match.group(3) or 1)
        ).isoformat()

        parsed_url = urlparse(url)
        if parsed_url.scheme != "https" or not parsed_url.netloc:
            raise ValueError("Invalid official URL. Existing data preserved.")

        seen_ids.add(event_id)

        old = existing.get((name, event_date), {})
        status = (row.get("ステータス") or "").strip()
        notes = (row.get("備考") or "").strip()

        events.append({
            "title": name,
            "date": event_date,
            "dateLabel": raw_date,
            "region": (row.get("都道府県") or "").strip(),
            "category": (row.get("カテゴリ") or "その他").strip(),
            "venue": (row.get("会場") or "公式で確認").strip(),
            "price": (row.get("料金") or "公式で確認").strip(),
            "description": old.get("description") or
                "。".join(filter(None, [status, notes]))[:180],
            "url": url
        })

    if len(events) < MIN_EVENTS:
        raise ValueError("Too few events. Existing data preserved.")

    events.sort(key=lambda item: (item["date"], item["title"]))

    temporary = OUTPUT.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(events, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8"
    )
    temporary.replace(OUTPUT)

    print(f"Synced {len(events)} published events.")


if __name__ == "__main__":
    main()
