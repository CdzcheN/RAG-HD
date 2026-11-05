"""CPU preflight and separate development/test packs; never run model inference."""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from rag_hd.challenges_v2 import canonical_title, bounded_occurrences
from rag_hd.formal_cleaning import aliases
from rag_hd.formal_protocol import verify_source_isolation
from rag_hd.generation import messages
from rag_hd.self_check import messages as assessment_messages
from rag_hd.io import read_jsonl, write_jsonl, write_json, file_sha256, fingerprint
from rag_hd.schema import visible_input, validate_record


def package(run, records, config):
    """Test receives no runnable convenience launcher; development is the first stage."""
    corpus = {d['document_id']:d for d in read_jsonl(run/'corpus.jsonl')}
    result = {}
    for name, rows in [('development',[r for r in records if r['formal_split']!='test']),
                       ('test',[r for r in records if r['formal_split']=='test'])]:
        directory = run/'partitions'/name
        if directory.exists(): raise ValueError('Do not overwrite an existing inference pack')
        directory.mkdir(parents=True)
        raw_ids = {d for r in rows for d in r['audit']['gold_document_ids']}
        raw_ids.update(e.get('origin_document_id',e['document_id']) for r in rows for e in r['evidence'])
        write_jsonl(directory/'prepared.jsonl',rows)
        write_jsonl(directory/'corpus.jsonl',[corpus[d] for d in sorted(raw_ids)])
        manifest = json.loads((run/'data_manifest.json').read_text())
        manifest.update(records=len(rows),base_questions=len(rows)//2,groups=len({r['group_id'] for r in rows}),
                        prepared_sha256=file_sha256(directory/'prepared.jsonl'),
                        corpus_sha256=file_sha256(directory/'corpus.jsonl'),
                        condition_counts=dict(Counter(r['condition'] for r in rows)),
                        parent_prepared_sha256=file_sha256(run/'prepared.jsonl'),
                        execution_partition=name,
                        purpose='Formal development inputs' if name=='development' else 'Held-out final test; model/threshold freeze required before inference')
        write_json(directory/'data_manifest.json',manifest)
        write_json(directory/'config.json',config)
        for filename in ('runtime_manifest.json','frozen_splits.json','frozen_rule_assignments.jsonl'):
            shutil.copy2(run/filename,directory/filename)
        write_json(directory/'status.json',{'stage':'prepare_complete' if name=='development' else 'held_out_pending_model_freeze'})
        with (run/'construction_review.csv').open(encoding='utf-8-sig',newline='') as stream:
            reader = csv.DictReader(stream); columns = reader.fieldnames
            table = list(reader)
        indices = {r['source_cleaning_number'] for r in rows}
        with (directory/'construction_review.csv').open('w',encoding='utf-8-sig',newline='') as stream:
            writer = csv.DictWriter(stream,fieldnames=[*columns,'原清洗编号'])
            writer.writeheader()
            for index,row in enumerate((r for r in table if int(r['编号']) in indices),1):
                writer.writerow(dict(row,编号=index,原清洗编号=row['编号']))
        result[name] = {'directory':str(directory),'rows':len(rows),
                        'prepared_sha256':file_sha256(directory/'prepared.jsonl')}
    return result


