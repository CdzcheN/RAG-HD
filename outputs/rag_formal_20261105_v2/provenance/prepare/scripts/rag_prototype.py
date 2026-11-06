"""Pinned local RAG pilot. Stages run separately to release GPU memory."""
import argparse
import csv
from datetime import datetime, timezone
from importlib.metadata import version
import json
from pathlib import Path
import subprocess
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rag_hd.io import file_sha256, fingerprint, load_config, read_jsonl, write_json, write_jsonl


def status(run, stage):
    write_json(run / "status.json", {"stage": stage, "updated_at_utc": datetime.now(timezone.utc).isoformat()})
    print(stage, flush=True)


def prepare(config, run):
    if config.get('challenge'):
        if config['challenge']['protocol_version']=='controlled-challenge-formal-v1':
            from rag_hd.formal_cleaning import prepare as prepare_formal
            return prepare_formal(config,run,ROOT)
        if config['challenge']['protocol_version']=='controlled-challenge-v2':
            from rag_hd.challenges_v2 import prepare as prepare_v2
            return prepare_v2(config,run,ROOT)
        from rag_hd.challenges import prepare_challenges
        return prepare_challenges(config, run, ROOT)
    from rag_hd.data import SOURCES, convert_question, read_pool
    from rag_hd.retrieval import Retriever
    from rag_hd.schema import assign_groups, document_dict, evidence_text, validate_record, visible_input
    if config['data']['split'] != 'train':
        raise ValueError('The development pilot uses the original train split only')
    all_documents, selected, sources = {}, [], {}
    for name in SOURCES:
        revision = config['data'][name + '_revision']
        pool, sources[name] = read_pool(name, revision, ROOT / '.cache/rag/hub',
                                        config['data']['pool_per_dataset'], config['seed'])
        questions = []
        for row in pool:
            question, documents = convert_question(name, row, revision)
            questions.append(question)
            for document in documents:
                all_documents.setdefault(document.document_id, document)
        questions.sort(key=lambda row: fingerprint([config['seed'], 'pilot-question', row['base_question_id']]))
        count = config['data']['samples_per_dataset']
        if len(questions) < count:
            raise ValueError('Insufficient pool for sample count')
        selected.extend(questions[:count])
    retrieval = config['retrieval']
    retriever = Retriever(list(all_documents.values()), k1=retrieval['k1'], b=retrieval['b'])
    records = []
    for question in selected:
        evidence = retriever.search(question['question'], retrieval['top_k'],
                                    retrieval['max_words_per_document'], retrieval['max_evidence_words'])
        record = dict(question, evidence=evidence, visible_evidence=evidence_text(evidence),
                      protocol_version=config['protocol_version'], condition='normal',
                      construction={'operation': 'none', 'seed': config['seed']},
                      evidence_label='undetermined')
        record['visible_input_sha256'] = fingerprint(visible_input(record))
        record['sample_id'] = 'sample:' + fingerprint([record['base_question_id'], 'normal', record['visible_input_sha256']])
        visible_by_id = {item['document_id']: ' '.join(item['text'].split()) for item in evidence}
        gold = record['audit']['gold_document_ids']
        record['audit']['gold_document_recall'] = sum(doc in visible_by_id for doc in gold) / len(gold)
        record['audit']['all_gold_support_visible'] = all(
            ' '.join(item['text'].split()) in visible_by_id.get(item['document_id'], '')
            for item in record['audit']['gold_support'])
        records.append(record)
    assign_groups(records)
    for record in records:
        validate_record(record)
    write_jsonl(run / 'prepared.jsonl', records)
    write_jsonl(run / 'corpus.jsonl', [document_dict(doc) for doc in retriever.documents])
    manifest = {'sources': sources, 'seed': config['seed'], 'records': len(records),
                'corpus_documents': len(all_documents), 'groups': len({r['group_id'] for r in records}),
                'corpus_scope': 'Union of contexts of the fixed sampled train pools; this is a closed-corpus development pilot.',
                'prepared_sha256': file_sha256(run / 'prepared.jsonl'),
                'corpus_sha256': file_sha256(run / 'corpus.jsonl'),
                'diagnostic_only_mean_gold_document_recall': sum(r['audit']['gold_document_recall'] for r in records)/len(records)}
    write_json(run / 'data_manifest.json', manifest)
    print(json.dumps(manifest, ensure_ascii=False, indent=2), flush=True)


