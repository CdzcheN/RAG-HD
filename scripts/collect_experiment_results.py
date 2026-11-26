"""Collect plotting-ready experiment data without recomputing or mutating results."""
import argparse
import csv
import json
import shutil
from pathlib import Path


def copy_file(src, root, dest_root):
    rel = src.relative_to(root)
    return str(rel)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    (out / "汇总").mkdir(exist_ok=True)

    # Index all machine-readable result files. The original files remain in
    # place; duplicating hundreds of MB would make the plotting package heavy.
    sources = []
    for base in (root / "results", root / "outputs"):
        for path in sorted(base.rglob("*")):
            if path.is_file() and path.suffix.lower() in {".json", ".jsonl", ".csv", ".sha256"}:
                sources.append(copy_file(path, root, out))

    final = root / "results/rag_formal_final_20261105"
    audit = root / "outputs/rag_formal_20261105_v2/partitions/test/human_audit_100/human_audit_100.csv"
    minicheck = root / "results/minicheck_20261103/benchmark/metrics.csv"

    shutil.copy2(final / "总体方法比较.csv", out / "汇总/正式总体方法比较.csv")
    shutil.copy2(final / "方法与分组比较.csv", out / "汇总/正式分组比较.csv")
    shutil.copy2(audit, out / "汇总/100条人工审计.csv")
    shutil.copy2(minicheck, out / "汇总/MiniCheck公开基准.csv")
    shutil.copy2(final / "resources_summary.json", out / "汇总/正式阶段资源汇总.json")

    group = __import__("pandas").read_csv(final / "方法与分组比较.csv", encoding="utf-8-sig")
    group[group["分组维度"] == "overall"].to_csv(out / "汇总/正式总体每种子结果.csv", index=False, encoding="utf-8-sig")
    group[group["分组维度"] != "overall"].to_csv(out / "汇总/正式分组每种子结果.csv", index=False, encoding="utf-8-sig")

    with (out / "原始结果索引.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["相对路径", "来源类别", "用途"])
        for rel in sources:
            category = "results" if rel.startswith("results/") else "outputs"
            writer.writerow([rel, category, "原始机器可读结果，未重算"])

    manifest = {
        "status": "collected_without_recomputation",
        "created_from": ["results/", "outputs/"],
        "summary_files": [
            "汇总/正式总体方法比较.csv", "汇总/正式分组比较.csv",
            "汇总/正式总体每种子结果.csv", "汇总/正式分组每种子结果.csv",
            "汇总/100条人工审计.csv", "汇总/MiniCheck公开基准.csv",
            "汇总/正式阶段资源汇总.json",
        ],
        "raw_machine_readable_files": len(sources),
        "frozen_test_policy": "No training, threshold selection, test re-evaluation, or result mutation was performed.",
        "notes": {
            "formal_overall": "95 common factual answers, 14 positive hallucination labels.",
            "formal_test": "120 inputs, 60 source groups, 25 refusals retained as undetermined.",
            "audit": "100-row stratified human quality audit; not a replacement for full independent double annotation.",
            "plotting": "Use 汇总/ files for direct plotting; use 原始结果索引.csv to trace every source file.",
        },
    }
    (out / "汇总清单.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
