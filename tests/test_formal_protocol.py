import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from rag_hd.formal_protocol import development_splits, verify_source_isolation, rule_assignments


class FormalProtocolTests(unittest.TestCase):
    def setUp(self):
        self.rows = []
        for dataset in ('squad', 'hotpot'):
            for kind in ('retrieval_failure', 'evidence_conflict', 'outdated_answer'):
                for i in range(50):
                    sid = f'{dataset}-{kind}-{i}'
                    self.rows.append({'base_question_id': sid, 'component_id': sid, 'gold_titles': [sid],
                                      'dataset': dataset, 'proposed_challenge_type': kind,
                                      'planned_split': 'train' if i < 30 else 'validation' if i < 40 else 'test'})
        self.noise = [{'base_question_id': r['base_question_id'],
                       'evidence': [{'title': r['base_question_id']+f'-noise-{i}'} for i in range(5)]} for r in self.rows]

    def test_final_test_is_fixed_and_development_folds_change(self):
        splits = development_splits(self.rows)
        self.assertEqual(splits['13']['test'], splits['42']['test'])
        self.assertEqual(splits['13']['test'], splits['2026']['test'])
        self.assertNotEqual(splits['13']['train'], splits['42']['train'])
        self.assertEqual([len(splits['13'][part]) for part in ('train', 'validation', 'test')], [180, 60, 60])
        self.assertEqual(splits, development_splits(list(reversed(self.rows))))

    def test_group_owned_noise_stays_disjoint_in_every_fold(self):
        checks = verify_source_isolation(self.rows, self.noise, development_splits(self.rows))
        for report in checks.values():
            self.assertEqual(report['source_counts'], {'train': 1080, 'validation': 360, 'test': 360})
            self.assertEqual(report['cross_partition_canonical_source_overlap'], 0)

    def test_shared_noise_or_encoded_target_alias_is_rejected(self):
        self.noise[1]['evidence'][0]['title'] = self.noise[0]['evidence'][0]['title'].replace('-', '%2D')
        with self.assertRaisesRegex(ValueError, 'Shared target or distractor'):
            verify_source_isolation(self.rows, self.noise, development_splits(self.rows))

    def test_unseen_rule_families_only_go_to_fixed_test_sources(self):
        families = json.loads((ROOT/'configs/formal_rule_families.json').read_text())
        assignments = rule_assignments(self.rows, families, 20260919)
        self.assertEqual(len(assignments), 300)
        unseen = [r for r in assignments if r['exposure'] == 'heldout_wording']
        self.assertEqual(len(unseen), 20)
        self.assertTrue(all(r['planned_split'] == 'test' for r in unseen))
        self.assertTrue(all(r['both_pair_members_use_same_rule'] for r in assignments))
        self.assertEqual(assignments, rule_assignments(list(reversed(self.rows)), families, 20260919))

    def test_missing_distractor_or_reused_component_is_rejected(self):
        self.noise[0]['evidence'].pop()
        with self.assertRaisesRegex(ValueError, 'five reserved'):
            verify_source_isolation(self.rows, self.noise, development_splits(self.rows))
        self.rows[0]['component_id'] = self.rows[1]['component_id']
        with self.assertRaisesRegex(ValueError, 'independent source'):
            development_splits(self.rows)


if __name__ == '__main__':
    unittest.main()
