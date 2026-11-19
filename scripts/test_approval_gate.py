#!/usr/bin/env python3
"""Unit tests for WEJ Instagram dry-run approval gate."""
import datetime as dt
import hashlib
import json
import unittest
from approval_gate import fingerprint, inspect

def fixture():
    post = {"id": "test", "status": "approved", "caption": "test caption",
            "media_urls": [f"https://cdn.example.org/{i}.png" for i in range(4)],
            "canva_page_count": 4, "event_date": "2026-12-31",
            "verification_status": "verified", "official_check_status": "verified",
            "media_export_status": "ready", "approval_ready": True,
            "review_blockers": [], "instagram_media_id": None}
    post["content_hash"] = fingerprint(post)
    post["approved_hash"] = post["content_hash"]
    return post

class GateTests(unittest.TestCase):
    def setUp(self):
        self.today = dt.date(2026, 10, 11)

    def test_valid_approved(self):
        self.assertEqual(inspect(fixture(), self.today), [])

    def test_missing_approval(self):
        p = fixture()
        p["status"] = "review"
        self.assertTrue(inspect(p, self.today))

    def test_changed_caption(self):
        p = fixture()
        p["caption"] += " changed"
        self.assertIn("approval hash mismatch", inspect(p, self.today))

    def test_expired_event(self):
        p = fixture()
        p["event_date"] = "2026-10-10"
        self.assertIn("event already ended", inspect(p, self.today))

    def test_duplicate_publication(self):
        p = fixture()
        p["instagram_media_id"] = "123"
        self.assertIn("already has Instagram media ID", inspect(p, self.today))

    def test_missing_media(self):
        p = fixture()
        p["media_urls"] = []
        self.assertIn("missing carousel media", inspect(p, self.today))

    def test_unverified(self):
        p = fixture()
        p["official_check_status"] = "pending"
        self.assertIn("official event information not verified", inspect(p, self.today))

    def test_canva_temporary_url(self):
        p = fixture()
        p["media_urls"][0] = "https://media.canva.com/image.png"
        self.assertIn("temporary Canva URL cannot be published", inspect(p, self.today))

if __name__ == "__main__":
    unittest.main()
