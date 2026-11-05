"""Recover technical provenance for a user-confirmed, simplified review table."""
import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from rag_hd.io import file_sha256, fingerprint, read_jsonl, write_json, write_jsonl
from rag_hd.schema import LABELS


def convert(run, confirmation):
    if not confirmation.strip():
        raise ValueError('Explicit user confirmation is required')
    table = run/'review_assistance/review_assisted.csv'
    with table.open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.DictReader(stream))
    mapping = read_jsonl(run/'review_requests.jsonl')
    backup = run/'provenance/review_before_cleanup/review_assisted.csv'
    with backup.open(encoding='utf-8-sig', newline='') as stream:
        original = list(csv.DictReader(stream))
    if len(rows) != len(original) or len(mapping) != len(rows):
        raise ValueError('Reviewed table must cover every original row')
    originals = {str(i): row for i, row in enumerate(original, 1)}
    requests = {row['sample_id']: row for row in mapping}
    seen, reviews = set(), []
    for row in rows:
        number = row['编号']
        if number in seen or number not in originals:
            raise ValueError('Duplicate or unknown display number')
        seen.add(number)
        old = originals[number]
        request = requests[old['sample_id']]
        for chinese, english in [('问题','question'), ('可见证据','visible_evidence'), ('生成回答','answer')]:
            if row[chinese] != old[english] or old[english] != request[english]:
                raise ValueError(f'Reviewed {english} changed; review the original content')
        if row['参考答案'] != '；'.join(request['reference_answers']):
            raise ValueError('Reference answers changed')
        if (old['answer_sha256'] != fingerprint(request['answer']) or
                old['visible_input_sha256'] != request['visible_input_sha256']):
            raise ValueError('Original provenance does not match reviewed input')
        if row['证据支持标签'] not in LABELS or row['答案正确性'] not in ('correct','incorrect','undetermined'):
            raise ValueError('Invalid reviewed label')
        if not row['判断依据'].strip():
            raise ValueError('Every row needs a rationale, including undetermined')
        reviews.append(dict(request, evidence_label=row['证据支持标签'],
                            answer_correctness=row['答案正确性'], rationale=row['判断依据'],
                            review_source='human', reviewer='user-confirmed assistant draft',
                            annotation_origin='assistant_draft_confirmed_by_user',
                            confirmation=confirmation))
    write_jsonl(run/'confirmed_review.jsonl', reviews)
    write_json(run/'review_confirmation.json', {
        'status': 'user_confirmed', 'confirmation': confirmation,
        'annotation_origin': 'assistant_draft_confirmed_by_user',
        'independent_human_annotation': False, 'rows': len(reviews),
        'recorded_at_utc': datetime.now(timezone.utc).isoformat(),
        'reviewed_table_sha256': file_sha256(table),
        'confirmed_review_sha256': file_sha256(run/'confirmed_review.jsonl')})
    return len(reviews)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, required=True)
    parser.add_argument('--confirmation', required=True)
    args = parser.parse_args()
    print(f'Converted {convert(args.run_dir, args.confirmation)} user-confirmed rows; no inference performed.')
