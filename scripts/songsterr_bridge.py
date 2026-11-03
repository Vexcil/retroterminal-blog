"""Read-only, bounded Songsterr metadata bridge. Never fetch arbitrary URLs."""
import json
import math
import re
import threading
import time
from urllib.parse import quote
from urllib.request import Request, urlopen
from tab_catalog import normalize

_cache = {}
_lock = threading.Lock()


def fetch(path):
    now = time.monotonic()
    with _lock:
        cached = _cache.get(path)
        if cached and now - cached[0] < 600:
            return cached[1]
    request = Request('https://www.songsterr.com' + path, headers={'User-Agent': 'RetroTerminal-Tabs/1.0', 'Accept': 'application/json'})
    with urlopen(request, timeout=10) as response:
        raw = response.read(4 * 1024 * 1024 + 1)
    if len(raw) > 4 * 1024 * 1024:
        raise ValueError('Songsterr response is too large.')
    data = json.loads(raw)
    with _lock:
        if len(_cache) >= 100:
            _cache.pop(next(iter(_cache)))
        _cache[path] = (now, data)
    return data


def songsterr_response(route, query):
    if route == '/api/songsterr/search':
        term = query.get('q', [''])[0].strip()
        if not 2 <= len(term) <= 120:
            raise ValueError('Enter between 2 and 120 search characters.')
        page = query.get('page', ['1'])[0]
        if not page.isdecimal() or not 1 <= int(page) <= 50:
            raise ValueError('Invalid search page.')
        offset = (int(page) - 1) * 20
        artist = query.get('artist', [''])[0].strip()
        artist_id = query.get('artist_id', [''])[0]
        if artist_id and not re.fullmatch(r'[1-9][0-9]{0,9}', artist_id):
            raise ValueError('Invalid Songsterr artist ID.')
        if artist and not artist_id:
            candidates = fetch('/api/search?pattern=' + quote(artist) + '&size=50&from=0&more=true')
            exact = [s for s in candidates.get('records', []) if normalize(s.get('artist')) == normalize(artist)]
            artist_id = str(exact[0].get('artistId') or '') if exact else ''
            if not artist_id:
                return {'items': [], 'has_more': False, 'page': int(page)}
        path = '/api/artist/' + artist_id + '/search' if artist_id else '/api/search'
        pattern = '' if artist else term
        result = fetch(path + '?pattern=' + quote(pattern) + '&size=20&from=' + str(offset) + '&more=true')
        songs = result.get('records') if isinstance(result, dict) else None
        if not isinstance(songs, list):
            raise ValueError('Songsterr returned an unexpected search response.')
        return {'items': [{'id': s['songId'], 'artist_id': s.get('artistId'), 'artist': str(s.get('artist', ''))[:200], 'title': str(s.get('title', ''))[:200]}
                          for s in songs[:20] if isinstance(s, dict) and isinstance(s.get('songId'), int)],
                'has_more': len(songs) == 20 and int(page) < 50, 'page': int(page), 'artist_id': int(artist_id) if artist_id else None}
    song_id = query.get('id', [''])[0]
    if not re.fullmatch(r'[1-9][0-9]{0,9}', song_id):
        raise ValueError('Invalid Songsterr song ID.')
    meta = fetch('/api/meta/' + song_id)
    if not isinstance(meta, dict):
        raise ValueError('Songsterr returned an unexpected song response.')
    revision = meta.get('revisionId')
    if not isinstance(revision, int) or revision <= 0:
        raise ValueError('Songsterr returned no valid revision.')
    entries = fetch('/api/video-points/' + song_id + '/' + str(revision) + '/list')
    if not isinstance(entries, list):
        raise ValueError('Songsterr returned an unexpected timing response.')
    videos = []
    for entry in entries[:100]:
        if not isinstance(entry, dict):
            continue
        points = entry.get('points', [])
        vid = entry.get('videoId', '')
        if not isinstance(vid, str) or not re.fullmatch(r'[A-Za-z0-9_-]{11}', vid) or not isinstance(points, list) or not 2 <= len(points) <= 20000:
            continue
        if any(isinstance(p, bool) or not isinstance(p, (int, float)) or not math.isfinite(p) or not 0 <= p <= 86400 for p in points):
            continue
        if any(b <= a for a, b in zip(points, points[1:])):
            continue
        videos.append({'videoId': vid, 'feature': str(entry.get('feature') or 'Full mix')[:80], 'points': points})
    return {'id': int(song_id), 'revision': revision, 'artist': meta.get('artist', ''), 'title': meta.get('title', ''), 'videos': videos}
