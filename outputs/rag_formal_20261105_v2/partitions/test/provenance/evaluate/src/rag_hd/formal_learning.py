"""Formal development training using the pre-inference source assignments."""
from collections import Counter, defaultdict
import json
from pathlib import Path

from .io import file_sha256, fingerprint, read_jsonl, write_json, write_jsonl
from .schema import visible_input

SEEDS = ('13', '42', '2026')
VARIANTS = {'minicheck_logreg': ['base'],
            'logreg_all': ['base', 'lexical', 'authority', 'time'],
            'without_lexical': ['base', 'authority', 'time'],
            'without_authority': ['base', 'lexical', 'time'],
            'without_time': ['base', 'lexical', 'authority']}


def validate_assignments(records, splits):
    """Never redraw a split when a source or label is inconvenient."""
    bases = defaultdict(list)
    for row in records:
        bases[row['base_question_id']].append(row)
    if len(records) != 480 or len(bases) != 240:
        raise ValueError('Require exactly 480 development rows / 240 source bases')
    if len({r['sample_id'] for r in records}) != 480:
        raise ValueError('Duplicate sample identity')
    owner = {}
    for base, rows in bases.items():
        if (len(rows) != 2 or len({r['pair_id'] for r in rows}) != 1 or
                len({r['group_id'] for r in rows}) != 1):
            raise ValueError('Both pair members must stay in the same source group')
        group = rows[0]['group_id']
        if group in owner and owner[group] != base:
            raise ValueError('Source group shared across base identities')
        owner[group] = base
    test = None
    for seed in SEEDS:
        parts = splits[seed]
        for part, count in [('train', 180), ('validation', 60), ('test', 60)]:
            if len(parts[part]) != count or len(set(parts[part])) != count:
                raise ValueError('Frozen split counts or unique identities changed')
        train, validation, final = (set(parts[k]) for k in ('train', 'validation', 'test'))
        if train & validation or (train | validation) & final:
            raise ValueError('Overlapping frozen partitions')
        if train | validation != set(bases):
            raise ValueError('Development rows do not match frozen train/validation sources')
        if test is not None and final != test:
            raise ValueError('Final test must be shared across the three seeds')
        test = final
    return {'development_rows': 480, 'development_bases': 240, 'final_test_bases': 60,
            'seeds': list(SEEDS), 'split_recomputed': False}


def require_confirmation(run, records):
    path = run/'review_confirmation.json'
    if not path.exists():
        raise ValueError('User confirmation of actual answers is required before training')
    confirmation = json.loads(path.read_text())
    if confirmation.get('status') != 'user_confirmed':
        raise ValueError('User confirmation of actual answers is required before training')
    files = {'confirmed_review.jsonl': 'confirmed_review_sha256',
             'review_readable.csv': 'reviewed_table_sha256',
             'construction_review.csv': 'construction_table_sha256'}
    for filename, key in files.items():
        if file_sha256(run/filename) != confirmation.get(key):
            raise ValueError('Confirmed review changed; review and confirm the new version')
    reviews = read_jsonl(run/'confirmed_review.jsonl')
    by_id = {r['sample_id']: r for r in reviews}
    if len(by_id) != len(reviews) or set(by_id) != {r['sample_id'] for r in records}:
        raise ValueError('Confirmed reviews must cover every development row')
    for row in records:
        review = by_id[row['sample_id']]
        if (review['answer_sha256'] != fingerprint(row['answer']) or
                review['visible_input_sha256'] != fingerprint(visible_input(row)) or
                review['evidence_label'] != row['evidence_label']):
            raise ValueError('Confirmed labels have not been imported for these answers/inputs')
    return confirmation


