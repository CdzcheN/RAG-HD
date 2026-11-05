"""Validate frozen development assignments or train after actual-answer confirmation."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from rag_hd.formal_learning import train, validate_assignments
from rag_hd.io import read_jsonl


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--check-only', action='store_true')
    action.add_argument('--train', action='store_true')
    args = parser.parse_args()
    if args.check_only:
        splits = json.loads((args.run_dir.parent.parent/'frozen_splits.json').read_text())
        result = validate_assignments(read_jsonl(args.run_dir/'records.jsonl'), splits)
        result.update(models_fitted=0, thresholds_selected=0,
                      user_confirmation_present=(args.run_dir/'review_confirmation.json').exists())
    else:
        result = train(args.run_dir, args.output_dir, ROOT)
    print(json.dumps(result, ensure_ascii=False, indent=2))
