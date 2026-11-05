"""Intervention invariants independent of model predictions."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from rag_hd.challenges import make_pair, evidence_entry, replacement_for, value_kind
from rag_hd.data import convert_question
from rag_hd.io import fingerprint
from rag_hd.schema import Document, assign_groups, validate_record, visible_input


class ChallengeTests(unittest.TestCase):
    def setUp(self):
        self.q, self.docs = convert_question('squad', {
            'id':'toy', 'title':'Synthetic country', 'question':'Which city is the capital?',
            'context':'The capital of this country is Northport.',
            'answers':{'text':['Northport'],'answer_start':[31]}}, 'synthetic-revision')
        noise = Document.create('Geography','The country has a river and a mountain.','synthetic-revision')
        self.retrieved = [dict(evidence_entry(noise), rank=1)]

    def pair(self, kind):
        pair = make_pair(self.q,self.docs,self.retrieved,kind,'Bayport',13)
        assign_groups(pair)
        for row in pair:
            validate_record(row)
            self.assertEqual(row['evidence_label'],'undetermined')
            self.assertFalse(row['audit']['all_gold_support_visible'])
            self.assertNotIn('reference_answers',visible_input(row))
        self.assertEqual(pair[0]['group_id'],pair[1]['group_id'])
        self.assertEqual(pair[0]['pair_id'],pair[1]['pair_id'])
        self.assertNotEqual(pair[0]['sample_id'],pair[1]['sample_id'])
        return pair

    def test_deletion_removes_target_and_preserves_noise(self):
        normal, challenge = self.pair('retrieval_failure')
        self.assertIn('Northport',normal['visible_evidence'])
        self.assertNotIn('Northport',challenge['visible_evidence'])
        self.assertIn('mountain',challenge['visible_evidence'])
        self.assertTrue(challenge['construction']['removed_evidence'])

    def test_alias_surviving_deletion_is_rejected(self):
        q = deepcopy(self.q)
        other = Document.create('Alternative support','Northport is also described here.','synthetic-revision')
        q['audit']['gold_document_ids'].append(other.document_id)
        with self.assertRaises(ValueError):
            make_pair(q,self.docs+[other],self.retrieved,'retrieval_failure','Bayport',13)

    def test_conflict_exposes_rule_and_both_values(self):
        normal, challenge = self.pair('evidence_conflict')
        self.assertEqual(normal['question'],challenge['question'])
        self.assertIn('source_tier=primary',challenge['question'])
        self.assertNotIn('Bayport',normal['visible_evidence'])
        self.assertIn('Northport',challenge['visible_evidence'])
        self.assertIn('Bayport',challenge['visible_evidence'])
        self.assertEqual(normal['audit']['reference_answers'],challenge['audit']['reference_answers'])

    def test_time_exposes_expiry_update_and_same_query_date(self):
        normal, challenge = self.pair('outdated_answer')
        self.assertEqual(normal['question'],challenge['question'])
        self.assertIn('2025-06-01',challenge['question'])
        self.assertIn('valid_until=2024-12-31',challenge['visible_evidence'])
        self.assertIn('supersedes=2024-record',challenge['visible_evidence'])
        self.assertIn('Northport',challenge['visible_evidence'])
        self.assertNotIn('Northport',normal['visible_evidence'])
        self.assertEqual(challenge['audit']['reference_answers'],['Bayport'])

    def test_building_pairs_is_deterministic_and_cannot_change_source(self):
        before = fingerprint([self.q,self.retrieved])
        self.assertEqual(self.pair('evidence_conflict'),self.pair('evidence_conflict'))
        self.assertEqual(before,fingerprint([self.q,self.retrieved]))

    def test_replacements_preserve_value_kind_and_date_validity(self):
        def question(query, answer):
            return {'question':query,'base_question_id':'synthetic','audit':{'reference_answers':[answer]}}
        year = question('In which year?', '1780')
        self.assertEqual(replacement_for(year,[],13),'1784')
        date = question('When?', 'February 29, 2096')
        self.assertEqual(replacement_for(date,[],13),'February 29, 2104')
        self.assertIsNone(value_kind(question('Who designed it?','Apple Inc.')))
        self.assertIsNone(value_kind(question('Who operated it?','Republic Airways')))
        self.assertIsNone(value_kind(question('Who objected?','His opponents')))
        self.assertIsNone(value_kind(question('What country?','American')))
        self.assertEqual(value_kind(question('Who led it?','George Armstrong Custer')),'person')


if __name__ == '__main__':
    unittest.main()
