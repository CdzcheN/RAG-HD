# 输出中的数据来源与修改说明

实验输出包含第三方数据文本、原始标注及本项目生成/构造内容。数据文本不因本项目发布而改变原有来源或许可。

| 来源 | 本次使用的版本 | 上游数据卡标注的许可 | 用途 |
|---|---|---|---|
| [SQuAD](https://huggingface.co/datasets/rajpurkar/squad) | `7b6d24c440a36b6815f21b70d25016731768db1f` | CC BY-SA 4.0 | RAG来源问题与证据，构造控制条件 |
| [HotpotQA](https://huggingface.co/datasets/hotpotqa/hotpot_qa) | `1908d6afbbead072334abe2965f91bd2709910ab` | CC BY-SA 4.0 | RAG来源问题与证据，构造控制条件 |
| [LLM-AggreFact](https://huggingface.co/datasets/lytang/LLM-AggreFact) | `981dfd0bd8e58e7238a9ab92b2e6ea44bce918e4` | CC BY-ND 4.0 | MiniCheck官方评测复现 |

上游对应版本的数据卡原文保存在`source_dataset_cards/`，其中包含原作者、项目和论文引用信息。SQuAD/HotpotQA证据含Wikipedia来源；应继续保留上游归属及适用条款。本项目基于这些数据的改造材料按原数据的适用条款分享，不将原始文本声明为本项目独创。

对SQuAD/HotpotQA，本项目进行了来源筛选、问题范围澄清、证据节选、干扰检索及受控统计值/版本/来源优先级构造；逐项变化见`audit`、`construction`、清洗记录和构造规格。更改后的统计值仅用于受控实验，不能当作当前真实世界事实。生成回答及助手复核意见也不等同于原数据集金标。

MiniCheck官方基准预测保留LLM-AggreFact输入行并追加预测列；来源的doc/claim/label不是本项目构造的挑战。该数据卡注明仅用于评测，不得用于任何NLP模型的预训练或微调；本项目将它用于官方基准评测，轻量分类器训练使用另行构造的SQuAD/HotpotQA开发数据。合作开发者应继续遵守上游许可及访问条件，访问凭据自行配置，不随实验输出分享。