def validated_features(run, output, records, root):
    from .valid_evidence import features
    path = output/'valid_evidence_cache.jsonl'
    manifest = json.loads((output/'feature_manifest.json').read_text())
    implementation = {name: file_sha256(root/'src/rag_hd'/name)
                      for name in ('valid_evidence.py', 'minicheck_adapter.py')}
    if (manifest['feature_cache_sha256'] != file_sha256(path) or
            manifest['implementation'] != implementation or manifest['label_inputs_used']):
        raise ValueError('Feature cache or frozen implementation changed')
    values = read_jsonl(path)
    cache = {v['sample_id']: v for v in values}
    if len(cache) != len(values) or set(cache) != {r['sample_id'] for r in records}:
        raise ValueError('Feature cache must cover exactly the development rows')
    config = json.loads((run/'config.json').read_text())
    for row in records:
        value = cache[row['sample_id']]
        public = visible_input(row)
        expected = fingerprint([public, row['answer'], row['minicheck']['risk'],
                                config['minicheck'], implementation])
        if (value['cache_key'] != expected or
                value['answer_sha256'] != fingerprint(row['answer']) or
                value['visible_input_sha256'] != fingerprint(public) or
                value['original_risk'] != row['minicheck']['risk']):
            raise ValueError('Stale feature input, answer or original risk')
        if value['features'] is not None:
            calculated = features(public, row['answer'], value['original_risk'],
                                  value['filtered_risk'], value['selection'])
            if calculated != value['features']:
                raise ValueError('Feature values changed')
    # Importing confirmed labels changes records.jsonl. Cache identities above
    # deliberately cover only public input, answers, baseline and implementation.
    return cache


