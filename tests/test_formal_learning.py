import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from rag_hd.formal_learning import require_confirmation, train, validate_assignments
from rag_hd.io import file_sha256, fingerprint, write_json, write_jsonl
from rag_hd.schema import visible_input
from rag_hd.valid_evidence import select, features


class FormalLearningTests(unittest.TestCase):
    def setUp(self):
        self.rows = [{'sample_id': f'{i}:{j}', 'base_question_id': f'b{i}',
                      'pair_id': f'p{i}', 'group_id': f'g{i}'}
                     for i in range(240) for j in range(2)]
        self.splits = {str(s): {'train': [f'b{i}' for i in range(180)],
                               'validation': [f'b{i}' for i in range(180, 240)],
                               'test': [f't{i}' for i in range(60)]} for s in (13, 42, 2026)}

    def test_accepts_exact_frozen_development_without_drawing_test(self):
        result = validate_assignments(self.rows, self.splits)
        self.assertFalse(result['split_recomputed'])
        self.assertEqual(result['development_rows'], 480)

    def test_rejects_test_sources_in_development(self):
        self.splits['13']['validation'][0] = 't0'
        with self.assertRaisesRegex(ValueError, 'Overlapping'):
            validate_assignments(self.rows, self.splits)

    def test_rejects_duplicate_missing_or_unpaired_rows(self):
        variants = [self.rows[:-1], copy.deepcopy(self.rows), copy.deepcopy(self.rows)]
        variants[1][1]['sample_id'] = variants[1][0]['sample_id']
        variants[2][1]['group_id'] = 'another group'
        for rows in variants:
            with self.subTest(rows=len(rows)), self.assertRaises(ValueError):
                validate_assignments(rows, self.splits)

    def test_rejects_shared_source_groups(self):
        self.rows[2]['group_id'] = self.rows[3]['group_id'] = 'g0'
        with self.assertRaisesRegex(ValueError, 'shared'):
            validate_assignments(self.rows, self.splits)

    def test_rejects_seed_specific_test(self):
        self.splits['42']['test'][0] = 'different_test'
        with self.assertRaisesRegex(ValueError, 'shared'):
            validate_assignments(self.rows, self.splits)

    def test_drafts_do_not_authorize_training(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, 'confirmation'):
                require_confirmation(Path(directory), self.rows)

    def test_training_scaling_thresholds_and_freeze_stay_in_fixed_partitions(self):
        import joblib
        from rag_hd.learning import choose_threshold
        from rag_hd.formal_gate import validate_test_freeze
        with tempfile.TemporaryDirectory() as directory:
            master = Path(directory)
            run = master/'partitions/development'
            test = master/'partitions/test'
            output = master/'features'
            for path in (run, test, output): path.mkdir(parents=True)
            write_json(master/'frozen_splits.json', self.splits)
            write_json(test/'status.json', {'stage': 'held_out_pending_model_freeze'})
            write_json(run/'data_manifest.json', {'execution_partition': 'development'})
            write_json(run/'config.json', {'minicheck': {}})
            implementation = {name: file_sha256(ROOT/'src/rag_hd'/name)
                              for name in ('valid_evidence.py', 'minicheck_adapter.py')}
            reviews, cached = [], []
            for row in self.rows:
                index = int(row['base_question_id'][1:])
                positive = index % 4 == 0
                risk = (0.8 if positive else 0.2) + (0.1 if index >= 180 else 0)
                row.update(question='What number?', visible_evidence='The number is 1.', answer='1',
                           is_refusal=False, evidence_label='unsupported' if positive else 'supported',
                           minicheck={'risk': risk}, self_check={'risk': risk})
                public = visible_input(row)
                selection = select(public)
                cached.append({'sample_id': row['sample_id'],
                               'cache_key': fingerprint([public, row['answer'], risk, {}, implementation]),
                               'answer_sha256': fingerprint(row['answer']),
                               'visible_input_sha256': fingerprint(public), 'original_risk': risk,
                               'filtered_risk': risk, 'selection': selection,
                               'features': features(public, row['answer'], risk, risk, selection)})
                reviews.append({'sample_id': row['sample_id'], 'answer_sha256': fingerprint('1'),
                                'visible_input_sha256': fingerprint(public),
                                'evidence_label': row['evidence_label']})
            write_jsonl(run/'records.jsonl', self.rows)
            write_jsonl(run/'confirmed_review.jsonl', reviews)
            for name in ('review_readable.csv', 'construction_review.csv'):
                (run/name).write_text('Synthetic confirmed test fixture\n')
            write_json(run/'review_confirmation.json', {
                'status': 'user_confirmed', 'annotation_origin': 'synthetic_test_fixture',
                'confirmed_review_sha256': file_sha256(run/'confirmed_review.jsonl'),
                'reviewed_table_sha256': file_sha256(run/'review_readable.csv'),
                'construction_table_sha256': file_sha256(run/'construction_review.csv')})
            write_jsonl(output/'valid_evidence_cache.jsonl', cached)
            write_json(output/'feature_manifest.json', {
                'implementation': implementation, 'label_inputs_used': False,
                'feature_cache_sha256': file_sha256(output/'valid_evidence_cache.jsonl'),
                'source_records_sha256': 'old pre-confirmation hash is intentionally different'})
            final_rows, final_cache = [], []
            for i in range(120):
                row = dict(self.rows[i], sample_id=f'final{i}', base_question_id=f't{i//2}')
                final_rows.append(row)
                value = dict(cached[i], sample_id=row['sample_id'])
                final_cache.append(value)
            write_jsonl(test/'prepared.jsonl', final_rows)
            write_jsonl(test/'records.jsonl', final_rows)
            write_json(test/'data_manifest.json', {'execution_partition': 'test'})
            write_json(test/'config.json', {'minicheck': {}})
            final_output = output/'final_test'
            final_output.mkdir()
            write_jsonl(final_output/'valid_evidence_cache.jsonl', final_cache)
            write_json(final_output/'feature_manifest.json', {
                'implementation': implementation, 'label_inputs_used': False,
                'feature_cache_sha256': file_sha256(final_output/'valid_evidence_cache.jsonl')})
            with patch('rag_hd.learning.choose_threshold', wraps=choose_threshold) as threshold:
                result = train(run, output, ROOT)
                self.assertEqual(threshold.call_count, 24)
                self.assertTrue(all(len(c.args[0]) == 120 for c in threshold.call_args_list))
            self.assertFalse(result['final_test_evaluated'])
            self.assertEqual(result['common_development_rows'], 480)
            model = joblib.load(output/'formal_training/seed_13/minicheck_logreg.joblib')
            self.assertAlmostEqual(model['model'][0].mean_[0], 0.35)
            self.assertTrue(validate_test_freeze(test)['artifacts_sha256'])
            self.assertFalse((test/'generation.jsonl').exists())
            self.assertEqual(json.loads((test/'status.json').read_text())['stage'],
                             'held_out_pending_model_freeze')
            sys.path.insert(0, str(ROOT/'scripts'))
            from predict_formal_frozen import predict
            with patch('sklearn.linear_model.LogisticRegression.fit', side_effect=AssertionError('No test fitting')):
                predict(test, output/'formal_training', final_output)
                first = (final_output/'frozen_predictions.jsonl').read_bytes()
                for row in final_rows:
                    row.update(evidence_label='undetermined', audit={'reference_answers': ['private changed']})
                write_jsonl(test/'records.jsonl', final_rows)
                predict(test, output/'formal_training', final_output)
                self.assertEqual(first, (final_output/'frozen_predictions.jsonl').read_bytes())
            manifest = json.loads((final_output/'frozen_prediction_manifest.json').read_text())
            self.assertEqual(manifest['prediction_rows'], 360)
            self.assertFalse(manifest['label_inputs_used'])
            (run/'review_readable.csv').write_text('changed review')
            with self.assertRaisesRegex(ValueError, 'review changed'):
                require_confirmation(run, self.rows)


if __name__ == '__main__':
    unittest.main()
