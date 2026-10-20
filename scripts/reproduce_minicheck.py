"""Evaluate the vendored MiniCheck Flan-T5 checkpoint with its official protocol.

Reference: baselines/MiniCheck/benchmark_evaluation_demo.ipynb (Apache-2.0).
This wrapper selects Flan-T5 and adds a smoke test and saved experiment records.
"""

import argparse
import csv
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
import json
from pathlib import Path
import platform
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
MODEL_ID = "lytang/MiniCheck-Flan-T5-Large"
DATASET_ID = "lytang/LLM-AggreFact"


def positive_int(value):
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", choices=["smoke", "benchmark"], default="smoke")
    parser.add_argument("--batch-size", type=positive_int, default=1,
                        help="Number of document chunks per model forward pass.")
    parser.add_argument("--limit", type=positive_int,
                        help="First N benchmark examples, for debugging only.")
    parser.add_argument("--dataset-revision", default="main",
                        help="Dataset Git ref; resolved to a commit before loading.")
    parser.add_argument("--cache-dir", type=Path, default=ROOT / ".cache" / "minicheck")
    parser.add_argument("--output-dir", type=Path,
                        default=ROOT / "outputs" / "minicheck_reproduction")
    args = parser.parse_args()
    if args.task == "smoke" and args.limit is not None:
        parser.error("--limit only applies to --task benchmark")
    return args


def package_versions():
    result = {}
    for package in ("torch", "transformers", "datasets", "huggingface_hub",
                    "nltk", "accelerate", "scikit-learn", "numpy", "minicheck"):
        try:
            result[package] = version(package)
        except PackageNotFoundError:
            result[package] = None
    return result


def main():
    args = parse_args()
    # Keep heavy imports here so --help also works before environment setup.
    import nltk
    import torch
    from minicheck.minicheck import MiniCheck

    try:
        nltk.sent_tokenize("An English sentence.")
    except LookupError as error:
        raise SystemExit(
            "NLTK sentence resources are missing. Follow the punkt / punkt_tab "
            "download and NLTK_DATA setup in 项目资料/MiniCheck复现指南.md."
        ) from error

    output_dir = args.output_dir / args.task
    output_dir.mkdir(parents=True, exist_ok=True)
    args.cache_dir.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["git", "-C", str(ROOT / "baselines" / "MiniCheck"), "rev-parse", "HEAD"],
        text=True, capture_output=True, check=False,
    )
    metadata = {
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "task": args.task,
        "model_id": MODEL_ID,
        "model_revision": None,
        "minicheck_code_revision": result.stdout.strip() if result.returncode == 0 else None,
        "python": sys.version,
        "platform": platform.platform(),
        "packages": package_versions(),
        "cuda_available": torch.cuda.is_available(),
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "batch_size": args.batch_size,
        "chunk_size": 500,
        "max_model_len": 2048,
        "support_threshold": 0.5,
        "threshold_rule": "support_probability > 0.5",
        "limit": args.limit,
    }
    print("Device:", metadata["gpu"] or "CPU")
    scorer = MiniCheck(model_name="flan-t5-large", batch_size=args.batch_size,
                      max_model_len=2048, cache_dir=str(args.cache_dir / "models"))
    metadata["model_revision"] = getattr(scorer.model.model.config, "_commit_hash", None)

    if args.task == "smoke":
        doc = ("A group of students gather in the school library to study for "
               "their upcoming final exams.")
        records = [
            {"dataset": "official_smoke", "doc": doc,
             "claim": "The students are preparing for an examination.", "label": 1},
            {"dataset": "official_smoke", "doc": doc,
             "claim": "The students are on vacation.", "label": 0},
        ]
    else:
        from datasets import load_dataset
        from huggingface_hub import HfApi
        revision = HfApi().dataset_info(DATASET_ID, revision=args.dataset_revision).sha
        dataset = load_dataset(DATASET_ID, split="test", revision=revision,
                               cache_dir=str(args.cache_dir / "datasets"))
        metadata.update(dataset_id=DATASET_ID, dataset_revision=revision,
                        test_rows_total=len(dataset))
        if args.limit is not None:
            dataset = dataset.select(range(min(args.limit, len(dataset))))
        metadata["is_full_test"] = len(dataset) == metadata["test_rows_total"]
        records = [dict(row) for row in dataset]

    metadata["evaluated_rows"] = len(records)
    metadata_path = output_dir / "run_config.json"
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    docs = [record["doc"] for record in records]
    claims = [record["claim"] for record in records]
    predictions, probabilities, _, _ = scorer.score(docs=docs, claims=claims, chunk_size=500)
    prediction_path = output_dir / "predictions.jsonl"
    with prediction_path.open("w", encoding="utf-8") as stream:
        for index, (record, prediction, probability) in enumerate(
                zip(records, predictions, probabilities)):
            record.update(row_index=index, pred_label=int(prediction),
                          support_probability=float(probability))
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")

    if args.task == "smoke":
        labels = [int(prediction) for prediction in predictions]
        passed = labels == [1, 0]
        print("Predicted labels:", labels, "(expected [1, 0])")
        print("Support probabilities:", [round(float(p), 6) for p in probabilities])
        metadata["smoke_passed"] = passed
    else:
        from sklearn.metrics import balanced_accuracy_score
        groups = sorted({record["dataset"] for record in records})
        metric_rows = []
        for group in groups:
            rows = [record for record in records if record["dataset"] == group]
            labels = [int(row["label"]) for row in rows]
            # A truncated debugging slice can contain just one class.
            bacc = (100 * balanced_accuracy_score(labels, [row["pred_label"] for row in rows])
                    if len(set(labels)) == 2 else None)
            metric_rows.append({"dataset": group, "n": len(rows), "bacc_percent": bacc})
        if metadata["is_full_test"] and any(row["bacc_percent"] is None for row in metric_rows):
            raise RuntimeError("A full benchmark group has only one label class; inspect data.")
        values = [row["bacc_percent"] for row in metric_rows if row["bacc_percent"] is not None]
        average = sum(values) / len(values) if values else None
        average_name = "Average" if metadata["is_full_test"] else "Debug partial average"
        metric_rows.append({"dataset": average_name, "n": len(records), "bacc_percent": average})
        with (output_dir / "metrics.csv").open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=["dataset", "n", "bacc_percent"])
            writer.writeheader()
            writer.writerows(metric_rows)
        for row in metric_rows:
            score = f'{row["bacc_percent"]:.2f}' if row["bacc_percent"] is not None else "N/A (one class)"
            print(f'{row["dataset"]:24s} n={row["n"]:6d} BAcc={score}')
        metadata["macro_balanced_accuracy_percent"] = average
        metadata["is_official_comparable_run"] = metadata["is_full_test"]
    metadata["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Saved:", output_dir)
    if args.task == "smoke" and not passed:
        raise SystemExit("Smoke test did not match the official example labels.")


if __name__ == "__main__":
    main()
