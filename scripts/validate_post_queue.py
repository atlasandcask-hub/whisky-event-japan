#!/usr/bin/env python3
"""Validate WEJ draft approval queue; never publish."""
import hashlib, json
from pathlib import Path
p=Path(__file__).resolve().parents[1]/"posting"/"queue.json"
d=json.loads(p.read_text(encoding="utf-8"))
assert d["schema_version"]==1 and d["auto_publish_enabled"] is False
assert isinstance(d["posts"],list)
ids=set()
for x in d["posts"]:
 assert isinstance(x.get("id"),str) and x["id"] not in ids
 ids.add(x["id"])
 assert x["status"] in {"draft","review","approved","publishing","published","failed","cancelled"}
 assert isinstance(x.get("caption"),str) and isinstance(x.get("media_urls"),list)
 assert all(isinstance(u,str) and u.startswith("https://") for u in x["media_urls"])
 payload={"caption":x["caption"],"media_urls":x["media_urls"]}
 digest=hashlib.sha256(json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()).hexdigest()
 if x["status"] in {"approved","publishing","published"}:
  assert x.get("content_hash")==digest and x.get("approved_hash")==digest
  assert x["media_urls"] and x["caption"], "Cannot approve incomplete post"
 if x["status"]=="published": assert x.get("instagram_media_id")
print("Validated",len(ids),"posts; publishing disabled")
