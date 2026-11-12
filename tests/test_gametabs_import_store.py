import sys, tempfile, unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from gametabs_import_store import find_import, remember_import
class ImportMappingTests(unittest.TestCase):
    def test_reuse_and_missing_file(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            def safe_join(base,key):
                p=(base/key).resolve()
                if not p.is_relative_to(base): raise ValueError()
                return p
            handler=SimpleNamespace(data_dir=root,files_dir=root,safe_join=safe_join)
            self.assertIsNone(find_import(handler,'game/title'))
            file=root/'test.gp5'; file.write_bytes(b'test')
            remember_import(handler,'game/title',file)
            self.assertEqual(find_import(handler,'game/title'),file)
            self.assertIsNone(find_import(handler,'other/title'))
            file.unlink()
            self.assertIsNone(find_import(handler,'game/title'))
