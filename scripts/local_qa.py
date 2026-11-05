"""Ask the deployed local Qwen model using explicitly provided evidence."""
import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG', ':4096:8')
os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--question', required=True)
    evidence = parser.add_mutually_exclusive_group(required=True)
    evidence.add_argument('--evidence')
    evidence.add_argument('--evidence-file', type=Path)
    parser.add_argument('--config', type=Path, default=ROOT/'configs/rag_prototype.yaml')
    args = parser.parse_args()
    text = args.evidence if args.evidence is not None else args.evidence_file.read_text(encoding='utf-8')
    if not args.question.strip() or not text.strip():
        parser.error('Question and evidence must be non-empty')
    from rag_hd.io import load_config
    from rag_hd.generation import LocalGenerator, messages
    from rag_hd.resources import GpuUsage
    config = load_config(args.config)
    usage = GpuUsage(config['generation']['memory_limit_mib'])
    with usage:
        model = LocalGenerator(config['generation'], ROOT/'.cache/rag/hub', config['seed'])
        result = model.complete(messages({'question': args.question, 'visible_evidence': text}),
                                config['generation']['max_new_tokens'])
    print(json.dumps({'model': config['generation']['model_id'], 'revision': config['generation']['revision'],
                      'answer': result['text'], 'inference': result, 'resources': usage.result},
                     ensure_ascii=False, indent=2))
    if not usage.result['within_limit']:
        raise SystemExit('Resource limit was exceeded or measurement was unavailable')


if __name__ == '__main__':
    main()
