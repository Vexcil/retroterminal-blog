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
    if not re.fullmatch(r'/(?:tabs(?:\?[^#]*)?|top-tabs)', path):
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
            if attrs.get('id') in ('tabs-page-tabs-list', 'top-tabs-page-tabs-list'):
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
# The provider currently exposes unpaginated lists (50 Top Tabs / 30 search
# results observed). Slice only these genuine ordered results; never invent a
# ranking or imply this is a complete count of all matching catalog entries.
_SEARCH_CACHE = {}
PAGE_SIZE = 20

def search(query):
    term = query.get('q', [''])[0].strip()
    if term and not 2 <= len(term) <= 120:
        raise ValueError('Enter between 2 and 120 search characters.')
    page = str(query.get('page', ['1'])[0])
    if not page.isdecimal() or not 1 <= int(page) <= 50:
        raise ValueError('Invalid GameTabs results page.')
    page = int(page)
    path = '/tabs?' + urlencode({'search': term}) if term else '/top-tabs'
    now = time.monotonic()
    with _LOCK:
        cached = _SEARCH_CACHE.get(path)
        if cached and now - cached[0] < 300:
            items = cached[1]
        else:
            items = parse_search(fetch(path))
            if len(_SEARCH_CACHE) >= 32:
                _SEARCH_CACHE.pop(next(iter(_SEARCH_CACHE)))
            _SEARCH_CACHE[path] = (now, items)
    offset = (page - 1) * PAGE_SIZE
    status = session_status()
    return {'items': items[offset:offset + PAGE_SIZE],
            'page': page, 'has_more': offset + PAGE_SIZE < len(items),
            'mode': 'search' if term else 'top', 'pagination': 'local',
            'total_available': len(items), 'page_size': PAGE_SIZE,
            'source_url': ORIGIN + path,
            'import_available': status['connected'], 'login_required': not status['connected']}
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

# Session state is deliberately outside repository and public import storage.
import os
import stat
import tempfile
import threading
import time
from pathlib import Path
from http.cookiejar import Cookie, CookieJar
from urllib.request import HTTPCookieProcessor
from urllib.error import HTTPError
_LOCK = threading.RLock()
_ALLOWED = re.compile(r'/(?:tabs(?:\?[^#]*)?|tabs/[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+|tab-file-download/[0-9]+|preparing-tab-file-download/[a-fA-F0-9-]+|file-download/[a-fA-F0-9-]+|api/auth/cookie_login/|login(?:\?[^#]*)?)\Z')

def _path(url):
    p = urlsplit(url)
    if (p.scheme and p.scheme != 'https') or (p.netloc and p.netloc != 'gametabs.net') or p.fragment:
        raise ValueError('Unexpected GameTabs download destination.')
    value = p.path + ('?' + p.query if p.query else '')
    if not _ALLOWED.fullmatch(value):
        raise ValueError('Unexpected GameTabs download path.')
    return value

class _SessionRedirect(_SameOriginRedirect):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        _path(newurl)
        if req.data is not None:
            raise ValueError('Unexpected login redirect.')
        return super().redirect_request(req, fp, code, msg, headers, newurl)

def _session_path():
    p = Path(os.environ.get('GAMETABS_SESSION_FILE', '/gametabs-session/session.json'))
    if not p.is_absolute() or p.parent.resolve() != p.parent:
        raise ValueError('GameTabs session directory must be absolute and not symlinked.')
    st = p.parent.stat()
    if st.st_uid != os.getuid() or stat.S_IMODE(st.st_mode) != 0o700:
        raise ValueError('GameTabs session directory must be owner-only (0700).')
    return p

