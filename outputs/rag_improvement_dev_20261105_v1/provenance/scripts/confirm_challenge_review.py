"""Import the user-confirmed Chinese tables without exposing bookkeeping columns."""
import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from rag_hd.io import file_sha256, fingerprint, read_jsonl, write_json, write_jsonl
from rag_hd.schema import LABELS, visible_input


def read_table(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def confirm(run, confirmation):
    if not confirmation.strip():
        raise ValueError('Explicit user confirmation required')
    records = read_jsonl(run/'prepared.jsonl')
    generated = {r['sample_id']:r for r in read_jsonl(run/'generation.jsonl')}
    table = read_table(run/'review_readable.csv')
    drafts = {r['sample_id']:r for r in read_jsonl(run/'review_drafts/answer_assessments.jsonl')}
    construction = read_table(run/'construction_review.csv')
    findings = {r['pair_id']:r for r in read_jsonl(run/'review_drafts/construction_assessments.jsonl')}
    mappings = {str(r['display_number']):r for r in __import__('json').loads((run/'review_row_mapping.json').read_text())['rows']}
    if len(table) != len(records) or len(construction)*2 != len(records):
        raise ValueError('Both confirmed tables must be complete')
    by_id = {r['sample_id']:r for r in records}
    reviews, seen = [], set()
    for row in table:
        number = row['编号']
        if number in seen or number not in mappings:
            raise ValueError('Duplicate or unknown display number')
        seen.add(number)
        mapping = mappings[number]
        record = by_id[mapping['sample_id']]
        answer = generated[record['sample_id']]
        for field, value in [('问题',record['question']),('可见证据',record['visible_evidence']),
                             ('生成回答',answer['answer']),('参考答案','；'.join(record['audit']['reference_answers']))]:
            if row[field] != value:
                raise ValueError(f'Immutable reviewed content changed: {field}')
        if mapping['answer_sha256'] != fingerprint(answer['answer']) or mapping['visible_input_sha256'] != fingerprint(visible_input(record)):
            raise ValueError('Reviewed input/answer provenance mismatch')
        label, correctness = row['证据支持标签'], row['答案正确性']
        if label not in LABELS or correctness not in ('correct','incorrect','undetermined') or not row['判断依据'].strip():
            raise ValueError('Every row requires valid labels and rationale')
        if answer['is_refusal'] and label != 'undetermined':
            raise ValueError('Keep refusals outside factual-answer labels')
        reviews.append({'sample_id':record['sample_id'],'question':record['question'],
                        'visible_evidence':record['visible_evidence'],'answer':answer['answer'],
                        'visible_input_sha256':record['visible_input_sha256'],
                        'answer_sha256':fingerprint(answer['answer']), 'evidence_label':label,
                        'answer_correctness':correctness,'rationale':row['判断依据'],
                        'review_source':'human','reviewer':'user-confirmed assistant draft',
                        'annotation_origin':'assistant_draft_confirmed_by_user',
                        'assistant_draft':drafts[record['sample_id']], 'confirmation':confirmation})
    quality, seen_pairs = [], set()
    for row in construction:
        number = int(row['编号'])
        if number in seen_pairs or not 1 <= number <= len(construction):
            raise ValueError('Duplicate or unknown construction number')
        seen_pairs.add(number)
        a,b = records[2*number-2:2*number]
        for field, value in [('挑战类型',b['challenge_type']),('原始问题',b['audit']['original_question']),
                             ('原始值',b['construction']['original_value']),
                             ('替换值',b['construction']['replacement_value'] or '不涉及替换'),
                             ('正常证据',a['visible_evidence']),('挑战证据',b['visible_evidence'])]:
            if row[field] != value:
                raise ValueError(f'Construction content changed: {field}')
        finding = findings[a['pair_id']]
        if not row['构造检查备注'].strip():
            raise ValueError('Missing construction review')
        kind = finding['construction_finding'] if row['构造检查备注'] == finding['rationale'] else 'user_edited_needs_classification'
        quality.append({'pair_id':a['pair_id'],'group_id':a['group_id'],'display_number':number,
                        'finding':kind,'basic':kind=='basic','rationale':row['构造检查备注'],
                        'annotation_origin':'assistant_draft_confirmed_by_user'})
    backup = run/'provenance/before_review_confirmation_20261105'
    backup.mkdir(parents=True,exist_ok=True)
    for name in ('records.jsonl','metrics.json','status.json'):
        if not (backup/name).exists():
            shutil.copy2(run/name,backup/name)
    write_jsonl(run/'confirmed_review.jsonl',reviews)
    write_jsonl(run/'confirmed_construction.jsonl',quality)
    write_json(run/'review_confirmation.json',{
        'status':'user_confirmed','rows':len(reviews),'construction_pairs':len(quality),
        'confirmation':confirmation,'recorded_at_utc':datetime.now(timezone.utc).isoformat(),
        'annotation_origin':'assistant_draft_confirmed_by_user','independent_human_annotation':False,
        'reviewed_table_sha256':file_sha256(run/'review_readable.csv'),
        'construction_table_sha256':file_sha256(run/'construction_review.csv'),
        'confirmed_review_sha256':file_sha256(run/'confirmed_review.jsonl')})
    print(f'Confirmed {len(reviews)} answer rows and {len(quality)} pairs; undetermined retained.')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir',type=Path,required=True)
    parser.add_argument('--confirmation',required=True)
    args=parser.parse_args()
    confirm(args.run_dir,args.confirmation)
