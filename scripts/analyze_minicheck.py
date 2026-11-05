"""Recompute saved MiniCheck predictions without loading or running the model.

Run from any directory with Python 3.9+. Plotting additionally needs matplotlib.
Only complete official benchmark runs are accepted. Outputs are local by default;
copy reviewed summaries to results/minicheck/ when archiving an experiment.
Reference values: https://llm-aggrefact.github.io/, retrieved 2026-10-24.
"""

import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = ROOT / "outputs" / "minicheck_reproduction"
OFFICIAL = {
    "AggreFact-CNN": 69.9,
    "AggreFact-XSum": 74.3,
    "TofuEval-MediaS": 73.6,
    "TofuEval-MeetB": 77.3,
    "Wice": 72.2,
    "Reveal": 86.2,
    "ClaimVerify": 74.6,
    "FactCheck-GPT": 74.7,
    "ExpertQA": 59.0,
    "Lfqa": 85.2,
    "RAGTruth": 78.0,
}


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark-dir", type=Path,
                        default=DEFAULT_OUTPUT_ROOT / "benchmark",
                        help="Directory containing a full run's predictions, config and metrics.")
    parser.add_argument("--output-dir", type=Path,
                        default=DEFAULT_OUTPUT_ROOT / "analysis",
                        help="Directory for recomputed metrics, examples and optional plots.")
    parser.add_argument("--skip-plots", action="store_true",
                        help="Only use the Python standard library; do not generate plots.")
    return parser.parse_args()


def divide(a, b):
    return a / b if b else None


def roc_auc(labels, scores):
    """Mann-Whitney AUC, assigning mean ranks to tied scores."""
    ordered = sorted(zip(scores, labels))
    positive = sum(labels)
    negative = len(labels) - positive
    if not positive or not negative:
        return None
    rank_sum = 0.0
    i = 0
    while i < len(ordered):
        j = i + 1
        while j < len(ordered) and ordered[j][0] == ordered[i][0]:
            j += 1
        rank_sum += sum(y for _, y in ordered[i:j]) * ((i + 1 + j) / 2)
        i = j
    return (rank_sum - positive * (positive + 1) / 2) / (positive * negative)


def average_precision(labels, scores):
    """Non-interpolated AP with all tied scores admitted together."""
    positive = sum(labels)
    if not positive:
        return None
    ordered = sorted(zip(scores, labels), reverse=True)
    tp = 0
    ap = 0.0
    i = 0
    while i < len(ordered):
        j = i + 1
        while j < len(ordered) and ordered[j][0] == ordered[i][0]:
            j += 1
        new_tp = sum(y for _, y in ordered[i:j])
        tp += new_tp
        ap += (new_tp / positive) * (tp / j)
        i = j
    return ap


def metrics(name, rows):
    counts = Counter((r["label"], r["pred_label"]) for r in rows)
    tn, fp, fn, tp = [counts[k] for k in [(0, 0), (0, 1), (1, 0), (1, 1)]]
    y = [r["label"] for r in rows]
    scores = [r["support_probability"] for r in rows]
    f1_support = divide(2 * tp, 2 * tp + fp + fn)
    f1_unsupported = divide(2 * tn, 2 * tn + fp + fn)
    bacc = 50 * (tp / (tp + fn) + tn / (tn + fp))
    return {
        "dataset": name,
        "n": len(rows),
        "n_supported": tp + fn,
        "n_unsupported": tn + fp,
        "unsupported_prevalence_percent": 100 * (tn + fp) / len(rows),
        "accuracy_percent": 100 * (tp + tn) / len(rows),
        "balanced_accuracy_percent": bacc,
        "macro_f1": (f1_support + f1_unsupported) / 2,
        "micro_f1": (tp + tn) / len(rows),
        "roc_auc": roc_auc(y, scores),
        "unsupported_average_precision": average_precision(
            [1 - v for v in y], [1 - s for s in scores]
        ),
        "support_precision_percent": 100 * tp / (tp + fp),
        "support_recall_percent": 100 * tp / (tp + fn),
        "unsupported_precision_percent": 100 * tn / (tn + fn),
        "unsupported_recall_percent": 100 * tn / (tn + fp),
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "tp": tp,
        "official_bacc_percent": OFFICIAL.get(name),
        "delta_vs_rounded_official_pp": bacc - OFFICIAL[name] if name in OFFICIAL else None,
    }


