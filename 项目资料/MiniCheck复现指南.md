# MiniCheck-Flan-T5-Large 复现指南

本项目采用 **公开权重的推理与指标复现**：先验证官方两条样例，再按官方协议评测 LLM-AggreFact，最后接入 RAG-HD 的回答级幻觉检测。论文的训练数据合成与重新微调是另一项工作；baseline 复现阶段使用已经发布的 `lytang/MiniCheck-Flan-T5-Large` 权重。

已准备独立入口：[scripts/reproduce_minicheck.py](../scripts/reproduce_minicheck.py)。脚本调用仓库内官方 MiniCheck 包，保留默认证据切块和输入长度，输出预测、分组指标和运行配置。

## 1. 当前仓库与环境检查

截至 2026-10-24，根据已保存的真实运行记录：

- `baselines/MiniCheck` 已存在，代码提交为 `b58b9fa69acbd1015ec970fa65dd752413a053d2`。
- 官方 `benchmark_evaluation_demo.ipynb` 默认使用 `Bespoke-MiniCheck-7B`；本项目应显式选择 `flan-t5-large`。
- 2026-10-23 已完成官方两条 smoke 样例和完整 LLM-AggreFact test 评测；29,320 条记录、11 个子数据集的宏平均 BAcc 为 **75.0093%**，详见[结果分析与版本记录](../results/minicheck/README.md)。
- 实验记录使用 Python 3.10.22、NVIDIA GeForce RTX 3090，主要依赖版本保存在 [benchmark/run_config.json](../results/minicheck/benchmark/run_config.json)。在其他机器上仍需单独确认驱动、CUDA 和模型缓存，CPU 可用于样例验证。
- 根目录 `requirements.txt` 已将原先冲突的 Transformers / Hub 约束修正为记录中的 `transformers==4.56.2` 和 `huggingface_hub==0.36.2`；下面仍提供 MiniCheck 独立环境的最小安装命令。

## 2. 准备独立环境

以下为 Bash 命令，在项目根目录执行。主要依赖按真实实验记录固定，保留项目的 Torch / NumPy 数值版本。运行记录没有覆盖全部传递依赖，因此这些版本尚不等于完整环境锁定；重建环境成功后仍应保存完整版本清单。

```bash
conda create -n minicheck-repro python=3.10 -y
conda activate minicheck-repro
python -m pip install -U pip
```

安装推理依赖和本地 MiniCheck 包：

```bash
python -m pip install \
  "torch==2.10.0" "numpy==2.2.6" \
  "transformers==4.56.2" "huggingface_hub==0.36.2" \
  "datasets==3.6.0" "accelerate==1.15.0" \
  "nltk==3.10.4" "scikit-learn==1.7.2" "sentencepiece>=0.2" \
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

准备 NLTK 分句资源，保存在用户主目录下的私有目录中：

```bash
export NLTK_DATA="$HOME/nltk_data"
mkdir -p "$NLTK_DATA"
chmod 700 "$NLTK_DATA"

python - <<'PY'
import os

# 新建的子目录和文件也不允许组用户或其他用户写入。
os.umask(0o077)
import nltk

for package in ("punkt", "punkt_tab"):
    nltk.download(package, download_dir=os.environ["NLTK_DATA"], raise_on_error=True)

nltk.data.find("tokenizers/punkt")
print(nltk.sent_tokenize("This is a test. It works."))
PY
```

预期最后输出 `['This is a test.', 'It works.']`。`punkt` 用于满足官方 MiniCheck 导入时的资源检查，`punkt_tab` 用于 NLTK 分句。

如果此前下载到 `.cache/nltk_data` 时遇到 `NLTK will not authorize the non-private download directory` 或 `Security Violation [downloader.lock]`，说明目标目录或其上级目录允许组用户或其他用户写入，触发了 NLTK 路径安全检查。只修改 `.cache/nltk_data` 本身的权限不能解决上级目录的权限问题；使用上述私有目录重新下载即可。通过 Python API 下载也避免了 `python -m nltk.downloader` 的模块重复加载 `RuntimeWarning`，该警告不是这次权限错误的原因。参见 [NLTK 路径安全实现](https://github.com/nltk/nltk/blob/develop/nltk/pathsec.py)与[数据目录配置说明](https://www.nltk.org/data.html)。

如果出现 `Security Violation [pathsec.urlopen]: refusing a proxied fetch`，说明 NLTK 检测到了代理。代理负责连接目标地址，NLTK 无法对最终连接的 IP 实施 SSRF 防护，因此默认拒绝。仅在确认当前代理可信、适合用于这些公开资源下载时，使用官方提供的选项对本次下载显式放行：

```bash
NLTK_ALLOW_PROXIED_URLOPEN=1 python - <<'PY'
import os

