"""Score-blind, evidence-anchored review assistance; never creates human labels."""
import csv
import json
from collections import Counter
from pathlib import Path

from .io import file_sha256, fingerprint, read_jsonl, write_json
from .schema import LABELS, visible_input


def validate_suggestions(requests, suggestions):
    indexed = {row['sample_id']: row for row in requests}
    if len(indexed) != len(requests):
        raise ValueError('Duplicate request IDs')
    seen = set()
    for suggestion in suggestions:
        sid = suggestion['sample_id']
        if sid in seen or sid not in indexed:
            raise ValueError('Duplicate or unknown suggestion ID')
        seen.add(sid)
        row = indexed[sid]
        if row['visible_input_sha256'] != fingerprint(visible_input(row)):
            raise ValueError('Request input hash mismatch')
        if row['answer_sha256'] != fingerprint(row['answer']):
            raise ValueError('Request answer hash mismatch')
        for field in ('visible_input_sha256', 'answer_sha256'):
            if suggestion.get(field) != row[field]:
                raise ValueError('Stale suggestion: input or answer changed')
        if suggestion.get('review_source') != 'assistant' or not suggestion.get('rationale', '').strip():
            raise ValueError('Suggestions require assistant provenance and rationale')
        if suggestion.get('evidence_label') not in LABELS:
            raise ValueError('Invalid suggested label')
        if suggestion.get('answer_correctness') not in ('correct', 'incorrect', 'undetermined'):
            raise ValueError('Invalid suggested correctness')
        if row['answer'] == 'INSUFFICIENT_EVIDENCE' and suggestion['evidence_label'] != 'undetermined':
            raise ValueError('Refusals are outside factual-label evaluation')
        anchors = suggestion.get('evidence_anchors', [])
        if not anchors:
            raise ValueError('At least one visible evidence anchor is required')
        for anchor in anchors:
            start, end = anchor.get('start'), anchor.get('end')
            if (type(start) is not int or type(end) is not int or
                    not 0 <= start < end <= len(row['visible_evidence']) or
                    row['visible_evidence'][start:end] != anchor.get('quote')):
                raise ValueError('Evidence quote does not match visible text offsets')
    if seen != set(indexed):
        raise ValueError('Review assistance must cover every request, without score-based selection')


def export_packet(request_path, suggestion_path, output_dir):
    requests, suggestions = read_jsonl(request_path), read_jsonl(suggestion_path)
    validate_suggestions(requests, suggestions)
    hints = {row['sample_id']: row for row in suggestions}
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    fields = ['sample_id', 'question', 'visible_evidence', 'answer', 'reference_answers',
              'visible_input_sha256', 'answer_sha256', 'evidence_label', 'answer_correctness',
              'reviewer', 'rationale', 'suggested_evidence_label',
              'suggested_answer_correctness', 'assistant_rationale', 'assistant_evidence_anchors']
    csv_rows, pages = [], [
        '# 20 条原型的辅助复核稿' if len(requests) == 20 else '# 原型辅助复核稿',
        '此稿由助手依据已保存文本分析，不是人工金标。全文不读取检测分数；建议不进入正式指标。',
        '先阅读问题、完整可见证据和回答，再核对建议；参考答案及隐藏支撑只用于答案正确性诊断，不能补足可见证据。',
        'review_assisted.csv 已预填助手判断与理由，并去掉 review_source 列。请直接检查 evidence_label、answer_correctness 和 rationale，必要时修改；检查完成后通知助手。确认前不导入评估。',
        'supported 要求全部实质性事实均有支撑；unsupported 表示至少一个事实无依据；contradicted 要求存在明确反证。拒答单列。',
    ]
    for index, row in enumerate(requests, 1):
        hint = hints[row['sample_id']]
        csv_rows.append({key: row[key] for key in (
            'sample_id', 'question', 'visible_evidence', 'answer', 'visible_input_sha256', 'answer_sha256')})
        csv_rows[-1].update(reference_answers=json.dumps(row['reference_answers'], ensure_ascii=False),
                            evidence_label=hint['evidence_label'], answer_correctness=hint['answer_correctness'],
                            reviewer='Codex assistant（待用户检查）', rationale=hint['rationale'],
                            suggested_evidence_label=hint['evidence_label'],
                            suggested_answer_correctness=hint['answer_correctness'],
                            assistant_rationale=hint['rationale'],
                            assistant_evidence_anchors=json.dumps(hint['evidence_anchors'], ensure_ascii=False))
        pages.extend([f'\n## {index:02d}. {row["sample_id"]}\n', f'**问题**：{row["question"]}\n',
                      f'**回答**：{row["answer"]}\n', '**完整可见证据**：\n',
                      *['> ' + line for line in row['visible_evidence'].splitlines()],
                      f'\n**助手建议**：证据支持 `{hint["evidence_label"]}`；答案正确性 `{hint["answer_correctness"]}`。',
                      hint['rationale'], '\n**可见文本定位**（Unicode 字符偏移，左闭右开）：'])
        pages.extend(f'- [{a["start"]}:{a["end"]}] {a["quote"]}' for a in hint['evidence_anchors'])
        pages.extend(['\n**仅用于正确性诊断的参考答案**：' + json.dumps(row['reference_answers'], ensure_ascii=False),
                      f'\n输入 SHA-256：`{row["visible_input_sha256"]}`；回答 SHA-256：`{row["answer_sha256"]}`。'])
    csv_path = output_dir / 'review_assisted.csv'
    if csv_path.exists():
        with csv_path.open(encoding='utf-8-sig', newline='') as stream:
            existing = list(csv.DictReader(stream))
        editable = {'evidence_label', 'answer_correctness', 'reviewer', 'rationale'}
        if len(existing) != len(csv_rows) or any(
                any(old.get(k) != new[k] for k in fields if k not in editable)
                for old, new in zip(existing, csv_rows)):
            raise ValueError('Existing review belongs to different inputs/suggestions; use a new output directory')
    else:
        with csv_path.open('w', encoding='utf-8-sig', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(csv_rows)
    (output_dir / 'review_packet.md').write_text('\n\n'.join(pages) + '\n', encoding='utf-8')
    manifest = {'status': 'assistant_suggestions_pending_human_review', 'rows': len(requests),
                'suggestion_source': 'assistant', 'formal_labels_created': 0,
                'draft_labels_prefilled': True, 'user_confirmation': 'pending',
                'suggested_evidence_label_counts': dict(Counter(r['evidence_label'] for r in suggestions)),
                'requests_sha256': file_sha256(request_path), 'suggestions_sha256': file_sha256(suggestion_path),
                'csv_sha256': file_sha256(csv_path), 'packet_sha256': file_sha256(output_dir / 'review_packet.md'),
                'score_inputs': [], 'note': 'Suggestions are not ground truth and no AUC is computed here.'}
    write_json(output_dir / 'review_packet_manifest.json', manifest)
    return manifest
