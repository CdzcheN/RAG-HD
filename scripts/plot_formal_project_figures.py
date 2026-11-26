"""Generate formal Chinese-captioned project route, architecture and results PNGs."""
import argparse
import json
from pathlib import Path

import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib import font_manager
import pandas as pd


FONT_PATH = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
font_manager.fontManager.addfont(FONT_PATH)
FONT = font_manager.FontProperties(fname=FONT_PATH).get_name()
mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": [FONT, "DejaVu Sans"],
    "axes.unicode_minus": False,
    "svg.fonttype": "none",
    "pdf.fonttype": 42,
    "font.size": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
})
BLUE = "#2f6f9f"
TEAL = "#238b8d"
ORANGE = "#d67b2f"
RED = "#b54b4b"
GREY = "#6b7280"
LIGHT = "#eef4f7"


def save(fig, out, name):
    path = out / name
    fig.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def box(ax, x, y, w, h, text, color=LIGHT, edge=BLUE, fs=11):
    patch = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.012,rounding_size=0.02",
                           linewidth=1.4, facecolor=color, edgecolor=edge)
    ax.add_patch(patch)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            wrap=True, color="#1f2937")


def arrow(ax, x1, y1, x2, y2, color=GREY):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=14,
                                 linewidth=1.4, color=color))


def route(out):
    fig, ax = plt.subplots(figsize=(13, 5.8))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.set_title("图1  RAG 幻觉检测项目技术路线", loc="left", fontsize=16, weight="bold", pad=14)
    stages = [
        (0.03, "公开数据与\n来源清洗", "SQuAD / HotpotQA\n问题范围与来源隔离"),
        (0.21, "受控挑战构造", "检索失败\n证据冲突\n答案过时"),
        (0.39, "RAG 推理", "BM25 检索\nQwen 生成\n模型自评"),
        (0.57, "证据核验", "原 MiniCheck\n有效证据筛选\n重评分"),
        (0.75, "学习与消融", "逻辑回归融合\n3 个随机种子\n固定验证阈值"),
        (0.90, "冻结评估", "AUC / AP / F1\n分组分析\nbootstrap 与置换检验"),
    ]
    for i, (x, title, desc) in enumerate(stages):
        box(ax, x, 0.40, 0.12 if i < 5 else 0.09, 0.23, f"{title}\n\n{desc}",
            color="#eaf3f7" if i not in (1, 5) else "#fff3e6", edge=BLUE if i != 5 else ORANGE, fs=9)
        if i < len(stages) - 1:
            w = 0.12 if i < 5 else 0.09
            next_x = stages[i + 1][0]
            arrow(ax, x + w, 0.515, next_x, 0.515)
    ax.text(0.03, 0.16, "冻结边界：最终测试仅在模型、数据划分、阈值和分析方案冻结后运行；解盲后不再调参。",
            fontsize=10, color=RED)
    ax.text(0.03, 0.08, "数据规模：300 个基础问题 → 300 条挑战 + 300 条正常对照；开发 480 条，最终测试 120 条。",
            fontsize=10, color=GREY)
    return save(fig, out, "图1_项目技术路线.png")


