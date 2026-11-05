"""Evaluate confirmed final-test labels against immutable frozen predictions."""
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
from rag_hd.formal_gate import validate_test_freeze
from rag_hd.formal_learning import require_confirmation, validated_features, VARIANTS
from rag_hd.formal_statistics import paired_contrast, holm_adjust
from rag_hd.io import file_sha256, read_jsonl, write_json
from rag_hd.learning import metrics
from rag_hd.schema import visible_input

SEEDS = (13, 42, 2026)
METHODS = ('self_check', 'minicheck', 'valid_evidence_minicheck', *VARIANTS)


def validate_predictions(records, predictions, thresholds, cache):
    indexed = {(r['seed'], r['sample_id']): r for r in predictions}
    expected = {(seed, r['sample_id']) for seed in SEEDS for r in records}
    if len(indexed) != len(predictions) or set(indexed) != expected:
        raise ValueError('Incomplete, duplicate or unknown frozen predictions')
    for seed in SEEDS:
        for record in records:
            sid = record['sample_id']
            row = indexed[seed, sid]
            if (set(row['scores']) != set(METHODS) or
                    row['frozen_validation_thresholds'] != thresholds[seed]):
                raise ValueError('Frozen method set or validation thresholds changed')
            expected_baselines = {'self_check': record['self_check']['risk'],
                                  'minicheck': record['minicheck']['risk'],
                                  'valid_evidence_minicheck': cache[sid]['filtered_risk']}
            if any(row['scores'][m] != value for m, value in expected_baselines.items()):
                raise ValueError('Immutable baseline predictions changed')
            for method, score in row['scores'].items():
                if score is not None and not valid_risk(score):
                    raise ValueError('Invalid predicted risk')
                expected_label = None if score is None else bool(score >= thresholds[seed][method])
                if row['predicted_hallucination'][method] != expected_label:
                    raise ValueError('Frozen classification changed')
    common = [r for r in records if not r['is_refusal'] and r['evidence_label'] != 'undetermined'
              and all(valid_risk(indexed[seed, r['sample_id']]['scores'][m])
                      for seed in SEEDS for m in METHODS)]
    return indexed, common


def metric_report(labels, scores, threshold):
    if not labels:
        return {'rows': 0, 'positives': 0, 'roc_auc': None, 'average_precision': None,
                'precision': None, 'recall': None, 'macro_f1': None, 'micro_f1': None,
                'threshold': threshold, 'confusion_matrix_true_rows_0_1': [[0, 0], [0, 0]],
                'not_computable_reason': 'No common factual rows'}
    return metrics(labels, scores, threshold)


