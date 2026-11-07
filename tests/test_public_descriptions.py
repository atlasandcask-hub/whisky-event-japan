"""Current 100-event migration and required-description regression checks."""
import csv
import io
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import sync_events as sync


class PublicDescriptionTests(unittest.TestCase):
    def setUp(self):
        self.before = json.loads((ROOT/'tests/fixtures/events_2026-11-05_before.json').read_text())
        self.current = json.loads((ROOT/'tests/fixtures/events_after_2026-11-05.json').read_text())
        self.source = (ROOT/'tests/fixtures/sheet_public_2026-11-05.csv').read_text()

    def test_migration_preserves_all_ids_and_every_other_field(self):
        result = sync.build_events(self.source, self.before)
        self.assertEqual(len(result), 100)
        before = {e['id']: e for e in self.before}
        changed = set()
        for event in result:
            delta = {key for key in event if event[key] != before[event['id']][key]}
            self.assertLessEqual(delta, {'publicDescription'})
            if delta:
                changed.add(event['id'])
        originally_blank = {e['id'] for e in self.before if not e['publicDescription']}
        self.assertEqual(len(originally_blank), 24)
        self.assertEqual(changed, originally_blank | {'WEJ-2026-061', 'WEJ-2026-066'})
        self.assertTrue(all(e['publicDescription'].strip() for e in result))
        self.assertEqual({e['id']: e for e in result}, {e['id']: e for e in self.current})

    def test_two_syncs_preserve_sheet_descriptions(self):
        first = sync.build_events(self.source, self.current)
        self.assertEqual(sync.build_events(self.source, first), first)

    def test_blank_new_event_stops_even_with_internal_notes(self):
        data = list(csv.DictReader(io.StringIO(self.source)))
        data.append(dict(data[0], ID='WEJ-2026-999', 公開用説明='', 備考='Canva制作済み'))
        keys = list(data[-1])
        out = io.StringIO()
        writer = csv.DictWriter(out, keys)
        writer.writeheader()
        writer.writerows(data)
        with self.assertRaises(sync.SyncError) as caught:
            sync.build_events(out.getvalue(), self.current)
        self.assertIn('WEJ-2026-999', str(caught.exception.problems))
        self.assertIn('公開用説明が空欄', str(caught.exception.problems))

    def test_existing_blank_can_be_repaired_but_never_published(self):
        self.assertTrue(sync.validate_events(self.before))
        self.assertEqual(sync.validate_events(self.current), [])
        event = dict(self.current[0], publicDescription=' \n ')
        self.assertIn('公開用説明が空欄', str(sync.validate_events([event])))

    def test_missing_id_and_internal_description_stop_at_current_scale(self):
        data = list(csv.DictReader(io.StringIO(self.source)))
        out = io.StringIO()
        writer = csv.DictWriter(out, data[0].keys())
        writer.writeheader(); writer.writerows(data[1:])
        with self.assertRaises(sync.SyncError):
            sync.build_events(out.getvalue(), self.current)
        data[0]['公開用説明'] = 'Metricool投稿ID・Instagram制作履歴'
        out = io.StringIO(); writer = csv.DictWriter(out, data[0].keys())
        writer.writeheader(); writer.writerows(data)
        with self.assertRaises(sync.SyncError):
            sync.build_events(out.getvalue(), self.current)


if __name__ == '__main__':
    unittest.main()
