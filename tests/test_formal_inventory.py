import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from rag_hd.formal_inventory import (candidate_reason, components, nominate, partition,
                                     prior_sources, reserve_noise, prepare, SPLIT_QUOTAS, KINDS)
from rag_hd.io import write_json, write_jsonl
from rag_hd.schema import Document


class FormalInventoryTests(unittest.TestCase):
    def test_encoded_aliases_and_transitive_shared_sources_cannot_split(self):
        rows = [{'base_question_id': str(i), 'gold_titles': titles}
                for i, titles in enumerate([['A', 'B'], ['B', 'C & D'], ['C &amp; D'], ['Other']])]
        groups = components(rows)
        self.assertEqual(sorted(len(g['members']) for g in groups), [1, 3])
        self.assertEqual(groups, components(list(reversed(rows))))

    def test_nomination_is_order_invariant_and_satisfies_every_stratum(self):
        rows = [{'base_question_id': f'{dataset}:{i}', 'dataset': dataset,
                 'gold_titles': [f'{dataset} title {i}']} for dataset in ('squad', 'hotpot') for i in range(500)]
        groups = components(rows)
        chosen, deficits = nominate(groups, 20260919)
        self.assertFalse(deficits)
        self.assertEqual(len(chosen), 300)
        self.assertEqual(len({r['component_id'] for r in chosen}), 300)
        self.assertEqual((chosen, deficits), nominate(list(reversed(groups)), 20260919))
        for split, count in SPLIT_QUOTAS.items():
            for dataset in ('squad', 'hotpot'):
                for kind in KINDS:
                    self.assertEqual(sum(r['planned_split'] == split and r['dataset'] == dataset
                                         and r['proposed_challenge_type'] == kind for r in chosen), count)

    def test_scarcity_is_reported_without_reusing_sources(self):
        groups = components([{'base_question_id': 'q', 'dataset': 'squad', 'gold_titles': ['Unique']}])
        chosen, deficits = nominate(groups, 20260919)
        self.assertEqual(len(chosen), 1)
        self.assertTrue(deficits)

    def test_prior_hidden_gold_and_visible_sources_are_both_excluded(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); run = root/'old'; run.mkdir()
            write_json(run/'status.json', {'stage': 'complete'})
            write_jsonl(run/'corpus.jsonl', [{'document_id': 'gold', 'title': 'C%20%26%20D'}])
            write_jsonl(run/'prepared.jsonl', [{'base_question_id': 'q',
                         'evidence': [{'title': 'Visible_page'}], 'audit': {'gold_document_ids': ['gold']}}])
            titles, questions, _ = prior_sources(root, ['old'])
            self.assertEqual(titles, {'c & d', 'visible page'})
            self.assertEqual(questions, {'q'})

    def test_numeric_slot_and_alias_checks_are_not_semantic_approval(self):
        question = {'base_question_id': 'q', 'question': 'How many buildings are there?',
                    'audit': {'reference_answers': ['25']}}
        gold = [Document.create('Town', 'There are 25 buildings.', 'r')]
        self.assertIsNone(candidate_reason(question, gold, set(), set()))
        question['audit']['reference_answers'] = ['25', '24']
        self.assertEqual(candidate_reason(question, gold, set(), set()), 'ambiguous_reference_aliases')
        question['audit']['reference_answers'] = ['25']
        gold = [Document.create('Town', 'There were 25 houses and 25 trees.', 'r')]
        self.assertEqual(candidate_reason(question, gold, set(), set()), 'nonunique_numeric_slot')

    def test_reserved_noise_sources_are_exclusive_and_answer_free(self):
        documents = [Document.create(f'Noise {i}', 'Unrelated scenic place.', 'r') for i in range(15)]
        rows = [{'base_question_id': str(i), 'component_id': str(i), 'planned_split': split,
                 'question': 'How many scenic places?', 'reference_answers': ['99']}
                for i, split in enumerate(('train', 'validation'))]
        reservations = reserve_noise(rows, {'train': documents, 'validation': documents}, 1)
        titles = [d['title'] for r in reservations for d in r['evidence']]
        self.assertEqual(len(titles), 10)
        self.assertEqual(len(set(titles)), 10)
        self.assertTrue(all(len(r['evidence']) == 5 for r in reservations))

    def test_preparation_never_overwrites_an_existing_review_sheet(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); sheet = root/'候选来源复核.csv'; sheet.write_text('user edits')
            with self.assertRaisesRegex(ValueError, 'preserve review'):
                prepare(root, {}, {}, root)
            self.assertEqual(sheet.read_text(), 'user edits')


if __name__ == '__main__':
    unittest.main()
