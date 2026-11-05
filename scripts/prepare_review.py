"""Export score-blind assistant suggestions as a readable human review packet."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from rag_hd.review_packet import export_packet


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, required=True)
    parser.add_argument('--suggestions', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(export_packet(args.run_dir / 'review_requests.jsonl', args.suggestions,
                                 args.output_dir), ensure_ascii=False, indent=2))
