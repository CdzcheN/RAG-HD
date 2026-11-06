"""Conservative dataset-derived labels and common-cohort detector evaluation."""
from collections import Counter
import math

from .schema import LABELS, normalize_answer


def qa_scores(answer, references):
    normalized = normalize_answer(answer)
    exact = any(normalized == normalize_answer(ref) for ref in references)
    scores = []
    for ref in references:
        tokens, gold = normalized.split(), normalize_answer(ref).split()
        overlap = sum((Counter(tokens) & Counter(gold)).values())
        scores.append(2 * overlap / (len(tokens) + len(gold)) if tokens and gold else float(tokens == gold))
    return {"exact_match": exact, "token_f1": max(scores, default=0.0),
            "note": "Answer-level QA diagnostics, not evidence-support ground truth."}


def initial_label(record, generated):
    if generated["is_refusal"]:
        return {"evidence_label": "undetermined", "label_source": "refusal_excluded",
                "rationale": "Refusals are reported separately from factual-answer AUC."}
    exact = qa_scores(generated["answer"], record["audit"]["reference_answers"])["exact_match"]
    if exact and record["audit"]["all_gold_support_visible"]:
        return {"evidence_label": "supported", "label_source": "dataset_exact_answer_and_complete_support",
                "rationale": "Entire normalized answer equals an annotated reference and all annotated support is visible."}
    return {"evidence_label": "undetermined", "label_source": "requires_review",
            "rationale": "Reference mismatch or incomplete annotated support does not establish hallucination."}


def valid_risk(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and 0 <= value <= 1


def evaluate(records):
    from sklearn.metrics import average_precision_score, roc_auc_score
    report = {"total": len(records), "refusals": sum(r['is_refusal'] for r in records),
              "label_counts": dict(Counter(r['evidence_label'] for r in records)),
              "qa_exact_match_rate": sum(r['qa']['exact_match'] for r in records) / len(records) if records else None,
              "qa_metric_note": "Whole-sentence answers can differ from short reference aliases; EM is diagnostic only.",
              "methods": {}}
    labeled = [r for r in records if not r['is_refusal'] and r['evidence_label'] != 'undetermined']
    common = [r for r in labeled if all(valid_risk(r[method].get('risk')) for method in ('self_check', 'minicheck'))]
    report.update(labeled_factual_answers=len(labeled), common_evaluation_rows=len(common),
                  refusal_rate=report['refusals'] / len(records) if records else None,
                  label_coverage=len(labeled) / len(records) if records else None,
                  common_coverage=len(common) / len(records) if records else None)
    labels = [int(r['evidence_label'] != 'supported') for r in common]
    for method in ('self_check', 'minicheck'):
        risks = [r[method]['risk'] for r in common]
        report['methods'][method] = {
            "score_missing_on_all_inputs": sum(not valid_risk(r[method].get('risk')) for r in records),
            "roc_auc": float(roc_auc_score(labels, risks)) if len(set(labels)) == 2 else None,
            "average_precision": float(average_precision_score(labels, risks)) if len(set(labels)) == 2 else None,
            "not_computable_reason": None if len(set(labels)) == 2 else 'Common labeled cohort has fewer than two classes.'}
    report['threshold_metrics'] = 'Not tuned or reported on this development pilot; select on a later validation split.'
    return report
