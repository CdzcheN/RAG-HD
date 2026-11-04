# 本机 MiniCheck 完整复现结果

推理日期：2026-11-03；独立离线核查日期：2026-11-04。工作分支为 `reproduce/minicheck`。本目录是本机新运行的摘要，上游历史归档保留在 `results/minicheck/`。

## 结论与核查

公开权重 MiniCheck-Flan-T5-Large 的推理与完整 LLM-AggreFact test 评测复现成功。

| 项目 | 本次结果 |
| --- | ---: |
| 样本数 / 子数据集数 | 29,320 / 11 |
| 各子数据集等权平均 BAcc | **75.00931317412265%** |
| 上游归档的宏平均 BAcc | 75.00931317412265% |
| 官方榜单参考值 | 75.0% |
| 相对官方四舍五入值的差异 | +0.009313 个百分点 |
| Pooled ROC-AUC | 0.8174340592 |
| 不支持类 AP | 0.5785900540 |
| 完整评测耗时（含初始化及保存） | 7,518.267 秒，约 2 小时 5 分 18 秒 |

官方参考为 [LLM-AggreFact 榜单](https://llm-aggrefact.github.io/)，参考行和各子集数值保存在 `analysis/summary.json`；其中访问日期沿用原分析脚本记录，不代表本次重新访问日期。

本次重新读取逐条预测进行离线重算，结果与流水线自动生成的分析完全一致。样本索引连续，标签与概率合法，没有空文档、空 claim 或阈值规则错误；逐组重算 BAcc 与保存值的最大差异为 0。预测标签严格使用 `support_probability > 0.5`。

完整预测、分组指标文件及两条样例预测的 SHA-256 均与上游原始文件校验清单相同，即这三份产物与上游记录逐字节一致。运行时间、Python 版本等配置来自本机新记录，不能要求其文件校验值与旧配置一致。详见 `verification.json`。

## 分组指标

| 子数据集 | 样本数 | BAcc % |
| --- | ---: | ---: |
| AggreFact-CNN | 558 | 69.95 |
| AggreFact-XSum | 558 | 74.26 |
| ClaimVerify | 1,088 | 74.59 |
| ExpertQA | 3,702 | 58.87 |
| FactCheck-GPT | 1,566 | 74.72 |
| Lfqa | 1,911 | 85.19 |
| RAGTruth | 16,371 | 77.98 |
| Reveal | 1,710 | 86.25 |
| TofuEval-MediaS | 726 | 73.58 |
| TofuEval-MeetB | 772 | 77.30 |
| Wice | 358 | 72.42 |

BAcc 的最后一行 Average 对子数据集等权，不能用混合全部样本的 BAcc（74.7085%）代替。

## 版本与文件

- 来源提交：`e8eb721f74912dd82d359c28c2202cbc3629b557`，实际运行入口修改保存在 `provenance/source_changes.patch`。
- 官方子模块：`b58b9fa69acbd1015ec970fa65dd752413a053d2`。
- 模型提交：`96eafd01cee2d16cf81aaa2fb226b14f422a37b3`。
- 数据提交：`981dfd0bd8e58e7238a9ab92b2e6ea44bce918e4`。
- Python 3.10.12；RTX 3090；batch size 1；证据切块 500；输入上限 2,048；仅加载已校验本地模型文件。
- 实际依赖及运行入口见 `provenance/`。依赖快照含本机 wheel 的安装来源，供审计使用；重建环境的主要版本配方为 `requirements-minicheck.txt`。

原始完整预测、原始错误文本及运行日志仍位于本地 `outputs/minicheck_20261103/`，未复制至本目录。可在仓库根目录执行：

```bash
sha256sum -c results/minicheck_20261103/source_artifacts.sha256
sha256sum -c results/minicheck_20261103/archive_artifacts.sha256
```

## 后续实验边界

本次完成公开权重推理与官方基准复现，没有重新训练 MiniCheck，也没有验证项目挑战集上的 AUC 提升 0.10。正式项目指标需在共同的 RAG 问题、证据、回答和独立标签上比较自评、MiniCheck 与改进方法。

原基准中的 9 组标签冲突输入保留在官方可比指标中；不能将其直接用作项目挑战集标签。RAGTruth 的不支持类 Precision 较低、ExpertQA 的 AUC 较弱，可作为后续观察方向，但需用本项目原型中的真实错误验证。固定分数排序上的问题与阈值问题应分别处理，项目阈值只由验证集选择。

本次没有记录完整任务的峰值显存，先前某一时刻约 6.7 GB 的观测不能证明 ≤12 GB 的全程约束已验收。下一阶段应为生成与检测分别记录峰值显存、运行时间和失败情况。

下一阶段任务与验收顺序见 [项目计划](../../plan.md)。
