import hashlib
import http.client
import json
from pathlib import Path
import socket
import tempfile
import threading
import unittest
from unittest.mock import patch
from http.server import ThreadingHTTPServer
from PIL import Image
import inline_display as display


class DisplayTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / 'display'
        self.cfg = display.config(self.root)
        self.source = Path(self.temp.name) / 'original.jpg'
        Image.new('RGB', (384, 384), 'orange').save(self.source)
        self.server = None

    def tearDown(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        self.temp.cleanup()

    def start(self):
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), display.handler(self.root, self.cfg))
        self.cfg['port'] = self.server.server_port
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def request(self, path, headers=None, method='GET'):
        conn = http.client.HTTPConnection('127.0.0.1', self.cfg['port'], timeout=2)
        conn.request(method, path, headers=headers or {})
        result = conn.getresponse()
        answer = (result.status, dict(result.getheaders()), result.read())
        conn.close()
        return answer

    def test_thumbnail_immutable_and_original_preserved(self):
        original = self.source.read_bytes()
        first = display.export_image(self.root, self.cfg, self.source)
        second = display.export_image(self.root, self.cfg, self.source)
        self.assertEqual(first, second)
        self.assertEqual((first['width'], first['height']), (144, 144))
        self.assertEqual(self.source.read_bytes(), original)
        with Image.open(first['path']) as image:
            self.assertEqual(image.size, (144, 144))

    def test_config_survives_reuse(self):
        self.assertEqual(self.cfg, display.config(self.root, port=19999))

    def test_read_only_config_does_not_create_store(self):
        root = self.root / 'never-created'
        with patch.object(Path, 'mkdir', side_effect=AssertionError('read must not write')):
            self.assertIsNone(display.config(root, create=False))
        self.assertFalse(root.exists())

    def test_invalid_config_rejected_without_rotating(self):
        path = self.root / 'config.json'
        for invalid in ({}, {'port': '18764', 'token': 'a' * 48}, [], {'port': True}):
            path.write_text(json.dumps(invalid))
            original = path.read_bytes()
            with self.assertRaises(ValueError):
                display.config(self.root)
            self.assertEqual(path.read_bytes(), original)

    def test_corrupt_cache_is_nonfatal_and_readonly(self):
        library = self.root / 'empty-library'
        library.mkdir()
        (library / 'index.json').write_text('{"items": {}}')
        path = self.root / 'catalog.json'
        path.write_text('{broken')
        result = display.display_catalog(self.root, self.cfg, library)
        self.assertEqual(result['items'], [])
        self.assertTrue(result['warnings'])
        self.assertEqual(path.read_text(), '{broken')

    def test_nested_directory_creation_and_library_save_with_shim(self):
        from meme_buddy import save
        nested = self.root / 'new' / 'nested'
        original = Path.mkdir
        def shim(path, *args, **kwargs):
            self.assertNotIn('parents', kwargs)
            if path.is_dir():
                raise FileExistsError('simulated shim')
            return original(path, *args, **kwargs)
        with patch.object(Path, 'mkdir', shim):
            display.ensure_directory(nested)
            save(nested, {'items': {}})
            save(nested, {'items': {}, 'version': 1})
        self.assertEqual(json.loads((nested / 'index.json').read_text())['version'], 1)

    def test_thumbnail_drops_exif(self):
        exif = Image.Exif()
        exif[0x010E] = 'private location note'
        Image.new('RGB', (200, 200), 'blue').save(self.source, exif=exif)
        item = display.export_image(self.root, self.cfg, self.source)
        with Image.open(item['path']) as image:
            self.assertFalse(image.getexif())
            self.assertNotIn('exif', image.info)

    def test_warmup_isolates_failure_and_cached_joins_live_meaning(self):
        library = Path(self.temp.name) / 'library'
        assets = library / 'assets'
        assets.mkdir(parents=True)
        items = {}
        for color in ('red', 'blue'):
            source = assets / (color + '.png')
            Image.new('RGB', (100, 100), color).save(source)
            key = hashlib.sha256(source.read_bytes()).hexdigest()
            items[key] = {'file': 'assets/' + source.name, 'ready': True, 'meaning': color}
        gif = assets / 'animated.gif'
        Image.new('RGB', (16, 16), 'red').save(gif, save_all=True,
            append_images=[Image.new('RGB', (16, 16), 'blue')], duration=100, loop=0)
        gif_id = hashlib.sha256(gif.read_bytes()).hexdigest()
        items[gif_id] = {'file': 'assets/animated.gif', 'ready': True}
        index = library / 'index.json'
        index.write_text(json.dumps({'items': items}))
        original = index.read_bytes()
        result = display.display_catalog(self.root, self.cfg, library, warmup=True)
        good = [x for x in result['items'] if 'inline' in x]
        self.assertEqual(len(good), 2)
        self.assertEqual(len({x['inline']['url'] for x in good}), 2)
        self.assertTrue(any(x.get('id') == gif_id and 'error' in x for x in result['items']))
        self.assertEqual(index.read_bytes(), original)
        items[good[0]['id']]['meaning'] = 'updated meaning'
        index.write_text(json.dumps({'items': items}))
        with patch.object(Path, 'mkdir', side_effect=AssertionError('cached must be read only')):
            cached = display.display_catalog(self.root, self.cfg, library)
        updated = next(x for x in cached['items'] if x['id'] == good[0]['id'])
        self.assertEqual(updated['meaning'], 'updated meaning')
        self.assertEqual(updated['inline'], good[0]['inline'])
        self.assertNotIn(self.cfg['token'], (self.root / 'catalog.json').read_text())
        page = display.display_catalog(self.root, self.cfg, library, limit=1)
        self.assertEqual(len(page['items']), 1)
        self.assertEqual(page['next_offset'], 1)
        export = self.root / 'assets' / good[0]['inline']['url'].rsplit('/', 1)[1]
        export.unlink()
        missing = display.display_catalog(self.root, self.cfg, library, ids=[good[0]['id']])
        self.assertIn('error', missing['items'][0])

    def test_existing_directories_skip_broken_mkdir_shim(self):
        first = display.export_image(self.root, self.cfg, self.source)
        with patch.object(Path, 'mkdir', side_effect=FileExistsError('simulated shim')):
            self.assertEqual(display.config(self.root), self.cfg)
            self.assertEqual(display.export_image(self.root, self.cfg, self.source), first)

    def test_directory_errors_not_hidden(self):
        blocked = self.root / 'blocked'
        blocked.write_text('not a directory')
        with self.assertRaises(FileExistsError):
            display.ensure_directory(blocked)
        with patch.object(Path, 'mkdir', side_effect=PermissionError('denied')):
            with self.assertRaises(PermissionError):
                display.ensure_directory(self.root / 'missing')
        link = self.root / 'link'
        link.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(ValueError):
            display.ensure_directory(link)

    def test_concurrent_directory_creation_accepted(self):
        target = self.root / 'concurrent'
        original = Path.mkdir
        def raced(path, *args, **kwargs):
            original(path, *args, **kwargs)
            raise FileExistsError('created concurrently')
        with patch.object(Path, 'mkdir', raced):
            display.ensure_directory(target)
        self.assertTrue(target.is_dir())

    def test_http_exact_asset_only(self):
        self.start()
        item = display.export_image(self.root, self.cfg, self.source)
        route = '/' + self.cfg['token'] + '/' + Path(item['path']).name
        status, headers, body = self.request(route)
        self.assertEqual(status, 200)
        self.assertEqual(body, Path(item['path']).read_bytes())
        self.assertIn('immutable', headers['Cache-Control'])
        for bad in ('/', '/config.json', '/' + self.cfg['token'] + '/',
                    '/' + self.cfg['token'] + '/../config.json', '/wrong/health'):
            self.assertEqual(self.request(bad)[0], 404)
        self.assertEqual(self.request(route, {'Host': 'attacker.invalid'})[0], 403)
        self.assertEqual(self.request('/' + self.cfg['token'] + '/stop',
                                      {'Origin': 'http://attacker.invalid'}, 'POST')[0], 403)

    def test_symlink_not_served(self):
        self.start()
        assets = self.root / 'assets'
        assets.mkdir()
        (assets / ('a' * 64 + '.png')).symlink_to(self.source)
        self.assertEqual(self.request('/' + self.cfg['token'] + '/' + 'a' * 64 + '.png')[0], 404)

    def test_animation_rejected_not_silently_flattened(self):
        gif = Path(self.temp.name) / 'animated.gif'
        Image.new('RGB', (16, 16), 'red').save(gif, save_all=True,
            append_images=[Image.new('RGB', (16, 16), 'blue')], duration=100, loop=0)
        with self.assertRaises(ValueError):
            display.export_image(self.root, self.cfg, gif)

    def test_daemon_restart_preserves_url_and_bytes(self):
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            self.cfg['port'] = sock.getsockname()[1]
        (self.root / 'config.json').write_text(json.dumps(self.cfg))
        item = display.export_image(self.root, self.cfg, self.source)
        route = '/' + self.cfg['token'] + '/' + Path(item['path']).name
        try:
            display.ensure(self.root, self.cfg)
            first = self.request(route)[2]
            self.request('/' + self.cfg['token'] + '/stop', method='POST')
            import time
            for _ in range(30):
                if not display.probe(self.cfg):
                    break
                time.sleep(0.1)
            display.ensure(self.root, self.cfg)
            self.assertEqual(self.request(route)[2], first)
            self.assertEqual(display.export_image(self.root, self.cfg, self.source)['url'], item['url'])
        finally:
            if display.probe(self.cfg):
                self.request('/' + self.cfg['token'] + '/stop', method='POST')
                time.sleep(0.6)
            for child in display._CHILDREN:
                child.wait(timeout=3)


if __name__ == '__main__':
    unittest.main()
