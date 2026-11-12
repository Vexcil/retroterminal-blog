"""Account-scoped My Tabs memberships; archive files remain shared and untouched."""
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import os
import re

def _principal(value):
    if not isinstance(value,str) or not value or len(value)>256 or any(ord(c)<32 or ord(c)==127 for c in value):
        raise ValueError('A verified account principal is required.')
    return value

def _key(value):
    # Caller must additionally validate this canonical relative key exists in
    # the shared archive. Never accept URLs or decode paths in the store.
    if not isinstance(value,str) or not value or len(value)>4096 or '\\' in value or re.match(r'^[A-Za-z][A-Za-z0-9+.-]*://', value) or any(ord(c)<32 or ord(c)==127 for c in value) or any(p in ('','.','..') for p in value.split('/')):
        raise ValueError('A canonical archive file key is required.')
    return value

@contextmanager
def _connect(data_dir):
    root=Path(data_dir)
    root.mkdir(parents=True,exist_ok=True)
    path=root/'my-tabs.sqlite3'
    try:
        fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    except FileExistsError:
        pass
    else:
        os.close(fd)
    connection=sqlite3.connect(path,timeout=10)
    try:
        connection.execute('CREATE TABLE IF NOT EXISTS memberships (principal TEXT NOT NULL, file TEXT NOT NULL, favorite INTEGER NOT NULL DEFAULT 0 CHECK(favorite IN (0,1)), added_at TEXT NOT NULL, PRIMARY KEY(principal,file))')
        with connection:
            yield connection
    finally:
        connection.close()

def list_members(data_dir,principal):
    principal=_principal(principal)
    with _connect(data_dir) as db:
        return {row[0]: {'favorite':bool(row[1]),'added_at':row[2]} for row in db.execute('SELECT file,favorite,added_at FROM memberships WHERE principal=? ORDER BY added_at,file',(principal,))}

def add_member(data_dir,principal,file):
    principal,file=_principal(principal),_key(file)
    with _connect(data_dir) as db:
        db.execute('INSERT OR IGNORE INTO memberships(principal,file,favorite,added_at) VALUES (?,?,0,?)',(principal,file,datetime.now(timezone.utc).isoformat()))
        row=db.execute('SELECT favorite,added_at FROM memberships WHERE principal=? AND file=?',(principal,file)).fetchone()
        return {'favorite':bool(row[0]),'added_at':row[1]}

def remove_member(data_dir,principal,file):
    principal,file=_principal(principal),_key(file)
    with _connect(data_dir) as db:
        cursor=db.execute('DELETE FROM memberships WHERE principal=? AND file=?',(principal,file))
        return cursor.rowcount>0

def set_favorite(data_dir,principal,file,favorite):
    principal,file=_principal(principal),_key(file)
    if type(favorite) is not bool:
        raise ValueError('Favorite must be true or false.')
    with _connect(data_dir) as db:
        cursor=db.execute('UPDATE memberships SET favorite=? WHERE principal=? AND file=?',(int(favorite),principal,file))
        if not cursor.rowcount:
            raise KeyError('Add this tab to My Tabs before favoriting it.')
        row=db.execute('SELECT favorite,added_at FROM memberships WHERE principal=? AND file=?',(principal,file)).fetchone()
        return {'favorite':bool(row[0]),'added_at':row[1]}
