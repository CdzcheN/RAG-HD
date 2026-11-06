# 实验输出目录

本目录完整保留本机已有的正式实验、开发小批、历史准备快照、失败/中断运行、日志和代码快照，方便合作开发者复查。模型下载缓存、原始数据下载目录和Python环境仍不上传。文件内容及原有冻结记录保持原样，不为分享而改写历史结果。

## 建议先看这些

| 内容 | 目录或文件 |
|---|---|
| 最终结果、统计检验与结论 | [正式最终报告](../results/rag_formal_final_20261105/README.md) |
| 全部600条构造输入 | [rag_formal_20261105_v2/prepared.jsonl](rag_formal_20261105_v2/prepared.jsonl) |
| 开发480条：输入、实际回答、确认标签 | [开发records.jsonl](rag_formal_20261105_v2/partitions/development/records.jsonl) |
| 测试120条：输入、实际回答、确认标签 | [测试records.jsonl](rag_formal_20261105_v2/partitions/test/records.jsonl) |
| 300个基础问题的来源清洗说明 | [清洗结果.csv](rag_formal_20261105_v2/清洗结果.csv) |
| 固定训练/验证/测试来源划分 | [frozen_splits.json](rag_formal_20261105_v2/frozen_splits.json) |
| 构造规格、规则与干扰来源准备 | `rag_formal_20261105_v2/`及`rag_formal_inventory_20261105_v1/` |
| 15个分类器、标准化器和验证阈值 | `rag_formal_development_20261105_v1/formal_training/` |
| 测试特征及360条冻结预测 | `rag_formal_development_20261105_v1/final_test/` |
| 逐条预测与完整分组比较 | `rag_formal_development_20261105_v1/final_report/` |
| MiniCheck官方基准的29320条预测 | `minicheck_20261103/benchmark/` |

两个分区各有`review_readable.csv`、`construction_review.csv`、`confirmed_review.jsonl`及`review_confirmation.json`。主目录`prepared.jsonl`是推理前快照，读取带实际回答和最终标签的数据请使用两个分区的`records.jsonl`。标签来源为助手草稿经用户确认，不是独立双人标注。

## 历史记录如何理解

- `rag_prototype_*`：最初的本地生成/RAG原型。
- `rag_challenge_*`：早期挑战构造及修复；正式实验采用`rag_formal_20261105_v2`。
- `rag_improvement_dev_*`、`rag_repair_validation_*`：旧开发集上的方法开发与修复检查，不是最终测试。
- `rag_formal_20261105_v1`：正式构造的准备检查快照，无正式推理；`v2`为最终采用版本。
- 带`setup_failed`、`online_loader_stalled`的目录以及旧目录中的失败状态均为历史记录，保留以说明过程，不能当作当前正式结果。
- `provenance/`、`source_revision.txt`和早期状态文件记录当时状态；当前正式结果以最终报告和两个分区的确认记录为准。

最终测试已解盲，后续方法可以分析其错误，但不能继续用它选规则、调阈值后宣称独立测试提升。

## 在另一台机器使用

CSV、JSON和日志可直接查看。完整重跑还需要按仓库说明准备固定版本的模型、数据、依赖和访问授权；这些下载内容不在本目录。

部分启动脚本、日志及冻结清单保留原机器的绝对路径。直接查看结果不受影响；在不同路径运行原冻结校验时，需要在新的复现目录明确处理路径映射，不能将改写后的证书冒充原始冻结记录。原数据、模型及预测文件的内容应保持原样。

数据来源、许可及修改说明见[DATA_SOURCES.md](DATA_SOURCES.md)。
