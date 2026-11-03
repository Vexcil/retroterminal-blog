import sys
import unittest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from tab_catalog import identity, matches
from songsterr_bridge import songsterr_response
from tabs_host_server import TabsHostHandler


class CatalogTests(unittest.TestCase):
    def test_index_artist_labels_are_shared_and_refresh_after_index_changes(self):
        with tempfile.TemporaryDirectory() as folder:
            first = object.__new__(TabsHostHandler)
            second = object.__new__(TabsHostHandler)
            first.data_dir = second.data_dir = Path(folder)
            path = Path(folder) / 'tabs.json'
            path.write_text(json.dumps([{'title': 'Death - Symbolic'}]))
            loaded = first.get_index_entries()
            self.assertIs(second.get_index_entries(), loaded)
            self.assertEqual(loaded[0]['artist'], 'Death')
            path.write_text(json.dumps([{'title': 'Metallica - Creeping Death'}]))
            self.assertEqual(second.get_index_entries()[0]['artist'], 'Metallica')

    def test_artist_designations_and_song_titles_are_distinct(self):
        death = {'title': 'Death - Symbolic'}
        metallica = {'title': 'Metallica - Creeping Death'}
        self.assertEqual(identity(death), {'artist': 'Death', 'song_title': 'Symbolic'})
        self.assertTrue(matches(death, 'Death', 'artist', True))
        self.assertFalse(matches(metallica, 'Death', 'artist', True))
        self.assertTrue(matches(metallica, 'Death'))
        self.assertFalse(matches({'title': 'Death Cab For Cutie - A song'}, 'Death', 'artist', True))
        self.assertTrue(matches({'title': 'Castlevania-Wood Carving Partita'}, 'Castlevania', 'artist', True))
        self.assertTrue(matches({'title': 'A song', 'folder_path': 'Archive/Björk'}, 'Bjork', 'artist', True))
        self.assertTrue(matches({'title': 'A song', 'artist': 'AC/DC'}, 'AC DC', 'artist', True))
        self.assertEqual(identity({'title': '(02) - Infinite Dreams'})['artist'], '')

    def test_http_library_filter_is_applied_before_pagination(self):
        handler = object.__new__(TabsHostHandler)
        entries = [{'title': 'Metallica - Creeping Death'}, {'title': 'Death - Symbolic'}, {'title': 'Death - Crystal Mountain'}]
        handler.get_enriched_entries = lambda: entries
        handler.get_folder_options = lambda: []
        handler.send_json_body = lambda status, payload, **kwargs: payload
        result = handler.serve_tabs_page('search=Death&search_field=artist&artist_exact=1&page_size=1&page=2')
        self.assertEqual(result['total'], 2)
        self.assertEqual(result['page'], 2)
        self.assertEqual(result['items'][0]['title'], 'Death - Symbolic')

    @patch('songsterr_bridge.fetch')
    def test_songsterr_resolves_exact_artist_and_uses_artist_endpoint(self, fetch):
        fetch.side_effect = [
            {'records': [{'artist': 'Metallica', 'artistId': 20}, {'artist': 'Death', 'artistId': 1851}]},
            {'records': [{'songId': 6352, 'artistId': 1851, 'artist': 'Death', 'title': 'Symbolic'}]}]
        result = songsterr_response('/api/songsterr/search', {'q': ['Death'], 'artist': ['Death'], 'page': ['2']})
        self.assertIn('/api/artist/1851/search?', fetch.call_args.args[0])
        self.assertIn('from=20', fetch.call_args.args[0])
        self.assertEqual(result['items'][0]['artist_id'], 1851)
        self.assertFalse(result['has_more'])

    @patch('songsterr_bridge.fetch')
    def test_known_artist_id_skips_resolution_and_invalid_ids_never_fetch(self, fetch):
        fetch.return_value = {'records': []}
        songsterr_response('/api/songsterr/search', {'q': ['Death'], 'artist': ['Death'], 'artist_id': ['1851']})
        self.assertEqual(fetch.call_count, 1)
        with self.assertRaises(ValueError):
            songsterr_response('/api/songsterr/search', {'q': ['Death'], 'artist_id': ['../25']})
        self.assertEqual(fetch.call_count, 1)


if __name__ == '__main__':
    unittest.main()
