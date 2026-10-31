# -*- coding: utf-8 -*-
"""Figure 4: three-dimensional kernel density surfaces of DFA and RCD over
2013-2021, following the perspective-surface layout of the reference paper.
"""
from __future__ import annotations

import shutil
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import cm
from scipy.stats import gaussian_kde

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FIG = ROOT / "output" / "figures"

plt.rcParams.update({
    "font.family": "Times New Roman",
    "font.size": 8,
    "axes.labelsize": 8.5,
    "xtick.labelsize": 7.5,
    "ytick.labelsize": 7.5,
    "axes.linewidth": 0.7,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "mathtext.fontset": "stix",
})

YEARS = list(range(2013, 2022))
GRID = np.linspace(0, 1.0, 120)


def surface(ax, df, var, tag, label):
    years = sorted(df["year"].unique())
    Z = np.zeros((len(years), len(GRID)))
    for i, y in enumerate(years):
        x = df.loc[df["year"] == y, var].values
        Z[i] = gaussian_kde(x, bw_method=0.35)(GRID)
    X, Y = np.meshgrid(GRID, years)
    ax.plot_surface(X, Y, Z, cmap=cm.viridis, rstride=1, cstride=3,
                    linewidth=0.18, edgecolor="#2F2F2F", antialiased=True,
                    alpha=0.97, shade=False)
    ax.set_xlabel(label, labelpad=3)
    ax.set_ylabel("Year", labelpad=5)
    ax.set_zlabel("")
    ax.set_xlim(0, 1.0)
    ax.set_ylim(years[0], years[-1])
    ax.view_init(elev=24, azim=-113)
    ax.tick_params(axis="both", which="major", pad=0)
    ax.set_box_aspect((1.3, 1.0, 0.70))
    ax.text2D(0.5, 1.0, tag, transform=ax.transAxes, fontsize=11,
              fontweight="bold", ha="center", va="bottom")
    for pane in (ax.xaxis.pane, ax.yaxis.pane, ax.zaxis.pane):
        pane.set_edgecolor("#BBBBBB")
        pane.set_alpha(0.0)
    ax.grid(True, linewidth=0.35, color="#DDDDDD")


def main() -> None:
    df = pd.read_csv(DATA / "analysis_panel.csv")
    fig = plt.figure(figsize=(9.8, 4.1))
    ax1 = fig.add_subplot(1, 2, 1, projection="3d")
    ax2 = fig.add_subplot(1, 2, 2, projection="3d")
    surface(ax1, df, "dfa", "(a)", "DFA")
    surface(ax2, df, "rcd", "(b)", "RCD")
    fig.subplots_adjust(left=0.02, right=0.98, top=0.90, bottom=0.01,
                        wspace=0.0)
    out = FIG / "fig_kde3d"
    for ext in (".png", ".pdf"):
        fig.savefig(out.with_suffix(ext), bbox_inches="tight", facecolor="white")
        shutil.copy2(out.with_suffix(ext),
                     ROOT / "paper" / "figures" / f"fig_kde3d{ext}")
    plt.close(fig)
    print("3d kde saved")


if __name__ == "__main__":
    main()
