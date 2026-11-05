"""Regressions for alias chains, numeric units, coupled totals and complete cuts."""
from pathlib import Path
from decimal import Decimal
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from rag_hd.construction_edits import apply,locate,Edit,quantity_change,number,validate_constraints
from rag_hd.challenges_v2 import build_pair,bounded_occurrences,canonical_title
from rag_hd.schema import Document,assign_groups,validate_record


class RepairTests(unittest.TestCase):
    def test_quantity_boundaries_and_encoded_source_aliases(self):
        self.assertEqual(len(bounded_occurrences('There were 187,105, according to the record.','187,105')),1)
        self.assertEqual(len(bounded_occurrences('There were 32,000 people in 1932.','32')),0)
        self.assertEqual(len(bounded_occurrences('The share was 1.16%.','1.16%')),1)
        self.assertEqual(canonical_title('Example_%26amp%3B_City'),canonical_title('example & city'))
    def test_aliases_and_title_must_be_synchronized_without_changing_work_title(self):
        fields={'title':'Phil McGraw','text':'Phillip Calvin McGraw, known as Dr. Phil, hosts the show Dr. Phil.'}
        edits=[locate('title',fields['title'],'Phil McGraw','Vincente Minnelli','person_title'),
               locate('text',fields['text'],'Phillip Calvin McGraw','Vincente Minnelli','canonical_person'),
               locate('text',fields['text'],'Dr. Phil','Vincente Minnelli','person_alias',occurrence=0)]
        required=[{'field':e.field,'start':e.start,'end':e.end,'text':e.before} for e in edits]
        with self.assertRaises(ValueError):apply(fields,edits[:1],required)
        result,log=apply(fields,edits,required)
        self.assertEqual(result['title'],'Vincente Minnelli')
        self.assertIn('hosts the show Dr. Phil.',result['text'])
        self.assertNotIn('Phillip Calvin McGraw',result['text'])
        self.assertEqual(len(log),3)
        self.assertEqual(fields['title'],'Phil McGraw')

    def test_overlapping_or_stale_edit_rejected(self):
        fields={'text':'John Smith is a writer.'}
        edits=[locate('text',fields['text'],'John Smith','Nora Venn','person'),
               locate('text',fields['text'],'Smith','Venn','surname')]
        with self.assertRaises(ValueError):apply(fields,edits)
        with self.assertRaises(ValueError):apply({'text':'Jane Smith is a writer.'},edits[:1])

    def test_percentage_carry_grouping_and_bounds(self):
        self.assertEqual(quantity_change('99.9%',1),'100.0%')
        self.assertEqual(quantity_change('100%',1),'99%')
        self.assertEqual(quantity_change('1,999',1),'2,000')
        self.assertEqual(quantity_change('0',-1),'1')
        self.assertEqual(quantity_change('2,628',1,upper=2628),'2,627')
        with self.assertRaises(ValueError):quantity_change('101%',1)

    def test_no_automatic_birth_founding_or_death_year_changes(self):
        for role in ('birth_year','founding_year','death_year'):
            with self.subTest(role=role),self.assertRaises(ValueError):
                quantity_change('1979',1,role=role)

    def test_linked_percentages_must_sum_to_100(self):
        constraint=[{'kind':'sum','keys':['urban','rural'],'total':'100'}]
        validate_constraints({'urban':'48.3%','rural':'51.7%'},constraint)
        with self.assertRaises(ValueError):
            validate_constraints({'urban':'48.4%','rural':'51.7%'},constraint)
        validate_constraints({'urban':'48.4%','rural':'51.6%'},constraint)

    def test_complete_cut_removes_all_hops_and_keeps_document_count(self):
        one=Document.create('Synthetic bridge','The person is connected to Northport.','test')
        two=Document.create('Northport','Northport reports 321 residents.','test')
        q={'base_question_id':'synthetic','dataset':'hotpot','question':'What population does the linked city report?',
           'source_document_ids':[one.source_document_id,two.source_document_id],
           'audit':{'reference_answers':['321'],'gold_document_ids':[one.document_id,two.document_id]}}
        noise=[{'document_id':f'noise{i}','source_document_id':f'source{i}','title':f'Noise{i}',
                'version':'test','text':'A different place has a lake.','rank':i+1} for i in range(5)]
        spec={'type':'retrieval_failure','slot_role':'reported_quantity','excerpt_spans':{},'curation_note':'Synthetic two-hop fixture.'}
        a,b=build_pair(q,[one,two],noise,spec,13,1)
        assign_groups([a,b]);validate_record(a);validate_record(b)
        self.assertEqual(len(a['evidence']),5);self.assertEqual(len(b['evidence']),5)
        self.assertNotIn('Northport',b['visible_evidence'])
        self.assertNotIn('321',b['visible_evidence'])
        self.assertEqual(len(b['construction']['removed_evidence']),2)
        self.assertEqual(b['construction']['values_before'],b['construction']['values_after'])
        self.assertEqual(a['group_id'],b['group_id'])

    def test_missing_question_referent_is_rejected(self):
        doc=Document.create('Example','It was done in 1919.','test')
        q={'base_question_id':'synthetic','dataset':'squad','question':'What year was this done?',
           'source_document_ids':[doc.source_document_id],
           'audit':{'reference_answers':['1919'],'gold_document_ids':[doc.document_id]}}
        spec={'type':'outdated_answer','slot_role':'reported_quantity','excerpt_spans':{},'curation_note':'Ambiguous fixture.'}
        with self.assertRaises(ValueError):build_pair(q,[doc],[{}]*5,spec,13,1)


if __name__=='__main__':unittest.main()
