"""Bounded public GameTabs search; no guessed or anonymous download bypass."""
from html.parser import HTMLParser
import json
import re
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler
ORIGIN = 'https://gametabs.net'
ID_RE = re.compile(r'[a-zA-Z0-9_-]{1,200}/[a-zA-Z0-9_-]{1,240}\Z')
class GameTabsLoginRequired(ValueError):
    pass
class _SameOriginRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        p = urlsplit(newurl)
        if p.scheme != 'https' or p.netloc != 'gametabs.net':
            raise ValueError('GameTabs redirected outside its expected origin.')
        return super().redirect_request(req, fp, code, msg, headers, newurl)
def fetch(path):
    if not path.startswith('/tabs') or path.startswith('//'):
        raise ValueError('Invalid GameTabs path.')
    req = Request(ORIGIN + path, headers={'User-Agent': 'RetroTerminal-Tabs/1.0', 'Accept': 'text/html'})
    with build_opener(_SameOriginRedirect()).open(req, timeout=12) as response:
        raw = response.read(4 * 1024 * 1024 + 1)
    if len(raw) > 4 * 1024 * 1024:
        raise ValueError('GameTabs response is too large.')
    return raw.decode('utf-8')
def _tab_id(url):
    p = urlsplit(url)
    if p.scheme and (p.scheme != 'https' or p.netloc != 'gametabs.net'):
        return None
    if p.netloc and p.netloc != 'gametabs.net':
        return None
    if p.query or p.fragment or not p.path.startswith('/tabs/'):
        return None
    ident = p.path[len('/tabs/'):].rstrip('/')
    return ident if ID_RE.fullmatch(ident) else None
class _SearchParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.scope = 0
        self.items = []
        self.current = None
        self.saw_list = False
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'div':
            if attrs.get('id') == 'tabs-page-tabs-list':
                self.scope = 1
                self.saw_list = True
            elif self.scope:
                self.scope += 1
        if self.scope and tag == 'a':
            ident = _tab_id(attrs.get('href', ''))
            label = attrs.get('title', '')
            if ident and label:
                title, sep, game = label.rpartition(' - ')
                self.current = {'id': ident, 'title': (title if sep else label)[:240],
                                'artist': game[:240], 'url': ORIGIN + '/tabs/' + ident}
    def handle_endtag(self, tag):
        if tag == 'a' and self.current:
            self.items.append(self.current)
            self.current = None
        if tag == 'div' and self.scope:
            self.scope -= 1
def parse_search(html):
    parser = _SearchParser()
    parser.feed(html)
    if not parser.saw_list:
        raise ValueError('GameTabs returned an unexpected search page.')
    return list({item['id']: item for item in parser.items}.values())[:100]
def search(query):
    term = query.get('q', [''])[0].strip()
    if not 2 <= len(term) <= 120:
        raise ValueError('Enter between 2 and 120 search characters.')
    page = str(query.get('page', ['1'])[0])
    if page != '1':
        raise ValueError('GameTabs search currently supports its first results page only.')
    return {'items': parse_search(fetch('/tabs?' + urlencode({'search': term}))),
            'page': 1, 'has_more': False, 'import_available': False, 'login_required': True}
class _DetailParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tab = None
        self.disabled_files = False
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get('id') == 'tab-page-wrapper' and attrs.get('data-tab'):
            self.tab = json.loads(attrs['data-tab'])
        if tag == 'button' and 'tab-file-tile' in attrs.get('class', '').split() and 'disabled' in attrs:
            self.disabled_files = True
def import_tab(ident):
    if not isinstance(ident, str) or not ID_RE.fullmatch(ident):
        raise ValueError('Invalid GameTabs tab ID.')
    parser = _DetailParser()
    parser.feed(fetch('/tabs/' + ident))
    if not isinstance(parser.tab, dict) or not parser.tab.get('name'):
        raise ValueError('GameTabs returned an unexpected tab page.')
    if parser.disabled_files:
        raise GameTabsLoginRequired('GameTabs requires a connected account to download files. Search is available; direct import is not connected yet.')
    raise ValueError('No supported GameTabs download is available. Direct import requires a verified authenticated download flow.')
