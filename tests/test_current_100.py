"""2026-11-05 real public snapshot and source columns; all writes stay temporary."""
import csv
import io
import json
from contextlib import redirect_stderr, redirect_stdout
import test_sync_events as base
ROOT, MANUAL_IDS = base.ROOT, base.MANUAL_IDS
import sync_events as sync


class Current100Tests(base.SafetyTests):
    test_normal_92_and_new_event = None
    test_normal_92_round_trip_preserves_every_field = None
    test_reviewed_sheet_corrections_can_resolve_existing_internal_copy = None
    test_real_92_snapshot_is_preserved_but_existing_internal_copy_blocks_sync = None
    test_real_snapshot_all_ids_and_historical_18_are_present = None
    test_check_audits_real_snapshot_and_html_only_uses_public_description = None

    def setUp(self):
        super().setUp()
        self.original = json.loads((ROOT/'tests/fixtures/events_2026-11-05.json').read_text())
        self.events = json.loads((ROOT/'events.json').read_text())
        self.source = (ROOT/'tests/fixtures/sheet_public_2026-11-05.csv').read_text()
        self.approvals = json.loads((ROOT/'scripts/publication_holds.json').read_text())
        self.write(self.events)

    def real_sync(self, source=None):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = sync.sync(fetch=lambda: self.source if source is None else source)
        return code, out.getvalue(), err.getvalue()

    def encode(self, data):
        out = io.StringIO(); writer = csv.DictWriter(out, data[0].keys())
        writer.writeheader(); writer.writerows(data)
        return out.getvalue()

    def test_exact_100_ids_new_four_and_only_reviewed_copy_changes(self):
        source = list(csv.DictReader(io.StringIO(self.source)))
        self.assertEqual(len(source), 103)
        self.assertEqual(len({r['ID'] for r in source}), 103)
        self.assertEqual(len(self.events), 100)
        before = {e['id']: e for e in self.original}
        after = {e['id']: e for e in self.events}
        self.assertEqual(set(before), set(after))
        self.assertEqual(set(after), {r['ID'] for r in source if r['掲載判定']=='掲載'})
        self.assertTrue({f'WEJ-2026-{n}' for n in range(100,104)} <= set(after))
        self.assertNotIn('WEJ-2026-092', after)
        changes = {i: {k for k in before[i] if before[i][k] != after[i][k]}
                   for i in before if before[i] != after[i]}
        self.assertEqual(changes, {i: {'publicDescription'} for i in ['WEJ-2026-061','WEJ-2026-066']})

    def test_real_source_two_syncs_preserve_every_field(self):
        self.holds.write_text(json.dumps(self.approvals))
        before = self.output.read_bytes()
        for _ in range(2):
            code, _, err = self.real_sync(); self.assertEqual(code, 0, err)
            self.assertEqual(json.loads(self.output.read_text()), self.events)
        self.assertEqual(self.backup.read_bytes(), before)

    def test_approved_hold_removes_only_092_and_reports_it(self):
        previous = json.loads((ROOT/'tests/fixtures/events_2026-11-01.json').read_text())
        held = next(e for e in previous if e['id']=='WEJ-2026-092')
        self.write(self.events+[held])
        before = self.output.read_bytes()
        self.holds.write_text(json.dumps(self.approvals))
        code, out, err = self.real_sync(); self.assertEqual(code, 0, err)
        self.assertIn('承認済み掲載保留: WEJ-2026-092', out)
        self.assertEqual(json.loads(self.output.read_text()), self.events)
        self.assertEqual(self.backup.read_bytes(), before)

    def test_hold_without_approval_stops(self):
        previous = json.loads((ROOT/'tests/fixtures/events_2026-11-01.json').read_text())
        self.write(self.events+[next(e for e in previous if e['id']=='WEJ-2026-092')])
        before = self.output.read_bytes()
        code, _, err = self.real_sync(); self.assertEqual(code, 1)
        self.assertIn('WEJ-2026-092', err)
        self.assertEqual(self.output.read_bytes(), before)

    def test_approval_never_allows_missing_row_wrong_status_url_or_other_loss(self):
        self.holds.write_text(json.dumps(self.approvals))
        source = list(csv.DictReader(io.StringIO(self.source)))
        variants = [[r for r in source if r['ID']!='WEJ-2026-092']]
        for key, value in [('掲載判定','掲載'), ('掲載判定','未確認'), ('公式URL','https://example.com/changed')]:
            variants.append([dict(r, **{key:value}) if r['ID']=='WEJ-2026-092' else r for r in source])
        for missing in [{'WEJ-2026-100'}, MANUAL_IDS]:
            variants.append([r for r in source if r['ID'] not in missing])
        for data in variants:
            before = self.output.read_bytes()
            code, _, err = self.real_sync(self.encode(data))
            self.assertEqual(code, 1, err)
            self.assertEqual(self.output.read_bytes(), before)

    def test_malformed_approvals_fail_closed(self):
        for value in ['[]', '{', '{"WEJ-2026-092": {}}']:
            self.holds.write_text(value)
            before = self.output.read_bytes()
            self.assertEqual(self.real_sync()[0], 1)
            self.assertEqual(self.output.read_bytes(), before)

    def test_unreviewed_current_copy_stops_without_rewriting(self):
        self.write(self.original); before = self.output.read_bytes()
        code, _, err = self.real_sync(); self.assertEqual(code, 1)
        for i in ['WEJ-2026-061','WEJ-2026-066']: self.assertIn(i, err)
        self.assertEqual(self.output.read_bytes(), before)
