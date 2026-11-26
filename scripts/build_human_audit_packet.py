"""Build a score-blind, stratified 100-row human audit packet.

The packet is derived from the already frozen final-test records but does not
copy labels, detector scores, thresholds, or private construction metadata.
"""
import argparse
import csv
import hashlib
import json
import random
from collections import Counter
from pathlib import Path


def wording_group(row):
    family = row["audit"].get("rule_family", "plain_question")
    if "heldout" in family:
        return "unseen_wording"
    if "compatible" in family:
        return "seen_wording"
    return "not_applicable"


def boundary_candidate(row):
    text = str(row.get("construction", {})).lower()
    return any(word in text for word in ("approx", "bound", "ambigu", "round"))


def select(rows, n, seed):
    rng = random.Random(seed)
    by_condition = {}
    for row in rows:
        by_condition.setdefault(row["condition"], []).append(row)
    chosen = []

    # Preserve every refusal so refusal handling is auditable, then fill the
    # remaining quota evenly across normal and the three challenge conditions.
    refusals = [r for r in rows if r["is_refusal"]]
    chosen.extend(sorted(refusals, key=lambda r: r["sample_id"]))
    remaining = [r for r in rows if r not in chosen]
    # The frozen test contains only three non-refusal retrieval-failure
    # answers; retain all of them instead of inventing a quota the data cannot
    # satisfy.
    quotas = {"normal": 33, "retrieval_failure": 3,
              "evidence_conflict": 20, "outdated_answer": 19}
    for condition, quota in quotas.items():
        pool = [r for r in remaining if r["condition"] == condition]
        rng.shuffle(pool)
        chosen.extend(pool[:quota])
    assert len(chosen) == n, len(chosen)
    return sorted(chosen, key=lambda r: (r["condition"], r["sample_id"]))


def build(records_path, output_dir, seed):
    rows = [json.loads(line) for line in records_path.open(encoding="utf-8")]
    selected = select(rows, 100, seed)
    output_dir.mkdir(parents=True, exist_ok=False)
    fields = ["audit_id", "sample_id", "condition", "challenge_type",
              "dataset", "wording_group", "is_refusal", "boundary_candidate",
              "question", "visible_evidence", "answer", "annotator_id",
              "annotation_date", "evidence_label", "answer_correctness",
              "decision_basis", "disagreement", "final_disposition",
              "adjudicator_id", "adjudication_basis"]
    packet = output_dir / "human_audit_100.csv"
    with packet.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for i, row in enumerate(selected, 1):
            writer.writerow({
                "audit_id": f"audit-{i:03d}",
                "sample_id": row["sample_id"],
                "condition": row["condition"],
                "challenge_type": row["challenge_type"],
                "dataset": row["dataset"],
                "wording_group": wording_group(row),
                "is_refusal": str(bool(row["is_refusal"])).lower(),
                "boundary_candidate": str(boundary_candidate(row)).lower(),
                "question": row["question"],
                "visible_evidence": row["visible_evidence"],
                "answer": row["answer"],
                "annotator_id": "", "annotation_date": "",
                "evidence_label": "", "answer_correctness": "",
                "decision_basis": "", "disagreement": "",
                "final_disposition": "", "adjudicator_id": "",
                "adjudication_basis": "",
            })
    manifest = {
        "status": "human_annotation_pending",
        "purpose": "100-row stratified quality audit; score-blind and separate from frozen final evaluation",
        "source_records": str(records_path),
        "rows": len(selected),
        "seed": seed,
        "selection": {
            "all_25_refusals_included": True,
            "condition_quota_for_non_refusals": {"normal": 33, "retrieval_failure": 3, "evidence_conflict": 20, "outdated_answer": 19},
            "wording_groups": ["seen_wording", "unseen_wording", "not_applicable"],
            "boundary_candidates_flagged_without_revealing_labels": True,
        },
        "counts": {
            "condition": dict(Counter(r["condition"] for r in selected)),
            "challenge_type": dict(Counter(r["challenge_type"] for r in selected)),
            "wording_group": dict(Counter(wording_group(r) for r in selected)),
            "refusal": dict(Counter(str(bool(r["is_refusal"])).lower() for r in selected)),
            "boundary_candidate": dict(Counter(str(boundary_candidate(r)).lower() for r in selected)),
        },
        "annotation_rules": {
            "evidence_label": ["supported", "contradicted", "outdated", "unsupported", "undetermined"],
            "answer_correctness": ["correct", "incorrect", "undetermined"],
            "refusal": "Keep factual labels undetermined for a clear refusal; record refusal handling in decision_basis.",
            "disagreement": "Record the competing decision and reason; do not silently overwrite either annotator's entry.",
            "final_disposition": "Record adjudicated value or unresolved.",
        },
        "frozen_test_protection": "This packet contains no detector scores, thresholds, gold labels, private construction notes, or final-result fields.",
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest["packet_sha256"] = hashlib.sha256(packet.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20261126)
    args = parser.parse_args()
    print(json.dumps(build(args.records, args.output_dir, args.seed), ensure_ascii=False, indent=2))
