import csv
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import sync_events  # noqa: E402

HEADERS = [
    "ID", "掲載判定", "イベント名", "開催日", "カテゴリ", "都道府県", "会場",
    "料金", "公式URL", "チケットURL", "画像URL", "公開用説明", "備考",
    "ステータス", "最終更新日",
]
# 2026-10-21時点の公開データ（手動追加の18件を含む68件）の固定スナップショット
CURRENT_EVENTS = json.loads(
    (ROOT / "tests" / "fixtures" / "events_2026-10-21.json").read_text(encoding="utf-8")
)
MANUAL_IDS = [f"WEJ-2026-{n:03d}" for n in range(53, 71)]


def clean(value, fallback):
    return fallback if sync_events.find_internal_text(value) else value


def row_from_event(event, **overrides):
    row = {
        "ID": event["id"],
        "掲載判定": "掲載",
        "イベント名": clean(event["title"], "公開用イベント名"),
        "開催日": clean(event["dateLabel"], event["date"].replace("-", "/")),
        "カテゴリ": event["category"],
        "都道府県": clean(event["region"], "全国"),
        "会場": clean(event["venue"], "公式で確認"),
        "料金": clean(event["price"], "公式で確認"),
        "公式URL": event["url"],
        "チケットURL": event["ticketUrl"],
        "画像URL": event["imageUrl"],
        "公開用説明": clean(event["publicDescription"], "公開用の説明文です。"),
        "備考": "Canva完成／フィード2ページ目／WEJ-CAND-001／GitHub反映済",
        "ステータス": "",
        "最終更新日": event["addedAt"],
    }
    row.update(overrides)
    return row


def to_csv(rows):
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=HEADERS)
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def sample_event(n, **overrides):
    event = {
        "id": f"T-{n:03d}",
        "title": f"テストイベント{n}",
        "date": f"2026-11-{n:02d}",
        "addedAt": "2026-10-20",
        "imageUrl": "",
        "dateLabel": f"2026/11/{n:02d}",
        "region": "東京都",
        "category": "フェス",
        "venue": "テスト会場",
        "price": "3,000円",
        "publicDescription": f"承認済みの説明文{n}です。",
        "ticketUrl": f"https://example.com/ticket/{n}",
        "url": f"https://example.com/event/{n}",
    }
    event.update(overrides)
    return event


class SyncTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cwd = os.getcwd()
        os.chdir(self.tmp.name)

    def tearDown(self):
        os.chdir(self.cwd)
        self.tmp.cleanup()

    def write_existing(self, events):
        text = json.dumps(events, ensure_ascii=False, indent=2) + "\n"
        Path("events.json").write_text(text, encoding="utf-8")
        return text

    def run_sync(self, csv_text=None, error=None, dry_run=False):
        def fetch():
            if error:
                raise error
            return csv_text

        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = sync_events.sync(dry_run=dry_run, fetch=fetch)
        return code, out.getvalue(), err.getvalue()

    def output(self):
        return json.loads(Path("events.json").read_text(encoding="utf-8"))