def generator_key(record, config):
    return fingerprint({'input': record['visible_input_sha256'], 'generation': config['generation'],
                        'seed': config['seed'], 'protocol': config['protocol_version'],
                        'implementation': [file_sha256(ROOT / 'src/rag_hd/generation.py'),
                                           file_sha256(ROOT / 'src/rag_hd/self_check.py')]})


def minicheck_key(record, generated, config):
    return fingerprint([generated['cache_key'], generated['answer'], record['visible_input_sha256'],
                        config['minicheck'], file_sha256(ROOT / 'src/rag_hd/minicheck_adapter.py')])


def cached_rows(path, expected):
    rows = read_jsonl(path) if path.exists() else []
    if len({r['sample_id'] for r in rows}) != len(rows):
        raise ValueError(f'Duplicate cached sample IDs: {path}')
    result = {}
    for row in rows:
        if row['sample_id'] not in expected or row['cache_key'] != expected[row['sample_id']]:
            raise ValueError(f'Stale cache in {path}; use a new run directory')
        result[row['sample_id']] = row
    return result


def validate_assessment(row):
    if 'self_check' in row and row['self_check'].get('answer_sha256') != fingerprint(row['answer']):
        raise ValueError('Cached self-assessment refers to a different answer')


def validate_review_content(review, record, generated):
    if review.get('answer_sha256') != fingerprint(generated['answer']):
        raise ValueError('Review refers to a different answer or lacks its hash')
    if review.get('visible_input_sha256') != record['visible_input_sha256']:
        raise ValueError('Review refers to different visible evidence')
    for field, expected in [('answer',generated['answer']), ('question',record['question']),
                            ('visible_evidence',record['visible_evidence'])]:
        if field in review and review[field] != expected:
            raise ValueError(f'Review {field} was changed; review the original record')


def probe(config, run):
    from rag_hd.generation import LocalGenerator, messages
    from rag_hd.resources import GpuUsage
    from rag_hd.self_check import assess
    records = read_jsonl(run / 'prepared.jsonl')
    measurement = GpuUsage(config['generation']['memory_limit_mib'])
    if config.get('challenge', {}).get('probe_partition') == 'train':
        records = [r for r in records if r.get('formal_split') == 'train']
        if not records:
            raise ValueError('Formal resource probe requires training inputs')
    cases = []
    try:
        with measurement:
            generator = LocalGenerator(config['generation'], ROOT / '.cache/rag/hub', config['seed'])
            records.sort(key=lambda r: generator.inputs(messages(r))['input_ids'].shape[-1])
            for record in [records[0], records[-1]]:
                result = generator.complete(messages(record), config['generation']['max_new_tokens'])
                self_result = assess(generator, record, result['text'], config['generation']['self_retries'])
                cases.append({'sample_id': record['sample_id'], 'generation': result, 'self_check': self_result})
            repeated = generator.complete(messages(records[0]), config['generation']['max_new_tokens'])
            repeat_matches = repeated['text'] == cases[0]['generation']['text']
            # Stress the configured input boundary separately; no diagnostic label is attached.
            stress = dict(records[-1], visible_evidence='Neutral filler.' + ' neutral' * config['generation']['max_input_tokens'])
            while generator.inputs(messages(stress))['input_ids'].shape[-1] > config['generation']['max_input_tokens']:
                excess = generator.inputs(messages(stress))['input_ids'].shape[-1] - config['generation']['max_input_tokens']
                stress['visible_evidence'] = ' '.join(stress['visible_evidence'].split()[:-max(1, excess)])
            stress_result = generator.complete(messages(stress), config['generation']['max_new_tokens'])
            quantized_layers = generator.quantized_layers
    finally:
        if hasattr(measurement, 'result'):
            write_json(run / 'probe_resources.json', measurement.result)
            write_jsonl(run / 'probe_vram_samples.jsonl', measurement.samples)
    report = {'model_id': config['generation']['model_id'], 'revision': config['generation']['revision'],
              'quantized_linear_layers': quantized_layers, 'cases': cases,
              'repeated_generation': repeated, 'repeat_text_matches': repeat_matches,
              'stress_input': stress_result, 'resources': measurement.result,
              'passed': measurement.result['within_limit'] and repeat_matches and
                        all(c['self_check']['status'] == 'ok' for c in cases)}
    write_json(run / 'deployment_probe.json', report)
    print(json.dumps({k: report[k] for k in ('quantized_linear_layers','repeat_text_matches','resources','passed')}, indent=2), flush=True)
    if not report['passed']:
        raise RuntimeError('Local deployment probe failed; see deployment_probe.json')