def train(run, output, root):
    import joblib
    import numpy as np
    from .evaluation import valid_risk
    from .learning import choose_threshold, fit_model, metrics
    from .valid_evidence import GROUPS
    run, output, root = Path(run).resolve(), Path(output).resolve(), Path(root).resolve()
    if json.loads((run/'data_manifest.json').read_text()).get('execution_partition') != 'development':
        raise ValueError('Formal training accepts only the development execution package')
    records = read_jsonl(run/'records.jsonl')
    master = run.parent.parent
    splits_path = master/'frozen_splits.json'
    splits = json.loads(splits_path.read_text())
    validate_assignments(records, splits)
    confirmation = require_confirmation(run, records)
    cache = validated_features(run, output, records, root)
    common = [r for r in records if not r['is_refusal'] and r['evidence_label'] != 'undetermined'
              and all(valid_risk(r[m].get('risk')) for m in ('self_check', 'minicheck'))
              and valid_risk(cache[r['sample_id']]['filtered_risk'])
              and cache[r['sample_id']]['features'] is not None]
    cohorts = {seed: {part: [r for r in common if r['base_question_id'] in set(splits[seed][part])]
                      for part in ('train', 'validation')} for seed in SEEDS}
    for parts in cohorts.values():
        if len({r['evidence_label'] == 'supported' for r in parts['train']}) != 2:
            raise ValueError('Training has fewer than two classes; do not redraw frozen splits')
        if not parts['validation']:
            raise ValueError('Empty validation; do not redraw frozen splits')
    test_run = run.parent/'test'
    test_ids = sorted({r['base_question_id'] for r in read_jsonl(test_run/'prepared.jsonl')})
    if set(test_ids) != set(splits['13']['test']):
        raise ValueError('Held-out test identities changed')
    if (test_run/'model_freeze.json').exists():
        raise ValueError('A model freeze already exists; preserve it and its experiment')
    directory = output/'formal_training'
    directory.mkdir(exist_ok=False)
    artifacts = {}
    reports = []
    for seed, parts in cohorts.items():
        dest = directory/f'seed_{seed}'
        dest.mkdir()
        write_json(dest/'assignments.json', {k: splits[seed][k] for k in ('train', 'validation')})
        labels = {part: [int(r['evidence_label'] != 'supported') for r in rows]
                  for part, rows in parts.items()}
        scores = {part: {'self_check': [r['self_check']['risk'] for r in rows],
                         'minicheck': [r['minicheck']['risk'] for r in rows],
                         'valid_evidence_minicheck': [cache[r['sample_id']]['filtered_risk'] for r in rows]}
                  for part, rows in parts.items()}
        for variant, groups in VARIANTS.items():
            fields = [f for group in groups for f in GROUPS[group]]
            matrix = {part: np.array([[cache[r['sample_id']]['features'][f] for f in fields]
                                      for r in rows], dtype=float) for part, rows in parts.items()}
            if any(not np.isfinite(x).all() for x in matrix.values()):
                raise ValueError('Nonfinite model features')
            model = fit_model(matrix['train'], labels['train'], int(seed))
            joblib.dump({'model': model, 'feature_names': fields, 'seed': int(seed),
                         'purpose': 'formal_train_only'}, dest/(variant+'.joblib'))
            for part in parts:
                scores[part][variant] = model.predict_proba(matrix[part])[:, 1].tolist()
        methods = {}
        for name, values in scores['validation'].items():
            threshold, rule = choose_threshold(labels['validation'], values)
            methods[name] = {'threshold_rule': rule,
                             'validation': metrics(labels['validation'], values, threshold)}
        predictions = [{'sample_id': r['sample_id'], 'base_question_id': r['base_question_id'],
                        'split': part, 'label': labels[part][i],
                        'scores': {name: values[i] for name, values in scores[part].items()}}
                       for part, rows in parts.items() for i, r in enumerate(rows)]
        write_jsonl(dest/'development_predictions.jsonl', predictions)
        report = {'seed': int(seed), 'methods': methods,
                  'cohort_counts': {part: {'rows': len(rows), 'positives': sum(labels[part])}
                                    for part, rows in parts.items()},
                  'scaler_and_model_fit': 'formal_train_only',
                  'threshold_origin': 'formal_validation_only', 'final_test_evaluated': False}
        write_json(dest/'metrics.json', report)
        reports.append(report)
    summary = {'status': 'formal_models_and_thresholds_frozen', 'seeds': list(SEEDS),
               'common_development_rows': len(common), 'all_development_rows': len(records),
               'labels': dict(Counter(r['evidence_label'] for r in common)),
               'variant_groups': VARIANTS, 'hyperparameter_search': False,
               'annotation_origin': confirmation.get('annotation_origin'),
               'independent_double_annotation': False, 'final_test_evaluated': False,
               'seed_reports': reports}
    write_json(directory/'summary.json', summary)
    for path in directory.rglob('*'):
        if path.is_file(): artifacts[str(path)] = file_sha256(path)
    for path in [splits_path, run/'confirmed_review.jsonl', run/'config.json', test_run/'prepared.jsonl',
                 output/'valid_evidence_cache.jsonl', output/'feature_manifest.json',
                 root/'src/rag_hd/learning.py', root/'src/rag_hd/formal_learning.py',
                 root/'src/rag_hd/valid_evidence.py', root/'src/rag_hd/minicheck_adapter.py',
                 root/'src/rag_hd/generation.py', root/'src/rag_hd/self_check.py',
                 root/'scripts/rag_prototype.py', root/'scripts/extract_valid_evidence.py',
                 root/'scripts/predict_formal_frozen.py', root/'scripts/run_rag_formal_test.sh',
                 root/'项目资料/正式测试分析方案.md']:
        artifacts[str(path)] = file_sha256(path)
    certificate = {'protocol_version': 'formal-model-freeze-v1',
                   'threshold_origin': 'formal_validation_only',
                   'final_test_ids_sha256': fingerprint(test_ids),
                   'development_confirmation_sha256': file_sha256(run/'review_confirmation.json'),
                   'development_records_sha256': file_sha256(run/'records.jsonl'),
                   'development_splits': splits, 'artifacts_sha256': artifacts}
    write_json(test_run/'model_freeze.json', certificate)
    from .formal_gate import validate_test_freeze
    validate_test_freeze(test_run)
    return summary
