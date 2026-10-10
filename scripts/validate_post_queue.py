#!/usr/bin/env python3
"""Validate WEJ's non-publishing Instagram approval ledger."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
data = json.loads((ROOT / "posting" / "queue.json").read_text(encoding="utf-8"))
assert data["schema_version"] == 1
assert data["auto_publish_enabled"] is False, "Auto-publishing must remain disabled"
assert isinstance(data["posts"], list)
seen = set()
statuses = {"draft", "review", "approved", "publishing", "published", "failed", "cancelled"}
for post in data["posts"]:
    assert isinstance(post, dict)
    assert isinstance(post.get("id"), str) and post["id"]
    assert post["id"] not in seen, "Duplicate post ID"
    seen.add(post["id"])
    assert post.get("status") in statuses
    assert isinstance(post.get("caption"), str)
    assert isinstance(post.get("media_urls"), list)
    assert all(isinstance(u, str) and u.startswith("https://") for u in post["media_urls"])
    content = {"caption": post["caption"], "media_urls": post["media_urls"]}
    digest = hashlib.sha256(json.dumps(content, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    assert post.get("content_hash") == digest, f"Stale hash: {post['id']}"
    if post["status"] in {"approved", "publishing", "published"}:
        assert post.get("approved_hash") == digest, f"Approval invalid: {post['id']}"
    if post["status"] == "published":
        assert post.get("instagram_media_id"), f"Missing publication receipt: {post['id']}"
print(f"Validated {len(seen)} staged posts; automatic publishing disabled.")
