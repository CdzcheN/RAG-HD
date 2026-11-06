"""Materialize individually curated sources with checked numerical dependencies."""
from collections import Counter
from copy import deepcopy
import csv
from decimal import Decimal, ROUND_HALF_UP
import json
from pathlib import Path
import re
from html import unescape
from urllib.parse import unquote

from .challenges import DISCLOSURE, evidence_entry
from .challenges_v2 import bounded_occurrences, canonical_title
from .construction_edits import Edit, apply, number, format_number, quantity_change
from .formal_inventory import reserve_noise, partition, KINDS, SPLIT_QUOTAS
from .formal_protocol import development_splits, verify_source_isolation, rule_assignments
from .io import read_jsonl, write_jsonl, write_json, fingerprint, file_sha256
from .schema import Document, assign_groups, validate_record, evidence_text, visible_input, document_dict

VERSION = 'controlled-challenge-formal-v1'


def numeric_edit(text, before, after, role):
    matches = bounded_occurrences(text, before)
    if len(matches) != 1:
        raise ValueError(f'Ambiguous linked numeric source span: {before}')
    match = matches[0]
    return Edit('text', match.start(), match.end(), before, after, role)


def aliases(value):
    """Surface aliases only; never use a detector to label or select evidence."""
    core = value.rstrip('%').rstrip(',')
    result = {core, core+'%', core.replace(',', ''), core.replace(',', '')+'%'}
    if re.fullmatch(r'\d+', core) and int(core) < 10**12:
        small = ['zero','one','two','three','four','five','six','seven','eight','nine','ten',
                 'eleven','twelve','thirteen','fourteen','fifteen','sixteen','seventeen','eighteen','nineteen']
        tens = ['', '', 'twenty','thirty','forty','fifty','sixty','seventy','eighty','ninety']
        def words(n):
            if n < 20: return small[n]
            if n < 100: return tens[n//10]+(' '+small[n%10] if n%10 else '')
            if n < 1000: return small[n//100]+' hundred'+(' '+words(n%100) if n%100 else '')
            for scale, name in ((10**9,'billion'),(10**6,'million'),(1000,'thousand')):
                if n >= scale:
                    return words(n//scale)+' '+name+(' '+words(n%scale) if n%scale else '')
        spelled = words(int(core))
        result.update([spelled, spelled.replace(' ', '-')])
        for scale, name in ((10**9,'billion'),(10**6,'million'),(1000,'thousand')):
            if int(core) >= scale and int(core)%scale == 0:
                result.add(str(int(core)//scale)+' '+name)
        # Common British "and" between hundreds/thousands and the remainder.
        for separator in ('hundred ', 'thousand ', 'million ', 'billion '):
            if separator in spelled:
                result.add(spelled.replace(separator, separator.rstrip()+' and ', 1))
    return sorted(result)


def validate_numbers(old, new, spec, original, modified):
    """Check declared sums, conversions and rounded proportions before and after."""
    values = {'target': old}
    after = {'target': new}
    delta = number(new)-number(old)
    edits = [numeric_edit(original, old, new, 'target_reported_quantity')]
    for entry in spec.get('coupled_deltas', []):
        key, before = entry['key'], entry['before']
        changed = format_number(number(before)+delta*Decimal(entry.get('multiplier', 1)), before)
        values[key] = before; after[key] = changed
        edits.append(numeric_edit(original, before, changed, 'linked_'+key))
    for entry in spec.get('scaled_coupled', []):
        raw = number(new)*Decimal(entry['factor'])
        step = Decimal(entry['round_to'])
        rounded = (raw/step).quantize(Decimal(1), rounding=ROUND_HALF_UP)*step
        changed = format_number(rounded, entry['before'])
        values[entry['key']] = entry['before']; after[entry['key']] = changed
        edits.append(numeric_edit(original, entry['before'], changed, 'converted_'+entry['key']))
        if abs(number(old)*Decimal(entry['factor'])-number(entry['before'])) > step/2:
            raise ValueError('Original unit conversion violates declared rounding')
        if abs(raw-number(changed)) > step/2:
            raise ValueError('Updated unit conversion violates declared rounding')
    partition = spec.get('percentage_partition')
    if partition:
        total = number(partition['target_votes'])+number(partition['other_votes'])
        changed_votes = (total*number(new)/100).quantize(Decimal(1), rounding=ROUND_HALF_UP)
        updates = {'complement': format_number(100-number(new), partition['complement']),
                   'target_votes': format_number(changed_votes, partition['target_votes']),
                   'other_votes': format_number(total-changed_votes, partition['other_votes'])}
        for key, changed in updates.items():
            before = partition[key]
            values[key] = before; after[key] = changed
            edits.append(numeric_edit(original, before, changed, 'linked_'+key))
        for state in (values, after):
            if number(state['target'])+number(state['complement']) != 100:
                raise ValueError('Complementary vote percentages do not sum to 100')
            if number(state['target_votes'])+number(state['other_votes']) != total:
                raise ValueError('Vote counts changed the fixed valid-vote total')
            step = Decimal(partition['resolution'])
            for count, pct in [('target_votes','target'), ('other_votes','complement')]:
                rounded = (100*number(state[count])/total/step).quantize(Decimal(1), rounding=ROUND_HALF_UP)*step
                if rounded != number(state[pct]):
                    raise ValueError('Vote counts and printed percentage disagree')
    summed = spec.get('sum_constraint')
    if summed:
        for state in (values, after):
            parts = []
            for key, before in summed['parts'].items():
                value = state.get(key, state['target'] if before == '$target' else before)
                parts.append(number(value))
            total = number(state[summed['total_key']]) if 'total_key' in summed else number(summed['constant_total'])
            if sum(parts) != total:
                raise ValueError('Declared source parts do not sum to total')
    rounded_partition = spec.get('partition_rounding')
    if rounded_partition:
        denominator = number(rounded_partition['denominator'])
        step = Decimal(rounded_partition['resolution'])
        for state in (values, after):
            for key, share in rounded_partition['shares'].items():
                count = state.get(key, state['target'] if summed['parts'][key] == '$target' else summed['parts'][key])
                rounded = (100*number(count)/denominator/step).quantize(Decimal(1), rounding=ROUND_HALF_UP)*step
                if rounded != Decimal(share): raise ValueError('Population proportion rounding changed')
    scaled = spec.get('scaled_check')
    if scaled:
        for value in (old, new):
            if abs(number(value)*Decimal(scaled['factor'])-number(scaled['other'])) > Decimal(scaled['tolerance']):
                raise ValueError('Printed approximate area conversion no longer holds')
    ratio = spec.get('ratio_rounding_check')
    if ratio:
        if 'base' in ratio:
            step = Decimal(ratio['resolution'])
            for value in (old, new):
                rounded = (((number(value)/number(ratio['base'])-1)*100)/step).quantize(Decimal(1), rounding=ROUND_HALF_UP)*step
                if rounded != Decimal(ratio['reported_growth']): raise ValueError('Growth rounding changed')
        else:
            # Unknown denominator stays private/unknown: check existence of one common denominator,
            # not a fabricated exact population/land-area inferred from a rounded percentage.
            share = Decimal(ratio['share']); half = Decimal(ratio['share_percent_resolution'])/2
            offset = number(ratio.get('additive_count', '0'))
            low = max((number(v)+offset)*100/(share+half) for v in (old, new))
            high = min((number(v)+offset)*100/(share-half) for v in (old, new))
            if low >= high: raise ValueError('No common denominator preserves printed rounded share')
    modified_text, log = apply({'text': original}, edits)
    modified['text'] = modified_text['text']
    return {'values_before': values, 'values_after': after, 'exact_span_edits': log,
            'declared_constraints_passed': True}


def edit_record(row, spec, seed):
    docs = [Document(**d) for d in row['gold_evidence']]
    excerpts = []
    for doc in docs:
        quote = spec.get('source_excerpts', {}).get(doc.title, spec.get('excerpt_quote', doc.text))
        if doc.text.count(quote) != 1: raise ValueError('Source excerpt must be an exact unambiguous span')
        start = doc.text.index(quote)
        excerpts.append({'doc': doc, 'text': quote, 'start': start, 'end': start+len(quote)})
    old = spec.get('reference_override') or row['reference_answers'][0].strip()
    if spec.get('reference_normalization') == 'strip_trailing_comma': old = old.rstrip(',')
    occurrences = [(index, m) for index, e in enumerate(excerpts) for m in bounded_occurrences(e['text'], old)]
    if len(occurrences) != 1: raise ValueError(f'Curated target slot not unique: {row["base_question_id"]} {old}')
    index, _ = occurrences[0]
    modified = deepcopy(excerpts)
    if row['proposed_challenge_type'] == 'retrieval_failure':
        return docs, excerpts, modified, old, None, {'exact_span_edits': [], 'values_before': {'target': old},
                'values_after': {'target': old}, 'declared_constraints_passed': True, 'deletion_only': True}
    bounds = spec.get('target_bounds', {})
    if spec.get('percentage_bounds') or old.endswith('%'): bounds = {'lower':'0', 'upper':'100', **bounds}
    direction = 1 if int(fingerprint([seed, row['base_question_id'], 'quantity-direction']), 16)%2 else -1
    failures = []
    for sign in (direction, -direction):
        try:
            new = quantity_change(old, sign, lower=bounds.get('lower'), upper=bounds.get('upper'))
            audit = validate_numbers(old, new, spec, excerpts[index]['text'], modified[index])
            audit['numeric_bounds'] = bounds
            return docs, excerpts, modified, old, new, audit
        except ValueError as error:
            failures.append(str(error))
    raise ValueError(f'Neither deterministic numeric direction is coherent for {row["base_question_id"]}: {failures}')


def build_pair(row, spec, noise, family, texts, seed, number_in_batch, edited):
    docs, excerpts, modified, old, new, edit_audit = edited
    kind = row['proposed_challenge_type']
    if kind not in KINDS: raise ValueError('Unknown formal construction type')
    clean_question = spec.get('question_override') or row['question']
    if row['dataset'] == 'squad':
        clean_question = 'Evidence scope: '+unescape(unquote(docs[0].title)).replace('_', ' ')+'. '+clean_question
    def entries(items, version):
        return [evidence_entry(e['doc'], e['text'], version) for e in items]
    year = (2020, 2022, 2024)[number_in_batch%3]
    query_date = f'{year}-06-01'
    policy = '' if family == 'plain_question' else texts[family].format(year=year, query_date=query_date)
    question = clean_question if not policy else DISCLOSURE+policy+'\nOriginal question: '+clean_question
    if kind == 'retrieval_failure':
        base = entries(excerpts, 'source_snapshot=curated_exact_excerpt')
        normal, challenge = base+deepcopy(noise[:5-len(base)]), deepcopy(noise[:5])
    elif kind == 'evidence_conflict':
        primary = entries(excerpts, 'source_tier=primary')
        agreeing = entries(excerpts, 'source_tier=secondary')
        conflicting = entries(modified, 'source_tier=secondary')
        normal = primary+agreeing if number_in_batch%2 else agreeing+primary
        challenge = primary+conflicting if number_in_batch%2 else conflicting+primary
        normal += deepcopy(noise[:5-len(normal)]); challenge += deepcopy(noise[:5-len(challenge)])
    else:
        current = f'valid_from={year}-01-01; valid_until={year}-12-31; supersedes={year-1}-record'
        expired = f'valid_from={year-1}-01-01; valid_until={year-1}-12-31; superseded_by={year}-update'
        valid, agreeing = entries(modified,current), entries(modified,current+'; copy=current')
        old_entries = entries(excerpts, expired)
        normal = valid+agreeing if number_in_batch%2 else agreeing+valid
        challenge = valid+old_entries if number_in_batch%2 else old_entries+valid
        normal += deepcopy(noise[:5-len(normal)]); challenge += deepcopy(noise[:5-len(challenge)])
    result = []
    for condition, evidence in [('normal', normal), (kind, challenge)]:
        for rank, entry in enumerate(evidence, 1): entry['rank'] = rank
        audit = {'original_question': row['question'], 'source_revision': docs[0].version,
                 'source_question_id': row['base_question_id'].split(':',1)[1], 'source_split': 'train',
                 'gold_document_ids': [d.document_id for d in docs],
                 'gold_support': row['gold_support'], 'source_reference_answers': row['reference_answers'],
                 'reference_answers': [new if kind == 'outdated_answer' else old],
                 'question_revision': {'before': row['question'], 'after': clean_question, 'rationale': spec['rationale']},
                 'reference_override': spec.get('reference_override'),
                 'source_excerpts': [{'document_id': e['doc'].document_id, 'start': e['start'], 'end': e['end']} for e in excerpts],
                 'original_source_document_ids': [d.source_document_id for d in docs],
                 'all_gold_support_visible': False, 'annotation_origin': 'not_yet_answered_or_labeled',
                 'source_curation_origin': 'assistant_source_text_review',
                 'planned_split': row['planned_split'], 'rule_family': family,
                 'hop_note': spec.get('hop_note', 'No claim that all questions require two hops')}
        construction = {'protocol': VERSION, 'type': kind, 'original_value': old,
                        'replacement_value': new, 'slot_semantics': spec.get('slot_semantics', 'reported_quantity'),
                        'curation_note': spec['rationale'], 'not_an_answer_label': True, **edit_audit}
        record = {'base_question_id': row['base_question_id'], 'dataset': row['dataset'], 'question': question,
                  'source_document_ids': sorted('wiki-formal:'+fingerprint(canonical_title(d.title)) for d in docs),
                  'audit': audit, 'construction': construction, 'evidence': evidence,
                  'visible_evidence': evidence_text(evidence), 'condition': condition, 'challenge_type': kind,
                  'protocol_version': 'rag-prototype-v1', 'construction_protocol': VERSION, 'evidence_label': 'undetermined',
                  'formal_split': row['planned_split'], 'source_cleaning_number': spec['display_number']}
        record['visible_input_sha256'] = fingerprint(visible_input(record))
        record['pair_id'] = 'pair:'+fingerprint([VERSION, row['base_question_id'], kind])
        record['sample_id'] = 'sample:'+fingerprint([record['pair_id'], condition, record['visible_input_sha256']])
        if len(evidence) != 5 or sum(len(e['text'].split()) for e in evidence) > 1200:
            raise ValueError(f'Curated input exceeds evidence budget at row {spec["display_number"]}')
        result.append(record)
    return result


def prepare(config, run, root):
    root, run = Path(root), Path(run)
    if (run/'prepared.jsonl').exists() or (run/'generation.jsonl').exists():
        raise ValueError('Never overwrite a prepared formal batch; choose a new run')
    settings = config['challenge']
    inventory = root/settings['inventory']
    manifest = json.loads((inventory/'inventory_manifest.json').read_text())
    for name, digest in manifest['artifacts_sha256'].items():
        if file_sha256(inventory/name) != digest: raise ValueError('Original inventory changed')
    decisions = sorted(json.loads((root/settings['cleaning_decisions']).read_text())['decisions'],
                       key=lambda r:r['display_number'])
    replacements = {r['display_number']: r for r in json.loads((root/settings['replacement_decisions']).read_text())['decisions']}
    original = read_jsonl(inventory/'nominated_questions.jsonl')
    candidates = {r['base_question_id']: r for r in read_jsonl(inventory/'candidates.jsonl')}
    source_groups = read_jsonl(inventory/'source_components.jsonl')
    group = {sid: g['component_id'] for g in source_groups for sid in g['base_question_ids']}
    group_titles = {g['component_id']:g['titles'] for g in source_groups}
    if len(decisions) != 300 or {s['display_number'] for s in decisions} != set(range(1,301)):
        raise ValueError('Require an individual decision for every nominated source')
    selected, specs, changes = [], [], []
    for spec in sorted(decisions, key=lambda r: r['display_number']):
        row = deepcopy(original[spec['display_number']-1])
        if spec['base_question_id'] != row['base_question_id'] or not spec['rationale'].strip():
            raise ValueError('Missing or mismatched source review')
        spec = deepcopy(spec)
        if spec['action'] == 'replace':
            replacement = replacements[spec['display_number']]
            new_row = deepcopy(candidates[replacement['replacement_base_question_id']])
            if (new_row['dataset'] != row['dataset'] or
                    partition(group_titles[group[new_row['base_question_id']]],20260919) != row['planned_split']):
                raise ValueError('Replacement must preserve dataset and source partition')
            new_row.update(planned_split=row['planned_split'], proposed_challenge_type=row['proposed_challenge_type'],
                           component_id=group[new_row['base_question_id']])
            changes.append({'display_number': spec['display_number'], 'rejected_base': row['base_question_id'],
                            'selected_base': new_row['base_question_id'], 'reason': spec['rationale'],
                            'replacement_reason': replacement['rationale']})
            row = new_row
            spec['rejected_base_question_id'] = spec['base_question_id']
            spec.update(replacement)
            spec['base_question_id'] = new_row['base_question_id']
        selected.append(row); specs.append(spec)
    if len({r['component_id'] for r in selected}) != 300: raise ValueError('Reused replacement source component')
    if Counter((r['planned_split'],r['dataset'],r['proposed_challenge_type']) for r in selected) != {
            (split,dataset,kind): count for split,count in SPLIT_QUOTAS.items()
            for dataset in ('squad','hotpot') for kind in KINDS}:
        raise ValueError('Cleaned source strata do not match fixed quotas')
    edited = [edit_record(r, s, config['seed']) for r,s in zip(selected,specs)]
    # Re-retrieve using cleaned questions; reject both original and actual altered answer aliases.
    retrieval_rows = []
    for row, spec, edit in zip(selected, specs, edited):
        old, new = edit[3:5]
        retrieval_rows.append(dict(row, question=spec.get('question_override') or row['question'],
                                   reference_answers=sorted(set(aliases(old)+([] if new is None else aliases(new))))))
    pools = {'train': [], 'validation': [], 'test': []}
    for raw in read_jsonl(inventory/'noise_corpus.jsonl'):
        split = raw.pop('planned_pool'); pools[split].append(Document(**raw))
    reserved = reserve_noise(retrieval_rows, pools, config['seed'])
    splits = development_splits(selected)
    isolation = verify_source_isolation(selected, reserved, splits)
    families = json.loads((root/settings['rule_families']).read_text())
    assignments = rule_assignments(selected, families, 20260919)
    for assignment in assignments: assignment['status'] = 'frozen_before_inference'
    by_id = {r['base_question_id']: r for r in assignments}
    records = []
    for index, (row, spec, noise, edit) in enumerate(zip(selected,specs,reserved,edited), 1):
        records.extend(build_pair(row,spec,noise['evidence'],by_id[row['base_question_id']]['family'],
                                  families['texts'],config['seed'],index,edit))
    assign_groups(records)
    for record in records: validate_record(record)
    excluded = {r['canonical_title'] for r in read_jsonl(inventory/'excluded_prior_titles.jsonl')}
    titles = {canonical_title(e['title']) for r in records for e in r['evidence']}
    if titles & excluded: raise ValueError('Prior development source survived cleaning')
    corpus = {d.document_id: document_dict(d) for edit in edited for d in edit[0]}
    pool_by_id = {d.document_id: document_dict(d) for docs in pools.values() for d in docs}
    corpus.update({e['document_id']:pool_by_id[e['document_id']] for n in reserved for e in n['evidence']})
    run.mkdir(parents=True,exist_ok=True)
    write_jsonl(run/'prepared.jsonl', records)
    write_jsonl(run/'corpus.jsonl', corpus.values())
    write_json(run/'frozen_specs.json', specs)
    write_json(run/'frozen_splits.json', splits)
    write_jsonl(run/'frozen_rule_assignments.jsonl', assignments)
    write_jsonl(run/'noise_reservations.jsonl', reserved)
    write_json(run/'replacement_audit.json', changes)
    with (run/'清洗结果.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['编号','数据集','分区','挑战类型','处理','原候选问题','采用来源原问题','采用来源原参考答案','清洗后的问题','原始统计值','替换值','清洗依据','数量联动检查'])
        for index,(row,spec,edit) in enumerate(zip(selected,specs,edited),1):
            reason = decisions[index-1]['rationale']+(' 替补：'+spec['rationale'] if decisions[index-1]['action']=='replace' else '')
            writer.writerow([index,row['dataset'],row['planned_split'],row['proposed_challenge_type'],decisions[index-1]['action'],
                             original[index-1]['question'],row['question'],'；'.join(row['reference_answers']),spec.get('question_override') or row['question'],
                             edit[3],edit[4] or '不涉及替换',reason,'通过：'+('仅删除完整支撑' if edit[4] is None else '原始及修改后声明约束均检查')])
    with (run/'construction_review.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['编号','挑战类型','原始问题','修正后的问题','原始值','替换值','正常证据','挑战证据','构造检查备注'])
        for index,(spec,a,b) in enumerate(zip(specs,records[::2],records[1::2]),1):
            writer.writerow([index,b['challenge_type'],b['audit']['original_question'],a['question'],
                             b['construction']['original_value'],b['construction']['replacement_value'] or '不涉及替换',
                             a['visible_evidence'],b['visible_evidence'],'助手来源清洗：'+spec['rationale']+' 生成后的实际回答尚未标注。'])
    write_json(run/'data_manifest.json',{'construction_protocol':VERSION,'sources':manifest['sources'],
        'records':600,'base_questions':300,'groups':len({r['group_id'] for r in records}),
        'condition_counts':dict(Counter(r['condition'] for r in records)),
        'prior_source_exclusion_sha256':manifest['prior_runs_sha256'],
        'prepared_sha256':file_sha256(run/'prepared.jsonl'),'corpus_sha256':file_sha256(run/'corpus.jsonl'),
        'inventory_manifest_sha256':file_sha256(inventory/'inventory_manifest.json'),
        'source_decisions_sha256':file_sha256(root/settings['cleaning_decisions']),
        'replacement_decisions_sha256':file_sha256(root/settings['replacement_decisions']),
        'partition_checks':isolation,'source_reviews':300,'replaced_candidates':len(changes),
        'old_visible_source_overlap':0,'canonical_title_alias_overlap':0,
        'labels_created_by_construction':0,'detector_scores_used_for_cleaning':False,
        'new_old_numeric_aliases_excluded_from_noise':True,
        'purpose':'Source-curated controlled formal experiment inputs; actual answers still require review.',
        'source_review_origin':'assistant_source_text_review','independent_human_annotation':False,
        'disclosure':'Only declared sources/excerpts and explicit record rules; no natural full-Wikipedia retrieval claim.'})
    print('Prepared 300 curated source groups / 600 unlabeled inputs; frozen folds and source isolation checked.',flush=True)
