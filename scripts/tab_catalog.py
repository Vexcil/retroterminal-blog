"""Artist labels from existing index fields, without changing archived tabs."""
import re
import unicodedata
from functools import lru_cache


def normalize(value):
    text = ''.join(c for c in unicodedata.normalize('NFKD', str(value or '')) if not unicodedata.combining(c))
    return ' '.join(re.sub(r"[^\w]+", ' ', text.casefold().replace('_', ' ').replace("'", '').replace('’', '')).split())


@lru_cache(maxsize=200000)
def labels(title, artist='', folder_path=''):
    title, artist = str(title), str(artist or '').strip()
    split = re.split(r'\s+[-–—]\s+', title, maxsplit=1)
    song_title = split[1] if len(split) == 2 else title
    if not artist and len(split) == 2 and normalize(split[0]) and not normalize(split[0]).isdigit():
        artist = split[0].strip()
    designations = [artist] if artist else []
    designations += str(folder_path or '').replace('\\', '/').split('/')
    return artist, song_title, tuple(normalize(x) for x in designations if normalize(x))


def identity(item):
    artist, song_title, _ = labels(item.get('title', ''), item.get('artist', ''), item.get('folder_path', ''))
    return {'artist': artist, 'song_title': item.get('song_title') or song_title}


def matches(item, query, field='all', exact=False):
    wanted = normalize(query)
    if not wanted:
        return True
    artist, _, designations = labels(item.get('title', ''), item.get('artist', ''), item.get('folder_path', ''))
    artist_match = any(wanted == value if exact else wanted in value for value in designations)
    # Compact archive filenames also contain labels such as "Castlevania-Wood…".
    # Match a requested artist prefix without inventing a split for hyphenated names.
    title = str(item.get('title', ''))
    for separator in ('-', '–', '—'):
        start = 0
        while (position := title.find(separator, start)) >= 0:
            if normalize(title[:position]) == wanted:
                artist_match = True
                break
            start = position + 1
    return artist_match if field == 'artist' else wanted in normalize(title) or artist_match
