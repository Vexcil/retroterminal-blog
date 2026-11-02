import concurrent.futures
import copy
from functools import partial
from http.server import ThreadingHTTPServer
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from tabs_host_server import TabsHostHandler


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory()
        self.root=Path(self.folder.name)
        (self.root/'uploads').mkdir()
        (self.root/'uploads/a b.gp').write_bytes(b'fixture')
        config=self.root/'access.json'
        config.write_text(json.dumps({'home_ips':['127.0.0.1'],'origins':['https://retroterminal.net']}))
        self.previous=os.environ.get('TABS_ACCESS_CONFIG')
        os.environ['TABS_ACCESS_CONFIG']=str(config)
        self.handler=partial(TabsHostHandler,data_dir=self.root,files_dir=self.root,
            allow_origin='https://retroterminal.net',viewer_url='/',url_prefix='/files',play_counts_file=self.root/'plays.json')
        self.server=ThreadingHTTPServer(('127.0.0.1',0),self.handler)
        threading.Thread(target=self.server.serve_forever,daemon=True).start()
        self.base='http://127.0.0.1:'+str(self.server.server_port)
        self.file='https://tabs.retroterminal.net/files/uploads/a%20b.gp'
        self.sync=dict(version=1,videoId='lUBCXGeK694',barCount=2,points=[
            dict(barIndex=0,barOccurence=0,barPosition=0,millisecondOffset=0),
            dict(barIndex=1,barOccurence=0,barPosition=0,millisecondOffset=1000)])

    def tearDown(self):
        self.server.shutdown(); self.server.server_close()
        if self.previous is None: os.environ.pop('TABS_ACCESS_CONFIG',None)
        else: os.environ['TABS_ACCESS_CONFIG']=self.previous
        self.folder.cleanup()

    def request(self,method,body=None,file=None):
        target=self.base+'/api/youtube-sync'
        if method=='GET': target+='?'+urlencode({'file':file or self.file})
        payload=json.dumps(body).encode() if body is not None else None
        request=Request(target,data=payload,method=method,headers={'Content-Type':'application/json','Origin':'https://retroterminal.net'})
        try:
            with urlopen(request) as response: return response.status,json.load(response)
        except HTTPError as error:
            return error.code,json.load(error)

    def save(self,revision=0,sync=None):
        return self.request('POST',dict(file=self.file,revision=revision,sync=sync or self.sync))

    def test_persistence_and_origin_independent_identity(self):
        self.assertEqual(self.request('GET')[1]['revision'],0)
        self.assertEqual(self.save()[0],200)
        # A separately opened connection, using the tailnet URL, sees the same durable record.
        status,data=self.request('GET',file='https://vex-ser.adal-fort.ts.net:11443/files/uploads/a%20b.gp')
        self.assertEqual((status,data['revision'],data['sync']),(200,1,self.sync))
        self.assertTrue((self.root/'youtube-sync.sqlite3').is_file())
        self.server.shutdown(); self.server.server_close()
        self.server=ThreadingHTTPServer(('127.0.0.1',0),self.handler)
        threading.Thread(target=self.server.serve_forever,daemon=True).start()
        self.base='http://127.0.0.1:'+str(self.server.server_port)
        self.assertEqual(self.request('GET')[1]['sync'],self.sync)

    def test_conflicts_and_lost_response_retry(self):
        self.assertEqual(self.save()[0],200)
        self.assertEqual(self.save()[0],200)  # Identical retry is idempotent.
        other=copy.deepcopy(self.sync); other['points'][1]['millisecondOffset']=2000
        self.assertEqual(self.save(sync=other)[0],409)
        self.assertEqual(self.request('GET')[1]['sync'],self.sync)
        self.assertEqual(self.save(revision=1,sync=other)[1]['revision'],2)

    def test_concurrent_writers(self):
        other=copy.deepcopy(self.sync); other['videoId']='M7lc1UVf-VE'
        barrier=threading.Barrier(2)
        def write(sync):
            barrier.wait()
            return self.save(sync=sync)[0]
        with concurrent.futures.ThreadPoolExecutor(2) as pool:
            results=list(pool.map(write,[self.sync,other]))
        self.assertEqual(sorted(results),[200,409])
        self.assertEqual(self.request('GET')[1]['revision'],1)

    def test_invalid_timing_and_paths(self):
        bad=copy.deepcopy(self.sync); bad['points'][1]['millisecondOffset']=-1
        self.assertEqual(self.save(sync=bad)[0],400)
        self.assertEqual(self.request('GET',file='/files/../outside.gp')[0],400)
        self.assertEqual(self.request('GET',file='/files/missing.gp')[0],404)
        self.assertEqual(self.request('GET',file='https://example.com/not-an-archive.gp')[0],400)
        self.assertEqual(self.request('GET')[1]['revision'],0)

if __name__=='__main__': unittest.main()
