"""BM25 over the declared pilot corpus; labels never enter retrieval."""
import re

from .io import fingerprint


def tokenize(text):
    return re.findall(r"[a-z0-9]+", text.casefold())


class Retriever:
    def __init__(self, documents, k1=1.5, b=0.75):
        from rank_bm25 import BM25Okapi
        self.documents = sorted(documents, key=lambda doc: doc.document_id)
        if not self.documents:
            raise ValueError("Empty retrieval corpus")
        self.index = BM25Okapi([tokenize(doc.title + " " + doc.text) for doc in self.documents], k1=k1, b=b)

    def search(self, question, top_k, max_words_per_document, max_evidence_words):
        if min(top_k, max_words_per_document, max_evidence_words) <= 0:
            raise ValueError("Retrieval limits must be positive")
        scores = self.index.get_scores(tokenize(question))
        order = sorted(range(len(scores)), key=lambda i: (-float(scores[i]), self.documents[i].document_id))[:top_k]
        evidence = []
        remaining = max_evidence_words
        for index in order:
            if remaining <= 0:
                break
            doc = self.documents[index]
            words = doc.text.split()
            visible = " ".join(words[:min(max_words_per_document, remaining)])
            remaining -= len(visible.split())
            evidence.append({"document_id": doc.document_id, "source_document_id": doc.source_document_id,
                             "title": doc.title, "text": visible, "version": doc.version,
                             "rank": len(evidence) + 1, "bm25_score": float(scores[index]),
                             "content_sha256": fingerprint(visible), "truncated": len(visible.split()) < len(words)})
        return evidence
