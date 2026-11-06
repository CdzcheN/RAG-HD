"""Train the first evidence-policy MiniCheck extension on a reviewed development pilot."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
import numpy as np
import joblib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from rag_hd.evaluation import evaluate, valid_risk
from rag_hd.io import file_sha256, fingerprint, read_jsonl, write_json, write_jsonl
from rag_hd.learning import split_groups, choose_threshold, fit_model, metrics, grouped_auc_difference
from rag_hd.schema import visible_input
from rag_hd.valid_evidence import GROUPS


VARIANTS={'minicheck_logreg':['base'], 'logreg_all':['base','lexical','authority','time'],
          'without_lexical':['base','authority','time'], 'without_authority':['base','lexical','time'],
          'without_time':['base','lexical','authority']}


def train(run, output):
    records=read_jsonl(run/'records.jsonl')
    confirmation=json.loads((run/'review_confirmation.json').read_text())
    if confirmation['status']!='user_confirmed' or file_sha256(run/'confirmed_review.jsonl')!=confirmation['confirmed_review_sha256']:
        raise ValueError('Confirmed review is required')
    cache=read_jsonl(output/'valid_evidence_cache.jsonl')
    cached={r['sample_id']:r for r in cache}
    if len(cached)!=len(records):
        raise ValueError('Incomplete or duplicate features')
    for record in records:
        feature=cached[record['sample_id']]
        if feature['answer_sha256']!=fingerprint(record['answer']) or feature['visible_input_sha256']!=fingerprint(visible_input(record)):
            raise ValueError('Stale feature input or answer')
    common=[r for r in records if not r['is_refusal'] and r['evidence_label']!='undetermined'
            and all(valid_risk(r[m].get('risk')) for m in ('minicheck','self_check'))
            and valid_risk(cached[r['sample_id']]['filtered_risk'])]
    quality=read_jsonl(run/'confirmed_construction.jsonl')
    basic={r['pair_id'] for r in quality if r['basic']}
    write_json(output/'baseline_comparison.json',{
        'all_confirmed':evaluate(records),
        'basic_construction_sensitivity':evaluate([r for r in records if r['pair_id'] in basic]),
        'by_condition':{name:evaluate([r for r in records if r['condition']==name]) for name in sorted({r['condition'] for r in records})},
        'construction_selection_rule':'basic finding fixed by score-blind reviewed construction notes; both pair members kept/excluded together'})
    summaries=[]
    for seed in (13,42,2026):
        directory=output/f'seed_{seed}'
        directory.mkdir(exist_ok=True)
        split=split_groups(records,seed)
        write_json(directory/'groups.json',split)
        cohorts={name:[r for r in common if r['group_id'] in groups] for name,groups in split.items()}
        counts={name:{'all_groups':len(split[name]),'labeled_rows':len(rows),
                      'positive_labels':sum(r['evidence_label']!='supported' for r in rows)} for name,rows in cohorts.items()}
        if any(not rows for rows in cohorts.values()):
            raise ValueError('Empty development split; do not silently choose another seed')
        labels={name:[int(r['evidence_label']!='supported') for r in rows] for name,rows in cohorts.items()}
        scores={name:{} for name in cohorts}
        for name,rows in cohorts.items():
            scores[name]['self_check']=[r['self_check']['risk'] for r in rows]
            scores[name]['minicheck']=[r['minicheck']['risk'] for r in rows]
            scores[name]['valid_evidence_minicheck']=[cached[r['sample_id']]['filtered_risk'] for r in rows]
        coefficients={}
        for variant,groups in VARIANTS.items():
            fields=[field for group in groups for field in GROUPS[group]]
            matrix={name:np.array([[cached[r['sample_id']]['features'][field] for field in fields] for r in rows],dtype=float) for name,rows in cohorts.items()}
            if any(not np.isfinite(values).all() for values in matrix.values()):
                raise ValueError('Nonfinite features')
            model=fit_model(matrix['train'],labels['train'],seed)
            joblib.dump({'model':model,'feature_names':fields,'seed':seed,'purpose':'development_only'},directory/(variant+'.joblib'))
            coefficients[variant]={'features':fields,'standardized_coefficients':model[-1].coef_[0].tolist(),
                                   'intercept':model[-1].intercept_.tolist(),
                                   'scaler_train_mean':model[0].mean_.tolist()}
            for name in cohorts:
                scores[name][variant]=model.predict_proba(matrix[name])[:,1].tolist()
        thresholds={method:choose_threshold(labels['validation'],values) for method,values in scores['validation'].items()}
        method_reports={}
        predictions=[]
        for name,rows in cohorts.items():
            for index,r in enumerate(rows):
                predictions.append({'sample_id':r['sample_id'],'group_id':r['group_id'],'pair_id':r['pair_id'],
                                    'split':name,'label':labels[name][index],
                                    'scores':{m:v[index] for m,v in scores[name].items()},
                                    'construction_basic':r['pair_id'] in basic})
        tests=[r for r in predictions if r['split']=='test']
        for method in scores['test']:
            threshold,rule=thresholds[method]
            method_reports[method]={'threshold_rule':rule,
                                   'validation':metrics(labels['validation'],scores['validation'][method],threshold),
                                   'test':metrics(labels['test'],scores['test'][method],threshold)}
            sub=[r for r in tests if r['construction_basic']]
            method_reports[method]['basic_construction_test']=metrics([r['label'] for r in sub],[r['scores'][method] for r in sub],threshold) if sub else None
        comparisons={reference:grouped_auc_difference(tests,'logreg_all',reference,seed) for reference in ('self_check','minicheck')}
        write_jsonl(directory/'predictions.jsonl',predictions)
        write_json(directory/'coefficients.json',coefficients)
        result={'seed':seed,'split_counts':counts,'methods':method_reports,'paired_group_bootstrap':comparisons,
                'split_unit':'source_group','threshold_fit':'validation only','scaler_and_logreg_fit':'train only',
                'formal_held_out_test':False,'note':'All pilot labels informed development; these are exploratory internal partitions.'}
        write_json(directory/'metrics.json',result)
        summaries.append(result)
    aggregate={}
    for method in summaries[0]['methods']:
        for metric in ('roc_auc','average_precision','macro_f1'):
            values=[r['methods'][method]['test'][metric] for r in summaries]
            valid=[v for v in values if v is not None]
            aggregate.setdefault(method,{})[metric]={'values':values,'mean':float(np.mean(valid)) if valid else None,
                                                   'sample_std':float(np.std(valid,ddof=1)) if len(valid)>1 else None}
    result={'purpose':'Exploratory method development on user-reviewed pilot; no final gain claim.',
            'source_rows':len(records),'common_labeled_rows':len(common),'seeds':[13,42,2026],
            'methods':aggregate,'C':1.0,'class_weight':'balanced','solver':'liblinear',
            'feature_groups':GROUPS,'variants':VARIANTS,'hyperparameter_search':False,
            'new_generator_calls':0,'formal_test_claim':False,
            'source_records_sha256':file_sha256(run/'records.jsonl'),
            'feature_cache_sha256':file_sha256(output/'valid_evidence_cache.jsonl')}
    write_json(output/'summary.json',result)
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    train(args.run_dir,args.output_dir)
