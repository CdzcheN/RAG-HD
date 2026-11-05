# RAG 原型实验协议 v1

日期：2026-11-04。配置：`configs/rag_prototype.yaml`。本阶段验证本地闭环和标注流程，不作方法提升结论。正式实验前仍需人工核验标签协议，并隔离原型开发样本。

## 数据、范围与稳定性

使用 [SQuAD 1.1](https://huggingface.co/datasets/rajpurkar/squad) 的 `plain_text/train` 和 [HotpotQA](https://huggingface.co/datasets/hotpotqa/hotpot_qa) 的 `distractor/train`，两个来源的模型卡均标注 CC BY-SA 4.0。原始数据只保存在被 Git 忽略的本地缓存中。

| 数据 | 固定提交 | 完整 train 行数 | 原型候选池 / 问题数 |
| --- | --- | ---: | ---: |
| SQuAD | `7b6d24c440a36b6815f21b70d25016731768db1f` | 87,599 | 200 / 10 |
| HotpotQA | `1908d6afbbead072334abe2965f91bd2709910ab` | 90,447 | 200 / 10 |

按 `SHA256(seed, dataset, original_id)` 对完整训练 ID 排序，取前 200 条作为候选池；再按独立的 `pilot-question` 哈希命名空间选 10 个问题。种子为 `20260918`。这避免依赖 Parquet 物理行顺序；不按检测分数、生成正确性或标签挑选样本。

检索库是两个候选池全部给定上下文的并集、按文档内容去重，共 2,193 个段落。它是明确受限的开发语料，不是完整维基开放域检索基准。所有记录为 `condition=normal`，表示未施加人工挑战；自然检索失败仍然保留。不能把 `normal` 当成 `supported`。

文档 ID 由规范化来源标题与内容生成，来源 ID 对维基标题的大小写、空白和下划线做统一。基础问题 ID 保留来源数据集及原始 ID；样本 ID 加入实际可见输入内容哈希。共享来源文档或原问题的记录按连通分量赋同一 `group_id`，所有变体以后继承同组。原型当前有 20 个独立来源组；正式抽样后应重新进行完整分组审计。

## 字段和输入边界

`prepared.jsonl` 每条记录包含：

- 标识与来源：`sample_id`、`base_question_id`、`source_document_ids`、`group_id`、`dataset`。
- 可见内容：`question`、`evidence`、统一呈现的 `visible_evidence`、`visible_input_sha256`。
- 证据来源：每个片段的文档 ID、来源标题、版本、排名、BM25 分数、可见内容哈希及截断标记。
- 构造记录：协议版本、`condition`、`construction`；本轮操作为 `none`。
- 私有诊断命名空间 `audit`：标准答案、原始支撑文档与支撑句、来源提交、原始分割、金标文档召回率、支撑内容是否全部可见。

生成器、自评与 MiniCheck 都只接收实际问题与同一份 `visible_evidence`。自评和 MiniCheck 还接收相同的生成回答。标准答案、金标支撑句、构造类型、扰动位置和来源分组不进入模型输入或检测特征。

统一证据呈现包括标题、版本和正文，不包括金标标记。当前版本字段是数据提交；未来挑战中的有效时间与来源优先规则须以三种方法均可见的文本明确表达，另行升级协议。

## 检索与生成

BM25 使用 `rank-bm25==0.2.2`，`k1=1.5`、`b=0.75`；标题和正文共同分词，使用小写 ASCII 字母数字词项。取 Top-5，相同分数按文档 ID 排序。每个文档最多呈现前 250 个空白分词，总证据最多 1,200 词。实际可见证据及截断情况完整保存，诊断也基于截断后文本。

使用 [Qwen2.5-3B-Instruct 官方权重](https://huggingface.co/Qwen/Qwen2.5-3B-Instruct)，固定提交 `aa8e72537993ba99e69dfaafa59ed015b17504d1`，许可证为仓库内 Qwen Research License。权重和许可证缓存至 `.cache/rag/hub/`，不将权重提交到 Git。

本地加载配置为 bitsandbytes `0.48.2`、NF4 双重量化、float16 计算、单卡、SDPA、贪心解码。保留已验证的 Torch 2.10.0、Transformers 4.56.2 和主要基线依赖。代码关闭远程模型代码执行，并在推理时只读固定提交的本地文件。

生成提示词要求根据证据给出一句简短的事实回答，证据不足时只返回 `INSUFFICIENT_EVIDENCE`。输入上限 4,096 tokens，回答最多 128 个新 token。超过输入上限时明确失败，不静默截断；达到输出上限会记录标志。提示词保存在生成模块中，其源文件哈希参与缓存键。

## 两种检测分数

自评使用同一个生成模型，明确询问“证据是否支持这份回答中的全部事实”，要求严格 JSON：`{"support_confidence": NUMBER}`。仅接受 `[0,1]` 内的有限数值，拒绝布尔、字符串、额外字段、自然语言和越界结果。首次解析失败后只允许一次格式修正重试；保留两次原文、错误和 token 数。最终失败记 `parse_failed`，不填入默认概率。风险为 `1-c`。

MiniCheck 使用已经复现的原始固定权重，batch size 1、证据块 500、输入上限 2,048。为保持可见问题一致，文档输入为 `Question: ... / Evidence: ...`；claim 为生成回答的各句。官方代码在每个句子上对证据块取 MAX，项目再对句子支持分数取 MIN，风险为 `1-min(sentence_support)`。这是回答级项目封装，区别于公开基准的独立 claim 评测。

拒答和空回答不强行形成事实 claim，其检测风险为空并记录状态。两种方法分别保留原始解析/分句/逐块结果，最终验证可见输入与回答哈希一致。

## 标签协议与待人工核验项

标签取 `supported / unsupported / contradicted / outdated / undetermined`；前三种不支持类型中 `unsupported / contradicted / outdated` 组成幻觉正类。拒答另用 `is_refusal` 标记，不进入主事实幻觉 AUC。

答案正确性单独保存为 `answer_correctness=correct/incorrect/undetermined` 及其来源：完全匹配参考答案时可标为 correct，其余默认 undetermined、等待复核。另提供规范化 Exact Match 与 Token F1 诊断。短标准答案与整句生成回答可能无法达到 EM，因此不匹配既不能直接判答案错误，也不能直接作为证据支持标签。

自动标签规则只覆盖一种保守情况：**整个规范化回答与数据集标注答案完全相同，且全部原始金标支撑内容实际可见**，标为 `supported`。任何不满足此规则的情况记为 `undetermined`；错过别名或支撑未完整显示都不能据此自动标成幻觉。原型不使用 MiniCheck、自评或另一 NLI 分数生成真值。

其余回答需由人工根据问题、实际可见证据、参考答案和来源支撑复核。`review_requests.jsonl` 和 `review_template.csv` 是不含两种检测分数的复核清单；人工标注文件保留 `sample_id`、`visible_input_sha256`、`answer_sha256`，填写 `evidence_label`、`answer_correctness`、`review_source="human"`、`reviewer`、`rationale`。本程序不会伪造人工复核记录。导入时拒绝未知 ID、重复 ID、变动的原始输入/回答、缺失依据和拒答的事实标签，避免把旧回答的标注复用到新回答上。

待原型人工确认后，正式冻结拒答排除方式、无法判断的处理和人工分歧规则，再扩展三类成对挑战。

## 指标、缓存及资源记录

主比较只使用：非拒答、有可靠标签、两种方法都能给出有限风险分数的共同集合。报告全部输入数、拒答率、标签覆盖率、各方法缺失数及共同集合覆盖率。共同标签不足两类时 ROC-AUC 和 AP 均为空，并给出原因，不能强行补值。此开发批次不调阈值，不作性能提升或显著性结论。

每条生成和检测结果增量保存，支持中断后读取验证过的缓存。缓存键包含可见输入、生成配置/提示词、种子、模型提交、原始回答及相应模块内容哈希。配置或输入不符时拒绝复用，要求新建实验目录。

生成/自评分阶段结束后进程退出，才加载 MiniCheck。生成模型加载也计入资源测量，记录 CUDA 分配器的 allocated/reserved 峰值，以及每 0.5 秒通过 `nvidia-smi` 采样的本进程显存；三者均须不超过 12,288 MiB，缺少进程采样时不标记资源验收通过。进程采样不是瞬时峰值的精确上界，报告必须注明测量方式和实际测试的输入范围。

阶段状态保存至 `status.json`，原始文本、缓存和逐条数据均留在 `outputs/`。只有配置、代码、无原始数据的统计与校验摘要进入结果归档。
