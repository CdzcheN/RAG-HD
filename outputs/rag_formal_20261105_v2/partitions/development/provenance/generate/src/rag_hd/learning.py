"""Grouped exploratory development splits, train-only scaling and validation thresholds."""
import numpy as np
from sklearn.metrics import (average_precision_score, confusion_matrix, f1_score,
                             precision_score, recall_score, roc_auc_score)
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


def split_groups(records, seed):
    groups=sorted({r['group_id'] for r in records})
    order=list(np.random.default_rng(seed).permutation(groups))
    n_train, n_val=int(len(order)*0.6), int(len(order)*0.2)
    parts={'train':order[:n_train],'validation':order[n_train:n_train+n_val],'test':order[n_train+n_val:]}
    assert not set(parts['train']) & set(parts['validation'])
    assert not set(parts['train']) & set(parts['test'])
    assert not set(parts['validation']) & set(parts['test'])
    return parts


def choose_threshold(labels, scores):
    if len(set(labels))<2:
        return 0.5,'validation_single_class_fallback'
    candidates=sorted(set([0.0,0.5,1.0,*[float(s) for s in scores]]))
    ranked=[]
    for threshold in candidates:
        predicted=np.asarray(scores)>=threshold
        metric=f1_score(labels,predicted,labels=[0,1],average='macro',zero_division=0)
        ranked.append((-metric,abs(threshold-0.5),threshold))
    return min(ranked)[2],'max_validation_macro_f1_tie_nearest_0.5'


def metrics(labels, scores, threshold):
    predicted=np.asarray(scores)>=threshold
    two=len(set(labels))==2
    return {'rows':len(labels),'positives':int(sum(labels)),
            'roc_auc':float(roc_auc_score(labels,scores)) if two else None,
            'average_precision':float(average_precision_score(labels,scores)) if two else None,
            'precision':float(precision_score(labels,predicted,zero_division=0)),
            'recall':float(recall_score(labels,predicted,zero_division=0)),
            'macro_f1':float(f1_score(labels,predicted,labels=[0,1],average='macro',zero_division=0)),
            'micro_f1':float(f1_score(labels,predicted,labels=[0,1],average='micro',zero_division=0)),
            'confusion_matrix_true_rows_0_1':confusion_matrix(labels,predicted,labels=[0,1]).tolist(),
            'threshold':float(threshold),'not_computable_reason':None if two else 'Fewer than two classes.'}


def fit_model(matrix, labels, seed):
    if len(set(labels))<2:
        raise ValueError('Training labels have only one class; do not silently redraw split')
    model=make_pipeline(StandardScaler(),LogisticRegression(C=1.0,class_weight='balanced',
                        solver='liblinear',random_state=seed,max_iter=1000))
    model.fit(matrix,labels)
    return model


def grouped_auc_difference(rows, method, reference, seed, samples=1000):
    groups=sorted({r['group_id'] for r in rows})
    by_group={group:[r for r in rows if r['group_id']==group] for group in groups}
    rng=np.random.default_rng(seed)
    values=[]
    for _ in range(samples):
        sampled=[r for group in rng.choice(groups,size=len(groups),replace=True) for r in by_group[group]]
        labels=[r['label'] for r in sampled]
        if len(set(labels))<2:
            continue
        values.append(float(roc_auc_score(labels,[r['scores'][method] for r in sampled])-
                            roc_auc_score(labels,[r['scores'][reference] for r in sampled])))
    return {'valid_resamples':len(values),'requested_resamples':samples,
            'percentile_ci_95':np.quantile(values,[0.025,0.975]).tolist() if values else None,
            'unit':'source_group','note':'Exploratory development bootstrap, not held-out confirmatory evidence.'}
