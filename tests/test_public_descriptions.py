import csv, io, json, sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import sync_events as sync

class PublicDescriptionTests(unittest.TestCase):
    def setUp(self):
        self.events=json.loads((Path(__file__).resolve().parents[1]/'events.json').read_text())
        self.headers=['ID','掲載判定','イベント名','開催日','カテゴリ','都道府県','会場','料金','公式URL','確認日','公開用説明','備考']
        self.rows=[dict(zip(self.headers,[e['id'],'掲載',e['title'],e['dateLabel'],e['category'],e['region'],e['venue'],e['price'],e['url'],e['addedAt'],'','Canva制作履歴'])) for e in self.events]
    def build(self):
        f=io.StringIO();w=csv.DictWriter(f,self.headers);w.writeheader();w.writerows(self.rows)
        return sync.build_events(f.getvalue(), self.events)
    def test_current_100_roundtrip_and_no_blanks(self):
        self.assertEqual(self.build(),self.events)
        self.assertFalse(sync.validate_events(self.events))
        self.assertGreaterEqual(len(self.events),100)
    def test_missing_id_stops(self):
        self.rows.pop()
        with self.assertRaises(sync.SyncError):self.build()
    def test_new_without_description_stops(self):
        self.rows.append(dict(self.rows[0],ID='WEJ-2026-999'))
        with self.assertRaises(sync.SyncError):self.build()
    def test_new_with_description_succeeds(self):
        self.rows.append(dict(self.rows[0],ID='WEJ-2026-999',公開用説明='試飲を楽しむイベント。'))
        self.assertEqual(len(self.build()),len(self.events)+1)
    def test_internal_copy_stops(self):
        self.rows[0]['公開用説明']='Canva制作履歴'
        with self.assertRaises(sync.SyncError):self.build()
    def test_duplicate_id_stops(self):
        self.rows.append(dict(self.rows[0]))
        with self.assertRaises(sync.SyncError):self.build()
    def test_id_fallback_survives_title_change(self):
        self.rows[0]['イベント名']='変更後の名称'
        e=next(e for e in self.build() if e['id']==self.rows[0]['ID'])
        self.assertEqual(e['publicDescription'],self.events[0]['publicDescription'])
    def test_blank_public_json_rejected(self):
        self.events[0]['publicDescription']=' '
        self.assertTrue(sync.validate_events(self.events))
if __name__=='__main__':unittest.main()
