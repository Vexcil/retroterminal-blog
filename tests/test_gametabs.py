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
        with patch.object(g, 'fetch', return_value=html):
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
