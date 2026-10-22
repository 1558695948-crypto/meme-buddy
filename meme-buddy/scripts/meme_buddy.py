#!/usr/bin/env python3
"""Local Meme Buddy library. No network, message sending or image generation."""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import tempfile
import time

EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp', '.gif'}
ARRAYS = ('emotions', 'intents', 'tags', 'relationships', 'avoid')


def lexical_score(query, item):
    """Recall by values and explicit tag phrases; never JSON field names."""
    query = query.casefold().strip()
    values = []
    for field in ('description', 'meaning', 'text', 'emotions', 'intents', 'tags'):
        value = item.get(field, '')
        values.extend(value if isinstance(value, list) else [value])
    haystack = ' '.join(values).casefold()
    terms = set(re.findall(r'[\u3400-\u9fff]+|[a-z0-9]+', query))
    matches = {term for term in terms if term in haystack and (len(term) > 1 or term in item.get('tags', []))}
    for tag in item.get('tags', []):
        tag = tag.casefold().strip()
        if len(tag) < 2:
            continue
        for match in re.finditer(re.escape(tag), query):
            prefix = query[max(0, match.start() - 4):match.start()]
            if not any(prefix.endswith(word) for word in ('不', '没', '别', '不想', '不愿', '不要', '没有')):
                matches.add(tag)
                break
    return 2 * len(matches)


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


def compact_asset(root, key, item):
    image = asset_path(root, item)
    if not image.is_file():
        raise ValueError('asset file missing')
    return {'id': key, 'path': str(image), 'bytes': image.stat().st_size,
            'format': image.suffix.lower().lstrip('.'),
            **{field: item.get(field) for field in ('text', 'meaning', 'description', 'ready', 'intents', 'tags', 'sarcasm', 'avoid')}}


def run(args):
    root = Path(args.library).expanduser().resolve()
    index = root / 'index.json'
    data = json.loads(index.read_text(encoding='utf-8')) if index.exists() else {'version': 1, 'items': {}}
    items = data['items']
    if args.command == 'get':
        result = []
        for key in args.ids:
            try:
                result.append(compact_asset(root, key, items[key]))
            except (KeyError, ValueError, OSError) as error:
                result.append({'id': key, 'error': 'unknown image id' if isinstance(error, KeyError) else str(error)})
        return result
    if args.command == 'catalog':
        entries = []
        for key, item in sorted(items.items()):
            if not item.get('ready') and not args.include_pending:
                continue
            if args.tag and args.tag.casefold() not in [tag.casefold() for tag in item.get('tags', [])]:
                continue
            try:
                entries.append(compact_asset(root, key, item))
            except (ValueError, OSError):
                continue
        revision = hashlib.sha256(json.dumps(entries, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()
        end = args.offset + args.limit
        return {'revision': revision, 'total': len(entries), 'offset': args.offset,
                'next_offset': end if end < len(entries) else None,
                'items': entries[args.offset:end]}
    if args.command == 'onboarding-status':
        return data.get('onboarding', {'status': 'not_started'})
    if args.command == 'onboarding-complete':
        ids = list(dict.fromkeys(args.ids))
        if not 1 <= len(ids) <= 20:
            raise ValueError('starter collection must contain 1 to 20 unique images')
        for key in ids:
            item = items.get(key)
            if not item or not item.get('ready') or not asset_path(root, item).is_file():
                raise ValueError('starter image must exist and be annotated: ' + key)
        data['onboarding'] = {'status': 'complete', 'ids': ids, 'completed_at': time.time()}
        save(root, data)
        return data['onboarding']
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
        meta = json.loads(Path(args.metadata).read_text(encoding='utf-8'))
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
            score = lexical_score(args.query, item)
            for arg, field in ((args.emotion, 'emotions'), (args.intent, 'intents'), (args.relationship, 'relationships')):
                if arg:
                    match = arg.casefold() in [x.casefold() for x in item.get(field, [])]
                    if not match:
                        score = -100
                        break
                    if field != 'relationships':
                        score += 3 if match else 0
            if score <= 0:
                continue
        results.append({'id': key, **item, 'path': str(image), 'score': score})
    results.sort(key=lambda entry: (-entry['score'], entry['id']))
    return results[:args.limit]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--library', default='~/.meme-buddy')
    subs = parser.add_subparsers(dest='command', required=True)
    catalog = subs.add_parser('catalog')
    catalog.add_argument('--limit', type=int, choices=range(1, 101), default=20)
    catalog.add_argument('--offset', type=int, default=0)
    catalog.add_argument('--tag')
    catalog.add_argument('--include-pending', action='store_true')
    subs.add_parser('get').add_argument('ids', nargs='+')
    subs.add_parser('ingest').add_argument('source')
    annotate = subs.add_parser('annotate')
    annotate.add_argument('id')
    annotate.add_argument('metadata')
    for name in ('pending', 'list', 'search'):
        sub = subs.add_parser(name)
        sub.add_argument('--limit', type=int, choices=range(1, 101), default=12 if name != 'search' else 10)
        if name == 'search':
            sub.add_argument('--query', default='')
            sub.add_argument('--emotion')
            sub.add_argument('--intent')
            sub.add_argument('--relationship')
    feedback = subs.add_parser('feedback')
    feedback.add_argument('id')
    feedback.add_argument('action', choices=('like', 'dislike', 'used'))
    subs.add_parser('reset-feedback')
    subs.add_parser('onboarding-status')
    subs.add_parser('onboarding-complete').add_argument('--ids', nargs='+', required=True)
    args = parser.parse_args()
    if getattr(args, 'offset', 0) < 0:
        parser.error('offset must be nonnegative')
    try:
        print(json.dumps(run(args), ensure_ascii=False, indent=2))
    except (ValueError, KeyError, OSError) as error:
        parser.exit(1, f'Error: {error}\n')


if __name__ == '__main__':
    main()
