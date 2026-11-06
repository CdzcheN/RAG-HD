"""Read pinned local Parquet snapshots without dataset script execution."""
from pathlib import Path

from .io import fingerprint
from .schema import Document, source_id


SOURCES = {
    "squad": ("rajpurkar/squad", "plain_text"),
    "hotpot": ("hotpotqa/hotpot_qa", "distractor"),
}


def snapshot_path(name, revision, hub):
    repo, subset = SOURCES[name]
    return Path(hub) / ("datasets--" + repo.replace("/", "--")) / "snapshots" / revision / subset


def read_pool(name, revision, hub, size, seed):
    import pyarrow as pa
    import pyarrow.parquet as pq
    files = sorted(snapshot_path(name, revision, hub).glob("train-*.parquet"))
    if not files:
        raise FileNotFoundError(f"Missing pinned {name} train snapshot: {revision}")
    tables = [pq.read_table(path) for path in files]
    table = pa.concat_tables(tables)
    ids = table.column("id").to_pylist()
    indices = sorted(range(len(ids)), key=lambda i: fingerprint([seed, name, ids[i]]))[:size]
    if len(indices) < size:
        raise ValueError("Source has fewer rows than requested pool")
    selected = table.take(pa.array(indices)).to_pylist()
    if len({row['id'] for row in selected}) != len(selected):
        raise ValueError("Duplicate source question IDs")
    return selected, {"repo_id": SOURCES[name][0], "subset": SOURCES[name][1],
                      "revision": revision, "split": "train", "source_rows": len(ids),
                      "pool_size": len(selected), "selection": "lowest_sha256(seed,dataset,original_id)",
                      "pool_ids_sha256": fingerprint([row['id'] for row in selected])}


def convert_question(name, row, revision):
    if name == "squad":
        document = Document.create(row["title"], row["context"], revision)
        documents = [document]
        answers = row["answers"]["text"]
        gold_ids = [document.document_id]
        gold_sources = [document.source_document_id]
        support = [{"document_id": document.document_id, "text": row["context"]}]
    else:
        context = row["context"]
        if isinstance(context, list):
            context = {"title": [c["title"] for c in context],
                       "sentences": [c["sentences"] for c in context]}
        documents = [Document.create(title, " ".join(sentences), revision)
                     for title, sentences in zip(context["title"], context["sentences"])
                     if " ".join(sentences).strip()]
        by_title = {doc.title: doc for doc in documents}
        sentences_by_title = dict(zip(context["title"], context["sentences"]))
        facts = row["supporting_facts"]
        if isinstance(facts, list):
            facts = {"title": [f["title"] for f in facts], "sent_id": [f["sent_id"] for f in facts]}
        titles = sorted(set(facts["title"]))
        if any(title not in by_title for title in titles):
            raise ValueError("Hotpot supporting document missing from context")
        gold_ids = [by_title[title].document_id for title in titles]
        gold_sources = [source_id(title) for title in titles]
        support = [{"document_id": by_title[title].document_id,
                    "text": sentences_by_title[title][int(sent_id)].strip()}
                   for title, sent_id in zip(facts["title"], facts["sent_id"])]
        answers = [row["answer"]]
    question = {"base_question_id": f"{name}:{row['id']}", "dataset": name,
                "question": row["question"].strip(), "source_document_ids": gold_sources,
                "audit": {"reference_answers": answers, "gold_document_ids": gold_ids,
                          "gold_support": support, "source_question_id": row["id"],
                          "source_revision": revision, "source_split": "train"}}
    return question, documents
