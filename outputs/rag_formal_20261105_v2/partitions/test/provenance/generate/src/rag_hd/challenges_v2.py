"""Source-audited quantity interventions; legacy v1 predictions remain untouched."""
from collections import Counter
from copy import deepcopy
from decimal import Decimal
from html import unescape
import json
from pathlib import Path
import re
from urllib.parse import unquote
import unicodedata

from .challenges import DISCLOSURE, evidence_entry
from .construction_edits import apply, locate, quantity_change, number, format_number, validate_constraints
from .data import SOURCES, convert_question, read_pool
from .io import read_jsonl, write_jsonl, write_json, fingerprint, file_sha256
from .retrieval import Retriever
from .schema import Document, assign_groups, document_dict, evidence_text, visible_input, validate_record

VERSION='controlled-challenge-v2'


def canonical_title(title):
    return ' '.join(unicodedata.normalize('NFKC',unescape(unquote(title))).replace('_',' ').casefold().split())


def bounded_occurrences(text, value):
    if re.fullmatch(r'\d+(?:[,.]\d+)*%?',value):
        return [m for m in re.finditer(r'(?<!\w)\d+(?:[,.]\d+)*%?(?!\w)',text) if m.group()==value]
    return list(re.finditer(r'(?<!\w)'+re.escape(value)+r'(?!\w)',text,re.I))