class TestEventPreservation(SyncTestCase):
    def test_manual_18_events_missing_from_sheet_stop_sync(self):
        before = self.write_existing(CURRENT_EVENTS)
        rows = [row_from_event(e) for e in CURRENT_EVENTS if e["id"] not in MANUAL_IDS]

        code, _, err = self.run_sync(to_csv(rows))

        self.assertEqual(code, 1)
        self.assertEqual(Path("events.json").read_text(encoding="utf-8"), before)
        for event_id in MANUAL_IDS:
            self.assertIn(event_id, err)
        self.assertIn("シートに行がありません", err)

    def test_unpublished_judgement_in_sheet_stops_sync(self):
        before = self.write_existing(CURRENT_EVENTS)
        rows = [
            row_from_event(e, 掲載判定="候補" if e["id"] == "WEJ-2026-060" else "掲載")
            for e in CURRENT_EVENTS
        ]

        code, _, err = self.run_sync(to_csv(rows))

        self.assertEqual(code, 1)
        self.assertIn("WEJ-2026-060", err)
        self.assertIn("掲載判定が「候補」", err)
        self.assertEqual(Path("events.json").read_text(encoding="utf-8"), before)

    def test_all_current_events_kept_when_sheet_has_them(self):
        self.write_existing(CURRENT_EVENTS)
        rows = [row_from_event(e) for e in CURRENT_EVENTS]

        code, _, err = self.run_sync(to_csv(rows))

        self.assertEqual(code, 0, err)
        ids = {e["id"] for e in self.output()}
        self.assertEqual(ids, {e["id"] for e in CURRENT_EVENTS})
        self.assertTrue(set(MANUAL_IDS) <= ids)
        self.assertEqual(len(ids), 68)

    def test_events_are_matched_by_id_not_title(self):
        events = [sample_event(n) for n in range(1, 10)]
        self.write_existing(events)
        rows = [row_from_event(e, 公開用説明="") for e in events]
        rows[0]["イベント名"] = "名称を変更したテストイベント"

        code, _, err = self.run_sync(to_csv(rows))

        self.assertEqual(code, 0, err)
        first = next(e for e in self.output() if e["id"] == "T-001")
        self.assertEqual(first["title"], "名称を変更したテストイベント")
        self.assertEqual(first["publicDescription"], "承認済みの説明文1です。")


class TestInternalNotes(SyncTestCase):
    def test_internal_columns_never_published(self):
        events = [sample_event(n) for n in range(1, 10)]
        self.write_existing(events)

        code, _, err = self.run_sync(to_csv([row_from_event(e) for e in events]))

        self.assertEqual(code, 0, err)
        published = Path("events.json").read_text(encoding="utf-8")
        for word in ("Canva", "フィード", "WEJ-CAND", "GitHub", "備考", "ステータス"):
            self.assertNotIn(word, published)

    def test_internal_text_in_public_description_stops_sync(self):
        events = [sample_event(n) for n in range(1, 10)]
        before = self.write_existing(events)
        for memo in (
            "Canva完成。", "WEJ-CAND-012", "GitHub/Webサイト変更なし",
            "制作記録：フィード3ページ目", "9/4発表済を本日初検出。",
            "既存DB未確認イベント", "主催者公式サイトで料金を確認。",
        ):
            with self.subTest(memo=memo):
                rows = [row_from_event(e) for e in events]
                rows[2]["公開用説明"] = "人気のフェスです。" + memo

                code, _, err = self.run_sync(to_csv(rows))

                self.assertEqual(code, 1)
                self.assertIn("T-003", err)
                self.assertEqual(Path("events.json").read_text(encoding="utf-8"), before)

    def test_internal_text_in_title_or_price_stops_sync(self):
        events = [sample_event(n) for n in range(1, 10)]
        self.write_existing(events)
        rows = [row_from_event(e) for e in events]
        rows[0]["イベント名"] = "AnytimeWhisky2026／公式開催詳細・前売抽選特典確認"
        rows[1]["料金"] = "期間限定メニュー価格未確認"

        code, _, err = self.run_sync(to_csv(rows))

        self.assertEqual(code, 1)
        self.assertIn("T-001: title", err)
        self.assertIn("T-002: price", err)

    def test_description_copied_from_notes_stops_sync(self):
        events = [sample_event(n) for n in range(1, 10)]
        self.write_existing(events)
        rows = [row_from_event(e) for e in events]
        rows[0]["備考"] = rows[0]["公開用説明"] = "週末に開催されるフェスです。"

        code, _, err = self.run_sync(to_csv(rows))

        self.assertEqual(code, 1)
        self.assertIn("備考（内部メモ）と同一", err)

    def test_long_description_is_not_truncated(self):
        events = [sample_event(n) for n in range(1, 10)]
        self.write_existing(events)
        long_text = "ウイスキーの魅力を味わえるイベントです。" * 40
        rows = [row_from_event(e) for e in events]
        rows[0]["公開用説明"] = long_text

        code, _, err = self.run_sync(to_csv(rows))

        self.assertEqual(code, 0, err)
        first = next(e for e in self.output() if e["id"] == "T-001")
        self.assertEqual(first["publicDescription"], long_text)

    def test_missing_description_keeps_approved_text(self):
        events = [sample_event(n) for n in range(1, 10)]
        self.write_existing(events)
        rows = [row_from_event(e, 公開用説明="") for e in events]

        code, _, err = self.run_sync(to_csv(rows))

        self.assertEqual(code, 0, err)
        for event in self.output():
            n = int(event["id"][-3:])
            self.assertEqual(event["publicDescription"], f"承認済みの説明文{n}です。")

    def test_missing_description_with_internal_existing_text_stops_sync(self):
        events = [sample_event(n) for n in range(1, 10)]
        events[0]["publicDescription"] = "抽選販売。9/4発表済を本日初検出。"
        self.write_existing(events)
        rows = [row_from_event(e, 公開用説明="") for e in events]

        code, _, err = self.run_sync(to_csv(rows))

        self.assertEqual(code, 1)
        self.assertIn("T-001: publicDescription", err)

    def test_placeholder_and_normal_wording_are_allowed(self):
        event = sample_event(
            1, venue="公式で確認", price="公式で確認",
            publicDescription="最新情報は公式サイトでご確認ください。",
        )
        self.assertEqual(sync_events.validate_events([event]), [])

    def test_check_detects_internal_text_in_current_events(self):
        problems = "\n".join(sync_events.validate_events(CURRENT_EVENTS))
        for event_id in ("WEJ-2026-054", "WEJ-2026-055", "WEJ-2026-061", "WEJ-2026-066"):
            self.assertIn(event_id, problems)


