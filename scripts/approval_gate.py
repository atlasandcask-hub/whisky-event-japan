#!/usr/bin/env python3
"""WEJ approval gate. DRY RUN ONLY: this program cannot publish to Instagram."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "posting" / "queue.json"
ALLOWED = {"review", "approved", "published", "failed", "cancelled", "draft", "publishing"}

def fingerprint(post):
    payload = {"caption": post["caption"], "media_urls": post["media_urls"]}
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def inspect(post, today=None):
    today = today or dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).date()
    errors = []
    if post.get("status") != "approved":
        errors.append("not explicitly approved")
    if not post.get("caption", "").strip():
        errors.append("missing caption")
    urls = post.get("media_urls", [])
    if len(urls) != post.get("canva_page_count", 4):
        errors.append("missing carousel media")
    if any(urlparse(u).scheme != "https" or not urlparse(u).netloc for u in urls):
        errors.append("invalid media URL")
    if any("canva.com" in urlparse(u).netloc for u in urls):
        errors.append("temporary Canva URL cannot be published")
    digest = fingerprint(post)
    if post.get("content_hash") != digest or post.get("approved_hash") != digest:
        errors.append("approval hash mismatch")
    if post.get("verification_status") != "verified" or post.get("official_check_status") != "verified":
        errors.append("official event information not verified")
    if post.get("media_export_status") != "ready":
        errors.append("media export not ready")
    if not post.get("approval_ready"):
        errors.append("approval readiness not confirmed")
    if post.get("review_blockers"):
        errors.append("unresolved review blockers")
    try:
        if dt.date.fromisoformat(post["event_date"]) < today:
            errors.append("event already ended")
    except (ValueError, KeyError):
        errors.append("invalid event date")
    if post.get("instagram_media_id"):
        errors.append("already has Instagram media ID")
    return errors

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--post-id", required=True)
    parser.add_argument("--today", help="YYYY-MM-DD for deterministic tests")
    args = parser.parse_args()
    data = json.loads(QUEUE.read_text(encoding="utf-8"))
    if data.get("auto_publish_enabled") is not False:
        raise SystemExit("Unsafe configuration: publishing flag must be false")
    matches = [p for p in data["posts"] if p["id"] == args.post_id]
    if len(matches) != 1:
        raise SystemExit("Unknown or duplicate post ID")
    date = dt.date.fromisoformat(args.today) if args.today else None
    errors = inspect(matches[0], date)
    print(json.dumps({"post_id": args.post_id, "dry_run": True, "eligible": not errors,
                      "reasons": errors}, ensure_ascii=False, indent=2))
    if errors:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