def build_pair(question, docs, noise, spec, seed, index):
    kind=spec['type']
    original=question['audit']['reference_answers'][0].strip()
    gold_ids=set(question['audit']['gold_document_ids'])
    gold=[doc for doc in docs if doc.document_id in gold_ids]
    if not gold or len(noise)<5:
        raise ValueError('Need complete source support and five non-answer distractors')
    revised=spec.get('question_override') or question['question']
    if re.search(r'\b(this|that|these|those|it|he|she|they)\b',revised,re.I):
        raise ValueError('Question must be explicitly self-contained in the audited small pilot')
    excerpts=[]
    for doc in gold:
        start,end=spec['excerpt_spans'].get(doc.document_id,[0,len(doc.text)])
        if not 0<=start<end<=len(doc.text):
            raise ValueError('Invalid exact-source excerpt')
        excerpts.append({'doc':doc,'title':doc.title,'text':doc.text[start:end],
                         'source_excerpt_start':start,'source_excerpt_end':end})
    occurrences=[(i,m) for i,doc in enumerate(excerpts) for m in bounded_occurrences(doc['text'],original)]
    if len(occurrences)!=1:
        raise ValueError('Require one unambiguous target slot in the visible source excerpts')
    target_index,target_match=occurrences[0]
    bounds=spec.get('target_bounds',{})
    direction=1 if int(fingerprint([seed,question['base_question_id'],'quantity-direction']),16)%2 else -1
    replacement=quantity_change(original,direction,role=spec['slot_role'],
                                lower=bounds.get('lower'),upper=bounds.get('upper'))
    target=excerpts[target_index]
    edits=[locate('text',target['text'],original,replacement,'answer_quantity')]
    values_before={'target':original};values_after={'target':replacement};constraints=[]
    coupled=spec.get('coupled_quantity')
    if coupled:
        if coupled['relation']!='complement_to_100':
            raise ValueError('Unsupported linked quantity relation')
        updated=format_number(Decimal(100)-number(replacement),coupled['old'])
        edits.append(locate('text',target['text'],coupled['old'],updated,coupled['role']))
        values_before[coupled['role']]=coupled['old'];values_after[coupled['role']]=updated
        constraints.append({'kind':'sum','keys':['target',coupled['role']],'total':'100'})
    if bounds:
        constraints.append({'kind':'between','key':'target','lower':bounds['lower'],'upper':bounds['upper']})
    if kind=='retrieval_failure':
        values_after=dict(values_before)  # Deletion does not apply the proposed quantity edit.
    validate_constraints(values_before,constraints);validate_constraints(values_after,constraints)
    mutated=deepcopy(excerpts)
    modified,edit_log=apply({'title':target['title'],'text':target['text']},edits)
    mutated[target_index].update(modified)
    def entries(items,version):
        return [evidence_entry(item['doc'],item['text'],version) for item in items]
    base_entries=entries(excerpts,'source_snapshot=original_excerpt')
    scope=('Evidence scope: '+unquote(gold[0].title).replace('_',' ')+'. ') if question['dataset']=='squad' else ''
    scoped=scope+revised
    audit=deepcopy(question['audit'])
    audit.update(original_question=question['question'],question_revision={'before':question['question'],
                 'after':revised,'rationale':spec['curation_note']},
                 source_reference_answers=deepcopy(question['audit']['reference_answers']),
                 source_excerpts=[{'document_id':x['doc'].document_id,'start':x['source_excerpt_start'],
                                   'end':x['source_excerpt_end']} for x in excerpts],
                 all_gold_support_visible=False,normal_support_mode='audited_source_excerpts_plus_bm25_distractors')
    construction={'protocol':VERSION,'type':kind,'seed':seed,'original_value':original,
                  'replacement_value':replacement if kind!='retrieval_failure' else None,
                  'target_document_id':target['doc'].document_id,'slot_role':spec['slot_role'],
                  'curation_note':spec['curation_note'],'exact_span_edits':edit_log if kind!='retrieval_failure' else [],
                  'constraints':constraints,'values_before':values_before,'values_after':values_after,
                  'not_an_answer_label':True}
    if kind=='retrieval_failure':
        public_question=scoped
        normal=base_entries+deepcopy(noise[:5-len(base_entries)])
        challenge=deepcopy(noise[:5])
        construction['removed_evidence']=base_entries
        if any(bounded_occurrences(e['title']+' '+e['text'],answer)
               for e in challenge for answer in question['audit']['reference_answers']):
            raise ValueError('Answer alias/title survives complete-support removal')
    elif kind=='evidence_conflict':
        public_question=DISCLOSURE+('Record policy: if records disagree, use the entry marked source_tier=primary; '
                         'source_tier=secondary cannot override it.\nOriginal question: ')+scoped
        primary=entries(excerpts,'source_tier=primary')
        agreeing=entries(excerpts,'source_tier=secondary')
        competing=entries(mutated,'source_tier=secondary')
        normal=(primary+agreeing if index%2 else agreeing+primary)
        challenge=(primary+competing if index%2 else competing+primary)
        normal+=deepcopy(noise[:5-len(normal)]);challenge+=deepcopy(noise[:5-len(challenge)])
    elif kind=='outdated_answer':
        year=(2020,2022,2024)[index%3]
        current=f'valid_from={year}-01-01; valid_until={year}-12-31; supersedes={year-1}-record'
        old=f'valid_from={year-1}-01-01; valid_until={year-1}-12-31; superseded_by={year}-update'
        public_question=DISCLOSURE+(f'Query date: {year}-06-01. Record policy: use the version whose stated validity interval '
                         f'contains the query date; the {year} update explicitly supersedes the previous version. '
                         'Versions correct the reported statistic for the same observation; the historical observation date does not change.\nOriginal question: ')+scoped
        valid=entries(mutated,current)
        agreeing=entries(mutated,current+'; copy=current')
        expired=entries(excerpts,old)
        normal=(valid+agreeing if index%2 else agreeing+valid)
        challenge=(valid+expired if index%2 else expired+valid)
        normal+=deepcopy(noise[:5-len(normal)]);challenge+=deepcopy(noise[:5-len(challenge)])
        audit['reference_answers']=[replacement]
        audit['version_facts']={'old_value':original,'new_value':replacement,'query_date':f'{year}-06-01',
                                'synthetic_version_scenario':True,'interpretation':'reported_statistic_correction'}
    else:
        raise ValueError('Unknown intervention')
    output=[]
    for variant,evidence in [('normal',normal),(kind,challenge)]:
        for rank,entry in enumerate(evidence,1):entry['rank']=rank
        row=deepcopy(question)
        row['audit']=deepcopy(audit)
        row['audit']['original_source_document_ids']=list(question['source_document_ids'])
        row['source_document_ids']=sorted({'wiki-v2:'+fingerprint(canonical_title(d.title)) for d in gold})
        row.update(question=public_question,evidence=evidence,visible_evidence=evidence_text(evidence),
                   construction=deepcopy(construction),condition=variant,challenge_type=kind,
                   construction_protocol=VERSION,protocol_version='rag-prototype-v1',evidence_label='undetermined')
        row['visible_input_sha256']=fingerprint(visible_input(row))
        row['pair_id']='pair:'+fingerprint([question['base_question_id'],kind,VERSION])
        row['sample_id']='sample:'+fingerprint([row['pair_id'],variant,row['visible_input_sha256']])
        if len(evidence)!=5 or sum(len(e['text'].split()) for e in evidence)>1200:
            raise ValueError('Paired evidence count/budget exceeded')
        output.append(row)
    return output


