"""Authenticated, durable per-arrangement YouTube settings in the mounted data dir."""
from datetime import datetime, timezone
from contextlib import contextmanager
import json
import math
import re
import sqlite3
from urllib.parse import unquote, urlsplit

MAX_BODY = 2 * 1024 * 1024
MAX_BARS = 20000


def archive_key(handler, value):
    if not isinstance(value, str) or len(value) > 4096:
        raise ValueError('Choose a valid archive tab.')
    path = urlsplit(value).path
    if not path.startswith('/files/'):
        raise ValueError('Timing can only be saved for a tab in this library.')
    try:
        file = handler.safe_join(handler.files_dir, unquote(path[7:]))
    except (PermissionError, OSError, ValueError):
        raise ValueError('Invalid archive tab path.') from None
    if not file.is_file():
        raise FileNotFoundError('This tab is no longer in the library.')
    if file.suffix.lower() not in {'.gp', '.gp3', '.gp4', '.gp5', '.gpx', '.musicxml', '.xml', '.capx'}:
        raise ValueError('Unsupported tab file.')
    # File identity deliberately excludes the public/tailnet hostname.
    return file.relative_to(handler.files_dir).as_posix()


def integer(value, minimum, maximum):
    return type(value) is int and minimum <= value <= maximum


def validate_sync(value):
    if not isinstance(value, dict) or value.get('version') != 1:
        raise ValueError('Unsupported timing format.')
    video = value.get('videoId')
    count = value.get('barCount')
    points = value.get('points')
    if not isinstance(video, str) or not re.fullmatch(r'[A-Za-z0-9_-]{11}', video):
        raise ValueError('Invalid YouTube video ID.')
    if not integer(count, 1, MAX_BARS) or not isinstance(points, list) or len(points) > MAX_BARS + 1:
        raise ValueError('Invalid played-bar count or timing points.')
    clean = []
    previous = -1
    seen = set()
    for point in points:
        if not isinstance(point, dict):
            raise ValueError('Invalid timing point.')
        index, occurrence, position, ms = (point.get(k) for k in ('barIndex', 'barOccurence', 'barPosition', 'millisecondOffset'))
        if (not integer(index, 0, MAX_BARS - 1) or not integer(occurrence, 0, MAX_BARS - 1)
                or type(position) not in (int, float) or position not in (0, 1)
                or type(ms) not in (int, float) or not math.isfinite(ms) or not 0 <= ms <= 86400000 or ms <= previous):
            raise ValueError('Timing points must be valid and increase in playback order.')
        identity = (index, occurrence, position)
        if identity in seen:
            raise ValueError('Duplicate timing point.')
        seen.add(identity)
        previous = ms
        clean.append(dict(barIndex=index, barOccurence=occurrence, barPosition=position, millisecondOffset=ms))
    result = dict(version=1, videoId=video, barCount=count, points=clean)
    source = value.get('source')
    if isinstance(source, dict) and integer(source.get('songsterrId'), 1, 9999999999):
        result['source'] = {'songsterrId': source['songsterrId']}
        if integer(source.get('revision'), 1, 9999999999):
            result['source']['revision'] = source['revision']
        for field in ('artist', 'title'):
            if isinstance(source.get(field), str):
                result['source'][field] = source[field][:200]
    return result


@contextmanager
def connect(data_dir):
    data_dir.mkdir(parents=True, exist_ok=True)
    path = data_dir / 'youtube-sync.sqlite3'
    connection = sqlite3.connect(path, timeout=10)
    try:
        path.chmod(0o600)
        connection.execute('CREATE TABLE IF NOT EXISTS youtube_sync (file TEXT PRIMARY KEY, payload TEXT NOT NULL, revision INTEGER NOT NULL, updated_at TEXT NOT NULL)')
        with connection:
            yield connection
    finally:
        connection.close()


def record(connection, key):
    row = connection.execute('SELECT payload, revision, updated_at FROM youtube_sync WHERE file=?', (key,)).fetchone()
    return dict(sync=json.loads(row[0]), revision=row[1], updatedAt=row[2]) if row else dict(sync=None, revision=0, updatedAt=None)


def get_sync(handler, query):
    try:
        key = archive_key(handler, query.get('file', [''])[0])
        with connect(handler.data_dir) as connection:
            response = record(connection, key)
        return handler.send_json(200, response)
    except FileNotFoundError as error:
        return handler.send_json(404, {'error': str(error)})
    except (ValueError, TypeError) as error:
        return handler.send_json(400, {'error': str(error)})
    except (sqlite3.Error, OSError):
        return handler.send_json(503, {'error': 'Saved video timing is temporarily unavailable. Try again.'})


def save_sync(handler):
    try:
        length = int(handler.headers.get('Content-Length', '0'))
        if not 0 < length <= MAX_BODY:
            raise ValueError('Timing request is empty or too large.')
        data = json.loads(handler.rfile.read(length))
        if not isinstance(data, dict) or not integer(data.get('revision'), 0, 2147483647):
            raise ValueError('A valid timing revision is required.')
        key = archive_key(handler, data.get('file'))
        sync = validate_sync(data.get('sync'))
        with connect(handler.data_dir) as connection:
            connection.execute('BEGIN IMMEDIATE')
            current = record(connection, key)
            if data['revision'] != current['revision']:
                # A response can be lost after commit; retrying that identical save is safe.
                status = 200 if current['sync'] == sync else 409
                response = current if status == 200 else dict(current, error='Timing changed on another device. Load the server version before editing again.')
            else:
                updated = datetime.now(timezone.utc).isoformat()
                revision = current['revision'] + 1
                connection.execute('INSERT INTO youtube_sync (file,payload,revision,updated_at) VALUES (?,?,?,?) ON CONFLICT(file) DO UPDATE SET payload=excluded.payload,revision=excluded.revision,updated_at=excluded.updated_at',
                    (key, json.dumps(sync, ensure_ascii=False, allow_nan=False), revision, updated))
                status, response = 200, dict(sync=sync, revision=revision, updatedAt=updated)
        return handler.send_json(status, response)
    except FileNotFoundError as error:
        return handler.send_json(404, {'error': str(error)})
    except (ValueError, TypeError) as error:
        return handler.send_json(400, {'error': str(error)})
    except (sqlite3.Error, OSError):
        return handler.send_json(503, {'error': 'Could not save video timing. Your browser copy is retained; try again.'})