class TestNormalUpdatesAndFailures(SyncTestCase):
    def test_normal_update_and_new_event(self):
        events = [sample_event(n) for n in range(1, 10)]
        self.write_existing(events)
        rows = [row_from_event(e) for e in events]
        rows[0]["料金"] = "前売3,500円／当日4,000円"
        rows.append(row_from_event(sample_event(20)))

        code, out, err = self.run_sync(to_csv(rows))

        self.assertEqual(code, 0, err)
        published = {e["id"]: e for e in self.output()}
        self.assertEqual(published["T-001"]["price"], "前売3,500円／当日4,000円")
        self.assertIn("T-020", published)
        self.assertIn("追加: T-020", out)
        self.assertEqual(json.loads(Path("events.json.backup").read_text(encoding="utf-8")), events)

    def test_dry_run_does_not_write(self):
        events = [sample_event(n) for n in range(1, 10)]
        before = self.write_existing(events)
        rows = [row_from_event(e) for e in events]
        rows[0]["料金"] = "5,000円"

        code, out, err = self.run_sync(to_csv(rows), dry_run=True)

        self.assertEqual(code, 0, err)
        self.assertIn("更新: T-001 price", out)
        self.assertEqual(Path("events.json").read_text(encoding="utf-8"), before)

    def test_failures_keep_existing_data(self):
        events = [sample_event(n) for n in range(1, 10)]
        valid_rows = [row_from_event(e) for e in events]
        bad_date = [dict(r) for r in valid_rows]
        bad_date[0]["開催日"] = "未定"
        bad_url = [dict(r) for r in valid_rows]
        bad_url[0]["公式URL"] = "javascript:alert(1)"
        duplicated = valid_rows + [dict(valid_rows[0])]
        cases = {
            "network": (None, OSError("network down")),
            "headers": ("名前,日付\nA,2026/11/01\n", None),
            "empty": ("", None),
            "bad_date": (to_csv(bad_date), None),
            "bad_url": (to_csv(bad_url), None),
            "duplicate_id": (to_csv(duplicated), None),
            "too_few": (to_csv(valid_rows[:3]), None),
        }
        for name, (csv_text, error) in cases.items():
            with self.subTest(case=name):
                before = self.write_existing(events)

                code, _, err = self.run_sync(csv_text, error=error)

                self.assertEqual(code, 1)
                self.assertIn("既存の events.json は変更していません", err)
                self.assertEqual(Path("events.json").read_text(encoding="utf-8"), before)
                self.assertFalse(Path("events.json.tmp").exists())


if __name__ == "__main__":
    unittest.main()
