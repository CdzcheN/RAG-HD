"""Fill the readable review sheets from score-blind assistant draft assessments."""
import argparse
from collections import Counter
import csv
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from rag_hd.io import file_sha256, fingerprint, read_jsonl, write_json
from rag_hd.schema import LABELS, visible_input


def read_table(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        return reader.fieldnames, list(reader)


def write_table(path, fields, rows):
    temporary = path.with_suffix('.csv.tmp')
    with temporary.open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def prefill(run, preserve_construction_notes=False):
    records = read_jsonl(run/'prepared.jsonl')
    generated = {r['sample_id']:r for r in read_jsonl(run/'generation.jsonl')}
    drafts = read_jsonl(run/'review_drafts/answer_assessments.jsonl')
    constructions = read_jsonl(run/'review_drafts/construction_assessments.jsonl')
    answers_path, construction_path = run/'review_readable.csv', run/'construction_review.csv'
    fields, rows = read_table(answers_path)
    cfields, crows = read_table(construction_path)
    if (not records or not len(records) == len(drafts) == len(rows)
            or len(records) != 2*len(constructions) or len(constructions) != len(crows)):
        raise ValueError('Require every answer and exactly one construction review per pair')
    if any(r['判断依据'].strip() for r in rows) or (not preserve_construction_notes and any(r['构造检查备注'].strip() for r in crows)):
        raise ValueError('Review notes already exist; refusing to overwrite possible user edits')
    if any(r['证据支持标签'] != 'undetermined' or r['答案正确性'] != 'undetermined' for r in rows):
        raise ValueError('Existing labels were edited; preserve them before prefilling')
    official_paths = [run/'records.jsonl', run/'metrics.json', run/'status.json']
    official = {str(p):file_sha256(p) for p in official_paths}
    for index, (row, record, draft) in enumerate(zip(rows, records, drafts), 1):
        answer = generated[record['sample_id']]
        if row['编号'] != str(index) or draft['display_number'] != index or draft['sample_id'] != record['sample_id']:
            raise ValueError('Draft or display row identity mismatch')
        for column, expected in [('问题',record['question']), ('可见证据',record['visible_evidence']),
                                 ('生成回答',answer['answer']), ('参考答案','；'.join(record['audit']['reference_answers']))]:
            if row[column] != expected:
                raise ValueError(f'Original reviewed content changed: {column}')
        if (draft['answer_sha256'] != fingerprint(answer['answer']) or
                draft['visible_input_sha256'] != fingerprint(visible_input(record))):
            raise ValueError('Draft is for different evidence or answer')
        if draft['review_source'] != 'assistant' or draft['status'] != 'pending_user_review':
            raise ValueError('Do not misrepresent draft provenance')
        if draft['evidence_label'] not in LABELS or draft['answer_correctness'] not in ('correct','incorrect','undetermined'):
            raise ValueError('Invalid draft labels')
        if not draft['rationale'].strip():
            raise ValueError('Missing per-answer rationale')
        if answer['is_refusal'] and draft['evidence_label'] != 'undetermined':
            raise ValueError('Refusal must stay outside factual-answer labeling')
        if not draft['evidence_anchors']:
            raise ValueError('At least one visible passage anchor is required')
        for anchor in draft['evidence_anchors']:
            start, end = anchor['start'], anchor['end']
            if not 0 <= start < end <= len(record['visible_evidence']) or record['visible_evidence'][start:end] != anchor['quote']:
                raise ValueError('Evidence anchor must refer to actual visible text')
        row.update(证据支持标签=draft['evidence_label'], 答案正确性=draft['answer_correctness'], 判断依据=draft['rationale'])
    for index, (row, finding) in enumerate(zip(crows, constructions), 1):
        a, b = records[2*index-2:2*index]
        if row['编号'] != str(index) or finding['display_number'] != index or finding['pair_id'] != a['pair_id'] or a['pair_id'] != b['pair_id']:
            raise ValueError('Construction identity mismatch')
        if row['正常证据'] != a['visible_evidence'] or row['挑战证据'] != b['visible_evidence']:
            raise ValueError('Construction text was edited')
        if '修正后的问题' in row and row['修正后的问题'] != a['question']:
            raise ValueError('Revised question was edited')
        if finding['review_source'] != 'assistant' or finding['status'] != 'pending_user_review' or not finding['rationale'].strip():
            raise ValueError('Construction notes require assistant draft provenance')
        if preserve_construction_notes and row['构造检查备注'].strip():
            initial_note = row['构造检查备注']
            if (finding.get('initial_note') != initial_note or
                    not finding['rationale'].startswith(initial_note+'\n')):
                raise ValueError('Existing construction notes must be preserved verbatim')
        row['构造检查备注'] = finding['rationale']
    backup = run/'provenance/review_before_prefill_20261105'
    backup.mkdir(parents=True, exist_ok=False)
    for path in (answers_path, construction_path):
        (backup/path.name).write_bytes(path.read_bytes())
    write_table(answers_path, fields, rows)
    write_table(construction_path, cfields, crows)
    if any(file_sha256(Path(path)) != digest for path, digest in official.items()):
        raise RuntimeError('Formal evaluation artifacts changed unexpectedly')
    summary = {'status':'assistant_prefilled_pending_user_review', 'answer_rows':len(rows),
               'construction_rows':len(crows), 'review_source':'assistant', 'user_confirmation':'pending',
               'draft_evidence_label_counts':dict(Counter(r['evidence_label'] for r in drafts)),
               'draft_answer_correctness_counts':dict(Counter(r['answer_correctness'] for r in drafts)),
               'construction_finding_counts':dict(Counter(r['construction_finding'] for r in constructions)),
               'detector_scores_used_for_labels':False, 'formal_artifacts_unchanged':True,
               'formal_artifacts_sha256':official,
               'display_table_sha256':{p.name:file_sha256(p) for p in (answers_path,construction_path)},
               'draft_inputs_sha256':{name:file_sha256(run/'review_drafts'/name) for name in ('answer_assessments.jsonl','construction_assessments.jsonl')}}
    write_json(run/'review_drafts/status.json', summary)
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, required=True)
    parser.add_argument('--preserve-construction-notes', action='store_true',
                        help='Append to existing preparation notes, preserving their exact text')
    args = parser.parse_args()
    print(prefill(args.run_dir,args.preserve_construction_notes))
