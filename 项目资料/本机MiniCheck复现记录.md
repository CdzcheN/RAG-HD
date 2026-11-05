# 本机 MiniCheck 复现记录（2026-11-03）

## 代码与实验范围

- 工作分支：`reproduce/minicheck`。
- 来源：`https://github.com/CdzcheN/RAG-HD` 的 `baseline` 分支。
- 来源提交：`e8eb721f74912dd82d359c28c2202cbc3629b557`。
- 官方 MiniCheck 子模块：`b58b9fa69acbd1015ec970fa65dd752413a053d2`。
- 公开权重：`lytang/MiniCheck-Flan-T5-Large`，核对提交为 `96eafd01cee2d16cf81aaa2fb226b14f422a37b3`。
- 复现公开权重的推理与官方评测；后续方法改进以这一配置为基线。

`results/minicheck/` 是从上游复制的历史结果。它记录的 75.0093% 宏平均 BAcc 不能视为本机重跑结果。本机新实验使用独立的输出目录，保留逐条预测和实际运行配置。

## 本机环境

仓库位于 `/home/yqhe/project/rgzn/RAG-HD`。独立环境为仓库内的 `.venv/`，使用系统 Python 3.10.12，不影响已有 Conda 环境。主要依赖见 `requirements-minicheck.txt`；完整依赖清单位于本次实验目录的 `requirements.lock.txt`。实际 PyTorch 为 `2.10.0+cu128`，`pip check` 和 CUDA 检查均通过。

主机有 NVIDIA GeForce RTX 3090（24 GB 显存），驱动 595.99.02。Codex 沙箱中 GPU 不可见；沙箱外的 `nvidia-smi` 检查正常，因此 GPU 检查和推理需要在可访问主机 GPU 的环境中执行。普通主机终端可直接运行以下命令。

```bash
cd /home/yqhe/project/rgzn/RAG-HD
source .venv/bin/activate
export NLTK_DATA=/home/yqhe/nltk_data
export HF_HUB_CACHE="$PWD/.cache/minicheck/hub"
python -m pip check
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available())"
```

已验证 Hugging Face 数据访问授权，固定版本数据与模型已缓存至项目 `.cache/minicheck/`。模型权重 SHA-256 已独立校验为 `41291881e13c6235ed47149cec903bee9493e45d9d7325587a9fa2e266c526c0`。

本机 DNS 将公开下载域名解析至代理地址 `198.18.0.16`，NLTK 下载器将其拦截。已从 NLTK 官方 GitHub 下载并按官方索引 SHA-256 校验资源，安装至私有目录 `/home/yqhe/nltk_data`；没有关闭 NLTK 安全检查。`punkt` 校验值为 `51c3078994aeaf650bfc8e028be4fb42b4a0d177d41c012b6a983979653660ec`，`punkt_tab` 为 `e57f64187974277726a3417ca6f181ec5403676c717672eef6a748a7b20e0106`。

Transformers 在在线加载 `.bin` 权重时会启动额外的远程格式转换线程，本机出现推理完成后进程仍等待的现象。入口新增 `--local-model-files`，仅在官方构造器加载模型和 tokenizer 时传入 `local_files_only=True`，使用已缓存的同一份权重；官方子模块及评分代码保持原样。数据集下载和授权检查仍可联网。一键入口已启用此选项。

## 本机已验证结果

2026-11-03 14:42（北京时间），仅加载本地权重的官方两条样例通过，标签为 `[1, 0]`，支持分数为 `0.9805923700332642` 和 `0.00712132453918457`，与上游归档样例的概率最大差异为 0。本次文件位于 `outputs/minicheck_20261103/smoke/`。

100 条调试已于 14:42 完成，预测文件与配置保存在 `outputs/minicheck_20261103/debug/benchmark/`。该前缀样本只有一个标签类别，因此调试 BAcc 留空，符合脚本的处理规则。

完整基准于 2026-11-03 14:42:31 启动、16:47:50 完成，29,320 条、11 个子数据集，宏平均 BAcc 为 **75.00931317412265%**。随后自动执行离线分析，流水线于 16:47:54 标记 `complete`；2026-11-04 独立读取全部预测再次重算，结果与自动分析一致，完整性、严格阈值和指标重算检查均通过。

完整预测、分组指标及样例预测的 SHA-256 均与上游原始文件清单一致。本次公开权重推理与完整官方基准复现成功，结果单独归档在 [`results/minicheck_20261103/`](../results/minicheck_20261103/README.md)。全量评测耗时约 2 小时 5 分 18 秒；没有记录全程峰值显存，项目 ≤12 GB 显存与挑战集 AUC 提升目标仍需后续验收。

下一里程碑与待实施任务见 [`plan.md`](../plan.md) 第 9 节：先固定协议与字段，再跑通约 20 条正常样本的 RAG 闭环，随后构造约 120 次正常/挑战配对原型。

## 完整评测的数据授权

先在网页登录 Hugging Face 并获得 [LLM-AggreFact](https://huggingface.co/datasets/lytang/LLM-AggreFact) 访问权限，再在本机终端运行：

```bash
cd /home/yqhe/project/rgzn/RAG-HD
.venv/bin/hf auth login
.venv/bin/hf auth whoami
```

在终端交互提示中输入自己的只读 token，不把 token 写入代码、命令参数或聊天。数据授权由账号持有人完成。

## 本机运行命令

环境安装、模型缓存准备和账号授权完成后，推荐使用一键入口；重跑时指定新的目录，例如：

```bash
cd /home/yqhe/project/rgzn/RAG-HD
bash scripts/run_minicheck_reproduction.sh outputs/minicheck_new_run
```

入口检查 GPU 与数据权限，准备 NLTK 资源，然后依次运行样例、100 条调试、完整评测和离线分析。阶段状态位于实验目录的 `status.txt`，各阶段日志位于 `logs/`；同时保存完整依赖清单、来源提交与代码修改。入口要求使用新的实验目录，以保留已有运行记录。

以下命令均在仓库根目录执行，并沿用上述 `NLTK_DATA` 设置。先运行样例，再用单独目录调试，最后跑完整 test 集。数据版本与上游历史评测固定为同一提交。

```bash
python scripts/reproduce_minicheck.py --task smoke --batch-size 1 --local-model-files \
  --output-dir outputs/minicheck_20261103
python scripts/reproduce_minicheck.py --task benchmark --limit 100 --batch-size 1 --local-model-files \
  --dataset-revision 981dfd0bd8e58e7238a9ab92b2e6ea44bce918e4 \
  --output-dir outputs/minicheck_20261103/debug
python scripts/reproduce_minicheck.py --task benchmark --batch-size 1 --local-model-files \
  --dataset-revision 981dfd0bd8e58e7238a9ab92b2e6ea44bce918e4 \
  --output-dir outputs/minicheck_20261103
python scripts/analyze_minicheck.py --skip-plots \
  --benchmark-dir outputs/minicheck_20261103/benchmark \
  --output-dir outputs/minicheck_20261103/analysis
```

样例标签要求为 `[1, 0]`。完整评测要求 29,320 条、11 个子数据集，使用支持分数严格大于 0.5 的判定规则，并报告各子数据集等权平均 BAcc。100 条调试结果不能作为完整复现结论。
