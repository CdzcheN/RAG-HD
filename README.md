# RAG-HD：检索增强生成的幻觉检测与量化评估

课题 C09：搭建 RAG 管道，构造“检索失败、证据冲突、答案过时”挑战子集，比较自评置信度、MiniCheck 与改进方法的幻觉检测表现。课程要求与验收指标见[项目要求](项目资料/要求.md)。

## 当前进度

本机 `reproduce/minicheck` 分支已于 **2026-11-03** 完成独立重跑，**2026-11-04** 完成逐条预测离线核查：29,320 条、11 个子数据集，宏平均 BAcc **75.0093%**；完整预测和分组指标的 SHA-256 均与上游清单一致。本机配置、核查和摘要见[本次复现结果](results/minicheck_20261103/README.md)，后续执行顺序见 [plan.md](plan.md)。

`baseline` 分支已完成 MiniCheck-Flan-T5-Large 公开权重的推理与官方基准评测复现。2026-10-23 的完整 LLM-AggreFact test 评测包含 **29,320 条样本、11 个子数据集**，宏平均 BAcc 为 **75.0093%**。评测配置、分组指标与离线核查见[结果分析](results/minicheck/README.md)。

后续工作包括项目 RAG 管道、至少 300 条挑战样本、自评置信度对照，以及三个划分/训练种子下的比较与消融。当前基准结果尚未验证项目要求的 AUC 提升 0.10。

2026-11-04 已部署本地 Qwen2.5-3B-Instruct 4-bit，完成 SQuAD / HotpotQA 各 10 条正常问题的 BM25 → 生成 → 自评 → MiniCheck 原型推理。共 17 条事实回答、3 条拒答；标签现已由用户检查确认，其中 15 条进入共同评估。复核后的开发指标与挑战批次启动情况见下文。统计与资源见[原型验收结果](results/rag_prototype_20261104/README.md)，使用方法见[本地模型部署](项目资料/本地生成模型部署.md)，输入与标签边界见[原型实验协议](项目资料/RAG原型实验协议.md)。

## 本地生成与 RAG 原型

当前机器已准备模型、数据和 `.venv/` 环境，可直接使用本地问答入口：

```bash
.venv/bin/python scripts/local_qa.py \
  --question "What is the capital of the fictional region of Lumeria?" \
  --evidence "The fictional region of Lumeria has its capital in Bayport."
```

新建一次原型运行（复用本地权重和数据；GPU 阶段需在主机终端执行）：

```bash
bash scripts/run_rag_prototype.sh outputs/rag_prototype_new_run
```

配置位于 `configs/rag_prototype.yaml`，新增依赖见 `requirements-rag.txt`。本次运行目录是 `outputs/rag_prototype_20261104_v1/`，内有逐条结果、状态、日志、资源记录和不含检测分数的 `review_template.csv`。原型指标需经过可靠标签复核；`undetermined` 不自动当作负类。新增逻辑的 CPU 检查入口为：

```bash
.venv/bin/python -m unittest discover -s tests -v
```

20 条原型已整理助手辅助复核稿和人工填写表，位于本地运行目录的 `review_assistance/`。建议列与正式标签分开，尚不构成人工金标；导入方式、歧义案例和三类挑战实施草案见[原型标签复核与挑战准备](项目资料/原型标签复核与挑战准备.md)。

## 运行 MiniCheck

在仓库根目录执行，先初始化官方代码子模块：

```bash
git submodule update --init --recursive
conda create -n minicheck-repro python=3.10 -y
conda activate minicheck-repro
python -m pip install -U pip
```

按 [MiniCheck 复现指南](项目资料/MiniCheck复现指南.md)安装最小推理环境，准备 NLTK 资源并完成 Hugging Face 数据集授权后运行：

```bash
python scripts/reproduce_minicheck.py --task smoke --batch-size 1
python scripts/reproduce_minicheck.py --task benchmark --batch-size 1
```

小批调试可加 `--limit 100`；用不同的 `--output-dir` 保留调试与正式实验，避免覆盖。项目完整环境的依赖表为 [requirements.txt](requirements.txt)，MiniCheck 独立环境的安装配方见复现指南；本分支已将 Transformers / Hub 固定到记录中的兼容版本。

从已保存的完整预测重新计算指标，无需加载模型：

```bash
python scripts/analyze_minicheck.py --skip-plots
```

默认读取 `outputs/minicheck_reproduction/benchmark/` 并写入同级 `analysis/`。可用 `--benchmark-dir`、`--output-dir` 指定其他路径；省略 `--skip-plots` 时，已安装 Matplotlib 的环境还会生成图表。该分析入口要求完整官方基准，不接受 `--limit` 产生的不完整结果。

## 仓库导航

| 路径 | 用途 |
| --- | --- |
| [scripts/](scripts/) | MiniCheck 评测入口与离线分析脚本 |
| [baselines/MiniCheck/](baselines/MiniCheck/) | 官方 MiniCheck 子模块，固定到原始复现提交 |
| [results/minicheck/](results/minicheck/) | 可纳入版本管理的配置、指标、图表和分析报告 |
| `outputs/` | 本地原始预测与重新生成的分析产物，Git 忽略 |
| `.cache/` | 本地模型及数据缓存，Git 忽略 |
| [项目资料/要求.md](项目资料/要求.md) | 课程要求、项目目标与交付标准 |
| [项目资料/项目启动与实施指南.md](项目资料/项目启动与实施指南.md) | 项目整体实施方案，部分规划脚本尚待实现 |
| [项目资料/C09_项目实施指导.md](项目资料/C09_项目实施指导.md) | 实验协议、特征与评估设计 |
| [项目资料/docs/开题报告.md](项目资料/docs/开题报告.md) | 开题报告源文档，同目录含 Word / PDF 版本 |
| [项目资料/figures/minicheck_baseline.md](项目资料/figures/minicheck_baseline.md) | MiniCheck 接入流程及图示 |

原始预测保留在本地；仓库保存结果摘要及原始文件的 SHA-256 校验清单。获取数据授权并完成相同配置的实验后，可重新生成完整预测与错误案例。


## 用户复核后的挑战原型

20 条正常原型标签已由用户检查确认并导入，共 15 条进入共同评估：自评 ROC-AUC 0.6477、MiniCheck 0.7500。仅为小规模开发诊断，结果见[复核后原型记录](results/rag_pilot_reviewed_20261104/README.md)。

三类挑战的 60 个基础问题已形成 120 条正常/挑战配对，并启动本机后台推理，运行目录为 `outputs/rag_challenge_20261104_v4/`。[冻结协议](项目资料/挑战原型协议.md)明确了受控支撑补全、可见冲突来源规则、旧/新版有效区间及标注边界。可查看日志：

```bash
tail -n 30 -f outputs/rag_challenge_20261104_v4/logs/pipeline.log
```

生成后还需检查构造与实际回答标签；不会按挑战类型自动标成幻觉。简明复核表 `review_readable.csv` 会在流水线评估阶段生成。


## 首版轻量改进（2026-11-05）

120条挑战原型标签已获用户确认，保留34条未确定，86条进入共同评估。自评AUC **0.6296**，原始MiniCheck **0.7127**；仅依据公开来源/日期筛选有效证据后重评分，同批开发AUC **0.9117**。已实现逻辑回归、三个来源分组开发划分和三组消融，30项检查通过。

这是已用于方法开发的合成原型，不能作为独立测试或研究目标达标结论。数据质量边界、失败实验和统计区间见[首版改进结果](results/rag_improvement_dev_20261105/README.md)，复现入口见[开发协议](项目资料/轻量改进开发协议.md)。