def prepare(config,run,root):
    if (run/'generation.jsonl').exists():
        raise ValueError('Do not replace prepared inputs after generation; choose a new run')
    settings=config['challenge'];root=Path(root)
    specs=json.loads((root/settings['specs']).read_text())
    if len(specs)!=30 or Counter(s['type'] for s in specs)!={'retrieval_failure':10,'evidence_conflict':10,'outdated_answer':10}:
        raise ValueError('This repair pilot fixes exactly 30 audited specifications')
    excluded_sources=set();excluded_titles=set();excluded_questions=set();exclusion_manifests={}
    for previous in settings['previous_runs']:
        path=root/previous
        if json.loads((path/'status.json').read_text())['stage']!='complete':
            raise ValueError('Previous development run must be complete')
        previous_corpus={d['document_id']:d for d in read_jsonl(path/'corpus.jsonl')}
        for r in read_jsonl(path/'prepared.jsonl'):
            excluded_sources.update(r['source_document_ids'])
            excluded_sources.update(e['source_document_id'] for e in r['evidence'])
            excluded_titles.update(canonical_title(e['title']) for e in r['evidence'])
            excluded_titles.update(canonical_title(previous_corpus[doc_id]['title']) for doc_id in r['audit']['gold_document_ids'])
            excluded_questions.add(r['base_question_id'])
        exclusion_manifests[previous]=file_sha256(path/'prepared.jsonl')
    all_docs,chosen,sources={},{},{}
    spec_ids={s['base_question_id'] for s in specs}
    for name in SOURCES:
        revision=config['data'][name+'_revision']
        pool,sources[name]=read_pool(name,revision,root/'.cache/rag/hub',config['data']['pool_per_dataset'],config['seed'])
        for raw in pool:
            question,docs=convert_question(name,raw,revision)
            for doc in docs:
                if doc.source_document_id not in excluded_sources and canonical_title(doc.title) not in excluded_titles:
                    all_docs[doc.document_id]=doc
            if question['base_question_id'] in spec_ids:
                if question['base_question_id'] in excluded_questions or set(question['source_document_ids'])&excluded_sources:
                    raise ValueError('Selected base overlaps prior development sources')
                gold=[d for d in docs if d.document_id in question['audit']['gold_document_ids']]
                if any(canonical_title(d.title) in excluded_titles for d in gold):
                    raise ValueError('Encoded title alias overlaps prior development')
                chosen[question['base_question_id']]=(question,docs)
    if set(chosen)!=spec_ids:
        raise ValueError('Audited specification not present in pinned source pool')
    selected_sources=set()
    selected_titles=set()
    for question,docs in chosen.values():
        if selected_sources & set(question['source_document_ids']):
            raise ValueError('Selected base source groups overlap')
        selected_sources.update(question['source_document_ids'])
        titles={canonical_title(d.title) for d in docs if d.document_id in question['audit']['gold_document_ids']}
        if titles&selected_titles:
            raise ValueError('Canonical source titles overlap across bases')
        selected_titles.update(titles)
    if Counter((s['type'],chosen[s['base_question_id']][0]['dataset']) for s in specs)!={
            (kind,name):5 for kind in ('retrieval_failure','evidence_conflict','outdated_answer') for name in SOURCES}:
        raise ValueError('Require five bases per dataset per type')
    noise_docs=sorted([doc for doc in all_docs.values() if doc.source_document_id not in selected_sources and canonical_title(doc.title) not in selected_titles],
                      key=lambda d:fingerprint([config['seed'],'repair-noise',d.document_id]))[:settings['max_noise_corpus']]
    retriever=Retriever(noise_docs)
    records=[]
    for index,spec in enumerate(specs,1):
        question,docs=chosen[spec['base_question_id']]
        retrieved=retriever.search(spec.get('question_override') or question['question'],50,150,7500)
        safe=[e for e in retrieved if not any(bounded_occurrences(e['title']+' '+e['text'],answer)
                    for answer in question['audit']['reference_answers'])]
        pair=build_pair(question,docs,safe,spec,config['seed'],index)
        for row in pair:row['audit']['retrieval_before_intervention']=retrieved
        records.extend(pair)
    assign_groups(records)
    for row in records:validate_record(row)
    assert not excluded_sources & {e['source_document_id'] for r in records for e in r['evidence']}
    assert not excluded_titles & {canonical_title(e['title']) for r in records for e in r['evidence']}
    corpus={doc.document_id:doc for doc in noise_docs}
    for question,docs in chosen.values():
        for doc in docs:
            if doc.document_id in question['audit']['gold_document_ids']:corpus[doc.document_id]=doc
    write_jsonl(run/'prepared.jsonl',records)
    write_jsonl(run/'corpus.jsonl',[document_dict(d) for d in corpus.values()])
    write_json(run/'data_manifest.json',{'sources':sources,'seed':config['seed'],'records':len(records),
        'base_questions':30,'groups':len({r['group_id'] for r in records}),'construction_protocol':VERSION,
        'corpus_documents':len(corpus),'prepared_sha256':file_sha256(run/'prepared.jsonl'),
        'corpus_sha256':file_sha256(run/'corpus.jsonl'),'specs_sha256':file_sha256(root/settings['specs']),
        'prior_source_exclusion_sha256':exclusion_manifests,'excluded_prior_source_count':len(excluded_sources),
        'old_visible_source_overlap':0,'normal_and_challenge_evidence_count':5,
        'canonical_title_alias_overlap':0,'source_alias_normalization':'URL-decode, HTML-unescape, NFKC, underscore, case, whitespace',
        'condition_counts':dict(Counter(r['condition'] for r in records)),'labels_created_by_construction':0,
        'selection':'assistant source-text-audited specifications; not model-score selected',
        'purpose':'construction repair development pilot, not final held-out evaluation',
        'corpus_scope':'Audited source support plus fixed seeded fresh distractor corpus; controlled intervention only.'})
    print('Prepared 30 audited v2 pairs / 60 inputs, no old visible sources, no outcome labels.',flush=True)
