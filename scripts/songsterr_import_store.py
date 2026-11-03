"""Remember source IDs so retries and already-linked arrangements reuse one file."""
import json
from youtube_sync_store import connect


def existing_file(handler, key):
    try:
        path = handler.safe_join(handler.files_dir, key)
        return path if path.is_file() else None
    except (ValueError, PermissionError, OSError):
        return None


def prepare(db):
    db.execute('CREATE TABLE IF NOT EXISTS songsterr_imports (song_id INTEGER PRIMARY KEY, file TEXT NOT NULL)')


def find_import(handler, song_id):
    with connect(handler.data_dir) as db:
        prepare(db)
        row = db.execute('SELECT file FROM songsterr_imports WHERE song_id=?', (song_id,)).fetchone()
        if row:
            file = existing_file(handler, row[0])
            if file:
                return file
            db.execute('DELETE FROM songsterr_imports WHERE song_id=?', (song_id,))
        # Adopt links saved before imports had a source-ID registry.
        for key, payload in db.execute('SELECT file,payload FROM youtube_sync ORDER BY file'):
            if json.loads(payload).get('source', {}).get('songsterrId') != song_id:
                continue
            file = existing_file(handler, key)
            if file:
                db.execute('INSERT OR REPLACE INTO songsterr_imports VALUES (?,?)', (song_id, key))
                return file
    return None


def remember_import(handler, song_id, file):
    key = file.relative_to(handler.files_dir).as_posix()
    with connect(handler.data_dir) as db:
        prepare(db)
        db.execute('INSERT OR REPLACE INTO songsterr_imports VALUES (?,?)', (song_id, key))
