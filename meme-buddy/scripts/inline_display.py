#!/usr/bin/env python3
"""Opt-in loopback image delivery. Persistent immutable exports; no external network."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import URLError
from urllib.request import ProxyHandler, Request, build_opener

_CHILDREN = []  # Retain/reap intentionally detached Popen handles during tests or embedding.

def config(root, port=18764):
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = root / 'config.json'
    try:
        with path.open('x', encoding='utf-8') as out:
            json.dump({'port': port, 'token': secrets.token_hex(24)}, out)
        path.chmod(0o600)
    except FileExistsError:
        pass
    data = json.loads(path.read_text())
    if not (1024 <= data['port'] <= 65535 and re.fullmatch(r'[0-9a-f]{48}', data['token'])):
        raise ValueError('Invalid display config')
    return data


def base_url(cfg):
    return f"http://127.0.0.1:{cfg['port']}/{cfg['token']}"


def probe(cfg):
    try:
        with build_opener(ProxyHandler({})).open(base_url(cfg) + '/health', timeout=1) as res:
            return json.load(res).get('service') == 'meme-buddy-inline/1'
    except (OSError, ValueError, URLError):
        return False


def handler(root, cfg):
    assets = root / 'assets'

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # Do not log capability URLs or user paths.

        def allowed(self):
            return self.headers.get('Host') == f"127.0.0.1:{cfg['port']}"

        def do_GET(self):
            if not self.allowed():
                self.send_error(403)
                return
            prefix = '/' + cfg['token'] + '/'
            if self.path == prefix + 'health':
                body = b'{"service":"meme-buddy-inline/1"}'
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Cache-Control', 'no-store')
            else:
                match = re.fullmatch(re.escape(prefix) + r'([0-9a-f]{64}\.png)', self.path)
                if not match:
                    self.send_error(404)
                    return
                path = assets / match[1]
                if path.is_symlink() or not path.is_file():
                    self.send_error(404)
                    return
                body = path.read_bytes()
                self.send_response(200)
                self.send_header('Content-Type', 'image/png')
                self.send_header('Cache-Control', 'private, max-age=31536000, immutable')
                self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            if (not self.allowed() or self.headers.get('Origin') is not None
                    or self.path != '/' + cfg['token'] + '/stop'):
                self.send_error(403)
                return
            self.send_response(204)
            self.end_headers()
            threading.Thread(target=self.server.shutdown, daemon=True).start()

    return Handler


def serve(root, cfg):
    with ThreadingHTTPServer(('127.0.0.1', cfg['port']), handler(root, cfg)) as server:
        server.daemon_threads = True
        server.serve_forever()


def ensure(root, cfg):
    if probe(cfg):
        return
    args = [sys.executable, str(Path(__file__).resolve()), '--root', str(root), 'serve']
    options = {'start_new_session': True} if os.name != 'nt' else {
        'creationflags': subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP}
    with (root / 'service.log').open('ab') as log:
        child = subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                                 cwd=str(root), **options)
    _CHILDREN[:] = [process for process in _CHILDREN if process.poll() is None]
    _CHILDREN.append(child)
    for _ in range(40):
        if probe(cfg):
            return
        if child.poll() is not None:
            break
        time.sleep(0.1)
    raise RuntimeError('Could not start display service; port may be occupied. '
                       'Do not change an existing port/token: old messages depend on them.')


def export_image(root, cfg, source, size=144):
    # Pillow is needed only when preparing thumbnails, not when serving existing ones.
    from PIL import Image, ImageOps
    if not 64 <= size <= 256:
        raise ValueError('size must be 64..256')
    source = Path(source).expanduser().resolve(strict=True)
    if source.stat().st_size > 20 * 1024 * 1024:
        raise ValueError('Input exceeds 20 MiB')
    with Image.open(source) as image:
        if image.format not in ('PNG', 'JPEG', 'WEBP', 'GIF') or image.width * image.height > 16000000:
            raise ValueError('Unsupported image or more than 16 million pixels')
        if getattr(image, 'n_frames', 1) > 1:
            raise ValueError('Animated input is not supported by this static display adapter')
        image = ImageOps.exif_transpose(image).convert('RGBA')
        image.thumbnail((size, size), Image.Resampling.LANCZOS)
        from io import BytesIO
        out = BytesIO()
        image.save(out, format='PNG')  # Drop original metadata.
        blob = out.getvalue()
        width, height = image.size
    name = hashlib.sha256(blob).hexdigest() + '.png'
    assets = root / 'assets'
    assets.mkdir(exist_ok=True, mode=0o700)
    destination = assets / name
    if destination.is_symlink():
        raise ValueError('Export destination cannot be a symlink')
    if destination.exists() and hashlib.sha256(destination.read_bytes()).hexdigest() + '.png' != name:
        raise ValueError('Existing immutable export was modified')
    if not destination.exists():
        temp = assets / (secrets.token_hex(12) + '.tmp')
        try:
            temp.write_bytes(blob)
            temp.chmod(0o600)
            os.replace(temp, destination)
        finally:
            temp.unlink(missing_ok=True)
    url = base_url(cfg) + '/' + name
    return {'url': url, 'markdown': f'![表情]({url})', 'width': width, 'height': height,
            'bytes': len(blob), 'path': str(destination)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.home() / '.meme-buddy' / 'display')
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('ensure', 'status', 'stop', 'serve'):
        sub.add_parser(name)
    prepare = sub.add_parser('prepare')
    prepare.add_argument('image')
    prepare.add_argument('--size', type=int, default=144)
    args = parser.parse_args()
    root = args.root.expanduser().resolve()
    cfg = config(root)
    if args.command == 'serve':
        serve(root, cfg)
        return
    if args.command == 'ensure':
        ensure(root, cfg)
    elif args.command == 'prepare':
        result = export_image(root, cfg, args.image, args.size)
        ensure(root, cfg)
        print(json.dumps(result, ensure_ascii=False))
        return
    elif args.command == 'stop' and probe(cfg):
        request = Request(base_url(cfg) + '/stop', data=b'', method='POST')
        with build_opener(ProxyHandler({})).open(request, timeout=2):
            pass
        for _ in range(20):
            if not probe(cfg):
                break
            time.sleep(0.1)
    print(json.dumps({'running': probe(cfg), 'port': cfg['port'], 'root': str(root)}))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, ImportError, RuntimeError) as error:
        print(json.dumps({'error': str(error)}), file=sys.stderr)
        sys.exit(1)
