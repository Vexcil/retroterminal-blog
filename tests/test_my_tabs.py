import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import tabs_my_tabs as m

class MyTabsTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.root=Path(self.tmp.name)
    def tearDown(self): self.tmp.cleanup()
    def test_initial_empty_and_two_users(self):
        self.assertEqual(m.list_members(self.root,'Alice'),{})
        m.add_member(self.root,'Alice','Uploads/song.gp')
        self.assertEqual(m.list_members(self.root,'Bob'),{})
        m.add_member(self.root,'Bob','Uploads/song.gp')
        m.set_favorite(self.root,'Alice','Uploads/song.gp',True)
        self.assertTrue(m.list_members(self.root,'Alice')['Uploads/song.gp']['favorite'])
        self.assertFalse(m.list_members(self.root,'Bob')['Uploads/song.gp']['favorite'])
    def test_idempotent_add_keeps_favorite_and_timestamp(self):
        first=m.add_member(self.root,'Alice','song.gp');m.set_favorite(self.root,'Alice','song.gp',True)
        second=m.add_member(self.root,'Alice','song.gp')
        self.assertEqual(first['added_at'],second['added_at']);self.assertTrue(second['favorite'])
        self.assertEqual(len(m.list_members(self.root,'Alice')),1)
    def test_removal_preserves_other_account_and_file(self):
        f=self.root/'song.gp';f.write_bytes(b'unchanged')
        for p in ('Alice','Bob'):m.add_member(self.root,p,'song.gp')
        self.assertTrue(m.remove_member(self.root,'Alice','song.gp'))
        self.assertFalse(m.remove_member(self.root,'Alice','song.gp'))
        self.assertIn('song.gp',m.list_members(self.root,'Bob'))
        self.assertEqual(f.read_bytes(),b'unchanged')
    def test_favorite_requires_own_membership(self):
        m.add_member(self.root,'Alice','song.gp')
        with self.assertRaises(KeyError):m.set_favorite(self.root,'Bob','song.gp',True)
        with self.assertRaises(ValueError):m.set_favorite(self.root,'Alice','song.gp','true')
    def test_bad_identity_and_paths(self):
        for p in [None,'',{},'a\nb']:
            with self.assertRaises(ValueError):m.list_members(self.root,p)
        for key in ['../x','/files/x','https://host/x','a//b','a\\b']:
            with self.assertRaises(ValueError):m.add_member(self.root,'Alice',key)
    def test_literal_legacy_filename_characters(self):
        keys=['Legacy/100% complete?.gp5','Legacy/Chapter: 1 #theme.gp','Legacy/%2e%2e.gp','Legacy/a%2fb.gp','Legacy/a%252fb.gp']
        for key in keys:
            m.add_member(self.root,'Alice',key)
        self.assertEqual(set(m.list_members(self.root,'Alice')),set(keys))
        self.assertEqual(m.list_members(self.root,'Bob'),{})
    def test_existing_database_permissions_unchanged(self):
        m.list_members(self.root,'Alice')
        path=self.root/'my-tabs.sqlite3'
        path.chmod(0o640)
        m.list_members(self.root,'Alice')
        self.assertEqual(path.stat().st_mode&0o777,0o640)
    def test_persistence(self):
        m.add_member(self.root,'Alice','song.gp')
        self.assertIn('song.gp',m.list_members(self.root,'Alice'))
        self.assertEqual((self.root/'my-tabs.sqlite3').stat().st_mode&0o777,0o600)
if __name__=='__main__':unittest.main()