def _load():
    jar = CookieJar()
    try:
        p = _session_path()
        fd = os.open(p, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except FileNotFoundError:
        return jar
    with os.fdopen(fd, 'rb') as f:
        st = os.fstat(f.fileno())
        if not stat.S_ISREG(st.st_mode) or st.st_uid != os.getuid() or stat.S_IMODE(st.st_mode) != 0o600 or st.st_nlink != 1 or st.st_size > 65536:
            raise ValueError('Unsafe GameTabs session file.')
        data = json.loads(f.read(65537))
    if not isinstance(data, list) or len(data) > 100:
        raise ValueError('Invalid GameTabs session data.')
    for c in data:
        if not isinstance(c, dict) or not isinstance(c.get('name'), str) or not isinstance(c.get('value'), str) or not isinstance(c.get('path'), str) or (c.get('expires') is not None and not isinstance(c.get('expires'), (int, float))):
            raise ValueError('Invalid GameTabs cookie data.')
        if c.get('domain') not in ('gametabs.net', '.gametabs.net'):
            raise ValueError('Unexpected GameTabs cookie origin.')
        try:
            cookie = Cookie(**c)
        except (TypeError, ValueError, AttributeError):
            raise ValueError('Invalid GameTabs cookie data.') from None
        if not cookie.is_expired():
            jar.set_cookie(cookie)
    return jar

def _save(jar):
    p = _session_path()
    if p.is_symlink():
        raise ValueError('Unsafe GameTabs session file.')
    fields = ('version','name','value','port','port_specified','domain','domain_specified','domain_initial_dot','path','path_specified','secure','expires','discard','comment','comment_url','rfc2109')
    rows = []
    for c in jar:
        if c.domain not in ('gametabs.net', '.gametabs.net') or c.is_expired():
            continue
        row = {k: getattr(c, k) for k in fields}
        row['rest'] = c._rest
        rows.append(row)
    fd, name = tempfile.mkstemp(prefix='.session-', dir=p.parent)
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(rows, f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(name, p)
    finally:
        if os.path.exists(name):
            os.unlink(name)

def session_status():
    # Local availability is not a promise that the server has not revoked it.
    with _LOCK:
        try:
            available = any(True for _ in _load())
        except (OSError, ValueError, TypeError, AttributeError):
            available = False
    return {'connected': available}

def _request(opener, path, data=None, limit=4*1024*1024):
    path = _path(path)
    headers = {'User-Agent': 'RetroTerminal-Tabs/1.0'}
    if data is not None:
        headers['Content-Type'] = 'application/json'
    req = Request(ORIGIN + path, data=data, headers=headers)
    try:
        with opener.open(req, timeout=20) as response:
            final = _path(response.geturl())
            raw = response.read(limit + 1)
    except HTTPError as e:
        if e.code in (401, 403):
            raise GameTabsLoginRequired('GameTabs session expired or was rejected. Reconnect GameTabs on the server.') from None
        raise ValueError('GameTabs request failed.') from None
    if final.startswith('/login'):
        raise GameTabsLoginRequired('GameTabs session expired. Reconnect GameTabs on the server.')
    if len(raw) > limit:
        raise ValueError('GameTabs response is too large.')
    return raw

def connect(username, password):
    if not isinstance(username, str) or not isinstance(password, str) or not username.strip() or not password or len(username)>200 or len(password)>4096:
        raise ValueError('Username and password are required.')
    with _LOCK:
        _session_path()  # Fail before transmitting credentials if storage unsafe.
        jar = CookieJar()
        opener = build_opener(_SessionRedirect(), HTTPCookieProcessor(jar))
        _request(opener, '/api/auth/cookie_login/', json.dumps({'username': username, 'password': password}).encode())
        if not any(True for _ in jar):
            raise GameTabsLoginRequired('GameTabs did not provide a session.')
        # Confirm authenticated file access rather than treating a consent cookie as login.
        probe = _FilesParser()
        probe.feed(_request(opener, '/tabs/chrono-trigger/chrono-and-marle').decode('utf-8'))
        if probe.disabled_files or not probe.files:
            raise GameTabsLoginRequired('GameTabs login did not enable file access.')
        _save(jar)
    return {'connected': True}

class _FilesParser(_DetailParser):
    def __init__(self):
        super().__init__()
        self.files = []
        self.current = None
        self.download = None
    def handle_starttag(self, tag, attrs):
        super().handle_starttag(tag, attrs)
        a = dict(attrs)
        if tag == 'a':
            if a.get('id') == 'preparing-file-download-link':
                self.download = a.get('href')
            if 'tab-file-tile' in a.get('class', '').split():
                self.current = [a.get('href', ''), '']
    def handle_data(self, text):
        if self.current is not None:
            self.current[1] += text
    def handle_endtag(self, tag):
        if tag == 'a' and self.current is not None:
            self.files.append(self.current)
            self.current = None

def import_tab(ident):
    if not isinstance(ident, str) or not ID_RE.fullmatch(ident):
        raise ValueError('Invalid GameTabs tab ID.')
    with _LOCK:
        jar = _load()
        opener = build_opener(_SessionRedirect(), HTTPCookieProcessor(jar))
        parser = _FilesParser()
        parser.feed(_request(opener, '/tabs/' + ident).decode('utf-8'))
        if parser.disabled_files:
            raise GameTabsLoginRequired('GameTabs requires a connected account. Reconnect GameTabs on the server.')
        if not isinstance(parser.tab, dict) or not parser.tab.get('name'):
            raise ValueError('GameTabs returned an unexpected tab page.')
        selected = None
        for href, label in parser.files:
            match = re.search(r'([^\s/\\]+\.(?:gp[345x]?|gpx))\s*$', label.strip(), re.I)
            if match:
                path = _path(href)
                if not re.fullmatch(r'/tab-file-download/[0-9]+', path):
                    raise ValueError('Unexpected GameTabs attachment route.')
                selected = (path, match.group(1))
                break
        if selected is None:
            raise ValueError('This GameTabs tab has no Guitar Pro file.')
        prep = _FilesParser()
        prep.feed(_request(opener, selected[0]).decode('utf-8'))
        if not prep.download:
            raise ValueError('GameTabs returned no download link.')
        path = _path(prep.download)
        if not re.fullmatch(r'/file-download/[a-fA-F0-9-]+', path):
            raise ValueError('Unexpected GameTabs download route.')
        time.sleep(5.5)  # Respect the provider’s visible preparation countdown.
        raw = _request(opener, path, limit=32*1024*1024)
        if not (raw[:1] and (any(sig in raw[:40] for sig in (b'FICHIER GUITAR PRO', b'FICHIER GUITARE PRO', b'FILE GUITAR PRO')) or raw.startswith((b'BCFZ', b'BCFS', b'PK\x03\x04')))):
            raise ValueError('GameTabs returned an invalid Guitar Pro file.')
        if raw.startswith(b'PK\x03\x04'):
            import io, zipfile
            try:
                with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                    if 'Content/score.gpif' not in archive.namelist():
                        raise ValueError('Missing Guitar Pro score.')
            except (zipfile.BadZipFile, ValueError):
                raise ValueError('GameTabs returned an invalid Guitar Pro archive.') from None
        _save(jar)
        game = parser.tab.get('game') or {}
        return {'title': str(parser.tab['name'])[:240], 'artist': str(game.get('name', ''))[:240], 'filename': selected[1], 'data': raw}

if __name__ == '__main__':
    import argparse
    import getpass
    ap = argparse.ArgumentParser(description='Connect a persistent private GameTabs server session.')
    ap.add_argument('action', choices=['login','status'])
    args = ap.parse_args()
    try:
        result = connect(input('GameTabs username: '), getpass.getpass('GameTabs password: ')) if args.action == 'login' else session_status()
        print('GameTabs session saved; reconnect if it expires.' if result['connected'] else 'GameTabs is not connected.')
    except Exception:
        print('GameTabs connection failed. Check credentials and private session directory; no password was saved.')
        raise SystemExit(1)