os.umask(0o077)
import nltk

for package in ("punkt", "punkt_tab"):
    nltk.download(package, download_dir=os.environ["NLTK_DATA"], raise_on_error=True)

nltk.data.find("tokenizers/punkt")
print(nltk.sent_tokenize("This is a test. It works."))
PY
```

此命令沿用前面已设置的 `NLTK_DATA`，代理许可仅对这一次 Python 进程生效。若不需要代理且可以直接连接 GitHub，则可以在原下载命令的 `python` 前添加 `env -u http_proxy -u https_proxy -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY`，仅为该进程移除环境中的代理配置。无需关闭 NLTK 的整体安全检查。参见[官方代理许可实现](https://github.com/nltk/nltk/blob/develop/nltk/pathsec.py)。

每次开启新的终端都需要重新激活环境，并执行 `export NLTK_DATA="$HOME/nltk_data"`；资源下载只需成功完成一次。检查 GPU：

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

`lytang/LLM-AggreFact` 是需要授权访问的 gated dataset。首次运行 benchmark 前，需要同时完成网页授权和终端认证：

1. 在浏览器登录 Hugging Face，打开 [LLM-AggreFact 数据集页面](https://huggingface.co/datasets/lytang/LLM-AggreFact)，阅读并同意访问条件，点击页面上的 `Access repository` 或相应同意按钮。条款说明该资源用于评测，不应用于预训练或微调；授权时会按页面说明向作者共享账号信息。如果页面显示等待审批，应等待获得访问权限后再下载。
2. 在同一账号的 [Access Tokens 页面](https://huggingface.co/settings/tokens) 创建具有读取权限的 token；使用 fine-grained token 时，需允许读取这个 gated 数据集。
3. 在运行实验的机器上激活 `minicheck-repro`，执行：

```bash
hf auth login
hf auth whoami
```

按提示在本地终端输入 token；询问是否添加 Git 凭据时，此实验可以选择 `n`。`hf auth whoami` 显示的账号必须与网页获得授权的账号一致。如果没有 `hf` 命令，可使用现有 Python 包登录，无需升级依赖：

```bash
python -c 'from huggingface_hub import login; login()'
```

加载模型前，可以单独检查当前凭据是否有数据集访问权限：

```bash
python - <<'PY'
from huggingface_hub import HfApi

api = HfApi()
print("Hugging Face account:", api.whoami()["name"])
api.auth_check(repo_id="lytang/LLM-AggreFact", repo_type="dataset")
print("LLM-AggreFact access OK")
PY
```

脚本的 `HfApi()` 和 `load_dataset()` 默认读取本地登录凭据。若仍出现 `DatasetNotFoundError: ... gated dataset ... You must be authenticated`，确认网页已授权、token 属于同一账号且拥有相应读取权限。环境中的 `HF_TOKEN` 会覆盖保存的 token；`HF_HUB_DISABLE_IMPLICIT_TOKEN=1` 会阻止这类默认调用携带 token，如曾主动设置该项，可在本终端执行 `unset HF_HUB_DISABLE_IMPLICIT_TOKEN` 后重试。参见 [gated 数据集访问说明](https://huggingface.co/docs/hub/datasets-gated)、[登录命令](https://huggingface.co/docs/huggingface_hub/v0.34.6/guides/cli)和[凭据环境变量](https://huggingface.co/docs/huggingface_hub/v0.34.6/package_reference/environment_variables)。

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

### 已完成的运行与离线核查

本次完整结果及分析归档在 [`results/minicheck/`](../results/minicheck/README.md)，其中包含运行配置、官方分组指标、补充统计和图表。约 89 MiB 的完整预测继续保存在本地 `outputs/minicheck_reproduction/benchmark/predictions.jsonl`；`outputs/` 与 `.cache/` 由 Git 忽略。

基于本地预测重新计算指标，无需模型、GPU 或网络：

```bash
python scripts/analyze_minicheck.py --skip-plots
```

该入口只接受完整官方基准，默认读 `outputs/minicheck_reproduction/benchmark/`，写 `outputs/minicheck_reproduction/analysis/`，支持 `--benchmark-dir` 和 `--output-dir`。省略 `--skip-plots` 且已安装 Matplotlib 时也会生成图表。错误案例和冲突输入包含原始文本，仅随本地分析生成。

核对本次归档所对应的原始文件（在仓库根目录执行，需要本地保留原始输出）：

```bash
sha256sum -c results/minicheck/source_artifacts.sha256
```

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

本分支已保存公开权重推理与完整官方基准的真实结果；2026-10-24 的整理与离线核查没有重新运行模型推理。项目挑战集、自评置信度对照和多种子实验仍待后续实现。
