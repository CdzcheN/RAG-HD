import copy
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
spec = importlib.util.spec_from_file_location('formal_evaluation', ROOT/'scripts/evaluate_formal_test.py')
evaluation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluation)


class FormalEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.records = [{'sample_id': str(i), 'is_refusal': i == 2,
                         'evidence_label': ['supported', 'contradicted', 'undetermined', 'supported'][i],
                         'self_check': {'risk': .2}, 'minicheck': {'risk': .3}} for i in range(4)]
        self.cache = {str(i): {'filtered_risk': .4} for i in range(4)}
        self.thresholds = {seed: {m: .7 for m in evaluation.METHODS} for seed in evaluation.SEEDS}
        self.predictions = []
        for seed in evaluation.SEEDS:
            for row in self.records:
                scores = {m: .4 for m in evaluation.METHODS}
                scores.update(self_check=.2, minicheck=.3)
                if seed == 13 and row['sample_id'] == '3': scores['logreg_all'] = None
                self.predictions.append({'seed': seed, 'sample_id': row['sample_id'], 'scores': scores,
                                         'frozen_validation_thresholds': self.thresholds[seed].copy(),
                                         'predicted_hallucination': {m: None if v is None else False for m, v in scores.items()}})

    def test_every_method_and_seed_uses_one_common_cohort(self):
        _, common = evaluation.validate_predictions(self.records, self.predictions, self.thresholds, self.cache)
        self.assertEqual([r['sample_id'] for r in common], ['0', '1'])

    def test_changed_threshold_baseline_or_decision_is_rejected(self):
        for field in ('threshold', 'baseline', 'decision'):
            changed = copy.deepcopy(self.predictions)
            if field == 'threshold': changed[0]['frozen_validation_thresholds']['minicheck'] = .5
            elif field == 'baseline': changed[0]['scores']['minicheck'] = .4
            else: changed[0]['predicted_hallucination']['minicheck'] = True
            with self.subTest(field=field), self.assertRaises(ValueError):
                evaluation.validate_predictions(self.records, changed, self.thresholds, self.cache)

    def test_missing_duplicate_unknown_predictions_are_rejected(self):
        for changed in (self.predictions[:-1], [*self.predictions, self.predictions[0]],
                        [dict(self.predictions[0], sample_id='unknown'), *self.predictions[1:]]):
            with self.assertRaises(ValueError):
                evaluation.validate_predictions(self.records, changed, self.thresholds, self.cache)

    def test_empty_or_single_class_subgroups_do_not_invent_auc(self):
        self.assertIsNone(evaluation.metric_report([], [], .5)['roc_auc'])
        result = evaluation.metric_report([0, 0], [.2, .4], .5)
        self.assertIsNone(result['roc_auc'])
        self.assertIsNone(result['average_precision'])
        self.assertEqual(result['confusion_matrix_true_rows_0_1'], [[2, 0], [0, 0]])


if __name__ == '__main__': unittest.main()
