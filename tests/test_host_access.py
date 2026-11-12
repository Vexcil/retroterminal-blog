"""Exercise the real HTTP routes with an untrusted client."""
import hashlib
import http.client
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from functools import partial
import bcrypt
from http.server import ThreadingHTTPServer

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from tabs_host_server import TabsHostHandler


class HostAccessTests(unittest.TestCase):
    def test_private_routes_and_login(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            settings = dict(username='guest', salt='12' * 16,
                password_hash=hashlib.pbkdf2_hmac('sha256', b'test-password', bytes.fromhex('12' * 16), 260000).hex(),
                session_key='34' * 32, origins=['https://retroterminal.net'])
            settings['users']={'vex':{'algorithm':'bcrypt','password_hash':bcrypt.hashpw(b'vex-password',bcrypt.gensalt(rounds=4)).decode()}}
            config = root / 'access.json'
            config.write_text(json.dumps(settings))
            old = os.environ.get('TABS_ACCESS_CONFIG')
            os.environ['TABS_ACCESS_CONFIG'] = str(config)
            (root / 'tabs.json').write_text('[]')
            server = ThreadingHTTPServer(('127.0.0.1', 0), partial(TabsHostHandler,
                data_dir=root, files_dir=root, allow_origin='https://retroterminal.net',
                viewer_url='https://retroterminal.net/tabs/', url_prefix='/files', play_counts_file=root/'plays.json'))
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            connection = http.client.HTTPConnection(*server.server_address)
            def request(method, path, body=None, headers=None):
                connection.request(method, path, body, headers or {})
                response = connection.getresponse()
                result = (response.status, dict(response.getheaders()), response.read())
                return result
            try:
                for path in ('/api/tabs', '/data/tabs.json', '/files/example.gp', '/viewer/', '/api/youtube-sync?file=/files/example.gp', '/api/gametabs/search?q=chrono'):
                    self.assertEqual(request('GET', path)[0], 401)
                    result = request('HEAD', path)
                    self.assertEqual((result[0], result[2]), (401, b''))
                self.assertEqual(request('POST', '/api/songsterr/import', '{}')[0], 401)
                self.assertEqual(request('POST', '/api/gametabs/import', '{}')[0], 401)
                self.assertEqual(request('POST', '/api/youtube-sync', '{}')[0], 401)
                self.assertEqual(json.loads(request('GET', '/api/session')[2]), {'authenticated':False})
                result = request('POST', '/api/login', json.dumps({'username':'guest', 'password':'test-password'}),
                    {'Content-Type':'application/json', 'Origin':'https://retroterminal.net'})
                self.assertEqual(result[0], 200)
                cookie = result[1]['Set-Cookie']
                for flag in ('HttpOnly', 'Secure', 'SameSite=Lax'):
                    self.assertIn(flag, cookie)
                headers = {'Cookie':cookie.split(';')[0]}
                self.assertEqual(request('GET', '/data/tabs.json', headers=headers)[0], 200)
                result = request('POST','/api/login',json.dumps({'username':'vex','password':'vex-password'}),{'Content-Type':'application/json'})
                self.assertEqual(result[0],200)
                self.assertEqual(request('GET','/data/tabs.json',headers={'Cookie':result[1]['Set-Cookie'].split(';')[0]})[0],200)
                # Existing guest cookies remain valid after logging in as vex elsewhere.
                self.assertEqual(request('GET','/data/tabs.json',headers=headers)[0],200)
                self.assertEqual(request('POST','/api/login',json.dumps({'username':'vex','password':'test-password'}))[0],401)
                self.assertEqual(request('POST','/api/login',json.dumps({'username':'unknown','password':'test-password'}))[0],401)
                self.assertEqual(request('POST', '/api/play', '{}', dict(headers, Origin='https://untrusted.example'))[0], 403)
                self.assertEqual(request('POST', '/api/gametabs/import', '{"id":"game/title"}', dict(headers, Origin='https://untrusted.example'))[0], 403)
                self.assertEqual(request('POST', '/api/gametabs/import', '{"id":"../oops"}', headers)[0], 400)
                with patch('tabs_host_server.gametabs_import', return_value={'filename':'Test.gp5','data':b'FICHIER GUITAR PRO'+b'\0'*80}), patch.object(TabsHostHandler,'rebuild_index'):
                    first=request('POST','/api/gametabs/import','{"id":"game/title"}',headers)
                    self.assertEqual(first[0],201)
                with patch('tabs_host_server.gametabs_import', side_effect=AssertionError('should reuse')):
                    again=request('POST','/api/gametabs/import','{"id":"game/title"}',headers)
                    self.assertEqual(again[0],200)
                    self.assertTrue(json.loads(again[2])['alreadyExists'])
                with patch('tabs_host_server.gametabs_import', return_value={'filename':'bad.gp5','data':b'<html>not guitar pro</html>'}):
                    self.assertEqual(request('POST','/api/gametabs/import','{"id":"game/bad"}',headers)[0],400)

            finally:
                connection.close()
                server.shutdown()
                server.server_close()
                if old is None:
                    os.environ.pop('TABS_ACCESS_CONFIG', None)
                else:
                    os.environ['TABS_ACCESS_CONFIG'] = old

if __name__ == '__main__':
    unittest.main()
