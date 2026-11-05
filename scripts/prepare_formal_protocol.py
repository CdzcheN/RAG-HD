"""Record proposed folds and unseen wording without preparing inference inputs."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from rag_hd.formal_protocol import development_splits, verify_source_isolation, rule_assignments
from rag_hd.io import read_jsonl, write_json, write_jsonl, file_sha256

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inventory-dir', type=Path, required=True)
    args = parser.parse_args()
    output = args.inventory_dir
    if (output/'proposed_protocol_manifest.json').exists():
        raise ValueError('Preserve existing protocol proposals; choose a new inventory version')
    manifest = json.loads((output/'inventory_manifest.json').read_text())
    if manifest['quota_deficits'] or manifest['nominated_bases'] != 300:
        raise ValueError('Resolve source nomination deficits before proposing folds')
    for name, digest in manifest['artifacts_sha256'].items():
        if file_sha256(output/name) != digest:
            raise ValueError('Inventory changed after source screening')
    rows = read_jsonl(output/'nominated_questions.jsonl')
    splits = development_splits(rows)
    checks = verify_source_isolation(rows, read_jsonl(output/'noise_reservations.jsonl'), splits)
    families = json.loads((ROOT/'configs/formal_rule_families.json').read_text())
    assignments = rule_assignments(rows, families, manifest['settings']['partition_seed'])
    write_json(output/'proposed_splits.json', splits)
    write_jsonl(output/'proposed_rule_assignments.jsonl', assignments)
    write_json(output/'proposed_protocol_manifest.json', {
        'status': 'proposed_semantic_source_review_pending', 'generation_ready': False,
        'partition_checks': checks, 'fixed_test_bases': 60, 'training_seeds': [13, 42, 2026],
        'test_rule_counts': dict(Counter(r['exposure'] for r in assignments if r['planned_split'] == 'test')),
        'same_test_sources_across_seeds': True, 'noise_moves_with_its_owner_base': True,
        'inventory_manifest_sha256': file_sha256(output/'inventory_manifest.json'),
        'rule_families_sha256': file_sha256(ROOT/'configs/formal_rule_families.json'),
        'splits_sha256': file_sha256(output/'proposed_splits.json'),
        'rule_assignments_sha256': file_sha256(output/'proposed_rule_assignments.jsonl'),
        'labels_created': 0, 'generator_calls': 0})
    print('Proposed fixed 60-base holdout and three 180/60 development folds; source/noise isolation checked.')
