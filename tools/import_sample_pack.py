"""Import the shipped sample pack via the Skill CLI, preserving local preferences."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--library', default='~/.meme-buddy')
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    pack = root / 'sample-pack'
    cli = root / 'meme-buddy/scripts/meme_buddy.py'
    records = json.loads((pack / 'manifest.json').read_text())
    # Verify every asset before mutating the target library.
    for record in records:
        image = (pack / record['file']).resolve()
        if not image.is_relative_to(pack.resolve()):
            raise ValueError('unsafe sample path')
        if hashlib.sha256(image.read_bytes()).hexdigest() != record['id']:
            raise ValueError('sample checksum mismatch: ' + record['file'])
    for record in records:
        command = [sys.executable, str(cli), '--library', args.library]
        subprocess.run(command + ['ingest', str(pack / record['file'])], check=True, capture_output=True)
        metadata = {key: value for key, value in record.items() if key not in {'id', 'file'}}
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'metadata.json'
            target.write_text(json.dumps(metadata, ensure_ascii=False))
            subprocess.run(command + ['annotate', record['id'], str(target)], check=True, capture_output=True)
    print(f'Imported {len(records)} annotated memes.')


if __name__ == '__main__':
    main()
