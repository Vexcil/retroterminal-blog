import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import gametabs_bridge as g
SEARCH = '''<a href="https://gametabs.net/tabs/outside/ignore" title="Ignore"></a>
<div id="tabs-page-tabs-list"><div class="results-list">
<a href="https://gametabs.net/tabs/chrono-trigger/chrono-and-marle" title="Chrono and Marle - Chrono Trigger"><div><span>text</span></div></a>
<a href="https://evil.test/tabs/a/b" title="Bad"></a>
<a href="//evil.test/tabs/a/b" title="Bad"></a>
<a href="/tabs/a/../secret" title="Bad"></a></div></div>'''
class GameTabsTests(unittest.TestCase):
    def test_public_search(self):
        with patch.object(g, 'fetch', return_value=SEARCH) as fetch:
            result = g.search({'q': ['chrono trigger']})
            fetch.assert_called_once_with('/tabs?search=chrono+trigger')
        self.assertEqual(len(result['items']), 1)
        self.assertEqual(result['items'][0]['id'], 'chrono-trigger/chrono-and-marle')
        self.assertEqual(result['items'][0]['title'], 'Chrono and Marle')
        self.assertEqual(result['items'][0]['artist'], 'Chrono Trigger')
        self.assertFalse(result['has_more'])
        self.assertFalse(result['import_available'])
        self.assertTrue(result['login_required'])
    def test_login_required(self):
        html = '''<div id="tab-page-wrapper" data-tab="{&quot;name&quot;:&quot;Chrono and Marle&quot;}"><button disabled class="tab-file-tile"><span>arr.gp5</span></button></div>'''
        with patch.object(g, '_request', return_value=html.encode()), patch.object(g, '_load', return_value=g.CookieJar()):
            with self.assertRaises(g.GameTabsLoginRequired):
                g.import_tab('chrono-trigger/chrono-and-marle')
    def test_reject_bad_ids_without_fetch(self):
        with patch.object(g, 'fetch') as fetch:
            for ident in ['https://evil.test/file', '../secret', 'game/tab?x=1', 'game/%2e%2e', 'game/tab/extra']:
                with self.assertRaises(ValueError):
                    g.import_tab(ident)
            fetch.assert_not_called()
    def test_unexpected_html(self):
        with self.assertRaises(ValueError):
            g.parse_search('<html>login or error</html>')
    def test_query_limits(self):
        for query in [{'q': ['x']}, {'q': ['x' * 121]}, {'q': ['chrono'], 'page': ['2']}]:
            with self.assertRaises(ValueError):
                g.search(query)
    def test_redirect_blocks_external_origin(self):
        with self.assertRaises(ValueError):
            g._SameOriginRedirect().redirect_request(None, None, 302, '', {}, 'https://evil.test/')
if __name__ == '__main__':
    unittest.main()

class SessionTests(unittest.TestCase):
    def test_authenticated_download(self):
        detail = b'<div id="tab-page-wrapper" data-tab="{&quot;name&quot;:&quot;Song&quot;,&quot;game&quot;:{&quot;name&quot;:&quot;Game&quot;}}"><a class="tab-file-tile" href="https://gametabs.net/tab-file-download/27508">GP song.gp5</a></div>'
        prep = b'<a id="preparing-file-download-link" href="/file-download/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee">Download</a>'
        raw = b'\x18FICHIER GUITAR PRO v5.10' + b'\x00' * 100
        with patch.object(g, '_load', return_value=g.CookieJar()), patch.object(g, '_request', side_effect=[detail, prep, raw]) as request, patch.object(g, '_save'), patch.object(g.time, 'sleep') as sleep:
            result = g.import_tab('game/song')
        self.assertEqual(result['data'], raw)
        self.assertEqual(result['filename'], 'song.gp5')
        sleep.assert_called_once_with(5.5)
        self.assertEqual(request.call_count, 3)
    def test_path_restrictions(self):
        for path in ['https://evil.test/file-download/abcd', '//evil.test/file-download/abcd', '/file-download/../admin', '/api/users/', '/file-download/abcd?secret=1']:
            with self.assertRaises(ValueError):
                g._path(path)
    def test_private_session_roundtrip(self):
        import tempfile, os
        with tempfile.TemporaryDirectory() as d, patch.dict(os.environ, {'GAMETABS_SESSION_FILE': d+'/session.json'}):
            os.chmod(d, 0o700)
            jar = g.CookieJar()
            jar.set_cookie(g.Cookie(0,'session','TEST',None,False,'gametabs.net',False,False,'/',True,True,None,True,None,None,{},False))
            g._save(jar)
            self.assertEqual(os.stat(d+'/session.json').st_mode & 0o777, 0o600)
            self.assertTrue(g.session_status()['connected'])
            os.chmod(d+'/session.json',0o644)
            self.assertFalse(g.session_status()['connected'])
    def test_connect_saves_cookie_not_password(self):
        jar = g.CookieJar()
        jar.set_cookie(g.Cookie(0,'session','TEST',None,False,'gametabs.net',False,False,'/',True,True,None,True,None,None,{},False))
        with patch.object(g, '_session_path'), patch.object(g, 'CookieJar', return_value=jar), patch.object(g, '_request', return_value=b'<a class="tab-file-tile" href="/tab-file-download/27508">song.gp5</a>') as req, patch.object(g, '_save') as save:
            self.assertTrue(g.connect('name','secret')['connected'])
            self.assertEqual(req.call_args_list[0].args[1], '/api/auth/cookie_login/')
            self.assertEqual(save.call_args.args, (jar,))

class BadSessionTests(unittest.TestCase):
    def test_malformed_session_fails_closed(self):
        import tempfile, os
        with tempfile.TemporaryDirectory() as d, patch.dict(os.environ, {'GAMETABS_SESSION_FILE': d+'/session.json'}):
            os.chmod(d, 0o700)
            for content in ['{}', '[null]', '[{"domain":"gametabs.net"}]', 'invalid']:
                with open(d+'/session.json','w') as f:
                    f.write(content)
                os.chmod(d+'/session.json',0o600)
                self.assertFalse(g.session_status()['connected'])
