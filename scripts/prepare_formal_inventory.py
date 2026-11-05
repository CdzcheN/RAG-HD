"""Build formal source nominations without generating answers or labels."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from rag_hd.formal_inventory import prepare
from rag_hd.io import load_config

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--settings', type=Path, default=ROOT/'configs/formal_inventory.json')
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    settings = json.loads(args.settings.read_text())
    if settings['protocol_version'] != 'formal-source-inventory-v1':
        raise ValueError('Unsupported inventory settings')
    prepare(ROOT, settings, load_config(ROOT/settings['model_config']), args.output_dir)
