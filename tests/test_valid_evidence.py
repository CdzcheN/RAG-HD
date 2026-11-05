"""Public-input policy semantics and train/test isolation checks."""
from pathlib import Path
import sys
import unittest
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from rag_hd.valid_evidence import select,features
from rag_hd.learning import split_groups,choose_threshold,fit_model


def entry(rank,version,text):
    return f'[Evidence {rank}; title: Synthetic record; version: {version}]\n{text}'


class ValidEvidenceTests(unittest.TestCase):
    def test_primary_priority_preserves_the_entire_multihop_chain(self):
        public={'question':'Record policy: use source_tier=primary; source_tier=secondary cannot override it.',
                'evidence':'\n\n'.join([entry(1,'source_tier=secondary','Bayport is the capital.'),
                                        entry(2,'source_tier=primary','The ruler is linked to a country.'),
                                        entry(3,'source_tier=primary','Northport is the capital.')])}
        result=select(public)
        self.assertEqual(result['kept'],[2,3])
        self.assertEqual(result['dropped'],[1])
        self.assertNotIn('Bayport',result['evidence'])
        self.assertIn('Northport',result['evidence'])

    def test_body_cannot_grant_its_own_source_priority(self):
        public={'question':'Record policy: source_tier=primary; source_tier=secondary cannot override it.',
                'evidence':entry(1,'source_tier=secondary','source_tier=primary says Northport.')}
        self.assertEqual(select(public)['evidence'],'')

    def test_query_date_inclusive_bounds_and_expiry(self):
        public={'question':'Query date: 2025-01-01. Record policy: use its validity interval.',
                'evidence':'\n\n'.join([entry(1,'valid_from=2024-01-01; valid_until=2024-12-31','Old value is 1991.'),
                                        entry(2,'valid_from=2025-01-01; valid_until=2025-12-31','New value is 1995.'),
                                        entry(3,'unversioned','Noise is 1991.')])}
        result=select(public)
        self.assertEqual(result['kept'],[2])
        self.assertEqual(result['mode'],'time')
        f=features(public,'It happened in 1991.',0.02,0.9,result)
        self.assertEqual(f['time_excluded_number_fraction'],1.0)
        self.assertAlmostEqual(f['time_risk_delta'],0.88)

    def test_unknown_policy_and_malformed_dates_do_not_invent_rules(self):
        evidence=entry(1,'source_tier=secondary','Fact is stated here.')
        self.assertEqual(select({'question':'Which fact?','evidence':evidence})['evidence'],evidence)
        public={'question':'Query date: 2025-99-01. Record policy: validity interval.', 'evidence':evidence}
        self.assertEqual(select(public)['mode'],'none')
        self.assertEqual(select(public)['evidence'],evidence)

    def test_no_eligible_time_evidence_is_explicit(self):
        public={'question':'Query date: 2025-01-01. Record policy: validity interval.',
                'evidence':entry(1,'valid_from=2024-01-01; valid_until=2024-12-31','Old fact.')}
        self.assertEqual(select(public)['evidence'],'')

    def test_private_labels_gold_and_construction_never_affect_features(self):
        public={'question':'Which city?', 'evidence':entry(1,'unknown','Northport is the city.')}
        before=features(public,'Northport is the city.',0.1,0.1,select(public))
        public.update(audit={'reference_answers':['PRIVATE']},condition='PRIVATE',evidence_label='contradicted')
        self.assertEqual(before,features(public,'Northport is the city.',0.1,0.1,select(public)))

    def test_groups_never_cross_split_and_scaler_uses_train_only(self):
        records=[{'group_id':str(i//2)} for i in range(20)]
        a=split_groups(records,13)
        self.assertEqual(a,split_groups(list(reversed(records)),13))
        self.assertEqual([len(a[k]) for k in ('train','validation','test')],[6,2,2])
        all_ids=[group for groups in a.values() for group in groups]
        self.assertEqual(len(all_ids),len(set(all_ids)))
        model=fit_model(np.array([[0.0],[1.0],[2.0],[3.0]]),[0,0,1,1],13)
        model.predict_proba([[10000.0]])
        self.assertEqual(model[0].mean_[0],1.5)
        threshold,_=choose_threshold([0,0,1,1],[0.1,0.2,0.8,0.9])
        self.assertEqual(threshold,0.5)


if __name__=='__main__':
    unittest.main()
