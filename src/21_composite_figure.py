# -*- coding: utf-8 -*-
"""Figure 3: four panels combining the 2013/2021 bubble chart with the
regional time paths (former Figures 3 and 4).

(a) DFA vs RCD, 2013   (b) DFA vs RCD, 2021
(c) regional DFA means (d) regional RCD means
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

plt.rcParams.update({
    "font.family": "Times New Roman",
    "font.size": 9,
    "axes.labelsize": 10,
    "axes.labelweight": "bold",
    "xtick.labelsize": 8.5,
    "ytick.labelsize": 8.5,
    "legend.fontsize": 7.6,
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
REGIONS = ["East", "Central", "West", "Northeast"]
RCOLOR = {"East": "#1F618D", "Central": "#117A65", "West": "#A93226",
          "Northeast": "#B7950B"}
LABELS = {"Beijing": (-7, 9, "right"), "Shanghai": (-9, -8, "right"),
          "Guangdong": (8, -9, "left"), "Zhejiang": (8, 3, "left"),
          "Gansu": (8, -10, "left")}
S_MIN, S_MAX = 12.0, 330.0


def main() -> None:
    df = pd.read_csv(DATA / "analysis_panel.csv")
    df["pgdp"] = np.exp(df["ln_pgdp"])
    df["name"] = df["province"].map(EN)
    pmin, pmax = df["pgdp"].min(), df["pgdp"].max()
    size = lambda v: S_MIN + (v - pmin) / (pmax - pmin) * (S_MAX - S_MIN)

    fig, axes = plt.subplots(2, 2, figsize=(9.4, 6.9))

    # ---- (a),(b) bubble
    for ax, year, tag in zip(axes[0], [2013, 2021], "ab"):
        sub = df[df["year"] == year]
        for reg in REGIONS:
            g = sub[sub["region"] == reg]
            ax.scatter(g["dfa"], g["rcd"], s=size(g["pgdp"]),
                       color=RCOLOR[reg], alpha=0.72, edgecolors="white",
                       linewidths=0.6, label=reg, zorder=3)
        for _, r in sub.iterrows():
            if r["name"] in LABELS:
                dx, dy, ha = LABELS[r["name"]]
                ax.annotate(r["name"], (r["dfa"], r["rcd"]),
                            textcoords="offset points", xytext=(dx, dy),
                            fontsize=6.6, ha=ha, va="center", color="#333333")
        ax.set_xlim(-0.04, 1.06)
        ax.set_ylim(0.03, 0.90)
        ax.grid(True, linestyle="--", linewidth=0.4, color="#D5D5D5", zorder=0)
        ax.text(0.02, 0.97, f"({tag}) {year}", transform=ax.transAxes,
                fontsize=10, fontweight="bold", va="top")
        ax.set_xlabel("DFA")
        ax.set_ylabel("RCD")

    # ---- (c),(d) regional means
    for ax, var, tag, lab in [(axes[1][0], "dfa", "c", "DFA (regional mean)"),
                              (axes[1][1], "rcd", "d", "RCD (regional mean)")]:
        for reg in REGIONS:
            g = df[df["region"] == reg].groupby("year")[var].mean()
            ax.plot(g.index, g.values, marker="o", ms=2.6, lw=1.2,
                    color=RCOLOR[reg], label=reg)
        ax.set_xlabel("Year")
        ax.set_ylabel(lab)
        ax.grid(True, linestyle="--", linewidth=0.4, color="#D5D5D5", zorder=0)
        ax.text(0.02, 0.96, f"({tag})", transform=ax.transAxes, fontsize=10,
                fontweight="bold", va="top")

    from matplotlib.lines import Line2D
    handles = [Line2D([], [], color=RCOLOR[r], lw=1.6, marker="o", ms=3.2)
               for r in REGIONS]
    labels = REGIONS
    leg = fig.legend(handles, labels, loc="lower center", ncol=4, frameon=False,
                     title="Region", title_fontsize=8, fontsize=7.6,
                     bbox_to_anchor=(0.5, -0.005), columnspacing=1.4,
                     handletextpad=0.5)
    leg._legend_box.align = "left"

    ref = [30000, 60000, 120000]
    h2 = [plt.scatter([], [], s=size(v), color="#7F7F7F", alpha=0.6,
                      edgecolors="white", linewidths=0.6) for v in ref]
    leg2 = axes[0][1].legend(h2, [f"{v // 1000:,}k" for v in ref],
                             frameon=False, loc="lower right",
                             bbox_to_anchor=(0.99, 0.02),
                             title="GDP per capita (CNY)", title_fontsize=7,
                             labelspacing=0.85, handletextpad=0.9,
                             borderpad=0.5, fontsize=7)
    leg2._legend_box.align = "left"
    axes[0][1].add_artist(leg2)

    fig.tight_layout(rect=(0, 0.045, 1, 1))
    fig.subplots_adjust(hspace=0.27, wspace=0.22)
    out = FIG / "fig_distribution_trends"
    for ext in (".png", ".pdf"):
        fig.savefig(out.with_suffix(ext), bbox_inches="tight", facecolor="white")
        shutil.copy2(out.with_suffix(ext),
                     ROOT / "paper" / "figures" / f"fig_distribution_trends{ext}")
    plt.close(fig)
    print("composite figure saved")


if __name__ == "__main__":
    main()
