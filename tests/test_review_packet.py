"""Verify that assistance cannot silently become labels or cite hidden evidence."""
import csv
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from rag_hd.io import fingerprint, write_jsonl
from rag_hd.review_packet import export_packet, validate_suggestions
from rag_hd.schema import visible_input


class ReviewPacketTests(unittest.TestCase):
    def setUp(self):
        self.request = {'sample_id': 'synthetic', 'question': 'Where?',
                        'visible_evidence': 'The capital is Northport.', 'answer': 'Northport.',
                        'reference_answers': ['Northport']}
        self.request['visible_input_sha256'] = fingerprint(visible_input(self.request))
        self.request['answer_sha256'] = fingerprint(self.request['answer'])
        self.suggestion = {k: self.request[k] for k in ('sample_id', 'visible_input_sha256', 'answer_sha256')}
        self.suggestion.update(review_source='assistant', evidence_label='supported',
                               answer_correctness='correct', rationale='Supported by the visible sentence.',
                               evidence_anchors=[{'start': 15, 'end': 24, 'quote': 'Northport'}])

    def test_hidden_or_misaligned_quote_is_rejected(self):
        validate_suggestions([self.request], [self.suggestion])
        for patch in ({'quote': 'Hidden gold'}, {'start': -1}, {'end': 25}, {'start': True}):
            changed = deepcopy(self.suggestion)
            changed['evidence_anchors'][0].update(patch)
            with self.subTest(patch=patch), self.assertRaises(ValueError):
                validate_suggestions([self.request], [changed])

    def test_changed_input_or_answer_rejects_old_suggestion(self):
        for field in ('question', 'answer', 'visible_evidence'):
            changed = dict(self.request, **{field: 'Different content'})
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_suggestions([changed], [self.suggestion])
        changed = dict(self.suggestion, answer_sha256=fingerprint('Different answer'))
        with self.assertRaises(ValueError):
            validate_suggestions([self.request], [changed])

    def test_duplicate_missing_or_unknown_cases_are_rejected(self):
        for suggestions in ([], [self.suggestion, self.suggestion], [dict(self.suggestion, sample_id='unknown')]):
            with self.subTest(suggestions=suggestions), self.assertRaises(ValueError):
                validate_suggestions([self.request], suggestions)

    def test_refusal_cannot_get_a_factual_label(self):
        self.request['answer'] = 'INSUFFICIENT_EVIDENCE'
        self.request['answer_sha256'] = fingerprint(self.request['answer'])
        self.suggestion['answer_sha256'] = self.request['answer_sha256']
        with self.assertRaises(ValueError):
            validate_suggestions([self.request], [self.suggestion])

    def test_export_prefills_draft_without_source_column_and_preserves_human_work(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            requests, suggestions = root/'requests.jsonl', root/'suggestions.jsonl'
            # Unexpected score fields in the request must never enter the review packet.
            self.request['minicheck'] = {'risk': 'SECRET_DETECTOR_SCORE'}
            self.request['self_check'] = {'risk': 'SECRET_SELF_SCORE'}
            write_jsonl(requests, [self.request])
            write_jsonl(suggestions, [self.suggestion])
            manifest = export_packet(requests, suggestions, root/'packet')
            csv_path = root/'packet/review_assisted.csv'
            with csv_path.open(encoding='utf-8-sig', newline='') as stream:
                reader = csv.DictReader(stream)
                fields, rows = reader.fieldnames, list(reader)
            self.assertEqual(rows[0]['evidence_label'], 'supported')
            self.assertEqual(rows[0]['suggested_evidence_label'], 'supported')
            self.assertNotIn('review_source', fields)
            self.assertEqual(rows[0]['rationale'], self.suggestion['rationale'])
            self.assertEqual(manifest['user_confirmation'], 'pending')
            self.assertEqual(manifest['formal_labels_created'], 0)
            for path in (csv_path, root/'packet/review_packet.md'):
                self.assertNotIn('SECRET_', path.read_text())
            rows[0].update(reviewer='synthetic-fixture',
                           evidence_label='supported', rationale='Independent synthetic check.')
            with csv_path.open('w', encoding='utf-8-sig', newline='') as stream:
                writer = csv.DictWriter(stream, fieldnames=fields)
                writer.writeheader()
                writer.writerows(rows)
            before = csv_path.read_bytes()
            export_packet(requests, suggestions, root/'packet')
            self.assertEqual(csv_path.read_bytes(), before)
            changed = dict(self.suggestion, rationale='Changed assistant opinion')
            write_jsonl(suggestions, [changed])
            with self.assertRaises(ValueError):
                export_packet(requests, suggestions, root/'packet')


if __name__ == '__main__':
    unittest.main()
