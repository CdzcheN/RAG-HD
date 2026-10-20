# MiniCheck-Flan-T5-Large 复现指南

本项目采用 **公开权重的推理与指标复现**：先验证官方两条样例，再按官方协议评测 LLM-AggreFact，最后接入 RAG-HD 的回答级幻觉检测。论文的训练数据合成与重新微调是另一项工作；baseline 复现阶段使用已经发布的 `lytang/MiniCheck-Flan-T5-Large` 权重。

已准备独立入口：[scripts/reproduce_minicheck.py](../scripts/reproduce_minicheck.py)。脚本调用仓库内官方 MiniCheck 包，保留默认证据切块和输入长度，输出预测、分组指标和运行配置。

## 1. 当前仓库与环境检查

截至 2026-10-20 的本地检查：

- `baselines/MiniCheck` 已存在，代码提交为 `b58b9fa69acbd1015ec970fa65dd752413a053d2`。
- 官方 `benchmark_evaluation_demo.ipynb` 默认使用 `Bespoke-MiniCheck-7B`；本项目应显式选择 `flan-t5-large`。
- 当前终端是 Conda base、Python 3.13，尚未安装 MiniCheck 推理依赖。
- 当前 `nvidia-smi` 无法连接 NVIDIA 驱动，需要在实际运行机器上确认驱动与 CUDA 可用性。CPU 可用于样例验证，完整基准应在可用 GPU 环境运行。
- 根目录 `requirements.txt` 同时指定 `transformers>=4.56` 和 `huggingface_hub==0.29.3`。例如 Transformers 4.56.2 要求 `huggingface-hub>=0.34.0,<1.0`，这组约束存在冲突。下面使用独立的最小安装命令；后续统一项目环境时应修正根依赖表。

## 2. 准备独立环境

以下为 Bash 命令，在项目根目录执行。安装配方保留项目的 Torch / NumPy 数值版本，并固定 Transformers 版本；它是待实际安装验证的兼容性起点，成功安装后再保存完整版本锁定文件。

```bash
cd /home/xqyang/Project/RAG-HD
conda create -n minicheck-repro python=3.10 -y
conda activate minicheck-repro
python -m pip install -U pip
```

安装推理依赖和本地 MiniCheck 包：

```bash
python -m pip install \
  "torch==2.10.0" "numpy==2.2.6" \
  "transformers==4.56.2" "huggingface_hub>=0.34.0,<1.0" \
  "datasets>=3,<4" "accelerate>=1,<2" \
  "nltk>=3.9,<4" "scikit-learn>=1.5,<2" "sentencepiece>=0.2" \
  -e ./baselines/MiniCheck
```

其中，`-e ./baselines/MiniCheck` 表示以可编辑模式安装本地这份官方代码；其余官方依赖（如 pandas、openai）由包元数据补齐。

检查安装后的依赖是否一致：

```bash
python -m pip check
```

检查通过时，预期输出：

```text
No broken requirements found.
```

Flan-T5 路径调用本地模型推理，无需 OpenAI API key。首次运行需要访问 Hugging Face 下载模型；建议事先确认网络和磁盘空间。

准备 NLTK 分句资源，将下载内容保存在项目内：

```bash
python -m nltk.downloader -d .cache/nltk_data punkt punkt_tab
export NLTK_DATA="$PWD/.cache/nltk_data"
```

每次开启新的终端都需要重新激活环境，并设置 `NLTK_DATA`。检查 GPU：

```bash
nvidia-smi
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available())"
```

完整 GPU 评测前应看到 `torch.cuda.is_available()` 为 `True`。安装 Python 包不能代替操作系统的 GPU 驱动配置。

## 3. 第一步：官方两条样例

```bash
python scripts/reproduce_minicheck.py --task smoke --batch-size 1
```

官方例子使用“学生在图书馆准备考试”的同一文档，分别核验“学生正在准备考试”和“学生正在度假”。预期：

```text
Predicted labels: [1, 0] (expected [1, 0])
Support probabilities: [约 0.9806, 约 0.0071]
```

其中 `1=受到证据支持`、`0=不受证据支持`。概率允许随依赖或硬件存在小幅数值差异，先检查标签和分数方向。

如果显存不足，优先保持 `--batch-size 1` 并确认没有其他模型占用显存。修改量化、数据类型、切块大小或输入上限会改变复现实验配置，应单独记录。

## 4. 第二步：小批调试，再跑完整官方基准

先验证数据下载与输出链路：

```bash
python scripts/reproduce_minicheck.py --task benchmark --limit 100 --batch-size 1
```

`--limit 100` 只用于调试，不能把输出与完整基准的官方平均值比较。确认链路正常后，运行完整 test 集：

```bash
python scripts/reproduce_minicheck.py --task benchmark --batch-size 1
```

默认输出位于 `outputs/minicheck_reproduction/benchmark/`：

| 文件 | 内容 |
| --- | --- |
| `predictions.jsonl` | 每条样本的文档、claim、真实标签、预测标签、支持分数 |
| `metrics.csv` | 各子数据集 BAcc 与宏平均 BAcc |
| `run_config.json` | 官方代码提交、加载模型提交、数据集提交、依赖版本、GPU、切块与阈值配置 |

