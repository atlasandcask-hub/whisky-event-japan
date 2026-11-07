import csv
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from contextlib import redirect_stdout, redirect_stderr
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import sync_events as sync

SOURCE = ROOT / 'tests/fixtures/sheet_public_2026-11-05.csv'
BEFORE = ROOT / 'tests/fixtures/events_before_2026-11-05.json'


def encode(rows):
    out = io.StringIO()
    writer = csv.DictWriter(out, rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue()


class SafetyTests(unittest.TestCase):
    def setUp(self):
        self.events = json.loads((ROOT / 'tests/fixtures/events_after_2026-11-05.json').read_text())
        self.rows = list(csv.DictReader(io.StringIO(SOURCE.read_text())))

    def build(self, rows=None, events=None):
        return sync.build_events(encode(self.rows if rows is None else rows),
                                 self.events if events is None else events)

    def test_migration_preserves_100_ids_and_every_other_field(self):
        before = json.loads(BEFORE.read_text())
        self.assertEqual(len(before), 100)
        self.assertEqual(sum(not e['publicDescription'] for e in before), 24)
        by_id = {e['id']: e for e in before}
        self.assertEqual(set(by_id), {e['id'] for e in self.events})
        changed = []
        for event in self.events:
            keys = {k for k in event if event[k] != by_id[event['id']][k]}
            if keys:
                self.assertEqual(keys, {'publicDescription'})
                changed.append(event['id'])
        self.assertEqual(len(changed), 26)
        self.assertEqual(sync.validate_events(self.events), [])
        self.assertTrue(all(e['publicDescription'].strip() for e in self.events))

    def test_sheet_103_rows_matches_public_100_and_two_round_trips(self):
        self.assertEqual(len(self.rows), 103)
        result = self.build()
        for _ in range(2):
            self.assertEqual({e['id']: e for e in result}, {e['id']: e for e in self.events})
            result = self.build(events=result)

    def test_24_blank_baseline_is_repaired_from_sheet(self):
        self.assertEqual(self.build(events=json.loads(BEFORE.read_text())), self.events)

    def test_one_or_18_missing_and_same_count_replacement_stop(self):
        for missing in [{self.events[0]['id']}, {f'WEJ-2026-{n:03}' for n in range(53, 71)}]:
            for replacement in [False, True]:
                rows = [dict(r) for r in self.rows if r['ID'] not in missing]
                if replacement:
                    rows.extend(dict(rows[0], ID=f'WEJ-2026-{900+n}') for n in range(len(missing)))
                with self.assertRaises(sync.SyncError):
                    self.build(rows)

    def test_unpublish_and_duplicate_stop(self):
        rows = [dict(r) for r in self.rows]
        rows[0]['掲載判定'] = '非掲載'
        with self.assertRaises(sync.SyncError): self.build(rows)
        with self.assertRaises(sync.SyncError): self.build(self.rows + [self.rows[0]])

    def test_id_keeps_description_after_title_date_change_and_blank_sheet(self):
        rows = [dict(r) for r in self.rows]
        rows[0].update(イベント名='変更した名称', 開催日='2027/01/12', 公開用説明='')
        event = next(e for e in self.build(rows) if e['id'] == rows[0]['ID'])
        old = next(e for e in self.events if e['id'] == rows[0]['ID'])
        self.assertEqual(event['publicDescription'], old['publicDescription'])
        self.assertEqual(event['date'], '2027-01-12')

    def test_new_event_requires_description_and_valid_addition_succeeds(self):
        extra = dict(self.rows[0], ID='WEJ-2026-999', 公開用説明='')
        with self.assertRaises(sync.SyncError): self.build(self.rows + [extra])
        extra['公開用説明'] = '公式情報から確認した追加イベントの案内です。'
        self.assertEqual(len(self.build(self.rows + [extra])), 101)

    def test_existing_blank_without_fallback_stops(self):
        rows = [dict(r) for r in self.rows]
        rows[0]['公開用説明'] = ''
        events = [dict(e, publicDescription='' if e['id'] == rows[0]['ID'] else e['publicDescription']) for e in self.events]
        with self.assertRaises(sync.SyncError): self.build(rows, events)

    def test_no_description_column_keeps_existing(self):
        rows = [{k: v for k, v in r.items() if k != '公開用説明'} for r in self.rows]
        self.assertEqual(self.build(rows), self.events)

    def test_internal_fields_never_published_and_public_leaks_stop(self):
        rows = [dict(r, 備考='Canva・Muse・Metricool制作履歴') for r in self.rows]
        self.assertEqual(self.build(rows), self.events)
        for marker in ['Canva', 'WEJ-CAND-001', 'GitHub', '既存DB', '制作履歴', 'Muse', 'Metricool']:
            for key in ['イベント名', '料金', '公開用説明']:
                bad = [dict(r) for r in rows]
                bad[0][key] = '案内 ' + marker
                with self.assertRaises(sync.SyncError): self.build(bad)
        rows[0]['公開用説明'] = rows[0]['備考'] = '関係者のみで共有する文章'
        with self.assertRaises(sync.SyncError): self.build(rows)

    def test_bad_date_url_and_missing_header_stop(self):
        for key, value in [('開催日', '2026/02/30'), ('公式URL', 'javascript:alert(1)')]:
            rows = [dict(r) for r in self.rows]; rows[0][key] = value
            with self.assertRaises(sync.SyncError): self.build(rows)
        with self.assertRaises(sync.SyncError): sync.build_events('ID\nx\n', self.events)

    def test_atomic_backup_dry_run_and_failures(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'events.json'; backup = Path(directory) / 'events.json.backup'
            original = BEFORE.read_bytes(); output.write_bytes(original)
            with patch.object(sync, 'OUTPUT', output), patch.object(sync, 'BACKUP', backup), redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(sync.sync(dry_run=True, fetch=lambda: SOURCE.read_text()), 0)
                self.assertEqual(output.read_bytes(), original); self.assertFalse(backup.exists())
                self.assertEqual(sync.sync(fetch=lambda: SOURCE.read_text()), 0)
                self.assertEqual(backup.read_bytes(), original)
                published = output.read_bytes()
                self.assertEqual(json.loads(published), self.events)
                self.assertEqual(sync.sync(fetch=lambda: 'invalid'), 1)
                self.assertEqual(output.read_bytes(), published)
                with patch.object(Path, 'replace', side_effect=OSError('failure')):
                    self.assertEqual(sync.sync(fetch=lambda: SOURCE.read_text()), 1)
                self.assertEqual(output.read_bytes(), published)
                self.assertFalse(output.with_suffix('.json.tmp').exists())

    def test_html_escapes_only_public_description(self):
        html = (ROOT / 'index.html').read_text()
        self.assertIn('esc(e.publicDescription)', html)
        self.assertNotIn('esc(e.description)', html)
        self.assertNotIn('e.備考', html)


if __name__ == '__main__': unittest.main()
