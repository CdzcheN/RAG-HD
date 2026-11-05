"""Evaluate user-confirmed repair labels against predictions frozen before confirmation."""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from rag_hd.evaluation import valid_risk
from rag_hd.io import file_sha256, fingerprint, read_jsonl, write_json
from rag_hd.learning import metrics, grouped_auc_difference
from rag_hd.schema import visible_input

SEEDS = (13, 42, 2026)


def evaluate(run, output):
    confirmation = json.loads((run/'review_confirmation.json').read_text())
    if (confirmation['status'] != 'user_confirmed' or
            confirmation['confirmed_review_sha256'] != file_sha256(run/'confirmed_review.jsonl') or
            confirmation['reviewed_table_sha256'] != file_sha256(run/'review_readable.csv') or
            confirmation['construction_table_sha256'] != file_sha256(run/'construction_review.csv')):
        raise ValueError('Require intact user-confirmed tables and imported labels')
    records = read_jsonl(run/'records.jsonl')
    reviews = {r['sample_id']: r for r in read_jsonl(run/'confirmed_review.jsonl')}
    if len(reviews) != len(records) or len({r['sample_id'] for r in records}) != len(records):
        raise ValueError('Missing or duplicate reviewed records')
    features = json.loads((output/'feature_manifest.json').read_text())
    frozen = json.loads((output/'frozen_prediction_manifest.json').read_text())
    # Importing labels changes records.jsonl, but the feature snapshot refers to its pre-import copy.
    original = run/'provenance/before_review_confirmation_20261105/records.jsonl'
    if (features['source_records_sha256'] != file_sha256(original) or
            features['feature_cache_sha256'] != file_sha256(output/'valid_evidence_cache.jsonl') or
            frozen['feature_cache_sha256'] != features['feature_cache_sha256'] or
            frozen['prediction_sha256'] != file_sha256(output/'frozen_predictions.jsonl')):
        raise ValueError('Prediction or feature snapshot changed')
    for path, digest in frozen['source_model_files_sha256'].items():
        if file_sha256(Path(path)) != digest:
            raise ValueError('Frozen model or threshold changed')
    cached = {r['sample_id']: r for r in read_jsonl(output/'valid_evidence_cache.jsonl')}
    before = {r['sample_id']: r for r in read_jsonl(original)}
    for record in records:
        sid = record['sample_id']
        if (record['evidence_label'] != reviews[sid]['evidence_label'] or
                record['answer_correctness'] != reviews[sid]['answer_correctness'] or
                visible_input(record) != visible_input(before[sid]) or
                record['answer'] != before[sid]['answer'] or
                record['minicheck'] != before[sid]['minicheck'] or
                record['self_check'] != before[sid]['self_check'] or
                cached[sid]['visible_input_sha256'] != fingerprint(visible_input(record)) or
                cached[sid]['answer_sha256'] != fingerprint(record['answer'])):
            raise ValueError('Reviewed content or frozen method inputs changed')
    predictions = read_jsonl(output/'frozen_predictions.jsonl')
    indexed = {(r['seed'], r['sample_id']): r for r in predictions}
    if len(indexed) != len(predictions) or set(indexed) != {(s, r['sample_id']) for s in SEEDS for r in records}:
        raise ValueError('Incomplete, duplicate or unknown frozen predictions')
    methods = sorted(predictions[0]['scores'])
    source = Path(frozen['source_models'])
    thresholds = {}
    for seed in SEEDS:
        old = json.loads((source/f'seed_{seed}/metrics.json').read_text())
        thresholds[seed] = {m: old['methods'][m]['validation']['threshold'] for m in methods}
        for record in records:
            row = indexed[seed, record['sample_id']]
            if set(row['scores']) != set(methods) or row['frozen_validation_thresholds'] != thresholds[seed]:
                raise ValueError('Method set or threshold differs from frozen validation artifacts')
            for method, expected in [('self_check', record['self_check']['risk']),
                                     ('minicheck', record['minicheck']['risk']),
                                     ('valid_evidence_minicheck', cached[record['sample_id']]['filtered_risk'])]:
                if row['scores'][method] != expected:
                    raise ValueError('Baseline prediction mismatch')
    common = [r for r in records if not r['is_refusal'] and r['evidence_label'] != 'undetermined'
              and all(valid_risk(indexed[s, r['sample_id']]['scores'][m]) for s in SEEDS for m in methods)]
    quality = read_jsonl(run/'confirmed_construction.jsonl')
    basic = {r['pair_id'] for r in quality if r['basic']}
    reports = []
    for seed in SEEDS:
        def report(rows):
            labels = [int(r['evidence_label'] != 'supported') for r in rows]
            return {m: metrics(labels, [indexed[seed, r['sample_id']]['scores'][m] for r in rows],
                               thresholds[seed][m]) for m in methods} if rows else None
        bootstrap_rows = [{'group_id': r['group_id'], 'label': int(r['evidence_label'] != 'supported'),
                           'scores': indexed[seed, r['sample_id']]['scores']} for r in common]
        contrasts = {}
        for method, reference in [('valid_evidence_minicheck', 'minicheck'),
                                  ('logreg_all', 'minicheck'), ('logreg_all', 'valid_evidence_minicheck')]:
            contrasts[method+'_minus_'+reference] = grouped_auc_difference(bootstrap_rows, method, reference, seed)
        result = {'seed': seed, 'overall': report(common),
                  'by_condition': {k: report([r for r in common if r['condition'] == k])
                                   for k in sorted({r['condition'] for r in records})},
                  'by_challenge_type_including_normal_pair': {
                      k: report([r for r in common if r['challenge_type'] == k])
                      for k in sorted({r['challenge_type'] for r in records})},
                  'basic_construction_sensitivity': report([r for r in common if r['pair_id'] in basic]),
                  'paired_group_bootstrap': contrasts}
        write_json(output/f'confirmed_seed_{seed}_metrics.json', result)
        reports.append(result)
    summary = {'status': 'user_confirmed_frozen_evaluation_complete', 'total_rows': len(records),
               'refusals': sum(r['is_refusal'] for r in records),
               'label_counts': dict(Counter(r['evidence_label'] for r in records)),
               'common_rows': len(common), 'positive_rows': sum(r['evidence_label'] != 'supported' for r in common),
               'common_coverage': len(common)/len(records), 'score_missing_on_all_inputs': {
                   str(s): {m: sum(not valid_risk(indexed[s, r['sample_id']]['scores'][m]) for r in records)
                            for m in methods} for s in SEEDS},
               'threshold_origin': 'original development validation sets only; never selected on repair labels',
               'annotation_origin': confirmation['annotation_origin'], 'independent_double_annotation': False,
               'seeds_change': 'Existing training models; all seeds evaluated on the same 60 repair inputs',
               'formal_held_out_test': False, 'new_fit_calls': 0, 'methods': {}}
    for method in methods:
        summary['methods'][method] = {}
        for metric in ('roc_auc', 'average_precision', 'macro_f1', 'micro_f1', 'precision', 'recall'):
            values = [r['overall'][method][metric] for r in reports]
            summary['methods'][method][metric] = {'values': values, 'mean': float(np.mean(values)),
                                                'sample_std': float(np.std(values, ddof=1))} if all(v is not None for v in values) else {'values': values, 'mean': None, 'sample_std': None}
    summary['limitations'] = ['Only three positive labels; construction-repair development check, not a final independent test.',
                              'Bootstrap conditions on this batch; seed results share the same evaluation rows.',
                              'Do not use a t-test across repeated baseline AUCs as independent test evidence.']
    write_json(output/'confirmed_comparison.json', summary)
    with (output/'方法比较.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['种子', '方法', '共同评估数', '幻觉数', 'ROC-AUC', 'AP', '旧验证阈值', 'Precision', 'Recall', 'Macro-F1', 'Micro-F1', 'TN', 'FP', 'FN', 'TP'])
        for report in reports:
            for method, scores in report['overall'].items():
                matrix = scores['confusion_matrix_true_rows_0_1']
                writer.writerow([report['seed'], method, scores['rows'], scores['positives'], scores['roc_auc'],
                                 scores['average_precision'], scores['threshold'], scores['precision'], scores['recall'],
                                 scores['macro_f1'], scores['micro_f1'], *matrix[0], *matrix[1]])
    with (run/'review_readable.csv').open(encoding='utf-8-sig', newline='') as stream:
        display = list(csv.DictReader(stream))
    with (output/'逐条比较.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['编号', '条件', '证据支持标签', '答案正确性', '进入共同评估', '生成回答', '自评风险', '原MiniCheck风险', '有效证据风险', '判定依据'])
        included = {r['sample_id'] for r in common}
        for number, (record, row) in enumerate(zip(records, display), 1):
            scores = indexed[42, record['sample_id']]['scores']
            writer.writerow([number, record['condition'], record['evidence_label'], record['answer_correctness'],
                             record['sample_id'] in included, record['answer'], scores['self_check'], scores['minicheck'],
                             scores['valid_evidence_minicheck'], row['判断依据']])
    write_json(output/'confirmed_evaluation_manifest.json', {
        'confirmed_records_sha256': file_sha256(run/'records.jsonl'),
        'confirmation_sha256': file_sha256(run/'review_confirmation.json'),
        'frozen_prediction_sha256': file_sha256(output/'frozen_predictions.jsonl'),
        'common_sample_ids': [r['sample_id'] for r in common], 'seeds': list(SEEDS),
        'evaluation_source_sha256': file_sha256(Path(__file__)), 'new_fit_calls': 0})
    print(json.dumps({k: v for k, v in summary.items() if k != 'methods'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    evaluate(args.run_dir, args.output_dir)
