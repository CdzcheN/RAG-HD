# 原型辅助复核与挑战准备记录

2026-11-04，承接 `outputs/rag_prototype_20261104_v1/` 的 20 条原型。人工复核未完成，本记录不构成 P2.5 验收，也不计算检测 AUC。

- 完成 20 条助手文本分析建议：11 supported、3 unsupported、1 contradicted、5 undetermined（含 3 条拒答）。这些计数不是人工金标或方法性能。
- 导出不含检测分数的完整阅读稿和辅助 CSV；按用户要求预填 20 条标签、正确性和理由，并删除 review_source 列，等待用户检查确认。
- 原有运行状态与正式标签保持待人工复核，没有新增模型推理。
- 17 项 CPU 检查通过；复核导入测试确认 assistant 来源会被拒绝。
- 三类挑战的可见判定规则、配对与时间构造边界已形成草案，尚未冻结或启动 120 次推理。

操作方式、具体歧义和下一阶段草案见[原型标签复核与挑战准备](../../项目资料/原型标签复核与挑战准备.md)。本地阅读稿：`outputs/rag_prototype_20261104_v1/review_assistance/review_packet.md`；人工填写表：同目录 `review_assisted.csv`。

本目录只保存建议身份、理由、输入/回答哈希、证据区间及引用校验值，不保存完整数据集证据文本。`assistant_assessments_metadata.json` 中的来源始终是 assistant。`review_packet_manifest.json` 记录本地完整复核产物的校验值，`source_sha256.json` 固定本轮代码和说明，`verification.json` 记录验证范围。
