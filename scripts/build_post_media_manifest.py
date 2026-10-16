#!/usr/bin/env python3
"""Audit locally exported Canva PNGs and produce a non-publishing media manifest.

Expected paths: posting/media/<post-id>/01.png through 04.png.
Run from any directory: python scripts/build_post_media_manifest.py
No publishing, uploads, or network calls.
"""
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "posting" / "queue.json"
MEDIA = ROOT / "posting" / "media"
OUT = ROOT / "posting" / "media-manifest.json"
PNG = b"\x89PNG\r\n\x1a\n"

def dimensions(path):
    with path.open("rb") as f:
        header = f.read(24)
    if len(header) < 24 or header[:8] != PNG or header[12:16] != b"IHDR":
        raise ValueError(f"Not a valid PNG header: {path}")
    return struct.unpack(">II", header[16:24])

def main():
    data = json.loads(QUEUE.read_text(encoding="utf-8"))
    if data.get("auto_publish_enabled") is not False:
        raise SystemExit("Publishing safety flag must be false")
    manifest = {"schema_version": 1, "auto_publish_enabled": False, "posts": []}
    incomplete = 0
    for post in data["posts"]:
        pid = post["id"]
        expected = int(post.get("canva_page_count", 4))
        folder = MEDIA / pid
        found = sorted(folder.glob("*.png")) if folder.exists() else []
        expected_names = [f"{n:02d}.png" for n in range(1, expected + 1)]
        entry = {"id": pid, "ready": False, "files": [], "issues": []}
        if sorted(p.name for p in found) != expected_names:
            entry["issues"].append(f"Expected exactly {expected_names}; found {[p.name for p in found]}")
        else:
            for path in found:
                try:
                    w, h = dimensions(path)
                    if (w, h) != (1080, 1350):
                        entry["issues"].append(f"{path.name}: {w}x{h}, expected 1080x1350")
                    entry["files"].append({"path": path.relative_to(ROOT).as_posix(), "width": w, "height": h})
                except ValueError as e:
                    entry["issues"].append(str(e))
        entry["ready"] = not entry["issues"]
        incomplete += not entry["ready"]
        manifest["posts"].append(entry)
    OUT.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Media audit: {len(data['posts'])-incomplete}/{len(data['posts'])} complete; no publishing")
    if incomplete:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
