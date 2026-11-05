"""Paired source-cluster statistics for the prespecified final-test contrasts."""
import numpy as np


def auc(labels, scores):
    labels, scores = np.asarray(labels), np.asarray(scores, dtype=float)
    positive, negative = scores[labels == 1], scores[labels == 0]
    if not len(positive) or not len(negative):
        return None
    return float(np.mean((positive[:, None] > negative) + 0.5*(positive[:, None] == negative)))


def weighted_cluster_auc(labels, scores, row_groups, groups, weights):
    """AUC for cluster multiplicities; tied positive-negative pairs receive half credit."""
    labels, scores = np.asarray(labels), np.asarray(scores, dtype=float)
    indices = {group: i for i, group in enumerate(groups)}
    g = np.array([indices[x] for x in row_groups], dtype=int)
    p, n = np.flatnonzero(labels == 1), np.flatnonzero(labels == 0)
    kernel = np.zeros((len(groups), len(groups)))
    comparisons = (scores[p, None] > scores[n]) + 0.5*(scores[p, None] == scores[n])
    np.add.at(kernel, (np.repeat(g[p], len(n)), np.tile(g[n], len(p))), comparisons.ravel())
    positive = np.bincount(g[p], minlength=len(groups))
    negative = np.bincount(g[n], minlength=len(groups))
    weights = np.atleast_2d(weights)
    denominator = (weights @ positive)*(weights @ negative)
    numerator = np.einsum('bi,ij,bj->b', weights, kernel, weights, optimize=True)
    return np.divide(numerator, denominator, out=np.full(len(weights), np.nan), where=denominator > 0)


def paired_contrast(labels, left, right, row_groups, groups, samples=10000, seed=20260920):
    if len(groups) != len(set(groups)) or not set(row_groups) <= set(groups):
        raise ValueError('Require unique source groups covering every comparison row')
    if not (len(labels) == len(left) == len(right) == len(row_groups)):
        raise ValueError('Paired comparisons must have identical row coverage')
    if any(x not in (0, 1) for x in labels) or not np.isfinite([*left, *right]).all():
        raise ValueError('Invalid binary labels or nonfinite risks')
    initial_left, initial_right = auc(labels, left), auc(labels, right)
    if initial_left is None:
        return {'computable': False, 'reason': 'Fewer than two classes',
                'requested_resamples': samples, 'valid_resamples': 0,
                'auc_difference': None, 'percentile_ci_95': None, 'permutation_p_two_sided': None}
    rng = np.random.default_rng(seed)
    weights = rng.multinomial(len(groups), np.full(len(groups), 1/len(groups)), size=samples)
    difference = (weighted_cluster_auc(labels, left, row_groups, groups, weights) -
                  weighted_cluster_auc(labels, right, row_groups, groups, weights))
    valid = difference[np.isfinite(difference)]
    observed = initial_left - initial_right
    # Each exchange flips both methods for every factual answer of one source,
    # preserving normal/challenge pairing. Separate RNG retains reproducibility.
    rng = np.random.default_rng(seed)
    group_index = {g: i for i, g in enumerate(groups)}
    row_index = np.array([group_index[g] for g in row_groups])
    labels, left, right = np.asarray(labels), np.asarray(left), np.asarray(right)
    p, n = np.flatnonzero(labels == 1), np.flatnonzero(labels == 0)
    extreme = 0
    for start in range(0, samples, 256):
        flip = rng.integers(0, 2, size=(min(256, samples-start), len(groups)), dtype=np.int8)[:, row_index]
        a, b = np.where(flip, right, left), np.where(flip, left, right)
        ap, an = a[:, p, None], a[:, None, n]
        bp, bn = b[:, p, None], b[:, None, n]
        delta = np.mean((ap > an)+0.5*(ap == an), axis=(1, 2)) - np.mean((bp > bn)+0.5*(bp == bn), axis=(1, 2))
        extreme += int(np.sum(np.abs(delta) >= abs(observed)-1e-12))
    return {'computable': True, 'auc_difference': observed, 'requested_resamples': samples,
            'valid_resamples': len(valid), 'invalid_single_class_resamples': samples-len(valid),
            'percentile_ci_95': np.quantile(valid, [0.025, 0.975]).tolist() if len(valid) else None,
            'permutation_samples': samples, 'permutation_extreme_samples': extreme,
            'permutation_p_two_sided': (extreme+1)/(samples+1), 'seed': seed,
            'unit': 'all fixed source groups, including groups with zero common factual rows',
            'source_groups': len(groups), 'factual_rows': len(labels)}


def holm_adjust(pvalues):
    values = list(pvalues)
    order = sorted(range(len(values)), key=lambda i: values[i])
    result, previous = [0.0]*len(values), 0.0
    for rank, index in enumerate(order):
        previous = max(previous, min(1.0, values[index]*(len(values)-rank)))
        result[index] = previous
    return result