def write_json(output_dir, name, value):
    (output_dir / name).write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def main():
    args = parse_args()
    benchmark = args.benchmark_dir.resolve()
    output_dir = args.output_dir.resolve()
    try:
        config = json.loads((benchmark / "run_config.json").read_text(encoding="utf-8"))
        with (benchmark / "predictions.jsonl").open(encoding="utf-8") as stream:
            rows = [json.loads(line) for line in stream]
        with (benchmark / "metrics.csv").open(encoding="utf-8", newline="") as stream:
            stored = list(csv.DictReader(stream))
    except FileNotFoundError as error:
        raise SystemExit(f"Missing benchmark artifact: {error.filename}") from error
    if (config.get("task") != "benchmark" or not config.get("is_full_test")
            or config.get("dataset_id") != "lytang/LLM-AggreFact"
            or len(rows) != config.get("evaluated_rows")
            or len(rows) != config.get("test_rows_total")):
        raise SystemExit("Analysis requires a complete LLM-AggreFact benchmark run; partial runs are not supported.")
    groups = defaultdict(list)
    pairs = defaultdict(list)
    for r in rows:
        groups[r["dataset"]].append(r)
        digest = hashlib.sha256(json.dumps([r["doc"], r["claim"]]).encode()).hexdigest()
        pairs[digest].append(r)

    if set(groups) != set(OFFICIAL):
        raise SystemExit("Benchmark groups do not match the 11 official datasets.")
    if any({r["label"] for r in rs} != {0, 1} for rs in groups.values()):
        raise SystemExit("Every complete benchmark group must contain both label classes.")
    results = [metrics(name, groups[name]) for name in sorted(groups)]
    pooled = metrics("Pooled", rows)
    macro_bacc = mean(r["balanced_accuracy_percent"] for r in results)
    stored_by_name = {r["dataset"]: float(r["bacc_percent"]) for r in stored}
    metric_deltas = {
        r["dataset"]: r["balanced_accuracy_percent"] - stored_by_name[r["dataset"]]
        for r in results
    }
    metric_deltas["Average"] = macro_bacc - stored_by_name["Average"]
    audit = {
        "actual_rows": len(rows),
        "matches_config_evaluated_rows": len(rows) == config["evaluated_rows"],
        "matches_config_full_test_rows": len(rows) == config["test_rows_total"],
        "dataset_groups": len(groups),
        "matches_official_group_names": set(groups) == set(OFFICIAL),
        "row_index_mismatches": sum(r["row_index"] != i for i, r in enumerate(rows)),
        "invalid_labels": sum(r["label"] not in (0, 1) or r["pred_label"] not in (0, 1) for r in rows),
        "invalid_probabilities": sum(not math.isfinite(r["support_probability"]) or not 0 <= r["support_probability"] <= 1 for r in rows),
        "threshold_mismatches": sum(r["pred_label"] != int(r["support_probability"] > 0.5) for r in rows),
        "empty_documents": sum(not r["doc"].strip() for r in rows),
        "empty_claims": sum(not r["claim"].strip() for r in rows),
        "max_bacc_recalculation_difference_pp": max(abs(v) for v in metric_deltas.values()),
        "unique_documents": len({r["doc"] for r in rows}),
        "unique_document_claim_pairs": len(pairs),
        "duplicate_input_groups": sum(len(v) > 1 for v in pairs.values()),
        "duplicate_extra_rows": len(rows) - len(pairs),
        "duplicate_input_groups_with_probability_difference_gt_1e_6": sum(
            max(r["support_probability"] for r in v) - min(r["support_probability"] for r in v) > 1e-6
            for v in pairs.values() if len(v) > 1
        ),
    }
    conflicts = []
    for digest, same_input in pairs.items():
        if len({r["label"] for r in same_input}) > 1:
            conflicts.append({
                "input_sha256": digest,
                "claim": same_input[0]["claim"],
                "records": [{k: r[k] for k in ("dataset", "row_index", "label", "pred_label", "support_probability")} for r in same_input],
            })
    audit["conflicting_input_groups"] = len(conflicts)
    audit["conflicting_input_rows"] = sum(len(v["records"]) for v in conflicts)
    audit["minimum_errors_on_conflicting_inputs_for_deterministic_classifier"] = sum(
        min(Counter(r["label"] for r in v["records"]).values()) for v in conflicts
    )
    failures = [name for name in (
        "row_index_mismatches", "invalid_labels", "invalid_probabilities",
        "threshold_mismatches", "empty_documents", "empty_claims",
    ) if audit[name]]
    if audit["max_bacc_recalculation_difference_pp"] > 1e-9:
        failures.append("stored_metrics_mismatch")
    if failures:
        raise SystemExit("Benchmark audit failed: " + ", ".join(failures))
    output_dir.mkdir(parents=True, exist_ok=True)

    confidence = []
    for name, rs in [("Pooled", rows), ("ExpertQA", groups["ExpertQA"]), ("RAGTruth", groups["RAGTruth"])]:
        for title, select in [
            ("support_probability <= 0.1", lambda p: p <= 0.1),
            ("0.4 <= support_probability <= 0.6", lambda p: 0.4 <= p <= 0.6),
            ("support_probability >= 0.9", lambda p: p >= 0.9),
        ]:
            selected = [r for r in rs if select(r["support_probability"])]
            correct = sum(r["label"] == r["pred_label"] for r in selected)
            confidence.append({"dataset": name, "bin": title, "n": len(selected), "errors": len(selected) - correct, "accuracy_percent": 100 * correct / len(selected)})

    length_slices = []
    for field, bins in [
        ("doc", [(0, 250), (251, 500), (501, 1000), (1001, None)]),
        ("claim", [(0, 15), (16, 30), (31, 60), (61, None)]),
    ]:
        for lower, upper in bins:
            selected = [r for r in rows if len(r[field].split()) >= lower and (upper is None or len(r[field].split()) <= upper)]
            result = metrics(f"{field}_words_{lower}_{upper or 'plus'}", selected)
            length_slices.append(result)

    with (output_dir / "extended_metrics.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(pooled))
        writer.writeheader()
        writer.writerows(results + [pooled])

    examples = []
    for name, rs in sorted(groups.items()):
        for gold, pred, kind in [(0, 1, "unsupported_claim_accepted"), (1, 0, "supported_claim_rejected")]:
            errors = [r for r in rs if r["label"] == gold and r["pred_label"] == pred]
            errors.sort(key=lambda r: r["support_probability"], reverse=pred == 1)
            examples.extend(dict(r, error_type=kind) for r in errors[:2])
    with (output_dir / "error_examples.jsonl").open("w", encoding="utf-8") as f:
        for r in examples:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    elapsed = (datetime.fromisoformat(config["finished_at_utc"]) - datetime.fromisoformat(config["started_at_utc"])).total_seconds()
    summary = {
        "label_semantics": {"0": "unsupported", "1": "supported"},
        "hallucination_proxy_score": "1 - support_probability; this benchmark's unsupported label is not a new ground-truth label for the RAG-HD challenge set",
        "official_reference": {"url": "https://llm-aggrefact.github.io/", "accessed_date": "2026-10-24", "model": "MiniCheck-Flan-T5-L", "published_values_rounded_to_decimals": 1, "macro_bacc_percent": 75.0, "per_dataset_bacc_percent": OFFICIAL},
        "macro_balanced_accuracy_percent": macro_bacc,
        "macro_dataset_roc_auc": mean(r["roc_auc"] for r in results),
        "macro_bacc_delta_vs_rounded_official_pp": macro_bacc - 75.0,
        "pooled": pooled,
        "audit": audit,
        "runtime": {"recorded_elapsed_seconds": elapsed, "rows_per_second_including_setup": len(rows) / elapsed, "rows_per_minute_including_setup": 60 * len(rows) / elapsed, "gpu": config["gpu"], "peak_vram_recorded": False},
        "confidence_bins": confidence,
        "length_slices": length_slices,
        "analysis_notes": [
            "Published leaderboard values are rounded; small deltas do not establish an improvement.",
            "AP means non-interpolated average precision, not trapezoidal PR-AUC.",
            "No threshold was tuned on the test set; saved predictions use p_support > 0.5.",
            "Duplicate and conflicting records are preserved in official-comparable metrics.",
            "Length slices are descriptive and confounded by dataset composition.",
            "Rows share documents; independent-row confidence intervals would overstate effective sample size.",
            "No model inference was rerun; numerical and dataset audits only verify saved artifacts.",
        ],
    }
    write_json(output_dir, "summary.json", summary)
    write_json(output_dir, "conflicting_inputs.json", conflicts)
    print(json.dumps({"macro_bacc": macro_bacc, "macro_dataset_auc": summary["macro_dataset_roc_auc"], "pooled": pooled, "audit": audit, "runtime": summary["runtime"]}, ensure_ascii=False, indent=2))
    print("Saved:", output_dir)
    if args.skip_plots:
        return

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib unavailable; numeric analysis saved, plotting skipped")
        return

    ordered = sorted(results, key=lambda r: r["balanced_accuracy_percent"])
    positions = list(range(len(ordered)))
    fig, (left, right) = plt.subplots(1, 2, figsize=(13.6, 7.8), sharey=True, gridspec_kw={"width_ratios": [1.05, 1]})
    colors = ["#c44e52" if r["dataset"] == "ExpertQA" else "#d69b24" if r["dataset"] == "RAGTruth" else "#42789c" for r in ordered]
    left.barh(positions, [r["balanced_accuracy_percent"] for r in ordered], color=colors, alpha=0.88, height=0.62, label="Reproduced")
    left.scatter([OFFICIAL[r["dataset"]] for r in ordered], positions, marker="|", color="#111111", s=180, linewidths=1.8, label="Official (rounded)", zorder=3)
    for i, r in enumerate(ordered):
        left.text(r["balanced_accuracy_percent"] + 0.65, i, f'{r["balanced_accuracy_percent"]:.2f}', va="center", fontsize=10)
    left.axvline(macro_bacc, color="#656565", linestyle="--", linewidth=1.1)
    left.set_yticks(positions)
    left.set_yticklabels([r["dataset"] for r in ordered], fontsize=10)
    left.set_xlim(45, 100)
    left.set_xlabel("Balanced accuracy (%)")
    left.set_title("Official reproduction", fontsize=13, pad=15)
    left.legend(loc="lower right", fontsize=9, frameon=False)
    for i, r in enumerate(ordered):
        right.plot([r["unsupported_precision_percent"], r["unsupported_recall_percent"]], [i, i], color="#cccccc", linewidth=2, zorder=1)
    right.scatter([r["unsupported_precision_percent"] for r in ordered], positions, color="#c56547", s=50, marker="s", label="Precision", zorder=3)
    right.scatter([r["unsupported_recall_percent"] for r in ordered], positions, color="#327d68", s=50, label="Recall", zorder=3)
    right.set_xlim(0, 105)
    right.set_xlabel("Unsupported-class precision / recall (%)")
    right.set_title("Detection trade-off at p(support) = 0.5", fontsize=13, pad=15)
    right.legend(loc="lower left", fontsize=9, frameon=False)
    for ax in (left, right):
        ax.grid(axis="x", color="#e5e5e5", linewidth=0.7)
        ax.set_axisbelow(True)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
    fig.suptitle("MiniCheck-Flan-T5-Large | LLM-AggreFact full test", fontsize=17, y=0.97)
    fig.text(0.5, 0.918, f'{len(rows):,} examples | {len(groups)} datasets | Macro BAcc {macro_bacc:.2f}% | Pooled ROC-AUC {pooled["roc_auc"]:.4f}', ha="center", fontsize=11, color="#444444")
    fig.text(0.5, 0.025, "Unsupported = benchmark label 0. Precision varies with class prevalence. Official values: llm-aggrefact.github.io (2026-10-24).", ha="center", fontsize=9, color="#555555")
    fig.tight_layout(rect=(0.01, 0.065, 0.99, 0.89), w_pad=3)
    fig.savefig(output_dir / "results_overview.png", dpi=180, bbox_inches="tight")
    fig.savefig(output_dir / "results_overview.svg", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