def generate(config, run):
    from rag_hd.generation import LocalGenerator, messages
    from rag_hd.resources import GpuUsage
    from rag_hd.schema import REFUSAL
    from rag_hd.self_check import assess
    deployment = json.loads((run / 'deployment_probe.json').read_text())
    if not deployment['passed'] or deployment['revision'] != config['generation']['revision']:
        raise ValueError('Deployment probe must pass for this pinned model first')
    records = read_jsonl(run / 'prepared.jsonl')
    expected = {r['sample_id']: generator_key(r, config) for r in records}
    path = run / 'generation.jsonl'
    cached = cached_rows(path, expected)
    for row in cached.values():
        validate_assessment(row)
    if all(r['sample_id'] in cached and 'self_check' in cached[r['sample_id']] for r in records):
        print('All generation/self-assessment records served from validated cache.', flush=True)
        write_json(run / 'generation_cache_check.json', {'rows': len(records), 'new_inferences': 0})
        return
    meter = GpuUsage(config['generation']['memory_limit_mib'])
    try:
        with meter:
            generator = LocalGenerator(config['generation'], ROOT / '.cache/rag/hub', config['seed'])
            for index, record in enumerate(records):
                sample_id = record['sample_id']
                if sample_id not in cached:
                    result = generator.complete(messages(record), config['generation']['max_new_tokens'])
                    answer = result['text']
                    cached[sample_id] = {'sample_id': sample_id, 'cache_key': expected[sample_id],
                                         'visible_input_sha256': record['visible_input_sha256'], 'answer': answer,
                                         'is_refusal': answer.strip().rstrip('.!').upper() == REFUSAL,
                                         'generation': result}
                    write_jsonl(path, [cached[r['sample_id']] for r in records if r['sample_id'] in cached])
                row = cached[sample_id]
                validate_assessment(row)
                if 'self_check' not in row:
                    if row['is_refusal'] or not row['answer']:
                        row['self_check'] = {'status': 'refusal' if row['is_refusal'] else 'empty_answer',
                                             'risk': None, 'support_confidence': None, 'attempts': []}
                    else:
                        row['self_check'] = assess(generator, record, row['answer'], config['generation']['self_retries'])
                    row['self_check']['answer_sha256'] = fingerprint(row['answer'])
                    write_jsonl(path, [cached[r['sample_id']] for r in records if r['sample_id'] in cached])
                print(f"generation {index+1}/{len(records)} {record['dataset']} {row['self_check']['status']}", flush=True)
    finally:
        if hasattr(meter, 'result'):
            write_json(run / 'generation_resources.json', meter.result)
            write_jsonl(run / 'generation_vram_samples.jsonl', meter.samples)
    if not meter.result['within_limit']:
        raise RuntimeError('Generation memory measurement exceeds limit or process measurement missing')


