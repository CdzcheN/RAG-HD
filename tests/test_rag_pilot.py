"""CPU checks of leakage boundaries, actual Parquet parsing and cache safety."""
import importlib.util
import csv
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from rag_hd.data import convert_question, read_pool, snapshot_path
from rag_hd.evaluation import evaluate, initial_label
from rag_hd.io import fingerprint, write_jsonl
from rag_hd.retrieval import Retriever
from rag_hd.schema import Document, assign_groups, evidence_text, source_id, visible_input
from rag_hd.self_check import parse_confidence
from rag_hd.io import load_config

spec = importlib.util.spec_from_file_location('rag_prototype', ROOT/'scripts/rag_prototype.py')
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)


class PilotTests(unittest.TestCase):
    def test_transitive_source_groups_across_variants(self):
        records = [dict(base_question_id='a', source_document_ids=['x']),
                   dict(base_question_id='b', source_document_ids=['x','y']),
                   dict(base_question_id='c', source_document_ids=['y']),
                   dict(base_question_id='d', source_document_ids=['z']),
                   dict(base_question_id='a', source_document_ids=['x'])]
        assign_groups(records)
        self.assertEqual(len({r['group_id'] for r in records[:3]}), 1)
        self.assertEqual(records[0]['group_id'], records[4]['group_id'])
        self.assertNotEqual(records[0]['group_id'], records[3]['group_id'])
        self.assertEqual(source_id('Example_Page'), source_id('example page'))

    def test_visible_inputs_exclude_private_metadata(self):
        record = {'question':'Which city?', 'visible_evidence':'A public passage.',
                  'audit':{'reference_answers':['PRIVATE GOLD']}, 'construction':{'type':'HIDDEN CONDITION'}}
        public = json.dumps(visible_input(record))
        self.assertNotIn('PRIVATE GOLD', public)
        self.assertNotIn('HIDDEN CONDITION', public)
        before = fingerprint(visible_input(record))
        record['audit']['reference_answers'] = ['DIFFERENT PRIVATE GOLD']
        self.assertEqual(before, fingerprint(visible_input(record)))

    def test_parquet_sampling_survives_row_reordering(self):
        import pyarrow as pa
        import pyarrow.parquet as pq
        with tempfile.TemporaryDirectory() as folder:
            path = snapshot_path('squad','revision',folder)
            path.mkdir(parents=True)
            rows = [{'id':str(i), 'question':f'Question {i}', 'title':f'Page {i}',
                     'context':f'A synthetic fact {i}.', 'answers':{'text':[str(i)],'answer_start':[17]}} for i in range(12)]
            file = path/'train-00000-of-00001.parquet'
            pq.write_table(pa.Table.from_pylist(rows),file)
            a, meta_a = read_pool('squad','revision',folder,5,13)
            pq.write_table(pa.Table.from_pylist(list(reversed(rows))),file)
            b, meta_b = read_pool('squad','revision',folder,5,13)
            self.assertEqual(a,b)
            self.assertEqual(meta_a,meta_b)
            question, docs = convert_question('squad',a[0],'revision')
            self.assertEqual(question['audit']['gold_document_ids'],[docs[0].document_id])

    def test_hotpot_parser_preserves_both_supports(self):
        row = {'id':'toy', 'question':'Which city is linked to both people?', 'answer':'Bayport',
               'context':{'title':['Person One','Person Two','Noise'],
                          'sentences':[['One lives in Bayport.'],['Two lives in Bayport.'],['Unrelated fact.']]},
               'supporting_facts':{'title':['Person One','Person Two'],'sent_id':[0,0]}}
        question, docs = convert_question('hotpot',row,'revision')
        self.assertEqual(len(docs),3)
        self.assertEqual(len(question['source_document_ids']),2)
        self.assertEqual(len(question['audit']['gold_support']),2)

    def test_bm25_ties_and_visible_budget(self):
        docs = [Document.create('Beta','red '*10,'v'), Document.create('Alpha','blue '*10,'v')]
        a = Retriever(docs).search('unseen',2,3,5)
        b = Retriever(list(reversed(docs))).search('unseen',2,3,5)
        self.assertEqual(a,b)
        self.assertEqual(sum(len(r['text'].split()) for r in a),5)
        self.assertTrue(all(r['truncated'] for r in a))
        self.assertEqual(a[0]['document_id'], min(d.document_id for d in docs))

    def test_confidence_rejects_non_numeric_or_ambiguous_outputs(self):
        for raw in ['{"support_confidence":true}','{"support_confidence":"0.8"}',
                    '{"support_confidence":0.1,"support_confidence":0.9}',
                    '{"support_confidence":NaN}','{"support_confidence":1.1}',
                    '{"support_confidence":0.8,"extra":0}', 'Probably 0.8']:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                parse_confidence(raw)
        self.assertEqual(parse_confidence('{"support_confidence":0}'),0)
        self.assertEqual(parse_confidence('{"support_confidence":1}'),1)

    def test_reference_correctness_does_not_invent_support(self):
        record = {'audit':{'reference_answers':['Bayport'],'all_gold_support_visible':False}}
        answer = {'answer':'Bayport','is_refusal':False}
        self.assertEqual(initial_label(record,answer)['evidence_label'],'undetermined')
        record['audit']['all_gold_support_visible'] = True
        self.assertEqual(initial_label(record,answer)['evidence_label'],'supported')
        answer['answer'] = 'A different place'
        self.assertEqual(initial_label(record,answer)['evidence_label'],'undetermined')

    def test_metrics_share_a_common_cohort(self):
        def row(label, a, b):
            return {'evidence_label':label,'is_refusal':False,'qa':{'exact_match':False},
                    'self_check':{'risk':a},'minicheck':{'risk':b}}
        result = evaluate([row('supported',0.1,0.2),row('unsupported',0.9,0.8),
                           row('unsupported',None,0.1),row('undetermined',0.4,0.4)])
        self.assertEqual(result['common_evaluation_rows'],2)
        self.assertEqual(result['label_coverage'],0.75)
        self.assertEqual(result['methods']['self_check']['roc_auc'],1.0)
        self.assertEqual(result['methods']['minicheck']['roc_auc'],1.0)
        one_class = evaluate([row('supported',0.1,0.2)])
        self.assertIsNone(one_class['methods']['self_check']['roc_auc'])

    def test_cache_rejects_wrong_configuration_or_unknown_sample(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'cache.jsonl'
            write_jsonl(path,[{'sample_id':'one','cache_key':'old'}])
            with self.assertRaises(ValueError):
                cli.cached_rows(path,{'one':'new'})
            with self.assertRaises(ValueError):
                cli.cached_rows(path,{'two':'old'})
            self.assertEqual(len(cli.cached_rows(path,{'one':'old'})),1)

    def test_assessment_cache_cannot_change_answer(self):
        row = {'answer':'Original answer', 'self_check':{'answer_sha256':fingerprint('Original answer')}}
        cli.validate_assessment(row)
        row['answer'] = 'A different answer'
        with self.assertRaises(ValueError):
            cli.validate_assessment(row)

    def test_labels_cannot_be_reused_for_a_changed_answer(self):
        record = {'visible_input_sha256':'input', 'question':'Q', 'visible_evidence':'E'}
        generated = {'answer':'A'}
        review = {'answer_sha256':fingerprint('A'), 'visible_input_sha256':'input', 'answer':'A'}
        cli.validate_review_content(review,record,generated)
        with self.assertRaises(ValueError):
            cli.validate_review_content(review,record,{'answer':'B'})
        review['answer'] = 'Edited answer'
        with self.assertRaises(ValueError):
            cli.validate_review_content(review,record,generated)

    def test_blank_review_sheet_is_not_an_annotation(self):
        config = load_config(ROOT/'configs/rag_prototype.yaml')
        evidence = [{'rank':1,'title':'Synthetic page','version':'test','document_id':'doc:toy','text':'Northport is the city.'}]
        record = {'sample_id':'toy','base_question_id':'toy-base','group_id':'toy-group',
                  'source_document_ids':['toy-source'],'dataset':'synthetic','question':'Which city?',
                  'evidence':evidence,'visible_evidence':evidence_text(evidence),
                  'audit':{'reference_answers':['Northport'],'all_gold_support_visible':False,'gold_support':[]}}
        record['visible_input_sha256'] = fingerprint(visible_input(record))
        answer = {'sample_id':'toy','answer':'Northport is the city.','is_refusal':False,'generation':{},
                  'visible_input_sha256':record['visible_input_sha256']}
        answer['cache_key'] = cli.generator_key(record,config)
        answer['self_check'] = {'risk':0.1,'answer_sha256':fingerprint(answer['answer'])}
        mini = {'sample_id':'toy','cache_key':cli.minicheck_key(record,answer,config),
                'visible_input_sha256':record['visible_input_sha256'],'minicheck':{'risk':0.2}}
        with tempfile.TemporaryDirectory() as folder:
            run = Path(folder)
            for name,rows in [('prepared',[record]),('generation',[answer]),('minicheck',[mini])]:
                write_jsonl(run/(name+'.jsonl'),rows)
            self.assertTrue(cli.finish(config,run,None))
            self.assertTrue(cli.finish(config,run,run/'review_template.csv'))
            assistant_file = run/'assistant_suggestions.jsonl'
            write_jsonl(assistant_file,[{'sample_id':'toy', 'review_source':'assistant',
                                        'reviewer':'assistant', 'rationale':'Suggestion only.',
                                        'evidence_label':'supported'}])
            with self.assertRaises(ValueError):
                cli.finish(config,run,assistant_file)
            with (run/'review_template.csv').open(encoding='utf-8-sig',newline='') as stream:
                reader = csv.DictReader(stream)
                fields, reviews = reader.fieldnames, list(reader)
            reviews[0].update(evidence_label='supported',answer_correctness='correct',
                              review_source='human',reviewer='unit-test-fixture',rationale='Synthetic fixture only.')
            review_file = run/'synthetic_fixture_review.csv'
            with review_file.open('w',encoding='utf-8-sig',newline='') as stream:
                writer = csv.DictWriter(stream,fieldnames=fields)
                writer.writeheader()
                writer.writerows(reviews)
            self.assertFalse(cli.finish(config,run,review_file))
            labeled = json.loads((run/'records.jsonl').read_text())
            self.assertEqual(labeled['label_source'],'human_review')
            self.assertEqual(labeled['answer_correctness'],'correct')


if __name__ == '__main__':
    unittest.main()
