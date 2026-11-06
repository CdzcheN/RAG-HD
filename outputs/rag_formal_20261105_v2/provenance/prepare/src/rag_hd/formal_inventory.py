"""Prepare source-disjoint nominations, never labels or generation-ready inputs."""
from collections import Counter, defaultdict
import csv
from pathlib import Path
import re

from .challenges_v2 import bounded_occurrences, canonical_title
from .data import SOURCES, read_pool, convert_question
from .io import fingerprint, file_sha256, write_json, write_jsonl, read_jsonl
from .retrieval import Retriever
from .schema import document_dict

KINDS = ('retrieval_failure', 'evidence_conflict', 'outdated_answer')
SPLIT_QUOTAS = {'train': 30, 'validation': 10, 'test': 10}
NUMBER = re.compile(r'\d[\d,]*(?:\.\d+)?%?')
QUANTITY = re.compile(r'how many|population|percent|percentage|proportion|number of|total of', re.I)


def prior_sources(root, previous_runs):
    titles, questions, manifests = set(), set(), {}
    for previous in previous_runs:
        path = root/previous
        if __import__('json').loads((path/'status.json').read_text())['stage'] != 'complete':
            raise ValueError('All prior development batches must be complete')
        corpus = {d['document_id']: d for d in read_jsonl(path/'corpus.jsonl')}
        for row in read_jsonl(path/'prepared.jsonl'):
            questions.add(row['base_question_id'])
            titles.update(canonical_title(e['title']) for e in row['evidence'])
            titles.update(canonical_title(corpus[key]['title']) for key in row['audit']['gold_document_ids'])
        manifests[previous] = file_sha256(path/'prepared.jsonl')
    return titles, questions, manifests


def candidate_reason(question, gold, excluded_titles, excluded_questions):
    if question['base_question_id'] in excluded_questions:
        return 'previous_question'
    if any(canonical_title(d.title) in excluded_titles for d in gold):
        return 'previous_visible_or_gold_source'
    if not gold or len(gold) > 2:
        return 'unsupported_gold_document_count'
    references = question['audit']['reference_answers']
    value = references[0].strip()
    if not NUMBER.fullmatch(value):
        return 'not_exact_numeric_reference'
    # Multiple aliases can differ in punctuation, but conflicting numeric annotations need review.
    if any(not NUMBER.fullmatch(v.strip()) or v.strip().replace(',', '') != value.replace(',', '') for v in references):
        return 'ambiguous_reference_aliases'
    if not QUANTITY.search(question['question']):
        return 'not_explicit_quantity_question'
    if sum(len(bounded_occurrences(d.text, value)) for d in gold) != 1:
        return 'nonunique_numeric_slot'
    if sum(len(d.text.split()) for d in gold) > 700:
        return 'gold_text_over_preparation_budget'
    return None


def components(rows):
    """Transitive groups use canonical titles, including URL/HTML aliases."""
    parent = list(range(len(rows)))
    def find(index):
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index
    seen = {}
    for index, row in enumerate(rows):
        for title in row['gold_titles']:
            key = canonical_title(title)
            if key in seen:
                parent[find(index)] = find(seen[key])
            seen[key] = index
    grouped = defaultdict(list)
    for index, row in enumerate(rows):
        grouped[find(index)].append(row)
    result = []
    for members in grouped.values():
        titles = sorted({canonical_title(t) for r in members for t in r['gold_titles']})
        result.append({'component_id': 'formal-source:'+fingerprint(titles), 'titles': titles,
                       'members': sorted(members, key=lambda r: r['base_question_id'])})
    return sorted(result, key=lambda c: c['component_id'])


def partition(titles, seed):
    value = int(fingerprint([seed, sorted(titles)]), 16)/2**256
    return 'train' if value < .6 else 'validation' if value < .8 else 'test'


def nominate(groups, seed):
    """One base per source component; no replacement based on model outcomes."""
    selected, deficits, used = [], [], set()
    # Reserve scarce SQuAD components before Hotpot to avoid taking mixed components twice.
    for split, count in SPLIT_QUOTAS.items():
        for dataset in SOURCES:
            for kind in KINDS:
                options = []
                for component in groups:
                    if component['component_id'] in used or partition(component['titles'], seed) != split:
                        continue
                    for row in component['members']:
                        if row['dataset'] == dataset:
                            options.append((fingerprint([seed, kind, row['base_question_id']]), component, row))
                picked = 0
                for _, component, row in sorted(options, key=lambda v: v[0]):
                    if component['component_id'] in used:
                        continue
                    used.add(component['component_id'])
                    selected.append(dict(row, planned_split=split, proposed_challenge_type=kind,
                                         component_id=component['component_id']))
                    picked += 1
                    if picked == count:
                        break
                if picked < count:
                    deficits.append({'split': split, 'dataset': dataset, 'type': kind,
                                     'required': count, 'available_nominated': picked})
    return selected, deficits


