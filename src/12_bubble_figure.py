# -*- coding: utf-8 -*-
"""Figure 3: province-level DFA and RCD in 2013 and 2021, with bubble size
proportional to GDP per capita (the economic-development threshold variable).
"""
from __future__ import annotations

import shutil
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FIG = ROOT / "output" / "figures"
FIG.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.family": "Times New Roman",
    "font.size": 9,
    "axes.labelsize": 10,
    "axes.labelweight": "bold",
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 8,
    "axes.linewidth": 0.9,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "mathtext.fontset": "stix",
})

EN = {
    "北京": "Beijing", "天津": "Tianjin", "河北": "Hebei", "山西": "Shanxi",
    "内蒙古": "Inner Mongolia", "辽宁": "Liaoning", "吉林": "Jilin",
    "黑龙江": "Heilongjiang", "上海": "Shanghai", "江苏": "Jiangsu",
    "浙江": "Zhejiang", "安徽": "Anhui", "福建": "Fujian", "江西": "Jiangxi",
    "山东": "Shandong", "河南": "Henan", "湖北": "Hubei", "湖南": "Hunan",
    "广东": "Guangdong", "广西": "Guangxi", "海南": "Hainan",
    "重庆": "Chongqing", "四川": "Sichuan", "贵州": "Guizhou", "云南": "Yunnan",
    "陕西": "Shaanxi", "甘肃": "Gansu", "青海": "Qinghai",
    "宁夏": "Ningxia", "新疆": "Xinjiang",
}

REGION_ORDER = ["East", "Central", "West", "Northeast"]
REGION_COLOR = {
    "East": "#1F618D",
    "Central": "#117A65",
    "West": "#A93226",
    "Northeast": "#B7950B",
}

# Label anchors, offset in points, applied identically in both panels.
LABELS = {
    "Beijing": (-7, 9, "right"),
    "Shanghai": (-9, -8, "right"),
    "Guangdong": (8, -9, "left"),
    "Zhejiang": (8, 3, "left"),
    "Gansu": (8, -10, "left"),
}

S_MIN, S_MAX = 14.0, 430.0


def bubble_size(pgdp, pmin, pmax):
    z = (pgdp - pmin) / (pmax - pmin)
    return S_MIN + z * (S_MAX - S_MIN)


def save(fig, name):
    fig.savefig(FIG / f"{name}.png", bbox_inches="tight", facecolor="white")
    fig.savefig(FIG / f"{name}.pdf", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    for ext in (".png", ".pdf"):
        shutil.copy2(FIG / f"{name}{ext}",
                     ROOT / "paper" / "figures" / f"{name}{ext}")


def bubble_chart():
    df = pd.read_csv(DATA / "analysis_panel.csv")
    df["pgdp"] = np.exp(df["ln_pgdp"])
    df["name"] = df["province"].map(EN)
    assert df["name"].notna().all(), df.loc[df["name"].isna(), "province"].unique()

    # A common size scale across both panels keeps the within-panel ordering
    # comparable and makes the rise in income levels visible.
    pmin, pmax = df["pgdp"].min(), df["pgdp"].max()

    fig, axes = plt.subplots(1, 2, figsize=(9.4, 4.1), sharex=True, sharey=True)

    for ax, year in zip(axes, [2013, 2021]):
        sub = df[df["year"] == year]
        for reg in REGION_ORDER:
            g = sub[sub["region"] == reg]
            ax.scatter(g["dfa"], g["rcd"],
                       s=bubble_size(g["pgdp"], pmin, pmax),
                       color=REGION_COLOR[reg], alpha=0.72,
                       edgecolors="white", linewidths=0.6,
                       label=reg, zorder=3)
        for _, row in sub.iterrows():
            if row["name"] in LABELS:
                dx, dy, ha = LABELS[row["name"]]
                ax.annotate(row["name"], (row["dfa"], row["rcd"]),
                            textcoords="offset points", xytext=(dx, dy),
                            fontsize=7.2, ha=ha, va="center",
                            color="#333333", zorder=4)
        ax.axhline(0, color="#999999", lw=0.5, ls=":")
        ax.grid(True, linestyle="--", linewidth=0.4, color="#D5D5D5", zorder=0)
        ax.text(0.02, 0.97, f"({'ab'[[2013, 2021].index(year)]}) {year}",
                transform=ax.transAxes, fontsize=10.5, fontweight="bold",
                va="top")

    axes[0].set_xlim(-0.04, 1.06)
    axes[0].set_ylim(0.03, 0.90)
    for ax in axes:
        ax.set_xlabel("Digital factor allocation (DFA)")

    fig.supylabel("Regional coordinated development (RCD)",
                  fontsize=10, fontweight="bold", x=0.015)

    handles, labels = axes[0].get_legend_handles_labels()
    leg1 = axes[0].legend(handles, labels, frameon=False, loc="upper left",
                          bbox_to_anchor=(0.03, 0.93), title="Region",
                          title_fontsize=8,
                          handletextpad=0.5, labelspacing=0.35)
    leg1._legend_box.align = "left"

    ref_pgdp = [30000, 60000, 120000]
    ref_handles = [plt.scatter([], [], s=bubble_size(v, pmin, pmax),
                               color="#7F7F7F", alpha=0.6, edgecolors="white",
                               linewidths=0.6)
                   for v in ref_pgdp]
    leg2 = axes[1].legend(ref_handles,
                          [f"{v // 1000:,}k" for v in ref_pgdp],
                          frameon=False, loc="lower right",
                          bbox_to_anchor=(0.99, 0.02),
                          title="GDP per capita (CNY)",
                          title_fontsize=8, labelspacing=0.9,
                          handletextpad=0.9, borderpad=0.6)
    leg2._legend_box.align = "left"
    axes[1].add_artist(leg2)

    fig.tight_layout(rect=(0.03, 0, 1, 1))
    save(fig, "fig_bubble")


if __name__ == "__main__":
    bubble_chart()
    print("bubble figure saved")
