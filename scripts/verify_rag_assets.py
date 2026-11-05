"""Verify cached Hub objects and save portable checksums without raw data."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from rag_hd.io import load_config, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT/'configs/rag_prototype.yaml')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    config = load_config(args.config)
    hub = ROOT/'.cache/rag/hub'
    sources = [('model',config['generation']['model_id'],config['generation']['revision']),
               ('dataset','rajpurkar/squad',config['data']['squad_revision']),
               ('dataset','hotpotqa/hotpot_qa',config['data']['hotpot_revision'])]
    results = []
    for kind, repo, revision in sources:
        folder = hub / (("models--" if kind=='model' else "datasets--")+repo.replace('/','--'))/'snapshots'/revision
        if not folder.exists():
            raise FileNotFoundError(folder)
        files = []
        for path in sorted(folder.rglob('*')):
            if not path.is_file():
                continue
            blob = path.resolve()
            size = blob.stat().st_size
            sha256 = hashlib.sha256()
            git_sha1 = hashlib.sha1(f'blob {size}\0'.encode(), usedforsecurity=False) if len(blob.name)==40 else None
            with blob.open('rb') as stream:
                for block in iter(lambda:stream.read(1024*1024),b''):
                    sha256.update(block)
                    if git_sha1 is not None:
                        git_sha1.update(block)
            digest = git_sha1.hexdigest() if git_sha1 is not None else sha256.hexdigest()
            if digest != blob.name:
                raise RuntimeError(f'Hub object hash mismatch: {path.name}')
            files.append({'path':str(path.relative_to(folder)), 'size_bytes':size,
                          'sha256':sha256.hexdigest(), 'hub_object_hash_verified':True})
        results.append({'repo_type':kind,'repo_id':repo,'revision':revision,'files':files})
    write_json(args.output, {'sources':results})
    print(json.dumps({'repositories':len(results),'verified_files':sum(len(r['files']) for r in results)},indent=2))


if __name__=='__main__':
    main()
