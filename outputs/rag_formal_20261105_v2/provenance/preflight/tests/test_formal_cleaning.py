from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from rag_hd.formal_cleaning import aliases, numeric_edit, validate_numbers, edit_record
from rag_hd.schema import Document, document_dict


class FormalCleaningTests(unittest.TestCase):
    def test_numeric_span_does_not_change_embedded_year_digits(self):
        edit = numeric_edit('There were 13 boats in 2013.', '13', '14', 'count')
        self.assertEqual(edit.start, 11)
        result = {}; validate_numbers('13', '14', {}, 'There were 13 boats in 2013.', result)
        self.assertEqual(result['text'], 'There were 14 boats in 2013.')

    def test_total_and_component_move_together(self):
        source = 'There are 915 communities: 49 urban and 866 rural.'
        spec = {'coupled_deltas':[{'before':'866','key':'rural'}],
                'sum_constraint':{'parts':{'urban':'49','rural':'866'},'total_key':'target'}}
        result = {}; report = validate_numbers('915','916',spec,source,result)
        self.assertIn('867 rural', result['text'])
        self.assertEqual(report['values_after']['target'], '916')
        with self.assertRaisesRegex(ValueError, 'sum to total'):
            validate_numbers('915','916',{'sum_constraint':spec['sum_constraint']},source,{})

    def test_fixed_population_total_and_percentage_rounding(self):
        source = 'Population 1,325,968: 707,697 women (53.4%) and 618,271 men (46.6%).'
        spec = {'coupled_deltas':[{'before':'618,271','key':'male','multiplier':-1}],
                'sum_constraint':{'parts':{'female':'$target','male':'618,271'},'constant_total':'1,325,968'},
                'partition_rounding':{'denominator':'1,325,968','shares':{'female':'53.4','male':'46.6'},'resolution':'0.1'}}
        result = {}; validate_numbers('707,697','707,698',spec,source,result)
        self.assertIn('618,270 men', result['text'])
        self.assertIn('53.4%', result['text'])

    def test_percentage_and_raw_votes_remain_consistent(self):
        source = 'Rejected by 67.7% to 32.3%: 423,434 against and 201,975 for.'
        spec = {'percentage_partition':{'complement':'32.3%','target_votes':'423,434','other_votes':'201,975','resolution':'0.1'}}
        result = {}; report = validate_numbers('67.7%','67.8%',spec,source,result)
        after = report['values_after']
        self.assertEqual(after['complement'], '32.2%')
        self.assertEqual(sum(int(after[k].replace(',','')) for k in ('target_votes','other_votes')), 625409)

    def test_square_area_rounding_check_rejects_large_inconsistent_change(self):
        spec = {'scaled_check':{'other':'4,700,000','factor':'2.589988110336','tolerance':'50000'}}
        source = 'An area of 1,800,000 square miles (4,700,000 km2).'
        validate_numbers('1,800,000','1,800,001',spec,source,{})
        with self.assertRaisesRegex(ValueError, 'area conversion'):
            validate_numbers('1,800,000','2,000,000',spec,source,{})

    def test_acres_and_hectares_update_with_declared_rounding(self):
        spec = {'scaled_coupled':[{'before':'25','key':'hectares','factor':'0.40468564224','round_to':'1'}]}
        result = {}; validate_numbers('63','64',spec,'The resort occupied 63 acres (25 ha).',result)
        self.assertEqual(result['text'],'The resort occupied 64 acres (26 ha).')

    def test_known_and_unknown_denominator_rounding_checks(self):
        validate_numbers('147,754','147,755',{'ratio_rounding_check':{'base':'146,199','reported_growth':'1.1','resolution':'0.1'}},
                         'Population 147,754, versus 146,199, up 1.1%.',{})
        validate_numbers('840,000','840,001',{'ratio_rounding_check':{'share':'19','share_percent_resolution':'1'}},
                         '840,000 jobs represented 19% of the labour force.',{})
        with self.assertRaisesRegex(ValueError, 'common denominator'):
            validate_numbers('840,000','1,840,000',{'ratio_rounding_check':{'share':'19','share_percent_resolution':'1'}},
                             '840,000 jobs represented 19% of the labour force.',{})

    def test_aliases_include_formatted_percent_and_word_forms(self):
        self.assertTrue({'1,000','1000','1000%'}.issubset(aliases('1,000')))
        self.assertTrue({'seventeen','17','17%'}.issubset(aliases('17')))
        self.assertIn('twenty-one',aliases('21'))

    def test_retrieval_deletion_never_invents_a_time_or_definition_edit(self):
        doc = Document.create('History', 'The event was dated to 1.5 million years ago.', 'revision')
        row = {'base_question_id':'q','reference_answers':['1.5'],'gold_evidence':[document_dict(doc)],
               'proposed_challenge_type':'retrieval_failure'}
        result = edit_record(row,{},13)
        self.assertIsNone(result[4])
        self.assertEqual(result[5]['exact_span_edits'],[])

    def test_source_excerpt_and_authored_reference_are_checked(self):
        doc = Document.create('College','In 1587 the maximum was 70, including 50 priests.','r')
        row = {'base_question_id':'q','reference_answers':['1587'],'gold_evidence':[document_dict(doc)],
               'proposed_challenge_type':'evidence_conflict'}
        result = edit_record(row,{'reference_override':'70'},13)
        self.assertEqual(result[3],'70')
        with self.assertRaisesRegex(ValueError,'exact unambiguous span'):
            edit_record(row,{'excerpt_quote':'fabricated passage'},13)


if __name__=='__main__': unittest.main()
