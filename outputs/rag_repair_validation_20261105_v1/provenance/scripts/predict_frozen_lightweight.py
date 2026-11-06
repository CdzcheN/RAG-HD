"""Apply existing development models and validation thresholds without fitting or labels."""
import argparse
import json
from pathlib import Path
import sys

import joblib
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from rag_hd.io import file_sha256, fingerprint, read_jsonl, write_json, write_jsonl
from rag_hd.schema import visible_input

VARIANTS = ('minicheck_logreg', 'logreg_all', 'without_lexical',
            'without_authority', 'without_time')


def predict(run, source, output):
    records = read_jsonl(run/'records.jsonl')
    cache = read_jsonl(output/'valid_evidence_cache.jsonl')
    manifest = json.loads((output/'feature_manifest.json').read_text())
    frozen_features = json.loads((source/'feature_manifest.json').read_text())
    if (manifest['source_records_sha256'] != file_sha256(run/'records.jsonl') or
            manifest['feature_cache_sha256'] != file_sha256(output/'valid_evidence_cache.jsonl') or
            manifest['implementation'] != frozen_features['implementation']):
        raise ValueError('Require intact features from the frozen implementation')
    cached = {row['sample_id']: row for row in cache}
    if len(cached) != len(cache) or set(cached) != {r['sample_id'] for r in records}:
        raise ValueError('Incomplete, duplicate or unknown feature rows')
    for record in records:
        row = cached[record['sample_id']]
        if (row['visible_input_sha256'] != fingerprint(visible_input(record)) or
                row['answer_sha256'] != fingerprint(record['answer']) or
                row['original_risk'] != record['minicheck']['risk']):
            raise ValueError('Stale input, answer or baseline')
    official = {name: file_sha256(run/name) for name in ('records.jsonl', 'metrics.json', 'status.json')}
    frozen_files, predictions = {}, []
    for seed in (13, 42, 2026):
        directory = source/f'seed_{seed}'
        report = json.loads((directory/'metrics.json').read_text())
        frozen_files[str(directory/'metrics.json')] = file_sha256(directory/'metrics.json')
        models = {}
        for variant in VARIANTS:
            path = directory/(variant+'.joblib')
            frozen_files[str(path)] = file_sha256(path)
            bundle = joblib.load(path)  # Only trusted models produced locally in this project.
            if bundle['seed'] != seed:
                raise ValueError('Frozen model seed mismatch')
            models[variant] = bundle
        for record in records:
            row = cached[record['sample_id']]
            scores = {'self_check': record['self_check']['risk'],
                      'minicheck': row['original_risk'],
                      'valid_evidence_minicheck': row['filtered_risk']}
            for variant, bundle in models.items():
                if row['features'] is None:
                    scores[variant] = None
                    continue
                matrix = np.array([[row['features'][f] for f in bundle['feature_names']]], dtype=float)
                if not np.isfinite(matrix).all():
                    raise ValueError('Nonfinite frozen model input')
                scores[variant] = float(bundle['model'].predict_proba(matrix)[0, 1])
            thresholds = {name: report['methods'][name]['validation']['threshold'] for name in scores}
            predictions.append({'sample_id': record['sample_id'], 'seed': seed,
                                'scores': scores, 'frozen_validation_thresholds': thresholds,
                                'predicted_hallucination': {
                                    name: None if value is None else bool(value >= thresholds[name])
                                    for name, value in scores.items()}})
    if any(file_sha256(Path(path)) != digest for path, digest in frozen_files.items()):
        raise RuntimeError('Frozen model artifacts changed')
    if any(file_sha256(run/name) != digest for name, digest in official.items()):
        raise RuntimeError('Formal run artifacts changed')
    write_jsonl(output/'frozen_predictions.jsonl', predictions)
    write_json(output/'frozen_prediction_manifest.json', {
        'status': 'predictions_ready_labels_pending_user_review',
        'input_rows': len(records), 'prediction_rows': len(predictions),
        'seeds': [13, 42, 2026], 'frozen_model_count': 15,
        'fit_calls': 0, 'label_inputs_used': False, 'new_threshold_selection': False,
        'source_models': str(source), 'source_model_files_sha256': frozen_files,
        'feature_cache_sha256': file_sha256(output/'valid_evidence_cache.jsonl'),
        'prediction_sha256': file_sha256(output/'frozen_predictions.jsonl'),
        'formal_artifacts_unchanged': True, 'formal_held_out_test': False,
        'purpose': 'Construction repair development check; no new performance claim.'})
    print(f'Applied 15 frozen models to {len(records)} inputs; no fitting or label evaluation.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, required=True)
    parser.add_argument('--source-model-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    predict(args.run_dir, args.source_model_dir, args.output_dir)
