# -*- coding: utf-8 -*-
"""Kernel-density evolution of DFA and RCD, in the style of the reference
paper's Figure 6 (distributional shift over the sample period).
"""
from __future__ import annotations

import shutil
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FIG = ROOT / "output" / "figures"

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

YEARS = [2013, 2016, 2019, 2021]
BLUES = ["#BDD7EE", "#6BAED6", "#2171B5", "#08306B"]
GREENS = ["#C7E9C0", "#74C476", "#238B45", "#00441B"]


def kde_panel(ax, df, var, colors, tag):
    for year, color in zip(YEARS, colors):
        x = df.loc[df["year"] == year, var].values
        kde = gaussian_kde(x, bw_method=0.35)
        grid = np.linspace(0, 1.02, 400)
        y = kde(grid)
        ax.plot(grid, y, color=color, lw=1.5, label=str(year))
        ax.fill_between(grid, y, color=color, alpha=0.10)
        ax.axvline(x.mean(), color=color, lw=0.8, ls=":", ymax=0.35)
    ax.set_xlim(0, 1.02)
    ax.set_xlabel("Index value")
    ax.set_ylabel("Density")
    ax.text(0.02, 0.96, tag, transform=ax.transAxes, fontsize=10.5,
            fontweight="bold", va="top")
    ax.grid(True, linestyle="--", linewidth=0.4, color="#D5D5D5")
    ax.set_axisbelow(True)


def main() -> None:
    df = pd.read_csv(DATA / "analysis_panel.csv")
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.5))
    kde_panel(axes[0], df, "dfa", BLUES, "(a) DFA")
    kde_panel(axes[1], df, "rcd", GREENS, "(b) RCD")
    axes[0].legend(title="Year", frameon=False, loc="upper right",
                   title_fontsize=8, labelspacing=0.3)
    fig.tight_layout()
    out = FIG / "fig_kde"
    for ext in (".png", ".pdf"):
        fig.savefig(out.with_suffix(ext), bbox_inches="tight", facecolor="white")
        shutil.copy2(out.with_suffix(ext),
                     ROOT / "paper" / "figures" / f"fig_kde{ext}")
    plt.close(fig)
    print("kde figure saved")


if __name__ == "__main__":
    main()
