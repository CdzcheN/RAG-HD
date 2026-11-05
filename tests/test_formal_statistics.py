from pathlib import Path
import sys
import unittest

import numpy as np
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from rag_hd.formal_statistics import auc, weighted_cluster_auc, paired_contrast, holm_adjust


class FormalStatisticsTests(unittest.TestCase):
    def test_auc_matches_sklearn_with_ties_and_weighted_repeated_pairs(self):
        labels, scores = [1, 0, 1, 0], [0.7, 0.7, 0.4, 0.1]
        self.assertAlmostEqual(auc(labels, scores), roc_auc_score(labels, scores))
        weights = np.array([[2, 1, 0], [0, 2, 1], [0, 0, 3]])
        values = weighted_cluster_auc(labels, scores, ['a', 'a', 'b', 'b'], ['a', 'b', 'empty'], weights)
        repeated = [0, 1, 0, 1, 2, 3]
        self.assertAlmostEqual(values[0], roc_auc_score(np.array(labels)[repeated], np.array(scores)[repeated]))
        self.assertAlmostEqual(values[1], roc_auc_score(labels[2:], scores[2:]))
        self.assertTrue(np.isnan(values[2]))

    def test_identical_methods_have_zero_difference_ci_and_p_one(self):
        result = paired_contrast([1, 0, 1, 0], [.8, .2, .7, .3], [.8, .2, .7, .3],
                                 ['a', 'a', 'b', 'b'], ['a', 'b', 'empty'], samples=100)
        self.assertEqual(result['auc_difference'], 0)
        self.assertEqual(result['percentile_ci_95'], [0, 0])
        self.assertEqual(result['permutation_p_two_sided'], 1)

    def test_single_class_is_not_computable_and_invalid_bootstraps_are_counted(self):
        self.assertFalse(paired_contrast([0], [.1], [.2], ['a'], ['a'], samples=100)['computable'])
        result = paired_contrast([1, 0], [.8, .1], [.1, .8], ['a', 'b'], ['a', 'b'], samples=100)
        self.assertGreater(result['invalid_single_class_resamples'], 0)
        self.assertEqual(result['valid_resamples']+result['invalid_single_class_resamples'], 100)

    def test_exchange_is_paired_and_reproducible(self):
        args = ([1, 0, 1, 0], [.8, .2, .7, .3], [.2, .8, .3, .7],
                ['a', 'a', 'b', 'b'], ['a', 'b'])
        first = paired_contrast(*args, samples=500)
        self.assertEqual(first, paired_contrast(*args, samples=500))
        # Only two pair flips exist: identical method order or its reversal are
        # equally extreme. Exchanging individual rows would yield a different null.
        self.assertGreater(first['permutation_p_two_sided'], .4)
        self.assertLess(first['permutation_p_two_sided'], .6)

    def test_holm_preserves_original_order_and_monotonicity(self):
        np.testing.assert_allclose(holm_adjust([.03, .01, .04]), [.06, .03, .06])


if __name__ == '__main__': unittest.main()