def reserve_noise(selected, pools, seed):
    """Canonical distractor sources belong to one base, across all future folds."""
    reserved_titles, reservations = set(), []
    retrievers = {split: Retriever(documents) for split, documents in pools.items()}
    for row in selected:
        split = row['planned_split']
        retrieved = retrievers[split].search(row['question'], len(pools[split]), 150, 150*len(pools[split]))
        chosen = []
        for entry in retrieved:
            title = canonical_title(entry['title'])
            if title in reserved_titles or any(bounded_occurrences(entry['title']+' '+entry['text'], answer)
                                               for answer in row['reference_answers']):
                continue
            chosen.append(entry)
            reserved_titles.add(title)
            if len(chosen) == 5:
                break
        if len(chosen) != 5:
            raise ValueError(f'Not enough exclusive safe noise for {row["base_question_id"]}')
        reservations.append({'base_question_id': row['base_question_id'], 'component_id': row['component_id'],
                             'planned_split': split, 'evidence': chosen})
    return reservations


def prepare(root, settings, config, output):
    output.mkdir(parents=True, exist_ok=True)
    if (output/'inventory_manifest.json').exists() or (output/'候选来源复核.csv').exists():
        raise ValueError('Inventory already exists; preserve review work and choose a new directory')
    excluded, old_questions, previous = prior_sources(root, settings['previous_runs'])
    candidates, rejected, all_docs, sources = [], [], {}, {}
    counts = {}
    for dataset in SOURCES:
        revision = config['data'][dataset+'_revision']
        pool, sources[dataset] = read_pool(dataset, revision, root/'.cache/rag/hub',
                                          settings['pool_per_dataset'], settings['candidate_seed'])
        reasons = Counter()
        for raw in pool:
            try:
                question, docs = convert_question(dataset, raw, revision)
            except (IndexError, KeyError, ValueError) as error:
                reasons['invalid_source_support'] += 1
                rejected.append({'base_question_id': dataset+':'+raw['id'], 'reason': 'invalid_source_support',
                                 'error_type': type(error).__name__, 'detail': str(error)})
                continue
            for doc in docs:
                title = canonical_title(doc.title)
                if title in excluded:
                    continue
                # Keep one deterministic original paragraph per canonical noise source.
                if title not in all_docs or fingerprint(doc.document_id) < fingerprint(all_docs[title].document_id):
                    all_docs[title] = doc
            gold = [d for d in docs if d.document_id in question['audit']['gold_document_ids']]
            reason = candidate_reason(question, gold, excluded, old_questions)
            if reason:
                reasons[reason] += 1
                rejected.append({'base_question_id': question['base_question_id'], 'reason': reason})
                continue
            reasons['candidate'] += 1
            value = question['audit']['reference_answers'][0].strip()
            flags = []
            if re.search(r'\b(this|that|these|those|it|he|she|his|her|they|their)\b', question['question'], re.I):
                flags.append('题干指代需核对，不能自动当作自足问题')
            if re.search(r'how many years|how old|how long', question['question'], re.I):
                flags.append('时长／年龄不是可直接套用的统计更正，需单独判定')
            if '%' in value or re.search(r'percent|proportion', question['question'], re.I):
                flags.append('比例需要核对分母、其他分项和联动约束')
            candidates.append({'base_question_id': question['base_question_id'], 'dataset': dataset,
                               'question': question['question'], 'reference_answers': question['audit']['reference_answers'],
                               'gold_titles': [d.title for d in gold], 'gold_evidence': [document_dict(d) for d in gold],
                               'gold_support': question['audit']['gold_support'],
                               'automatic_flags': flags, 'source_review_status': 'pending_semantic_review',
                               'numeric_slot': [{'document_id': d.document_id, 'start': m.start(), 'end': m.end(), 'value': value}
                                                for d in gold for m in bounded_occurrences(d.text, value)]})
        counts[dataset] = dict(reasons)
        print(f'{dataset}: {len(pool)} checked, {reasons["candidate"]} numeric candidates', flush=True)
    groups = components(candidates)
    nominated, deficits = nominate(groups, settings['partition_seed'])
    target_titles = {canonical_title(t) for r in candidates for t in r['gold_titles']}
    pools = {split: [] for split in SPLIT_QUOTAS}
    for title, doc in sorted(all_docs.items(), key=lambda v: fingerprint([settings['noise_seed'], v[0]])):
        split = partition([title], settings['partition_seed'])
        if title not in target_titles and len(pools[split]) < settings['noise_pool_per_partition']:
            pools[split].append(doc)
    if any(len(documents) < 5 for documents in pools.values()):
        raise ValueError('Insufficient disjoint noise pools')
    reservations = reserve_noise(nominated, pools, settings['noise_seed'])
    # Separate targets and distractors by canonical source, not only document ID.
    owner = {}
    for row in nominated:
        for title in row['gold_titles']:
            title = canonical_title(title)
            if title in owner:
                raise ValueError('Nominated targets share a canonical source')
            owner[title] = row['base_question_id']
    for reservation in reservations:
        for doc in reservation['evidence']:
            title = canonical_title(doc['title'])
            if title in owner or title in excluded or title in target_titles:
                raise ValueError('Noise overlaps a prior, target or reserved source')
            owner[title] = reservation['base_question_id']
    write_jsonl(output/'candidates.jsonl', candidates)
    write_jsonl(output/'candidate_rejections.jsonl', rejected)
    write_jsonl(output/'nominated_questions.jsonl', nominated)
    write_jsonl(output/'noise_reservations.jsonl', reservations)
    write_jsonl(output/'excluded_prior_titles.jsonl', [{'canonical_title': t} for t in sorted(excluded)])
    write_jsonl(output/'source_components.jsonl', [{k: v for k, v in c.items() if k != 'members'} |
                {'base_question_ids': [r['base_question_id'] for r in c['members']]} for c in groups])
    write_jsonl(output/'noise_corpus.jsonl', [dict(document_dict(d), planned_pool=split)
                                            for split, docs in pools.items() for d in docs])
    with (output/'候选来源复核.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['编号', '数据集', '计划分区', '拟构造类型', '原始问题', '参考答案', '金标来源与正文', '自动检查备注', '来源语义检查', '修正后的问题', '构造约束与理由'])
        for number, row in enumerate(nominated, 1):
            writer.writerow([number, row['dataset'], row['planned_split'], row['proposed_challenge_type'],
                             row['question'], '；'.join(row['reference_answers']),
                             '\n\n'.join(d['title']+'\n'+d['text'] for d in row['gold_evidence']),
                             '；'.join(row['automatic_flags']) or '仅通过结构筛查，尚未核实题意及数量约束',
                             '待核对', '', ''])
    inventory = {'status': 'nominations_ready_semantic_review_pending', 'generation_ready': False,
                 'prior_canonical_titles_excluded': len(excluded), 'prior_runs_sha256': previous,
                 'sources': sources, 'settings': settings, 'screening_counts': counts,
                 'candidate_questions': len(candidates), 'source_components': len(groups),
                 'nominated_bases': len(nominated), 'planned_paired_inputs': 2*len(nominated),
                 'planned_challenge_inputs': len(nominated), 'quota_deficits': deficits,
                 'nominated_strata': dict(Counter('/'.join((r['planned_split'], r['dataset'], r['proposed_challenge_type'])) for r in nominated)),
                 'noise_pool_documents': {k: len(v) for k, v in pools.items()},
                 'reserved_noise_documents': sum(len(r['evidence']) for r in reservations),
                 'canonical_source_overlap_across_nominated_bases': 0,
                 'canonical_source_overlap_with_prior_batches': 0,
                 'noise_sources_bound_to_base_group': True,
                 'semantic_review_completed': 0, 'labels_created': 0, 'generator_calls': 0,
                 'selection_uses_detector_scores': False,
                 'checks_do_not_prove_semantic_validity': True,
                 'artifacts_sha256': {p.name: file_sha256(p) for p in output.iterdir() if p.suffix in ('.jsonl', '.csv')}}
    write_json(output/'inventory_manifest.json', inventory)
    print(f'Nominated {len(nominated)} bases; {len(deficits)} quota deficits; semantic review still required.', flush=True)
    return inventory