def score(config, run):
    from rag_hd.minicheck_adapter import AnswerScorer
    from rag_hd.resources import GpuUsage
    records = read_jsonl(run / 'prepared.jsonl')
    generated = {r['sample_id']: r for r in read_jsonl(run / 'generation.jsonl')}
    expected = {r['sample_id']: minicheck_key(r, generated[r['sample_id']], config) for r in records}
    path = run / 'minicheck.jsonl'
    cached = cached_rows(path, expected)
    if len(cached) == len(records):
        print('All MiniCheck records served from validated cache.', flush=True)
        write_json(run / 'minicheck_cache_check.json', {'rows': len(records), 'new_inferences': 0})
        return
    meter = GpuUsage(config['generation']['memory_limit_mib'])
    try:
        with meter:
            scorer = AnswerScorer(config['minicheck'], ROOT / '.cache/minicheck/models')
            for index, record in enumerate(records):
                sample_id = record['sample_id']
                if sample_id not in cached:
                    answer = generated[sample_id]
                    cached[sample_id] = {'sample_id': sample_id, 'cache_key': expected[sample_id],
                                         'visible_input_sha256': record['visible_input_sha256'],
                                         'minicheck': scorer.score(record, answer['answer'], answer['is_refusal'])}
                    write_jsonl(path, [cached[r['sample_id']] for r in records if r['sample_id'] in cached])
                print(f'minicheck {index+1}/{len(records)}', flush=True)
    finally:
        if hasattr(meter, 'result'):
            write_json(run / 'minicheck_resources.json', meter.result)
            write_jsonl(run / 'minicheck_vram_samples.jsonl', meter.samples)
    if not meter.result['within_limit']:
        raise RuntimeError('MiniCheck memory measurement exceeds limit or process measurement missing')


