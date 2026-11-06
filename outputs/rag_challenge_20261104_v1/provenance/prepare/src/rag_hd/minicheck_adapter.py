"""Official chunk MAX followed by answer-sentence MIN for the RAG pilot."""
from functools import partial
from unittest.mock import patch


class AnswerScorer:
    def __init__(self, config, cache):
        import nltk
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
        from minicheck.minicheck import MiniCheck
        nltk.sent_tokenize("Verify sentence resources.")
        self.config = config
        common = dict(local_files_only=True, revision=config["revision"])
        with patch.object(AutoModelForSeq2SeqLM, "from_pretrained", partial(
                AutoModelForSeq2SeqLM.from_pretrained, **common)), \
             patch.object(AutoTokenizer, "from_pretrained", partial(
                AutoTokenizer.from_pretrained, **common)):
            self.scorer = MiniCheck(model_name="flan-t5-large", batch_size=config["batch_size"],
                                   max_model_len=config["max_model_len"], cache_dir=str(cache))
        if self.scorer.model.model.config._commit_hash != config["revision"]:
            raise RuntimeError("MiniCheck revision mismatch")

    def score(self, record, answer, refusal=False):
        import nltk
        if refusal or not answer.strip():
            return {"status": "refusal" if refusal else "empty_answer", "sentences": [],
                    "sentence_support": [], "risk": None, "chunk_support": []}
        sentences = nltk.sent_tokenize(answer)
        # The question is visible to both baselines; it isn't a gold answer or hidden condition.
        document = f"Question: {record['question']}\n\nEvidence:\n{record['visible_evidence']}"
        _, support, chunks, probabilities = self.scorer.score(
            docs=[document] * len(sentences), claims=sentences, chunk_size=self.config["chunk_size"])
        return {"status": "ok", "sentences": sentences,
                "sentence_support": [float(p) for p in support],
                "risk": 1 - min(float(p) for p in support), "chunks": chunks,
                "chunk_support": [[float(p) for p in ps] for ps in probabilities]}
