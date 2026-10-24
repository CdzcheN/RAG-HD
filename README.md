# RAG-HD：检索增强生成的幻觉检测与量化评估

课题 C09：搭建 RAG 管道，构造“检索失败、证据冲突、答案过时”挑战子集，比较自评置信度、MiniCheck 与改进方法的幻觉检测表现。课程要求与验收指标见[项目要求](项目资料/要求.md)。

## 当前进度

`baseline` 分支已完成 MiniCheck-Flan-T5-Large 公开权重的推理与官方基准评测复现。2026-10-23 的完整 LLM-AggreFact test 评测包含 **29,320 条样本、11 个子数据集**，宏平均 BAcc 为 **75.0093%**。评测配置、分组指标与离线核查见[结果分析](results/minicheck/README.md)。

后续工作包括项目 RAG 管道、至少 300 条挑战样本、自评置信度对照，以及三个划分/训练种子下的比较与消融。当前基准结果尚未验证项目要求的 AUC 提升 0.10。

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
