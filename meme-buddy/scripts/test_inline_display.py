import hashlib
import http.client
import json
from pathlib import Path
import socket
import tempfile
import threading
import unittest
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