def architecture(out):
    fig, ax = plt.subplots(figsize=(13, 7))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.set_title("图2  有效证据 MiniCheck 重评分与轻量融合架构", loc="left", fontsize=16, weight="bold", pad=14)
    box(ax, 0.03, 0.60, 0.16, 0.20, "问题 q\n可见证据 D\n固定回答 a", color="#eaf3f7")
    arrow(ax, 0.19, 0.70, 0.29, 0.70)
    box(ax, 0.29, 0.60, 0.17, 0.20, "BM25 检索\n固定生成\nQwen2.5-3B", color="#eaf3f7")
    arrow(ax, 0.46, 0.70, 0.55, 0.70)
    box(ax, 0.55, 0.72, 0.18, 0.14, "原始证据评分\nMiniCheck → r₀", color="#eef6ef", edge=TEAL)
    box(ax, 0.55, 0.47, 0.18, 0.14, "公开规则解析\n来源优先级 / 时间区间", color="#fff3e6", edge=ORANGE)
    arrow(ax, 0.73, 0.54, 0.81, 0.54, color=ORANGE)
    box(ax, 0.81, 0.47, 0.15, 0.14, "有效证据 D_eff\n重评分 → r_eff", color="#fff3e6", edge=ORANGE)
    arrow(ax, 0.73, 0.79, 0.81, 0.79, color=TEAL)
    box(ax, 0.81, 0.72, 0.15, 0.14, "原始风险 r₀\n基线输出", color="#eef6ef", edge=TEAL)
    arrow(ax, 0.90, 0.61, 0.90, 0.39)
    arrow(ax, 0.90, 0.72, 0.90, 0.39)
    box(ax, 0.70, 0.18, 0.26, 0.16, "11 维轻量特征\n覆盖率、风险差、排除比例\nStandardScaler + LogisticRegression", color="#f1eef8", edge="#7864a9", fs=9)
    arrow(ax, 0.55, 0.47, 0.55, 0.35, color=ORANGE)
    ax.text(0.03, 0.25, "主方法：D_eff → 原 MiniCheck 重评分\n扩展方法：r₀、r_eff 及公开输入特征 → 逻辑回归", fontsize=11, color="#1f2937")
    ax.text(0.03, 0.10, "输入约束：不读取参考答案、隐藏金标、构造类别、注入位置或最终测试标签。", fontsize=10, color=RED)
    return save(fig, out, "图2_有效证据重评分架构.png")


def result_bars(out, overall):
    names = ["生成模型自评", "原 MiniCheck", "有效证据\nMiniCheck", "仅原分数\n逻辑回归", "完整特征\n融合", "去词汇\n特征", "去来源\n特征", "去时间\n特征"]
    vals = overall["AUC均值"].tolist()
    colors = [GREY, BLUE, ORANGE, "#7aa6c2", TEAL, "#5b9f72", "#8a9db0", RED]
    fig, ax = plt.subplots(figsize=(11, 6.2))
    bars=ax.bar(range(len(vals)), vals, color=colors, width=.68)
    ax.set_ylim(0, 1.05); ax.set_ylabel("ROC-AUC"); ax.set_xticks(range(len(vals)), names)
    ax.set_title("图3  正式冻结测试的总体方法比较", loc="left", fontsize=16, weight="bold", pad=14)
    ax.axhline(0.5, color="#9ca3af", lw=1, ls="--")
    for b,v in zip(bars, vals): ax.text(b.get_x()+b.get_width()/2, v+0.025, f"{v:.3f}", ha="center", fontsize=10)
    ax.text(0.01, -0.18, "共同评估：95 条事实回答，14 个幻觉正类；25 条拒答保留为 undetermined。有效证据 MiniCheck 相对自评提升 0.2862。",
            transform=ax.transAxes, fontsize=9, color=GREY)
    return save(fig, out, "图3_正式冻结测试方法比较.png")


def ablation(out, overall):
    keep = overall[overall["方法"].isin(["有效证据MiniCheck", "完整融合", "去词汇特征", "去来源特征", "去时间特征"])].copy()
    order=["有效证据MiniCheck","完整融合","去词汇特征","去来源特征","去时间特征"]
    keep["方法"] = pd.Categorical(keep["方法"], order, ordered=True); keep=keep.sort_values("方法")
    fig, ax=plt.subplots(figsize=(9,5.8))
    vals=keep["AUC均值"].tolist(); labels=["有效证据\n重评分","完整融合","去词汇","去来源","去时间"]
    colors=[ORANGE,TEAL,"#5b9f72","#8a9db0",RED]
    bars=ax.bar(labels, vals, color=colors, width=.62)
    ax.set_ylim(.65, .96); ax.set_ylabel("ROC-AUC"); ax.set_title("图4  轻量融合与特征消融结果", loc="left", fontsize=16, weight="bold", pad=14)
    for b,v in zip(bars, vals): ax.text(b.get_x()+b.get_width()/2, v+.008, f"{v:.3f}", ha="center", fontsize=10)
    ax.text(0.01,-.17,"去词汇特征高于完整融合，提示词面覆盖可能引入干扰；去时间特征下降，说明已识别时间规则具有增量信号。",
            transform=ax.transAxes, fontsize=9, color=GREY)
    return save(fig,out,"图4_特征消融结果.png")


