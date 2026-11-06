"""Apply formal frozen models and thresholds to final answers without fitting or labels."""
import argparse
import json
from pathlib import Path
import sys

import joblib
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from rag_hd.formal_gate import validate_test_freeze
from rag_hd.formal_learning import SEEDS, VARIANTS, validated_features
from rag_hd.io import file_sha256, read_jsonl, write_json, write_jsonl


def predict(run, models, output):
    run, models, output = Path(run).resolve(), Path(models).resolve(), Path(output).resolve()
    certificate = validate_test_freeze(run)
    if json.loads((run/'data_manifest.json').read_text()).get('execution_partition') != 'test':
        raise ValueError('Require the formal final-test execution package')
    records = read_jsonl(run/'records.jsonl')
    prepared = read_jsonl(run/'prepared.jsonl')
    if (len(records) != 120 or len(prepared) != 120 or
            {r['sample_id'] for r in records} != {r['sample_id'] for r in prepared}):
        raise ValueError('Require all and only the final 120 inputs')
    cache = validated_features(run, output, records, ROOT)
    frozen = certificate['artifacts_sha256']
    predictions = []
    for seed in SEEDS:
        directory = models/f'seed_{seed}'
        path = directory/'metrics.json'
        if frozen.get(str(path)) != file_sha256(path):
            raise ValueError('Thresholds are not part of the frozen certificate')
        report = json.loads(path.read_text())
        bundles = {}
        for variant in VARIANTS:
            path = directory/(variant+'.joblib')
            if frozen.get(str(path)) != file_sha256(path):
                raise ValueError('Model is not part of the frozen certificate')
            bundle = joblib.load(path)  # Locally trained and verified project artifact.
            if bundle['seed'] != int(seed) or bundle['purpose'] != 'formal_train_only':
                raise ValueError('Unexpected model identity')
            bundles[variant] = bundle
        for row in records:
            value = cache[row['sample_id']]
            scores = {'self_check': row['self_check']['risk'], 'minicheck': value['original_risk'],
                      'valid_evidence_minicheck': value['filtered_risk']}
            for variant, bundle in bundles.items():
                if value['features'] is None:
                    scores[variant] = None
                else:
                    matrix = np.array([[value['features'][f] for f in bundle['feature_names']]], dtype=float)
                    if not np.isfinite(matrix).all(): raise ValueError('Nonfinite input features')
                    scores[variant] = float(bundle['model'].predict_proba(matrix)[0, 1])
            thresholds = {name: report['methods'][name]['validation']['threshold'] for name in scores}
            predictions.append({'sample_id': row['sample_id'], 'seed': int(seed), 'scores': scores,
                                'frozen_validation_thresholds': thresholds,
                                'predicted_hallucination': {name: None if score is None else bool(score >= thresholds[name])
                                                           for name, score in scores.items()}})
    validate_test_freeze(run)
    path = output/'frozen_predictions.jsonl'
    if path.exists():
        if read_jsonl(path) != predictions: raise ValueError('Refuse to overwrite different frozen predictions')
    else:
        write_jsonl(path, predictions)
    write_json(output/'frozen_prediction_manifest.json', {
        'status': 'predictions_complete_test_labels_pending', 'input_rows': 120, 'prediction_rows': 360,
        'model_count': 15, 'fit_calls': 0, 'threshold_selection_calls': 0, 'label_inputs_used': False,
        'model_freeze_sha256': file_sha256(run/'model_freeze.json'),
        'test_records_sha256': file_sha256(run/'records.jsonl'), 'prediction_sha256': file_sha256(path)})
    print('Frozen predictions ready: 120 inputs x 3 seeds; no fitting or label evaluation.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, required=True)
    parser.add_argument('--model-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    predict(args.run_dir, args.model_dir, args.output_dir)
