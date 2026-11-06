"""Visible model inputs and private annotation metadata use separate namespaces."""
import re
import unicodedata
from dataclasses import asdict, dataclass

from .io import fingerprint


LABELS = {"supported", "unsupported", "contradicted", "outdated", "undetermined"}
REFUSAL = "INSUFFICIENT_EVIDENCE"


def source_id(title):
    normalized = " ".join(unicodedata.normalize("NFKC", title).replace("_", " ").casefold().split())
    if not normalized:
        raise ValueError("Empty document title")
    return "wiki:" + fingerprint(normalized)[:24]


@dataclass(frozen=True)
class Document:
    document_id: str
    source_document_id: str
    title: str
    text: str
    version: str

    @classmethod
    def create(cls, title, text, revision):
        text = text.strip()
        if not text:
            raise ValueError("Empty document")
        sid = source_id(title)
        return cls("doc:" + fingerprint([sid, text]), sid, title, text, revision)


def evidence_text(evidence):
    """One shared rendering: private answers/construction fields never enter it."""
    return "\n\n".join(
        f"[Evidence {entry['rank']}; title: {entry['title']}; version: {entry['version']}]\n{entry['text']}"
        for entry in evidence
    )


def visible_input(record):
    return {"question": record["question"], "evidence": record["visible_evidence"]}


def validate_record(record):
    for field in ("sample_id", "base_question_id", "group_id", "question", "visible_evidence"):
        if not isinstance(record.get(field), str) or not record[field].strip():
            raise ValueError(f"Missing/empty {field}")
    if not record.get("source_document_ids") or not record.get("evidence"):
        raise ValueError("Missing provenance or retrieved evidence")
    if record["visible_evidence"] != evidence_text(record["evidence"]):
        raise ValueError("Evidence rendering mismatch")
    if record["visible_input_sha256"] != fingerprint(visible_input(record)):
        raise ValueError("Visible input hash mismatch")
    ids = [entry["document_id"] for entry in record["evidence"]]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate retrieved document")
    if record.get("evidence_label", "undetermined") not in LABELS:
        raise ValueError("Unknown evidence label")


def assign_groups(records):
    """Connected components of shared source documents; variants stay together."""
    parent = list(range(len(records)))

    def find(index):
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    seen = {}
    for index, record in enumerate(records):
        for key in [record["base_question_id"], *record["source_document_ids"]]:
            if key in seen:
                parent[find(index)] = find(seen[key])
            else:
                seen[key] = index
    components = {}
    for index, record in enumerate(records):
        components.setdefault(find(index), set()).update(record["source_document_ids"])
    for index, record in enumerate(records):
        record["group_id"] = "group:" + fingerprint(sorted(components[find(index)]))


def normalize_answer(text):
    # SQuAD-style normalization; punctuation is removed, never used as a support label.
    import string
    text = "".join(ch for ch in text.lower() if ch not in string.punctuation)
    return " ".join(re.sub(r"\b(a|an|the)\b", " ", text).split())


def document_dict(document):
    return asdict(document)