def grouped(out, group):
    methods=["self_check","minicheck","valid_evidence_minicheck"]
    labels={"self_check":"生成模型自评","minicheck":"原 MiniCheck","valid_evidence_minicheck":"有效证据 MiniCheck"}
    groups=["normal","evidence_conflict","outdated_answer","retrieval_failure"]
    display=["正常","证据冲突","答案过时","检索失败"]
    fig, ax=plt.subplots(figsize=(10,6))
    width=.24; x=range(len(groups))
    for i,m in enumerate(methods):
        vals=[]
        for g in groups:
            row=group[(group["分组维度"]=="condition")&(group["分组"]==g)&(group["方法"]==m)]
            vals.append(float(row["ROC-AUC"].mean()) if not row.empty else float("nan"))
        ax.bar([v+(i-1)*width for v in x], vals, width, label=labels[m], color=[GREY,BLUE,ORANGE][i])
    ax.set_xticks(list(x),display); ax.set_ylim(0,1.05); ax.set_ylabel("ROC-AUC"); ax.legend(frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(.5,1.12))
    ax.set_title("图5  三类挑战与正常条件的分组结果", loc="left", fontsize=16, weight="bold", pad=14)
    ax.text(0.01,-.17,"检索失败组共同事实仅 3 条且全部为幻觉，AUC 不可计算；图中该组保留为空，避免用单一类别伪造指标。",
            transform=ax.transAxes, fontsize=9, color=RED)
    return save(fig,out,"图5_分组结果.png")


def audit(out, audit_path):
    audit_df=pd.read_csv(audit_path, encoding="utf-8-sig")
    fig, ax=plt.subplots(figsize=(8.5,5.5))
    labels=["正确", "不正确"]; vals=[(audit_df["answer_correctness"]=="correct").sum(),(audit_df["answer_correctness"]=="incorrect").sum()]
    bars=ax.bar(labels, vals, color=[TEAL,RED], width=.55)
    ax.set_ylim(0,100); ax.set_ylabel("样本数"); ax.set_title("图6  100 条分层人工质量审计", loc="left", fontsize=16, weight="bold", pad=14)
    for b,v in zip(bars,vals): ax.text(b.get_x()+b.get_width()/2,v+2,str(v),ha="center",fontsize=12)
    ax.text(0.01,-.17,"3 名标注者；6 条分歧均已仲裁。该审计不是每条均由两名标注者独立复核，不替代独立双人金标。", transform=ax.transAxes, fontsize=9, color=GREY)
    return save(fig,out,"图6_人工质量审计.png")


def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--output-dir",type=Path,required=True); args=parser.parse_args()
    out=args.output_dir; out.mkdir(parents=True,exist_ok=True)
    root=Path(__file__).resolve().parents[1]
    overall=pd.read_csv(root/"results/rag_formal_final_20261105/总体方法比较.csv",encoding="utf-8-sig")
    group=pd.read_csv(root/"results/rag_formal_final_20261105/方法与分组比较.csv",encoding="utf-8-sig")
    audit_path=root/"outputs/rag_formal_20261105_v2/partitions/test/human_audit_100/human_audit_100.csv"
    paths=[route(out),architecture(out),result_bars(out,overall),ablation(out,overall),grouped(out,group),audit(out,audit_path)]
    print("\n".join(str(p) for p in paths))


if __name__ == "__main__": main()
