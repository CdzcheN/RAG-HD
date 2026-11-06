"""Controlled, audited evidence interventions; construction never labels answers."""
from collections import Counter
from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path
import re

from .data import SOURCES, convert_question, read_pool
from .io import file_sha256, fingerprint, read_jsonl, write_json, write_jsonl
from .retrieval import Retriever
from .schema import assign_groups, document_dict, evidence_text, source_id, validate_record, visible_input

TYPES = ('retrieval_failure', 'evidence_conflict', 'outdated_answer')
VERSION = 'controlled-challenge-v1'
DISCLOSURE = ('This is a controlled document-version scenario, not a statement about current real-world facts. '
              'Answer the original question only from the supplied records, applying the record policy below. ')


def value_kind(question):
    value = question['audit']['reference_answers'][0].strip()
    if re.fullmatch(r'[0-9][0-9,]*(?:\.[0-9]+)?%?', value):
        return 'numeric'
    if re.search(r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\b', value, re.I) and re.search(r'\b\d{4}\b', value):
        return 'calendar_date'
    query = question['question'].casefold()
    if value[:1].isupper() and len(value.split()) <= 5:
        if query.startswith('who ') or re.search(r'which (?:actor|actress|singer|writer|author|person|director|star)\b',query):
            words = value.split()
            if (len(words) >= 2 and all(w[:1].isupper() or w.casefold() in ('of','the','de','van','von','bin','al') for w in words)
                    and not re.search(r'\b(?:Inc|Ltd|Corporation|Company|University|Committee|Group)\b',value)):
                return 'person'
        for location in ('city','country','state','town','village'):
            if re.search(r'(?:which|what) '+location+r'\b', query):
                if location == 'country' and value in ('American','British','German','French','Spanish','Italian','Irish','Scottish','Welsh','Canadian','Australian'):
                    return None  # Do not substitute a country noun for a nationality adjective.
                return location
    return None


def replacement_for(question, pool, seed):
    answer = question['audit']['reference_answers'][0].strip()
    kind = value_kind(question)
    if kind == 'numeric':
        # Preserve formatting, units and grammatical slot; never replace a year with a population.
        match = re.search(r'\d+', answer)
        value = int(match.group())
        if not re.fullmatch(r'\d+', answer):
            # Change the final numeric group, preserving comma/decimal/percent delimiters.
            match = list(re.finditer(r'\d+', answer))[-1]
            value = int(match.group())
        new = str(value + (4 if re.fullmatch(r'\d{4}',answer) else 1)).zfill(len(match.group()))
        return answer[:match.start()] + new + answer[match.end():]
    if kind == 'calendar_date':
        # Preserve leap-day validity even when crossing a non-leap century.
        match = re.search(r'\b\d{4}\b',answer)
        year = int(match.group()) + 4
        if year % 100 == 0 and year % 400 != 0:
            year += 4
        return answer[:match.start()] + str(year) + answer[match.end():]
    if kind:
        alternatives = sorted({q['audit']['reference_answers'][0] for q, _ in pool
                               if value_kind(q) == kind and q['audit']['reference_answers'][0].casefold() != answer.casefold()
                               and abs(len(q['audit']['reference_answers'][0].split())-len(answer.split())) <= 1
                               and not any(ref.casefold() in q['audit']['reference_answers'][0].casefold() for ref in question['audit']['reference_answers'])},
                              key=lambda v:fingerprint([seed,question['base_question_id'],v]))
        if alternatives:
            return alternatives[0]
    raise ValueError('No replacement of the same supported value kind')


def replace_value(text, old, new):
    return re.sub(re.escape(old), lambda match: new, text, flags=re.I)


def evidence_entry(document, text=None, version=None):
    text = document.text if text is None else text
    return dict(document_id='doc:' + fingerprint([document.source_document_id, text, version or document.version]),
                source_document_id=document.source_document_id, title=document.title, text=text,
                version=version or document.version, rank=0, bm25_score=None,
                content_sha256=fingerprint(text), truncated=False,
                origin_document_id=document.document_id)


def finalize(question, entries, kind, variant, audit, construction):
    row = deepcopy(question)
    row.update(question=question['question'], evidence=deepcopy(entries), condition=variant,
               challenge_type=kind, construction_protocol=VERSION, protocol_version='rag-prototype-v1',
               audit=deepcopy(audit), construction=deepcopy(construction), evidence_label='undetermined')
    for index, entry in enumerate(row['evidence'], 1):
        entry['rank'] = index
    row['visible_evidence'] = evidence_text(row['evidence'])
    row['visible_input_sha256'] = fingerprint(visible_input(row))
    row['sample_id'] = 'sample:' + fingerprint([row['base_question_id'], kind, variant, row['visible_input_sha256']])
    row['pair_id'] = 'pair:' + fingerprint([row['base_question_id'], kind, VERSION])
    row['audit']['all_gold_support_visible'] = False  # No automatic outcome labels from intervention metadata.
    return row


def make_pair(question, documents, retrieved, kind, replacement, seed):
    """Return paired input records, retaining a full private edit history."""
    gold_ids = set(question['audit']['gold_document_ids'])
    gold = [doc for doc in documents if doc.document_id in gold_ids]
    answer = question['audit']['reference_answers'][0]
    if not gold or (kind != 'retrieval_failure' and (not replacement or answer.casefold() == replacement.casefold())):
        raise ValueError('Need original support and a distinct replacement')
    target = next((doc for doc in gold if answer.casefold() in doc.text.casefold()), None)
    if target is None:
        raise ValueError('Reference must occur explicitly in support')
    # Remove accidental answer-bearing distractors from both members before the intervention.
    distractors = [deepcopy(e) for e in retrieved if e['document_id'] not in gold_ids
                   and not any(ref.casefold() in e['text'].casefold() for ref in question['audit']['reference_answers'])]
    distractors = distractors[:max(1, 4-len(gold))]
    entries = [evidence_entry(doc) for doc in gold] + distractors
    audit = deepcopy(question['audit'])
    audit['source_reference_answers'] = list(audit['reference_answers'])
    audit['original_question'] = question['question']
    audit['retrieval_before_intervention'] = retrieved
    audit['normal_support_mode'] = 'gold_support_topup_plus_bm25_distractors'
    normal_question, challenge_question = deepcopy(question), deepcopy(question)
    common = {'protocol': VERSION, 'seed': seed, 'type': kind,
              'target_document_id': target.document_id, 'original_value': answer,
              'replacement_value': replacement, 'not_an_answer_label': True}
    if kind == 'retrieval_failure':
        # Drop every gold passage (single-hop) or one answer-bearing hop (multi-hop).
        removed = [e for e in entries if e.get('origin_document_id') == target.document_id] if len(gold) > 1 else entries[:len(gold)]
        removed_ids = {e['document_id'] for e in removed}
        challenged = [e for e in entries if e['document_id'] not in removed_ids]
        # Remaining passages containing any answer alias would make the intended deletion ambiguous.
        for entry in challenged:
            if any(ref.casefold() in entry['text'].casefold() for ref in audit['reference_answers']):
                raise ValueError('Answer alias survives key-hop deletion')
        if not challenged:
            raise ValueError('Deletion requires at least one remaining passage')
        normal = finalize(normal_question, entries, kind, 'normal', audit, dict(common, operation='support_topup'))
        challenge = finalize(challenge_question, challenged, kind, kind, audit,
                             dict(common, operation='delete_key_support', removed_evidence=removed))
    elif kind == 'evidence_conflict':
        policy = ('Record policy: if records disagree, use the entry marked source_tier=primary; '
                  'source_tier=secondary cannot override it.\nOriginal question: ')
        normal_question['question'] = challenge_question['question'] = DISCLOSURE + policy + question['question']
        primary = [evidence_entry(doc, version='source_tier=primary') for doc in gold]
        secondary = evidence_entry(target, version='source_tier=secondary')
        altered = evidence_entry(target, replace_value(target.text, answer, replacement), 'source_tier=secondary')
        normal_entries = primary + [secondary] + distractors
        challenge_entries = primary + [altered] + distractors
        # Same placement in a pair; balanced primary/secondary precedence across base IDs.
        first = int(fingerprint([seed, question['base_question_id'], 'source-order']), 16) % 2
        if first:
            normal_entries = [secondary] + primary + distractors
            challenge_entries = [altered] + primary + distractors
        normal = finalize(normal_question, normal_entries, kind, 'normal', audit, dict(common, operation='agreeing_sources'))
        challenge = finalize(challenge_question, challenge_entries, kind, kind, audit,
                             dict(common, operation='replace_secondary_value', before=secondary, after=altered))
    elif kind == 'outdated_answer':
        policy = ('Query date: 2025-06-01. Record policy: use the version whose stated validity interval '
                  'contains the query date; the 2025 update explicitly supersedes the previous version.\nOriginal question: ')
        normal_question['question'] = challenge_question['question'] = DISCLOSURE + policy + question['question']
        # Both queries target the same new value, never a hidden present-day oracle.
        audit['reference_answers'] = [replacement]
        audit['version_facts'] = {'old_value': answer, 'new_value': replacement,
                                 'old_valid_until': '2024-12-31', 'new_valid_from': '2025-01-01',
                                 'query_date': '2025-06-01', 'synthetic_version_scenario': True}
        current = [evidence_entry(doc, replace_value(doc.text, answer, replacement),
                                 'valid_from=2025-01-01; valid_until=2025-12-31; supersedes=2024-record') for doc in gold]
        agreeing_copy = [evidence_entry(doc, replace_value(doc.text, answer, replacement),
                                      'valid_from=2025-01-01; valid_until=2025-12-31; copy=current') for doc in gold]
        old = [evidence_entry(doc, version='valid_from=2024-01-01; valid_until=2024-12-31; superseded_by=2025-update') for doc in gold]
        first = int(fingerprint([seed, question['base_question_id'], 'version-order']), 16) % 2
        normal_entries = (agreeing_copy + current if first else current + agreeing_copy) + distractors
        challenge_entries = (old + current if first else current + old) + distractors
        normal = finalize(normal_question, normal_entries, kind, 'normal', audit, dict(common, operation='current_agreeing_copies'))
        challenge = finalize(challenge_question, challenge_entries, kind, kind, audit,
                             dict(common, operation='introduce_expired_record', old_evidence=old, current_evidence=current))
    else:
        raise ValueError('Unknown challenge type')
    return normal, challenge


def prepare_challenges(config, run, root):
    challenge_config = config['challenge']
    pilot = Path(root) / challenge_config['confirmed_pilot']
    confirmation = json.loads((pilot/'review_confirmation.json').read_text())
    if json.loads((pilot/'status.json').read_text())['stage'] != 'complete' or confirmation['status'] != 'user_confirmed':
        raise ValueError('P2.5 user-reviewed pilot must be complete first')
    if file_sha256(pilot/'confirmed_review.jsonl') != confirmation['confirmed_review_sha256']:
        raise ValueError('Confirmed labels changed')
    excluded = read_jsonl(pilot/'prepared.jsonl')
    excluded_sources = {s for row in excluded for s in row['source_document_ids']}
    excluded_ids = {row['base_question_id'] for row in excluded}
    pool, corpus, sources = [], {}, {}
    rejected = Counter()
    for name in SOURCES:
        revision = config['data'][name+'_revision']
        raw, sources[name] = read_pool(name, revision, Path(root)/'.cache/rag/hub',
                                      config['data']['pool_per_dataset'], config['seed'])
        for item in raw:
            question, docs = convert_question(name, item, revision)
            corpus.update({doc.document_id: doc for doc in docs})
            refs = question['audit']['reference_answers']
            answer = refs[0].strip()
            gold = [doc for doc in docs if doc.document_id in question['audit']['gold_document_ids']]
            reason = None
            if question['base_question_id'] in excluded_ids or set(question['source_document_ids']) & excluded_sources:
                reason = 'pilot_source_overlap'
            elif not 3 <= len(answer) <= 60 or len(answer.split()) > 8 or answer.casefold() in ('yes','no'):
                reason = 'not_short_explicit_value'
            elif len(gold) > 2 or any(len(doc.text.split()) > 220 for doc in gold):
                reason = 'support_exceeds_controlled_budget'
            elif not any(answer.casefold() in doc.text.casefold() for doc in gold) or answer.casefold() in question['question'].casefold():
                reason = 'target_not_explicit_or_already_in_question'
            if reason:
                rejected[reason] += 1
            else:
                pool.append((question, docs))
    pool.sort(key=lambda pair: fingerprint([config['seed'], 'challenge-base', pair[0]['base_question_id']]))
    retriever = Retriever(list(corpus.values()), k1=config['retrieval']['k1'], b=config['retrieval']['b'])
    records, selections, used_sources, used_ids = [], [], set(), set()
    target_count = challenge_config['per_type'] // len(SOURCES)
    if challenge_config['per_type'] % len(SOURCES):
        raise ValueError('Per-type sample count must divide evenly across datasets')
    for kind in TYPES:
        for name in SOURCES:
            count = 0
            for question, docs in pool:
                if question['dataset'] != name or question['base_question_id'] in used_ids:
                    continue
                if set(question['source_document_ids']) & used_sources:
                    rejected['shared_selected_source'] += 1
                    continue
                answer = question['audit']['reference_answers'][0]
                try:
                    replacement = replacement_for(question,pool,config['seed']) if kind != 'retrieval_failure' else None
                except ValueError:
                    rejected['no_replacement'] += 1
                    continue
                retrieved = retriever.search(question['question'], config['retrieval']['top_k'],
                                             config['retrieval']['max_words_per_document'], config['retrieval']['max_evidence_words'])
                try:
                    pair = make_pair(question, docs, retrieved, kind, replacement, config['seed'])
                except ValueError:
                    rejected['ambiguous_or_empty_intervention'] += 1
                    continue
                if any(sum(len(e['text'].split()) for e in row['evidence']) > config['retrieval']['max_evidence_words'] for row in pair):
                    rejected['evidence_budget'] += 1
                    continue
                records.extend(pair)
                used_ids.add(question['base_question_id'])
                used_sources.update(question['source_document_ids'])
                selections.append({'base_question_id': question['base_question_id'], 'dataset': name, 'challenge_type': kind})
                count += 1
                if count == target_count:
                    break
            if count != target_count:
                raise RuntimeError(f'Insufficient eligible {name}/{kind}: {count}/{target_count}; do not silently change sampling')
    assign_groups(records)
    for row in records:
        validate_record(row)
    write_jsonl(run/'prepared.jsonl', records)
    write_jsonl(run/'corpus.jsonl', [document_dict(doc) for doc in retriever.documents])
    write_json(run/'selection_manifest.json', {'selected': selections, 'rejected_counts': dict(rejected),
               'selection_rule': 'fixed seeded ID order, textual construction eligibility only; no model scores',
               'excluded_pilot_sources': sorted(excluded_sources)})
    write_json(run/'data_manifest.json', {'sources': sources, 'seed': config['seed'], 'records': len(records),
               'base_questions': len(selections), 'groups': len({r['group_id'] for r in records}),
               'corpus_documents': len(corpus), 'construction_protocol': VERSION,
               'corpus_scope': 'Controlled support-topup intervention pilot; not full-Wikipedia retrieval evaluation.',
               'prepared_sha256': file_sha256(run/'prepared.jsonl'), 'corpus_sha256': file_sha256(run/'corpus.jsonl'),
               'confirmed_pilot_review_sha256': confirmation['confirmed_review_sha256'],
               'condition_counts': dict(Counter(r['condition'] for r in records)),
               'labels_created_by_construction': 0})
    print(f'Prepared {len(records)} records from {len(selections)} bases; no answer labels inferred.', flush=True)
