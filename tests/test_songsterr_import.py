import io
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from tabs_host_server import TabsHostHandler
from youtube_sync_store import connect


class ImportTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.files=self.root/'tabs'; self.files.mkdir()
        self.data=self.root/'data'
        self.lock=threading.Lock()

    def tearDown(self):
        self.tmp.cleanup()

    def request(self, song_id):
        handler=object.__new__(TabsHostHandler)
        payload=json.dumps({'id':song_id}).encode()
        handler.headers={'Content-Length':str(len(payload))}
        handler.rfile=io.BytesIO(payload)
        handler.files_dir=self.files; handler.data_dir=self.data
        handler.url_prefix='/files'; handler.upload_lock=self.lock
        handler.rebuild_index=lambda: None
        handler.send_json=lambda status,body:(status,body)
        return handler.import_songsterr()

    def generate(self, tracks, file, meta):
        file.write_bytes(b'example generated Guitar Pro file')

    def test_simultaneous_retries_fetch_and_generate_once(self):
        with patch('songsterr_vendor.gen_gp.fetch_all_tracks',return_value=({'artist':'Artist','title':'Song'},[])) as fetch, patch('songsterr_vendor.gen_gp.generate_gp',side_effect=self.generate):
            with ThreadPoolExecutor(2) as pool:
                results=list(pool.map(self.request,[42,42]))
            self.assertEqual(sorted(status for status,_ in results),[200,201])
            self.assertEqual(results[0][1]['file'],results[1][1]['file'])
            self.assertEqual(fetch.call_count,1)
            self.assertEqual(len(list(self.files.rglob('*.gp'))),1)

    def test_previously_saved_source_link_opens_existing_file_without_fetch(self):
        file=self.files/'original.gp'; file.write_bytes(b'existing')
        payload=json.dumps({'source':{'songsterrId':42}})
        with connect(self.data) as db:
            db.execute('INSERT INTO youtube_sync VALUES (?,?,?,?)',('original.gp',payload,7,'unchanged'))
        with patch('songsterr_vendor.gen_gp.fetch_all_tracks') as fetch:
            status,result=self.request(42)
        self.assertEqual(status,200); self.assertTrue(result['alreadyExists'])
        self.assertEqual(result['file'],'/files/original.gp'); fetch.assert_not_called()
        with connect(self.data) as db:
            self.assertEqual(db.execute('SELECT payload,revision,updated_at FROM youtube_sync').fetchone(),(payload,7,'unchanged'))

    def test_different_source_ids_with_same_title_are_not_merged(self):
        with patch('songsterr_vendor.gen_gp.fetch_all_tracks',return_value=({'artist':'Artist','title':'Song'},[])), patch('songsterr_vendor.gen_gp.generate_gp',side_effect=self.generate):
            first=self.request(42); second=self.request(43)
        self.assertEqual((first[0],second[0]),(201,201))
        self.assertNotEqual(first[1]['file'],second[1]['file'])
