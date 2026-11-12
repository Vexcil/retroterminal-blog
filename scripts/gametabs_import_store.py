"""Private source mapping; imported files reuse existing archive validation."""
from youtube_sync_store import connect
from songsterr_import_store import existing_file

def find_import(handler, source_id):
    with connect(handler.data_dir) as db:
        db.execute('CREATE TABLE IF NOT EXISTS gametabs_imports (source_id TEXT PRIMARY KEY, file TEXT NOT NULL)')
        row = db.execute('SELECT file FROM gametabs_imports WHERE source_id=?', (source_id,)).fetchone()
        return existing_file(handler, row[0]) if row else None

def remember_import(handler, source_id, file):
    with connect(handler.data_dir) as db:
        db.execute('CREATE TABLE IF NOT EXISTS gametabs_imports (source_id TEXT PRIMARY KEY, file TEXT NOT NULL)')
        db.execute('INSERT OR REPLACE INTO gametabs_imports VALUES (?,?)', (source_id, file.relative_to(handler.files_dir).as_posix()))