def verify(run):
    from transformers import AutoTokenizer
    config = json.loads((run/'config.json').read_text())
    manifest = json.loads((run/'data_manifest.json').read_text())
    if manifest['prepared_sha256'] != file_sha256(run/'prepared.jsonl'):
        raise ValueError('Prepared data changed')
    records = read_jsonl(run/'prepared.jsonl')
    if len(records)!=600 or len({r['base_question_id'] for r in records})!=300:
        raise ValueError('Expected exactly 300 pairs')
    if any('answer' in r or r['evidence_label']!='undetermined' for r in records):
        raise ValueError('Preflight must precede actual answers and labels')
    for r in records:
        validate_record(r)
        if r['visible_input_sha256'] != fingerprint(visible_input(r)):
            raise ValueError('Input digest mismatch')
    specs = json.loads((run/'frozen_specs.json').read_text())
    for spec, normal, challenge in zip(specs,records[::2],records[1::2]):
        if (normal['base_question_id'] != spec['base_question_id'] or normal['pair_id']!=challenge['pair_id'] or
                normal['question']!=challenge['question'] or normal['condition']!='normal' or
                normal['formal_split']!=challenge['formal_split']):
            raise ValueError('Source specification or paired input mismatch')
        if len(normal['evidence'])!=5 or len(challenge['evidence'])!=5:
            raise ValueError('Paired evidence counts differ')
        construction = challenge['construction']
        if not construction['declared_constraints_passed']:
            raise ValueError('Unchecked source arithmetic')
        prohibited = aliases(construction['original_value'])
        if construction['replacement_value']:
            prohibited += aliases(construction['replacement_value'])
        for record in (normal,challenge):
            for e in record['evidence']:
                if 'origin_document_id' not in e and any(bounded_occurrences(e['title']+' '+e['text'], a) for a in prohibited):
                    raise ValueError('Original/altered answer alias survived in noise')
        if challenge['condition']=='retrieval_failure' and any('origin_document_id' in e for e in challenge['evidence']):
            raise ValueError('Gold excerpt survived complete support deletion')
    raw_corpus = {d['document_id']:d for d in read_jsonl(run/'corpus.jsonl')}
    nominated = [{'base_question_id':r['base_question_id'],
                  'gold_titles':[raw_corpus[d]['title'] for d in r['audit']['gold_document_ids']]} for r in records[::2]]
    splits = json.loads((run/'frozen_splits.json').read_text())
    isolation = verify_source_isolation(nominated,read_jsonl(run/'noise_reservations.jsonl'),splits)
    model = config['generation']
    tokenizer = AutoTokenizer.from_pretrained(model['model_id'],revision=model['revision'],
                    cache_dir=str(ROOT/'.cache/rag/hub'),local_files_only=True,trust_remote_code=False)
    lengths, assessment_budgets = [], []
    for r in records:
        lengths.append(len(tokenizer.apply_chat_template(messages(r),tokenize=True,add_generation_prompt=True)))
        base = len(tokenizer.apply_chat_template(assessment_messages(r,''),tokenize=True,add_generation_prompt=True))
        assessment_budgets.append(base+2*model['max_new_tokens']+2*model['self_max_new_tokens']+200)
    if max(lengths)>model['max_input_tokens'] or max(assessment_budgets)>model['max_input_tokens']:
        raise ValueError('Input or conservative self-assessment budget exceeds configured context')
    implementations = {str(path.relative_to(ROOT)):file_sha256(path) for path in [
        ROOT/'src/rag_hd'/name for name in ('generation.py','self_check.py','minicheck_adapter.py','valid_evidence.py')]}
    packs = package(run,records,config)
    report = {'status':'preflight_complete','prepared_inputs_ready':True,'inference_started':False,
              'source_cleaning_rows':300,'inputs':600,'challenge_inputs':300,'normal_inputs':300,
              'source_reviews_origin':'assistant_source_text_review','independent_human_annotation':False,
              'replaced_candidates':20,'actual_answer_labels_created':0,
              'all_pair_questions_match':True,'all_evidence_counts':5,
              'complete_support_removal_checked':True,'new_old_numeric_aliases_absent_from_noise':True,
              'common_number_word_aliases_checked':True,'checks_do_not_exhaust_all_implicit_semantic_inference':True,
              'declared_numeric_constraints_checked':True,'partition_checks':isolation,
              'max_generation_prompt_tokens':max(lengths),'max_self_check_budget_estimate':max(assessment_budgets),
              'self_check_budget_note':'Conservative allowance; runtime retains strict no-truncation checks.',
              'max_input_tokens':model['max_input_tokens'],'tokenizer_revision':model['revision'],
              'partitions':packs,'test_inference_gate':'Freeze models and validation thresholds before test inference',
              'inference_implementation':implementations,'prepared_sha256':file_sha256(run/'prepared.jsonl'),
              'config_sha256':file_sha256(run/'config.json')}
    write_json(run/'preflight.json',report)
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir',type=Path,required=True)
    args = parser.parse_args()
    verify(args.run_dir)
