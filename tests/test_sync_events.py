"""Offline safety tests. Real snapshot is never silently cleaned for passing tests."""
import csv
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import sync_events as sync

SNAPSHOT = json.loads((ROOT / 'tests/fixtures/events_2026-10-28.json').read_text())
HEADERS = ['ID','掲載判定','イベント名','開催日','カテゴリ','都道府県','会場',
           '料金','公式URL','画像URL','チケットURL','公開用説明','備考','最終更新日']
MANUAL_IDS = {f'WEJ-2026-{n:03d}' for n in range(53, 71)}


def normal_events():
    # Deliberately synthetic descriptions; not a claim that current copy passes audit.
    return [dict(e, publicDescription='ウイスキーを楽しめるイベントです。') for e in SNAPSHOT]


def rows(events):
    mapping = {'ID':'id','イベント名':'title','開催日':'dateLabel','カテゴリ':'category',
               '都道府県':'region','会場':'venue','料金':'price','公式URL':'url',
               '画像URL':'imageUrl','チケットURL':'ticketUrl','公開用説明':'publicDescription',
               '最終更新日':'addedAt'}
    return [dict({k:e[v] for k,v in mapping.items()}, 掲載判定='掲載',
                 備考='Canva完成／WEJ-CAND-001／GitHub作業記録') for e in events]


def csv_text(data):
    out = io.StringIO()
    writer = csv.DictWriter(out, HEADERS)
    writer.writeheader()
    writer.writerows(data)
    return out.getvalue()


class SafetyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.output = Path(self.tmp.name) / 'events.json'
        self.backup = Path(self.tmp.name) / 'events.json.backup'
        self.events = normal_events()
        self.write(self.events)
        for name, value in [('OUTPUT',self.output),('BACKUP',self.backup)]:
            p = patch.object(sync, name, value); p.start(); self.addCleanup(p.stop)

    def write(self, events):
        self.output.write_text(json.dumps(events, ensure_ascii=False, indent=2)+'\n')

    def run_sync(self, data=None, **kwargs):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            result = sync.sync(fetch=lambda: csv_text(data if data is not None else rows(self.events)), **kwargs)
        return result, out.getvalue(), err.getvalue()

    def assert_stopped(self, data):
        before = self.output.read_bytes()
        code, _, err = self.run_sync(data)
        self.assertEqual(code, 1, err)
        self.assertEqual(self.output.read_bytes(), before)
        self.assertFalse(self.output.with_suffix('.json.tmp').exists())
        return err

    def test_normal_92_and_new_event(self):
        data = rows(self.events)
        extra = dict(data[0], ID='WEJ-2026-999', イベント名='追加イベント')
        data.append(extra)
        before = self.output.read_bytes()
        code, _, err = self.run_sync(data)
        self.assertEqual(code, 0, err)
        result = json.loads(self.output.read_text())
        self.assertEqual(len(result), 93)
        self.assertTrue({e['id'] for e in SNAPSHOT} <= {e['id'] for e in result})
        self.assertEqual(self.backup.read_bytes(), before)
        self.assertNotIn('Canva', self.output.read_text())
        self.assertNotIn('WEJ-CAND', self.output.read_text())
        for e in result:
            self.assertNotIn('備考', e)

    def test_normal_92_round_trip_preserves_every_field(self):
        code, _, err = self.run_sync()
        self.assertEqual(code, 0, err)
        self.assertEqual({e['id']:e for e in json.loads(self.output.read_text())},
                         {e['id']:e for e in self.events})

    def test_reviewed_sheet_corrections_can_resolve_existing_internal_copy(self):
        self.write(SNAPSHOT)
        data=rows(SNAPSHOT)
        for row in data:
            if row['ID'] in {'WEJ-2026-061', 'WEJ-2026-066'}:
                row['公開用説明']='レビュー済み公開文のテスト用代替値です。'
        code,_,err=self.run_sync(data)
        self.assertEqual(code,0,err)
        self.assertEqual(len(json.loads(self.output.read_text())),92)

    def test_real_92_snapshot_is_preserved_but_existing_internal_copy_blocks_sync(self):
        self.write(SNAPSHOT)
        err = self.assert_stopped(rows(SNAPSHOT))
        self.assertIn('WEJ-2026-061', err)
        self.assertIn('WEJ-2026-066', err)
        self.assertEqual(len(json.loads(self.output.read_text())), 92)

    def test_real_snapshot_all_ids_and_historical_18_are_present(self):
        self.assertEqual(len(SNAPSHOT), 92)
        self.assertEqual(len({e['id'] for e in SNAPSHOT}), 92)
        self.assertTrue(MANUAL_IDS <= {e['id'] for e in SNAPSHOT})

    def test_missing_18_stops_despite_74_remaining(self):
        err = self.assert_stopped([r for r in rows(self.events) if r['ID'] not in MANUAL_IDS])
        for event_id in MANUAL_IDS:
            self.assertIn(event_id, err)

    def test_one_missing_replaced_by_new_id_same_count_stops(self):
        data = rows(self.events); old_id = data[0]['ID']; data[0]['ID'] = 'WEJ-2026-999'
        self.assertIn(old_id, self.assert_stopped(data))

    def test_unpublished_existing_stops(self):
        data = rows(self.events); data[0]['掲載判定'] = '候補'
        self.assertIn(data[0]['ID'], self.assert_stopped(data))

    def test_id_preserves_description_image_ticket_after_title_and_date_changes(self):
        self.events[0].update(publicDescription='長い説明文。'*100,
                              imageUrl='https://example.com/photo.png',
                              ticketUrl='https://example.com/ticket')
        self.write(self.events)
        data = rows(self.events)
        data[0].update(イベント名='変更した名称', 開催日='2027/01/12', 公開用説明='', 画像URL='', チケットURL='')
        code, _, err = self.run_sync(data); self.assertEqual(code, 0, err)
        e = next(e for e in json.loads(self.output.read_text()) if e['id']==self.events[0]['id'])
        for field in ['publicDescription','imageUrl','ticketUrl']:
            self.assertEqual(e[field], self.events[0][field])
        self.assertEqual(e['date'], '2027-01-12')

    def test_duplicate_published_and_unpublished_ids_stop(self):
        for status in ['掲載','候補']:
            with self.subTest(status=status):
                data = rows(self.events); data.append(dict(data[0], 掲載判定=status))
                self.assertIn('重複', self.assert_stopped(data))

    def test_bad_values_stop_without_erasing_links(self):
        for key,value in [('ID',''),('イベント名',''),('開催日','2026/02/30'),
                          ('開催日','2026/01/011'),('開催日','prefix2026/01/01'),
                          ('公式URL','javascript:alert(1)'),('画像URL','http://example.com/a'),
                          ('チケットURL','https://'),('画像URL','https://bad host/a')]:
            with self.subTest(field=key):
                data=rows(self.events); data[0][key]=value; self.assert_stopped(data)

    def test_internal_memos_in_each_public_text_field_stop(self):
        for field in ['イベント名','カテゴリ','都道府県','会場','料金','公開用説明']:
            for marker in ['Canva完成','WEJ-CAND-001','GitHub','作業記録','未確認メモ','イベントDB掲載']:
                with self.subTest(field=field, marker=marker):
                    data=rows(self.events); data[0][field]='説明。'+marker
                    self.assert_stopped(data)

    def test_copying_notes_into_description_stops(self):
        data=rows(self.events); data[0]['公開用説明']=data[0]['備考']='メンバー間で整理する内容'
        self.assertIn('同一', self.assert_stopped(data))

    def test_malformed_existing_data_stops(self):
        for data in [None, {}, [None], self.events+[self.events[0]],
                     [dict(self.events[0], 備考='private')], [dict(self.events[0], price=123)], []]:
            with self.subTest(data_type=type(data).__name__):
                self.write(data); self.assert_stopped(rows(self.events))

    def test_missing_baseline_stops(self):
        self.output.unlink()
        code, _, _ = self.run_sync(); self.assertEqual(code,1)
        self.assertFalse(self.output.exists())

    def test_bad_csv_and_fetch_failure_preserve_bytes(self):
        for value in ['', 'ID,掲載判定\nA,掲載\n', csv_text(rows(self.events))+',extra\n']:
            with self.subTest(value=value[:20]):
                before=self.output.read_bytes()
                with patch.object(sync, 'build_events', wraps=sync.build_events), redirect_stderr(io.StringIO()):
                    self.assertEqual(sync.sync(fetch=lambda: value),1)
                self.assertEqual(self.output.read_bytes(),before)
        before=self.output.read_bytes()
        with redirect_stderr(io.StringIO()):
            def fail(): raise OSError('network failure')
            self.assertEqual(sync.sync(fetch=fail),1)
        self.assertEqual(self.output.read_bytes(),before)

    def test_dry_run_writes_nothing(self):
        before=self.output.read_bytes()
        data=rows(self.events); data[0]['料金']='5,000円'
        code,_,err=self.run_sync(data,dry_run=True)
        self.assertEqual(code,0,err); self.assertEqual(self.output.read_bytes(),before)
        self.assertFalse(self.backup.exists())

    def test_write_failure_preserves_output_and_backup(self):
        before=self.output.read_bytes()
        with patch.object(Path,'replace',side_effect=OSError('replace failed')):
            code,_,err=self.run_sync()
        self.assertEqual(code,1,err); self.assertEqual(self.output.read_bytes(),before)
        self.assertEqual(self.backup.read_bytes(),before)
        self.assertFalse(self.output.with_suffix('.json.tmp').exists())

    def test_check_audits_real_snapshot_and_html_only_uses_public_description(self):
        self.write(SNAPSHOT)
        with redirect_stderr(io.StringIO()): self.assertEqual(sync.check(),1)
        html=(ROOT/'index.html').read_text()
        self.assertIn('esc(e.publicDescription)', html)
        self.assertNotIn('esc(e.description)', html)
        self.assertNotIn('e.備考',html)
        # The output schema rejects legacy description/internal fields before HTML can consume them.
        bad=dict(self.events[0], description='Canva internal')
        self.assertTrue(sync.validate_events([bad]))


if __name__ == '__main__': unittest.main()
