import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from rag_hd.formal_gate import validate_test_freeze
from rag_hd.io import write_json, write_jsonl, fingerprint, file_sha256


class FormalGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name); self.run=self.root/'partitions/test'
        self.dev=self.root/'partitions/development';self.run.mkdir(parents=True);self.dev.mkdir()
        write_jsonl(self.run/'prepared.jsonl',[{'base_question_id':'final'}])
        write_jsonl(self.dev/'records.jsonl',[{'base_question_id':'train'}])
        write_json(self.dev/'review_confirmation.json',{'status':'user_confirmed'})
        parts={s:{'train':['train'],'validation':['validation'],'test':['final']} for s in ('13','42','2026')}
        write_json(self.root/'frozen_splits.json',parts)
        model=self.root/'model';model.write_text('frozen local model')
        self.certificate={'protocol_version':'formal-model-freeze-v1','threshold_origin':'formal_validation_only',
            'final_test_ids_sha256':fingerprint(['final']),
            'development_confirmation_sha256':file_sha256(self.dev/'review_confirmation.json'),
            'development_records_sha256':file_sha256(self.dev/'records.jsonl'),
            'development_splits':parts,'artifacts_sha256':{str(model):file_sha256(model)}}

    def test_missing_or_invalid_freeze_blocks_test(self):
        with self.assertRaisesRegex(ValueError,'held out'): validate_test_freeze(self.run)
        write_json(self.run/'model_freeze.json',{'protocol_version':'not accepted'})
        with self.assertRaisesRegex(ValueError,'Invalid formal'): validate_test_freeze(self.run)

    def test_train_or_validation_cannot_include_final_test(self):
        self.certificate['development_splits']['13']['train']=['final']
        write_json(self.run/'model_freeze.json',self.certificate)
        with self.assertRaisesRegex(ValueError,'overlap final test'): validate_test_freeze(self.run)

    def test_valid_certificate_and_changed_model(self):
        write_json(self.run/'model_freeze.json',self.certificate)
        self.assertEqual(validate_test_freeze(self.run),self.certificate)
        (self.root/'model').write_text('changed weights')
        with self.assertRaisesRegex(ValueError,'artifact changed'): validate_test_freeze(self.run)


if __name__=='__main__': unittest.main()
