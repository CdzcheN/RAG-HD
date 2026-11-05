"""Frozen comparisons must share a cohort and retain old validation thresholds."""
import contextlib
import csv
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from rag_hd.io import file_sha256, fingerprint, write_json, write_jsonl
from rag_hd.schema import visible_input

spec = importlib.util.spec_from_file_location('frozen_repair', ROOT/'scripts/evaluate_frozen_repair.py')
evaluation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluation)


class FrozenRepairTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.run = Path(self.temp.name)/'run'
        self.out = Path(self.temp.name)/'output'
        self.source = Path(self.temp.name)/'models'
        self.run.mkdir(); self.out.mkdir()
        self.records = []
        for i, label in enumerate(('supported', 'contradicted', 'undetermined', 'undetermined', 'supported')):
            self.records.append({'sample_id': str(i), 'group_id': str(i), 'pair_id': str(i),
                                 'condition': 'normal', 'challenge_type': 'evidence_conflict',
                                 'question': 'What is the number?', 'visible_evidence': 'Number: 10.',
                                 'answer': '10', 'evidence_label': label, 'answer_correctness': 'undetermined',
                                 'is_refusal': i == 2, 'self_check': {'risk': .2}, 'minicheck': {'risk': .3}})
        original = self.run/'provenance/before_review_confirmation_20261105/records.jsonl'
        original.parent.mkdir(parents=True)
        write_jsonl(original, self.records)
        write_jsonl(self.run/'records.jsonl', self.records)
        write_jsonl(self.run/'confirmed_review.jsonl', self.records)
        write_jsonl(self.run/'confirmed_construction.jsonl', [{'pair_id': str(i), 'basic': True} for i in range(5)])
        with (self.run/'review_readable.csv').open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=['判断依据'])
            writer.writeheader(); writer.writerows([{'判断依据': 'fixture'}]*5)
        (self.run/'construction_review.csv').write_text('fixture')
        self.confirmation = {'status': 'user_confirmed', 'annotation_origin': 'assistant_draft_confirmed_by_user',
                             'confirmed_review_sha256': file_sha256(self.run/'confirmed_review.jsonl'),
                             'reviewed_table_sha256': file_sha256(self.run/'review_readable.csv'),
                             'construction_table_sha256': file_sha256(self.run/'construction_review.csv')}
        write_json(self.run/'review_confirmation.json', self.confirmation)
        cache = [{'sample_id': r['sample_id'], 'visible_input_sha256': fingerprint(visible_input(r)),
                  'answer_sha256': fingerprint(r['answer']), 'filtered_risk': .4} for r in self.records]
        write_jsonl(self.out/'valid_evidence_cache.jsonl', cache)
        features = {'source_records_sha256': file_sha256(original),
                    'feature_cache_sha256': file_sha256(self.out/'valid_evidence_cache.jsonl')}
        write_json(self.out/'feature_manifest.json', features)
        self.predictions = []
        for seed in evaluation.SEEDS:
            directory = self.source/f'seed_{seed}'; directory.mkdir(parents=True)
            thresholds = {'self_check': .8, 'minicheck': .7, 'valid_evidence_minicheck': .6}
            write_json(directory/'metrics.json', {'methods': {m: {'validation': {'threshold': t}} for m, t in thresholds.items()}})
            for r in self.records:
                scores = {'self_check': .2, 'minicheck': .3, 'valid_evidence_minicheck': .4}
                if seed == 13 and r['sample_id'] == '4':
                    scores['self_check'] = None
                    r['self_check']['risk'] = None
                self.predictions.append({'seed': seed, 'sample_id': r['sample_id'], 'scores': scores,
                                         'frozen_validation_thresholds': thresholds.copy()})
        # Missing score must be consistent with the immutable baseline on every seed.
        for r in self.predictions:
            if r['sample_id'] == '4': r['scores']['self_check'] = None
        write_jsonl(original, self.records); write_jsonl(self.run/'records.jsonl', self.records)
        features['source_records_sha256'] = file_sha256(original); write_json(self.out/'feature_manifest.json', features)
        self.manifest = {'feature_cache_sha256': features['feature_cache_sha256'],
                         'source_models': str(self.source), 'source_model_files_sha256': {}}
        self.save_predictions()

    def save_predictions(self):
        write_jsonl(self.out/'frozen_predictions.jsonl', self.predictions)
        self.manifest['prediction_sha256'] = file_sha256(self.out/'frozen_predictions.jsonl')
        write_json(self.out/'frozen_prediction_manifest.json', self.manifest)

    def execute(self):
        with patch.object(evaluation, 'grouped_auc_difference', return_value={}), contextlib.redirect_stdout(io.StringIO()):
            evaluation.evaluate(self.run, self.out)

    def test_common_cohort_and_old_thresholds(self):
        with patch('sklearn.linear_model.LogisticRegression.fit', side_effect=AssertionError('No training')):
            self.execute()
        result = json.loads((self.out/'confirmed_comparison.json').read_text())
        self.assertEqual(result['common_rows'], 2)
        self.assertEqual(result['positive_rows'], 1)
        self.assertEqual(result['refusals'], 1)
        report = json.loads((self.out/'confirmed_seed_13_metrics.json').read_text())
        self.assertEqual(report['overall']['minicheck']['threshold'], .7)
        self.assertEqual(report['overall']['minicheck']['confusion_matrix_true_rows_0_1'], [[1, 0], [1, 0]])

    def test_changed_validation_threshold_rejected(self):
        self.predictions[0]['frozen_validation_thresholds']['minicheck'] = .1
        self.save_predictions()
        with self.assertRaisesRegex(ValueError, 'threshold differs'):
            self.execute()

    def test_changed_prediction_snapshot_rejected(self):
        with (self.out/'frozen_predictions.jsonl').open('a') as stream: stream.write('\n')
        with self.assertRaisesRegex(ValueError, 'snapshot changed'):
            self.execute()

    def test_changed_user_table_rejected(self):
        (self.run/'review_readable.csv').write_text('changed')
        with self.assertRaisesRegex(ValueError, 'user-confirmed'):
            self.execute()

    def test_changed_public_evidence_rejected(self):
        self.records[0]['visible_evidence'] = 'Number: 11.'
        write_jsonl(self.run/'records.jsonl', self.records)
        with self.assertRaisesRegex(ValueError, 'inputs changed'):
            self.execute()


if __name__ == '__main__':
    unittest.main()
