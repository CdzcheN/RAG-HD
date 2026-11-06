---
language:
- en
license: cc-by-nd-4.0
size_categories:
- 10K<n<100K
configs:
- config_name: default
  data_files:
  - split: dev
    path: data/dev-*
  - split: test
    path: data/test-*
dataset_info:
  features:
  - name: dataset
    dtype: string
  - name: doc
    dtype: string
  - name: claim
    dtype: string
  - name: label
    dtype: int64
  - name: contamination_identifier
    dtype: string
  splits:
  - name: dev
    num_bytes: 94376345
    num_examples: 30420
  - name: test
    num_bytes: 88297787
    num_examples: 29320
  download_size: 52751341
  dataset_size: 182674132
extra_gated_prompt: By clicking “Access repository” below, you confirm your understanding
  that this resource is permitted for use as an evaluation benchmark. Data in the  benchmark
  should not be used in pretraining or fine-tuning any NLP models.
---

# Important Update 08.09.2024

We announce the [LLM-AggreFact leaderboard](https://llm-aggrefact.github.io) with 35 latest fact-checking models being evaluated.

<p align="center">
    <img src="./performance.png" width="550">
</p>

We include one additional dataset [RAGTruth](https://arxiv.org/pdf/2401.00396) to our benchmark. 
We convert the dataset to the same format as in our benchmark and removed those non-checkworthy claims. 
We include a randomly sampled subset of the training set from RAGTruth into the validation set of the benchmark
since the original training set is too large after conversion.


# Important Update 05.03.2024

Following [Jacovi et al.](https://aclanthology.org/2023.emnlp-main.308.pdf) (2023), 
an identifier 64-character string is added to each instance in LLM-AggreFact to assist 
in future detection of contamination in web-crawl corpora.


# Benchmark Summary

LLM-AggreFact is a fact verification benchmark from the work ([GitHub Repo](https://github.com/Liyan06/MiniCheck)):

📃 **MiniCheck: Efficient Fact-Checking of LLMs on Grounding Documents** ([link](https://arxiv.org/pdf/2404.10774.pdf), EMNLP 2024)

It aggregates 11 of the most up-to-date publicly available datasets on factual consistency evaluation across 
both closed-book and grounded generation settings. In LLM-AggreFact:
1. Documents come from diverse sources, including Wikipedia paragraphs, interviews, and web text, covering domains
such as news, dialogue, science, and healthcare.
2. Claims to be verified are mostly generated from recent generative models (except for one dataset of human-written
claims), *without any human intervention in any format, such as injecting certain error types into model-generated claims*.

**This resource is permitted for use as an evaluation benchmark. Data in the 
  benchmark should not be used in pretraining or fine-tuning any NLP models.**


## Datasets in Benchmark:

LLM-AggreFact collects data from the following 11 datasets.

- AggreFact-CNN (SOTA set, [Tang et al., 2023](https://aclanthology.org/2023.acl-long.650.pdf))
- AggreFact-XSum (SOTA set, [Tang et al., 2023](https://aclanthology.org/2023.acl-long.650.pdf))
- TofuEval-MediaSum ([Tang et al., 2024](https://arxiv.org/pdf/2402.13249.pdf))
- TofuEval-MeetingBank ([Tang et al., 2024](https://arxiv.org/pdf/2402.13249.pdf))
- Wice ([Kamoi et al., 2023](https://aclanthology.org/2023.emnlp-main.470.pdf))
- Reveal ([Jacovi et al., 2024](https://arxiv.org/pdf/2402.00559.pdf))
- ClaimVerify ([Liu et al., 2023)](https://aclanthology.org/2023.findings-emnlp.467.pdf)
- FactCheck-GPT ([Wang et al., 2023](https://arxiv.org/pdf/2311.09000.pdf))
- ExpertQA ([Malaviya et al., 2024](https://arxiv.org/pdf/2309.07852.pdf))
- Lfqa ([Chen et al., 2023](https://arxiv.org/pdf/2310.12150.pdf))
- RAGTruth ([Niu et al., 2024](https://arxiv.org/pdf/2401.00396))


# Benchmark Access

```python
from datasets import load_dataset
dataset = load_dataset("lytang/LLM-AggreFact")
```

The benchmark contains the following fields:


```
DatasetDict({
    dev: Dataset({
        features: ['dataset', 'doc', 'claim', 'label', 'contamination_identifier'],
        num_rows: 30420
    })
    test: Dataset({
        features: ['dataset', 'doc', 'claim', 'label', 'contamination_identifier'],
        num_rows: 29320
    })
})
```

|Field| Description |
|--|--|
|dataset| One of the 10 datasets in the benchmark|
|doc| Document used to check the corresponding claim|
|claim| Claim to be checked by the corresponding document|
|label| 1 if the claim is supported, 0 otherwise|
|contamination_identifier| An identification string for contamination detection |


# Citation

```
@InProceedings{tang-etal-2024-minicheck,
  title = {MiniCheck: Efficient Fact-Checking of LLMs on Grounding Documents},
  author = {Liyan Tang and Philippe Laban and Greg Durrett},
  booktitle = {Proceedings of the 2024 Conference on Empirical Methods in Natural Language Processing},
  year = {2024},
  publisher = {Association for Computational Linguistics},
  url = {https://arxiv.org/pdf/2404.10774}
}
```