默认输出目录会覆盖同一任务上一次的结果；需要保留调试、正式或不同配置的实验时，指定不同的 `--output-dir`。正式评测的逐条预测在推理完成后保存；长任务应使用可靠终端，并预留足够运行时间。

脚本将数据集版本解析为具体提交后加载。需要再次使用同一版本时，从 `run_config.json` 读取 `dataset_revision`，传给 `--dataset-revision`。模型提交记录在 `model_revision`，后续应保留此次模型缓存并核对该值。

## 5. 官方评测口径

使用 `lytang/LLM-AggreFact` 的 `test`，固定官方标签规则：

```python
pred_label = 1 if support_probability > 0.5 else 0
```

对各个子数据集独立计算：

$$
\mathrm{BAcc}_d = \frac{\mathrm{TPR}_d + \mathrm{TNR}_d}{2}
$$

$$
\mathrm{Average}=\frac{1}{|\mathcal D|}\sum_{d\in\mathcal D}\mathrm{BAcc}_d.
$$

这是**各子数据集等权平均**。全部样本混在一起计算的 accuracy 或 pooled BAcc，是另一种统计量。

2026-10-20 查阅的作者官方榜单中，MiniCheck-Flan-T5-L 的 11 个数据集平均 BAcc 为 **75.0%**，例如 WiCE 为 **72.2%**、RAGTruth 为 **78.0%**。以同一数据版本和协议比较；项目提出的“相差不超过 2 个百分点”可作为复现检查目标，不能预先保证达成。

可只复现一个论文明确使用的完整子集并比较该子集的公开指标，但应完整保留子集筛选条件。当前入口默认完整基准；小批 `--limit` 不构成完整子集复现。

## 6. 第三步：接入你的 RAG baseline

官方指标复现完成后，换成本项目中已经生成并缓存的回答，保持生成模型与 MiniCheck 使用同一份证据。将回答切成句子，调用方式如下：

```python
from nltk import sent_tokenize
from minicheck.minicheck import MiniCheck

scorer = MiniCheck(model_name="flan-t5-large", batch_size=1, cache_dir=".cache/minicheck/models")

def answer_hallucination_risk(evidence: str, answer: str):
    sentences = sent_tokenize(answer)  # 英文 SQuAD / HotpotQA 场景
    if not evidence.strip() or not sentences:
        raise ValueError("空证据或空回答应按数据处理协议单独记录")
    _, support, chunks, chunk_probs = scorer.score(
        docs=[evidence] * len(sentences),
        claims=sentences,
        chunk_size=500,
    )
    return {
        "sentences": sentences,
        "sentence_support": [float(p) for p in support],
        "minicheck_risk": 1.0 - min(float(p) for p in support),
    }
```

这里的 `support[i]` 已经由官方代码对文档块取过 MAX；本项目再对各回答句子取 MIN。对应公式为：

$$
r_{\mathrm{mini}}=1-\min_i\max_j P(\mathrm{supported}\mid c_j,s_i).
$$

官方基准中 `label=1` 表示**支持**；本项目幻觉检测中 `y=1` 表示**幻觉**。使用项目自己的真实标签计算 `roc_auc_score(y_hallucination, r_mini)`，不要直接把“支持分数”当作“幻觉风险”。跨句 MIN 聚合属于本项目封装，与官方原始基准的 claim 评测分开记录。

分类阈值只在验证集选择。拒答和空输入遵守项目的数据处理协议，不能静默当作普通事实陈述，也不能由 MiniCheck 分数生成真实标签。

按 `sample_id` 缓存一次句子支持分数和回答风险；三个分组划分种子复用缓存，并在各自相同的测试样本上比较各方法。

## 7. 复现完成的检查标准

1. 官方两条样例的预测标签为 `[1, 0]`。
2. 得到完整基准或明确完整子集的 BAcc，并保留与对应公开值的差异。
3. 保存代码、模型、数据与依赖版本，保留逐条预测。
4. 对项目相同测试样本计算 MiniCheck 的幻觉 ROC-AUC / PR-AUC，以及验证集阈值下的分类指标。
5. 报告准确表述为“采用公开权重复现 MiniCheck 的推理与评测”，并说明项目额外采用的回答切句和 MIN 聚合。

环境成功后可保存完整依赖版本：

```bash
python -m pip freeze > outputs/minicheck_reproduction/requirements.lock.txt
```

## 参考来源

- [本地官方 Notebook](../baselines/MiniCheck/benchmark_evaluation_demo.ipynb)。
- [MiniCheck 官方代码与用法](https://github.com/Liyan06/MiniCheck)。
- [公开模型权重与官方样例](https://huggingface.co/lytang/MiniCheck-Flan-T5-Large)。
- [LLM-AggreFact 数据集](https://huggingface.co/datasets/lytang/LLM-AggreFact)。
- [作者官方榜单](https://llm-aggrefact.github.io/)。
- [Transformers 4.56.2 依赖约束](https://github.com/huggingface/transformers/blob/v4.56.2/src/transformers/dependency_versions_table.py)。

当前交付仅完成代码检查、入口静态检查及复现步骤整理；尚未在当前终端下载模型、安装依赖或产生真实 benchmark 分数。
