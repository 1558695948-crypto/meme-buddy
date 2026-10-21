"""Behavior checks using isolated temporary libraries."""
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

CLI = Path(__file__).with_name('meme_buddy.py')


class LibraryTests(unittest.TestCase):
    def test_retrieval_regressions(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            asset = root / 'assets/test.png'
            asset.parent.mkdir()
            asset.write_bytes(b'test fixture; never decoded')
            item = dict(file='assets/test.png', ready=True, description='托腮猫',
                        meaning='温和地思考细节', text='', emotions=['confused'],
                        intents=['question'], tags=['思考', '上班'], relationships=['friend'],
                        likes=0, dislikes=0, uses=0, last_used=0)
            def search(*arguments):
                (root / 'index.json').write_text(json.dumps({'version': 1, 'items': {'test': item}}, ensure_ascii=False), encoding='utf-8')
                result = subprocess.run([sys.executable, str(CLI), '--library', str(root), 'search', *arguments], capture_output=True, text=True, check=True)
                return json.loads(result.stdout)
            self.assertEqual(len(search('--query', '我有点懵，想再思考一下')), 1)
            self.assertEqual(search('--query', 'text'), [])
            self.assertEqual(search('--query', 'meaning'), [])
            self.assertEqual(search('--query', '思考', '--intent', 'thanks'), [])
            self.assertEqual(search('--relationship', 'friend'), [])
            self.assertEqual(search('--query', '火箭', '--relationship', 'friend'), [])
            self.assertEqual(search('--query', '不想上班'), [])
            item['dislikes'] = 2
            self.assertEqual(search('--query', '思考'), [])
            item['dislikes'] = 0
            import time
            item['last_used'] = time.time()
            self.assertEqual(search('--query', '思考'), [])

    def test_import_annotation_search_feedback_and_reset(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            def call(*args):
                result = subprocess.run([sys.executable, str(CLI), '--library', str(root / 'library'), *args], capture_output=True, text=True, check=True)
                return json.loads(result.stdout)
            def chunk(kind, payload):
                return struct.pack('!I', len(payload)) + kind + payload + struct.pack('!I', zlib.crc32(kind + payload))
            image = root / 'test.png'
            image.write_bytes(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('!2I5B', 1, 1, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(b'\x00\xff\x00\x00')) + chunk(b'IEND', b''))
            key = call('ingest', str(image))[0]['id']
            self.assertEqual(call('ingest', str(image))[0]['status'], 'duplicate')
            self.assertEqual(len(call('pending')), 1)
            self.assertEqual(call('search', '--query', 'thanks'), [])
            meta = root / 'meta.json'
            meta.write_text(json.dumps({'description': '猫感谢', 'meaning': '真诚表达感激', 'emotions': ['grateful'], 'intents': ['thanks'], 'relationships': ['friend']}))
            call('annotate', key, str(meta))
            self.assertEqual(call('pending'), [])
            self.assertEqual(call('search', '--emotion', 'grateful')[0]['id'], key)
            self.assertEqual(call('search', '--emotion', 'grateful', '--relationship', 'client'), [])
            self.assertEqual(call('search', '--query', '火箭升空'), [])
            call('feedback', key, 'used')
            entry = call('list')[0]
            self.assertEqual(entry['uses'], 1)
            self.assertEqual(entry['likes'], 0)
            call('feedback', key, 'like')
            call('reset-feedback')
            self.assertEqual(call('list')[0]['likes'], 0)
            self.assertTrue(Path(call('list')[0]['path']).is_file())
            fake = root / 'fake.png'
            fake.write_text('not an image')
            self.assertEqual(call('ingest', str(fake))[0]['status'], 'invalid_header')

    def test_path_escape_rejected(self):
        spec = importlib.util.spec_from_file_location('meme', CLI)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with self.assertRaises(ValueError):
            module.asset_path(Path('/tmp/library'), {'file': '../../outside.png'})


if __name__ == '__main__':
    unittest.main()