def evaluate(run, output, report_dir, samples=10000):
    run, output, report_dir = Path(run).resolve(), Path(output).resolve(), Path(report_dir).resolve()
    certificate = validate_test_freeze(run)
    records = read_jsonl(run/'records.jsonl')
    if len(records) != 120 or len({r['sample_id'] for r in records}) != 120:
        raise ValueError('Require exactly the final 120 records')
    confirmation = require_confirmation(run, records)
    reviewed = {r['sample_id']: r for r in read_jsonl(run/'confirmed_review.jsonl')}
    for row in records:
        review = reviewed[row['sample_id']]
        if row['answer_correctness'] != review['answer_correctness'] or row['rationale'] != review['rationale']:
            raise ValueError('Confirmed correctness or rationale differs from imported records')
    original_path = run/'provenance/before_review_confirmation_20261105/records.jsonl'
    before = {r['sample_id']: r for r in read_jsonl(original_path)}
    frozen = json.loads((output/'frozen_prediction_manifest.json').read_text())
    features = json.loads((output/'feature_manifest.json').read_text())
    if (frozen['test_records_sha256'] != file_sha256(original_path) or
            features['source_records_sha256'] != file_sha256(original_path) or
            frozen['prediction_sha256'] != file_sha256(output/'frozen_predictions.jsonl') or
            frozen['model_freeze_sha256'] != file_sha256(run/'model_freeze.json') or
            frozen['fit_calls'] != 0 or frozen['threshold_selection_calls'] != 0 or frozen['label_inputs_used']):
        raise ValueError('Pre-confirmation feature/prediction provenance changed')
    immutable_fields = ('sample_id', 'pair_id', 'group_id', 'base_question_id', 'condition',
                        'challenge_type', 'dataset', 'audit', 'construction', 'question',
                        'visible_evidence', 'answer', 'generation', 'is_refusal', 'self_check', 'minicheck')
    for row in records:
        if any(row[key] != before[row['sample_id']][key] for key in immutable_fields):
            raise ValueError('Answer, source, grouping or detector inputs changed at confirmation')
    cache = validated_features(run, output, records, ROOT)
    model_dir = output.parent/'formal_training'
    thresholds = {}
    for seed in SEEDS:
        path = model_dir/f'seed_{seed}/metrics.json'
        if certificate['artifacts_sha256'].get(str(path)) != file_sha256(path):
            raise ValueError('Thresholds do not belong to frozen validation artifacts')
        trained = json.loads(path.read_text())
        thresholds[seed] = {m: trained['methods'][m]['validation']['threshold'] for m in METHODS}
    indexed, common = validate_predictions(records, read_jsonl(output/'frozen_predictions.jsonl'), thresholds, cache)
    assignments = {r['base_question_id']: r for r in read_jsonl(run.parent.parent/'frozen_rule_assignments.jsonl')}
    exposure = {}
    for row in records:
        assignment = assignments[row['base_question_id']]
        if assignment['family'] != row['audit']['rule_family'] or assignment['planned_split'] != 'test':
            raise ValueError('Rule-family grouping changed from the frozen prepared inputs')
        exposure[row['sample_id']] = assignment['exposure']
    quality = read_jsonl(run/'confirmed_construction.jsonl')
    quality_by_pair = {r['pair_id']: r for r in quality}
    if len(quality_by_pair) != 60 or set(quality_by_pair) != {r['pair_id'] for r in records}:
        raise ValueError('Construction reviews must cover all 60 pairs')
    with (run/'construction_review.csv').open(encoding='utf-8-sig', newline='') as stream:
        reviewed_quality = {int(r['编号']): r['构造检查备注'] for r in csv.DictReader(stream)}
    for row in quality:
        if reviewed_quality[row['display_number']] != row['rationale']:
            raise ValueError('Construction finding differs from the confirmed table')
    groups = {
        'condition': lambda r: r['condition'],
        'challenge_type_including_normal_pair': lambda r: r['challenge_type'],
        'dataset': lambda r: r['dataset'],
        'rule_exposure': lambda r: exposure[r['sample_id']],
        'construction_quality': lambda r: quality_by_pair[r['pair_id']]['finding'],
        'condition_and_rule': lambda r: r['condition']+' / '+exposure[r['sample_id']]}

    def cohort_report(rows):
        ids = {r['sample_id'] for r in rows}
        cohort = [r for r in common if r['sample_id'] in ids]
        labels = [int(r['evidence_label'] != 'supported') for r in cohort]
        return {'input_rows': len(rows), 'source_pairs': len({r['pair_id'] for r in rows}),
                'refusals': sum(r['is_refusal'] for r in rows),
                'undetermined': sum(r['evidence_label'] == 'undetermined' for r in rows),
                'label_counts': dict(Counter(r['evidence_label'] for r in rows)),
                'common_rows': len(cohort), 'positive_rows': sum(labels),
                'common_coverage': len(cohort)/len(rows) if rows else None,
                'seeds': {str(seed): {m: metric_report(labels, [indexed[seed, r['sample_id']]['scores'][m]
                                                             for r in cohort], thresholds[seed][m])
                                      for m in METHODS} for seed in SEEDS}}

    overall = cohort_report(records)
    grouped = {name: {key: cohort_report([r for r in records if extract(r) == key])
                      for key in sorted({extract(r) for r in records})} for name, extract in groups.items()}
    aggregates = {}
    for method in METHODS:
        aggregates[method] = {}
        for metric in ('roc_auc', 'average_precision', 'precision', 'recall', 'macro_f1', 'micro_f1'):
            values = [overall['seeds'][str(seed)][method][metric] for seed in SEEDS]
            valid = [v for v in values if v is not None]
            aggregates[method][metric] = {'values': values, 'mean': float(np.mean(valid)) if valid else None,
                                         'sample_std': float(np.std(valid, ddof=1)) if len(valid) > 1 else None}
    labels = [int(r['evidence_label'] != 'supported') for r in common]
    source_groups = sorted({r['group_id'] for r in records})
    row_groups = [r['group_id'] for r in common]
    contrasts = {}
    for reference in ('minicheck', 'self_check'):
        # These three methods have identical risk vectors across model seeds.
        for method in ('valid_evidence_minicheck', reference):
            if any(indexed[s, r['sample_id']]['scores'][method] != indexed[13, r['sample_id']]['scores'][method]
                   for s in SEEDS for r in common):
                raise ValueError('Seed-independent baseline risks differ across seeds')
        contrasts['valid_evidence_minicheck_minus_'+reference] = paired_contrast(
            labels, [indexed[13, r['sample_id']]['scores']['valid_evidence_minicheck'] for r in common],
            [indexed[13, r['sample_id']]['scores'][reference] for r in common],
            row_groups, source_groups, samples=samples, seed=20260920)
    available = [key for key, result in contrasts.items() if result['computable']]
    adjusted = holm_adjust([contrasts[key]['permutation_p_two_sided'] for key in available])
    for key, value in zip(available, adjusted): contrasts[key]['permutation_p_holm_two_main_comparisons'] = value
    report = {'status': 'confirmed_final_test_evaluation_complete', 'overall': overall,
              'groups': grouped, 'method_seed_aggregates': aggregates, 'primary_contrasts': contrasts,
              'fit_calls': 0, 'threshold_selection_calls': 0, 'threshold_origin': 'formal_validation_only',
              'annotation_origin': confirmation['annotation_origin'], 'independent_double_annotation': False,
              'source_group_bootstrap_samples': samples, 'analysis_seed': 20260920,
              'seeds_share_same_test': True, 'construction_groups_selected_for_main_analysis': False,
              'limitations': ['Controlled numeric/statistical scenarios, not natural open-domain hallucinations.',
                              f'{sum(labels)} positive test labels; some subgroups have only one class.',
                              'Assistant drafts confirmed by the user are not independent double annotation.',
                              'Independent stratified human audit completion has not been established.',
                              'Three training seeds share the same test sources; no independent-seed t-test.']}
    report_dir.mkdir(parents=True, exist_ok=True)
    write_json(report_dir/'final_comparison.json', report)
    fields = ['分组维度', '分组', '种子', '方法', '输入数', '共同评估数', '幻觉数', 'ROC-AUC', 'AP',
              '验证阈值', 'Precision', 'Recall', 'Macro-F1', 'Micro-F1', 'TN', 'FP', 'FN', 'TP']
    with (report_dir/'方法与分组比较.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.writer(stream); writer.writerow(fields)
        for dimension, name, result in [('overall', 'all', overall),
                                        *((dim, name, value) for dim, values in grouped.items() for name, value in values.items())]:
            for seed in SEEDS:
                for method, scores in result['seeds'][str(seed)].items():
                    cm = scores['confusion_matrix_true_rows_0_1']
                    writer.writerow([dimension, name, seed, method, result['input_rows'], result['common_rows'],
                                     result['positive_rows'], scores['roc_auc'], scores['average_precision'], scores['threshold'],
                                     scores['precision'], scores['recall'], scores['macro_f1'], scores['micro_f1'], *cm[0], *cm[1]])
    included = {r['sample_id'] for r in common}
    with (report_dir/'逐条冻结预测对比.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['编号', '条件', '规则措辞组', '标签', '答案正确性', '进入共同评估', '生成回答', '种子',
                         *[f'{m}风险' for m in METHODS], *[f'{m}判为幻觉' for m in METHODS]])
        for number, row in enumerate(records, 1):
            for seed in SEEDS:
                prediction = indexed[seed, row['sample_id']]
                writer.writerow([number, row['condition'], exposure[row['sample_id']], row['evidence_label'],
                                 row['answer_correctness'], row['sample_id'] in included, row['answer'], seed,
                                 *[prediction['scores'][m] for m in METHODS],
                                 *[prediction['predicted_hallucination'][m] for m in METHODS]])
    validate_test_freeze(run)
    write_json(report_dir/'evaluation_manifest.json', {
        'test_confirmation_sha256': file_sha256(run/'review_confirmation.json'),
        'confirmed_records_sha256': file_sha256(run/'records.jsonl'),
        'frozen_prediction_sha256': file_sha256(output/'frozen_predictions.jsonl'),
        'model_freeze_sha256': file_sha256(run/'model_freeze.json'),
        'common_sample_ids': [r['sample_id'] for r in common],
        'evaluation_code_sha256': file_sha256(Path(__file__)),
        'statistics_code_sha256': file_sha256(ROOT/'src/rag_hd/formal_statistics.py'),
        'result_sha256': file_sha256(report_dir/'final_comparison.json'), 'fit_calls': 0})
    print(json.dumps({'common_rows': len(common), 'positives': sum(labels),
                      'methods': aggregates, 'primary_contrasts': contrasts}, indent=2))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--report-dir', type=Path, required=True)
    args = parser.parse_args()
    evaluate(args.run_dir, args.output_dir, args.report_dir)
