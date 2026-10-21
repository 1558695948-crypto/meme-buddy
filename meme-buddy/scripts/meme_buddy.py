#!/usr/bin/env python3
"""Local Meme Buddy library. No network, message sending or image generation."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import time

EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp', '.gif'}
ARRAYS = ('emotions', 'intents', 'tags', 'relationships', 'avoid')


def save(root, data):
    root.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=root, suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
        os.replace(name, root / 'index.json')
    finally:
        if os.path.exists(name):
            os.unlink(name)


def asset_path(root, item):
    candidate = (root / item['file']).resolve()
    if not candidate.is_relative_to((root / 'assets').resolve()):
        raise ValueError('asset path escapes library')
    return candidate


def valid_image(blob, suffix):
    return ((suffix == '.png' and blob.startswith(b'\x89PNG\r\n\x1a\n')) or
            (suffix in {'.jpg', '.jpeg'} and blob.startswith(b'\xff\xd8\xff')) or
            (suffix == '.gif' and blob[:6] in {b'GIF87a', b'GIF89a'}) or
            (suffix == '.webp' and blob[:4] == b'RIFF' and blob[8:12] == b'WEBP'))


def run(args):
    root = Path(args.library).expanduser().resolve()
    index = root / 'index.json'
    data = json.loads(index.read_text()) if index.exists() else {'version': 1, 'items': {}}
    items = data['items']
    if args.command == 'ingest':
        source = Path(args.source).expanduser().resolve()
        if not source.exists():
            raise ValueError('source does not exist')
        files = sorted(source.rglob('*')) if source.is_dir() else [source]
        result = []
        for file in files:
            suffix = file.suffix.lower()
            if not file.is_file() or file.is_symlink() or suffix not in EXTENSIONS:
                continue
            if file.stat().st_size > 20 * 1024 * 1024:
                result.append({'file': file.name, 'status': 'too_large'})
                continue
            blob = file.read_bytes()
            if not valid_image(blob, suffix):
                result.append({'file': file.name, 'status': 'invalid_header'})
                continue
            key = hashlib.sha256(blob).hexdigest()
            if key in items:
                result.append({'id': key, 'status': 'duplicate'})
                continue
            target = root / 'assets' / (key + suffix)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(file, target)
            items[key] = {'file': str(target.relative_to(root)), 'ready': False,
                          'likes': 0, 'dislikes': 0, 'uses': 0, 'last_used': 0}
            result.append({'id': key, 'status': 'pending'})
        save(root, data)
        return result
    if args.command == 'annotate':
        if args.id not in items:
            raise ValueError('unknown image id')
        meta = json.loads(Path(args.metadata).read_text())
        allowed = {'description', 'meaning', 'text', 'sarcasm', 'source', 'rights', *ARRAYS}
        if set(meta) - allowed:
            raise ValueError('unknown metadata fields')
        for field in ('description', 'meaning'):
            if not isinstance(meta.get(field), str) or not meta[field].strip():
                raise ValueError(field + ' must be nonempty text')
        for field in ARRAYS:
            if not isinstance(meta.get(field, []), list) or any(not isinstance(x, str) for x in meta.get(field, [])):
                raise ValueError(field + ' must be an array of strings')
        for field in ('text', 'source', 'rights'):
            if field in meta and not isinstance(meta[field], str):
                raise ValueError(field + ' must be text')
        if meta.get('sarcasm', 'none') not in {'none', 'possible', 'strong'}:
            raise ValueError('invalid sarcasm value')
        items[args.id].update(meta, ready=True)
        save(root, data)
        return {'id': args.id, 'status': 'annotated'}
    if args.command in {'feedback', 'reset-feedback'}:
        affected = items.values() if args.command == 'reset-feedback' else [items[args.id]]
        for item in affected:
            if args.command == 'reset-feedback':
                item.update(likes=0, dislikes=0, uses=0, last_used=0)
            elif args.action == 'used':
                item['uses'] += 1
                item['last_used'] = time.time()
            else:
                item['likes' if args.action == 'like' else 'dislikes'] += 1
        save(root, data)
        return {'status': 'updated'}
    results = []
    for key, item in items.items():
        if args.command == 'pending' and item['ready']:
            continue
        image = asset_path(root, item)
        if not image.is_file():
            continue
        score = 0
        if args.command == 'search':
            if not item['ready']:
                continue
            terms = args.query.casefold().split()
            haystack = json.dumps({k: item.get(k, '') for k in ('description', 'meaning', 'text', 'emotions', 'intents', 'tags')}, ensure_ascii=False).casefold()
            score = sum(2 for term in terms if term in haystack)
            for arg, field in ((args.emotion, 'emotions'), (args.intent, 'intents'), (args.relationship, 'relationships')):
                if arg:
                    match = arg.casefold() in [x.casefold() for x in item.get(field, [])]
                    if field == 'relationships' and item.get(field) and not match:
                        score = -100
                        break
                    score += 3 if match else 0
            if score <= 0:
                continue
            score += max(-2, min(2, item['likes'] - item['dislikes']))
            if time.time() - item['last_used'] < 3600:
                score -= 2
        results.append({'id': key, **item, 'path': str(image), 'score': score})
    results.sort(key=lambda entry: (-entry['score'], entry['uses'], entry['id']))
    return results[:args.limit]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--library', default='~/.meme-buddy')
    subs = parser.add_subparsers(dest='command', required=True)
    subs.add_parser('ingest').add_argument('source')
    annotate = subs.add_parser('annotate')
    annotate.add_argument('id')
    annotate.add_argument('metadata')
    for name in ('pending', 'list', 'search'):
        sub = subs.add_parser(name)
        sub.add_argument('--limit', type=int, choices=range(1, 101), default=12 if name != 'search' else 3)
        if name == 'search':
            sub.add_argument('--query', default='')
            sub.add_argument('--emotion')
            sub.add_argument('--intent')
            sub.add_argument('--relationship')
    feedback = subs.add_parser('feedback')
    feedback.add_argument('id')
    feedback.add_argument('action', choices=('like', 'dislike', 'used'))
    subs.add_parser('reset-feedback')
    args = parser.parse_args()
    try:
        print(json.dumps(run(args), ensure_ascii=False, indent=2))
    except (ValueError, KeyError, OSError) as error:
        parser.exit(1, f'Error: {error}\n')


if __name__ == '__main__':
    main()