def finish(config, run, review_path):
    from rag_hd.evaluation import evaluate, initial_label, qa_scores
    from rag_hd.schema import LABELS, validate_record
    records = read_jsonl(run / 'prepared.jsonl')
    generated = {r['sample_id']: r for r in read_jsonl(run / 'generation.jsonl')}
    mini = {r['sample_id']: r for r in read_jsonl(run / 'minicheck.jsonl')}
    reviews = {}
    if review_path:
        if review_path.suffix.lower() == '.csv':
            with review_path.open(encoding='utf-8-sig', newline='') as stream:
                review_rows = list(csv.DictReader(stream))
        else:
            review_rows = read_jsonl(review_path)
        for review in review_rows:
            if not any(review.get(key) for key in ('review_source','reviewer','rationale')):
                continue  # Untouched rows in the blank review sheet aren't annotations.
            if review['sample_id'] in reviews:
                raise ValueError('Duplicate review sample ID')
            if review.get('review_source') != 'human' or not review.get('reviewer') or not review.get('rationale'):
                raise ValueError('Human review requires explicit source, reviewer and rationale')
            if review['evidence_label'] not in LABELS:
                raise ValueError('Invalid reviewed evidence label')
            reviews[review['sample_id']] = review
        if set(reviews) - {r['sample_id'] for r in records}:
            raise ValueError('Review references unknown sample IDs')
    merged, review_requests = [], []
    for record in records:
        sample_id = record['sample_id']
        answer = generated[sample_id]
        if answer['cache_key'] != generator_key(record, config):
            raise ValueError('Generation cache no longer matches configuration')
        if answer['self_check'].get('answer_sha256') != fingerprint(answer['answer']):
            raise ValueError('Self-assessment refers to a different answer')
        if mini[sample_id]['cache_key'] != minicheck_key(record, answer, config):
            raise ValueError('MiniCheck result refers to a different answer or configuration')
        if answer['visible_input_sha256'] != mini[sample_id]['visible_input_sha256'] or answer['visible_input_sha256'] != record['visible_input_sha256']:
            raise ValueError('The two methods received different visible inputs')
        row = dict(record, answer=answer['answer'], is_refusal=answer['is_refusal'],
                   generation=answer['generation'], self_check=answer['self_check'], minicheck=mini[sample_id]['minicheck'],
                   qa=qa_scores(answer['answer'], record['audit']['reference_answers']))
        row.update(initial_label(record, answer))
        row['answer_correctness'] = 'correct' if row['qa']['exact_match'] and not row['is_refusal'] else 'undetermined'
        row['answer_correctness_source'] = 'dataset_exact_answer' if row['answer_correctness'] == 'correct' else 'requires_review'
        if sample_id in reviews:
            validate_review_content(reviews[sample_id], record, answer)
            if row['is_refusal'] and reviews[sample_id]['evidence_label'] != 'undetermined':
                raise ValueError('Refusals must remain outside factual-answer AUC')
            correctness = reviews[sample_id].get('answer_correctness') or 'undetermined'
            if correctness not in ('correct','incorrect','undetermined'):
                raise ValueError('Invalid reviewed answer correctness')
            row.update(evidence_label=reviews[sample_id]['evidence_label'], label_source='human_review',
                       rationale=reviews[sample_id]['rationale'], review=reviews[sample_id],
                       answer_correctness=correctness, answer_correctness_source='human_review')
        validate_record(row)
        merged.append(row)
        review_requests.append({'sample_id': sample_id, 'question': row['question'],
                                'visible_evidence': row['visible_evidence'], 'answer': row['answer'],
                                'visible_input_sha256': record['visible_input_sha256'],
                                'answer_sha256': fingerprint(row['answer']),
                                'reference_answers': row['audit']['reference_answers'],
                                'gold_support': row['audit']['gold_support'],
                                'evidence_label': row['evidence_label'], 'answer_correctness': row['answer_correctness'],
                                'review_source': '', 'reviewer': '', 'rationale': ''})
    write_jsonl(run / 'records.jsonl', merged)
    write_jsonl(run / 'review_requests.jsonl', review_requests)
    csv_path = run / 'review_template.csv'
    refresh_blank = False
    if csv_path.exists():
        with csv_path.open(encoding='utf-8-sig', newline='') as stream:
            reader = csv.DictReader(stream)
            previous = list(reader)
            refresh_blank = 'answer_sha256' not in (reader.fieldnames or []) and not any(
                r.get(key) for r in previous for key in ('review_source','reviewer','rationale'))
    if not csv_path.exists() or refresh_blank:  # Preserve every reviewer-edited template.
        with csv_path.open('w', encoding='utf-8-sig', newline='') as stream:
            fields = ['sample_id','question','visible_evidence','answer','reference_answers',
                      'visible_input_sha256','answer_sha256','evidence_label','answer_correctness',
                      'review_source','reviewer','rationale']
            writer = csv.DictWriter(stream, fieldnames=fields, extrasaction='ignore')
            writer.writeheader()
            for request in review_requests:
                writer.writerow(dict(request, reference_answers=json.dumps(request['reference_answers'],ensure_ascii=False)))
    report = evaluate(merged)
    report['groups'] = {name: evaluate([r for r in merged if r['dataset'] == name]) for name in sorted({r['dataset'] for r in merged})}
    if config.get('challenge'):
        for field in ('condition', 'challenge_type'):
            report[field + '_groups'] = {name: evaluate([r for r in merged if r[field] == name])
                                        for name in sorted({r[field] for r in merged})}
    report['protocol_version'] = config['protocol_version']
    report['purpose'] = 'Development flow validation; not a formal method-improvement experiment.'
    write_json(run / 'metrics.json', report)
    if config.get('challenge'):
        readable = run / 'review_readable.csv'
        if not readable.exists():
            with readable.open('w', encoding='utf-8-sig', newline='') as stream:
                writer = csv.DictWriter(stream, fieldnames=['编号','问题','可见证据','生成回答','参考答案','证据支持标签','答案正确性','判断依据'])
                writer.writeheader()
                for index, row in enumerate(merged, 1):
                    writer.writerow({'编号': index, '问题': row['question'], '可见证据': row['visible_evidence'],
                                     '生成回答': row['answer'], '参考答案': '；'.join(row['audit']['reference_answers']),
                                     '证据支持标签': row['evidence_label'], '答案正确性': row['answer_correctness'],
                                     '判断依据': ''})
            write_json(run/'review_row_mapping.json', {'rows': [
                {'display_number': i, 'sample_id': r['sample_id'],
                 'visible_input_sha256': r['visible_input_sha256'], 'answer_sha256': fingerprint(r['answer'])}
                for i, r in enumerate(merged, 1)]})
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
    return any(r['label_source'] == 'requires_review' for r in merged)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', choices=['download', 'prepare', 'probe', 'generate', 'score', 'evaluate'], required=True)
    parser.add_argument('--config', type=Path, default=ROOT / 'configs/rag_prototype.yaml')
    parser.add_argument('--run-dir', type=Path, default=ROOT / 'outputs/rag_prototype_20261104')
    parser.add_argument('--review', type=Path)
    args = parser.parse_args()
    config = load_config(args.config)
    run = args.run_dir.resolve()
    run.mkdir(parents=True, exist_ok=True)
    config_path = run / 'config.json'
    if config_path.exists() and json.loads(config_path.read_text()) != config:
        raise ValueError('Configuration differs from this run; choose a new directory')
    write_json(config_path, config)
    code_files = [Path(__file__), ROOT/'scripts/run_rag_prototype.sh', *sorted((ROOT/'src/rag_hd').glob('*.py'))]
    provenance = run / 'provenance' / args.stage
    provenance.mkdir(parents=True, exist_ok=True)
    stage_source = {str(p.relative_to(ROOT)): file_sha256(p) for p in code_files}
    for path in code_files:
        target = provenance / path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    write_json(provenance / 'manifest.json', {'code_sha256': stage_source, 'config_sha256':fingerprint(config)})
    if args.stage == 'prepare':
        packages = {}
        for name in ('torch','transformers','datasets','bitsandbytes','rank-bm25','accelerate','numpy','nltk'):
            packages[name] = version(name)
        write_json(run / 'runtime_manifest.json', {'python': sys.version, 'packages': packages,
                   'git_revision': subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,text=True,capture_output=True,check=True).stdout.strip(),
                   'config_sha256': fingerprint(config),
                   'code_sha256': stage_source})
    elif args.stage != 'download':
        manifest = json.loads((run / 'data_manifest.json').read_text())
        if manifest['prepared_sha256'] != file_sha256(run / 'prepared.jsonl'):
            raise ValueError('Prepared records changed after preparation; choose a new run')
    status(run, args.stage + '_running')
    try:
        if args.stage == 'download':
            from huggingface_hub import snapshot_download
            snapshot_download(config['generation']['model_id'], revision=config['generation']['revision'],
                              cache_dir=str(ROOT / '.cache/rag/hub'), allow_patterns=['*.json','*.safetensors','*.txt','LICENSE','README.md'])
            from rag_hd.data import SOURCES
            for name, (repo, subset) in SOURCES.items():
                snapshot_download(repo, repo_type='dataset', revision=config['data'][name+'_revision'],
                                  cache_dir=str(ROOT / '.cache/rag/hub'), allow_patterns=['README.md', subset + '/train-*.parquet'])
        elif args.stage == 'prepare':
            prepare(config, run)
        elif args.stage == 'probe':
            probe(config, run)
        elif args.stage == 'generate':
            generate(config, run)
        elif args.stage == 'score':
            score(config, run)
        else:
            pending = finish(config, run, args.review)
            status(run, 'inference_complete_review_pending' if pending else 'complete')
            return
        status(run, args.stage + '_complete')
    except BaseException as error:
        write_json(run / 'status.json', {'stage': args.stage + '_failed', 'error_type': type(error).__name__, 'error': str(error)})
        raise


if __name__ == '__main__':
    main()
