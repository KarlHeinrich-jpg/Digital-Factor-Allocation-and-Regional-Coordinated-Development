# -*- coding: utf-8 -*-
"""Paper figures (except the China maps, produced with the yile-paper-style
china_map.py script)."""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FIG = ROOT / "output" / "figures"
TAB = ROOT / "output" / "tables"
FIG.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.family": "Times New Roman",
    "font.size": 9,
    "axes.labelsize": 10,
    "axes.labelweight": "bold",
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 8.5,
    "axes.linewidth": 0.9,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "mathtext.fontset": "stix",
})


def save(fig, name):
    fig.savefig(FIG / f"{name}.png", bbox_inches="tight", facecolor="white")
    fig.savefig(FIG / f"{name}.pdf", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def framework():
    fig, ax = plt.subplots(figsize=(9.4, 5.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis("off")

    def box(x, y, w, h, text, fc="#EAF2F8", fs=8.6, bold=False):
        p = FancyBboxPatch((x, y), w, h,
                           boxstyle="round,pad=0.04,rounding_size=0.08",
                           linewidth=0.9, edgecolor="black", facecolor=fc)
        ax.add_patch(p)
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
                fontsize=fs, fontweight="bold" if bold else "normal")

    def arrow(x1, y1, x2, y2, style="-|>", ls="-", lw=1.0):
        a = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style,
                            mutation_scale=12, linewidth=lw, linestyle=ls,
                            color="black")
        ax.add_patch(a)

    ax.text(1.95, 5.55, "Digital factor allocation (DFA)", ha="center",
            fontsize=10.2, fontweight="bold")
    ax.text(8.4, 5.55, "Regional coordinated development (RCD)", ha="center",
            fontsize=10.2, fontweight="bold")

    for y, t in [(4.35, "Digital infrastructure"), (3.55, "Digital industry"),
                 (2.75, "Digital finance"), (1.95, "Digital human capital")]:
        box(0.25, y, 3.4, 0.58, t)
    for y, t in [(4.35, "Economic coordination"), (3.55, "Social coordination"),
                 (2.75, "Urban-rural coordination")]:
        box(7.0, y, 2.8, 0.58, t, fc="#E8F5E9")

    # main H1 arrow
    arrow(3.72, 3.25, 6.95, 3.25, lw=1.3)
    ax.text(3.95, 3.38, "H1 (+)", ha="left", va="bottom", fontsize=8.8,
            style="italic")

    # moderator
    box(3.80, 4.50, 2.40, 0.62, "Threshold:\neconomic development",
        fc="#FFF8E1", fs=7.3, bold=True)
    arrow(4.95, 4.47, 4.95, 3.32, style="-|>", ls=(0, (3, 2)), lw=1.0)
    ax.text(5.05, 3.92, "H2: weaker below\nstronger above", ha="left",
            va="center", fontsize=7.5)

    # mechanisms
    box(2.90, 0.75, 4.90, 0.72,
        "Mechanisms: industrial upgrading · financial deepening\n"
        "· technological investment", fc="#F3E5F5", fs=7.8)
    arrow(6.10, 1.48, 6.10, 3.20, style="-|>", lw=1.0)

    ax.text(5.0, 0.25, "Notes: The framework summarizes the testable hypotheses. "
            "The threshold model allows the DFA slope to differ across "
            "economic-development regimes.", ha="center", fontsize=7.2,
            style="italic")
    save(fig, "fig1_framework")


def scatter_threshold():
    df = pd.read_csv(DATA / "analysis_panel.csv")
    th = 10.5893
    df["regime"] = np.where(df["ln_pgdp"] <= th, "Below threshold",
                            "Above threshold")
    fig, axes = plt.subplots(1, 2, figsize=(9.0, 3.7))
    colors = {"Below threshold": "#2E86C1", "Above threshold": "#C0392B"}
    ax = axes[0]
    for g, sub in df.groupby("regime"):
        ax.scatter(sub["dfa"], sub["rcd"], s=12, alpha=0.55,
                   color=colors[g], label=g, edgecolors="none")
    for g, sub in df.groupby("regime"):
        z = np.polyfit(sub["dfa"], sub["rcd"], 1)
        xx = np.linspace(sub["dfa"].min(), sub["dfa"].max(), 50)
        ax.plot(xx, np.polyval(z, xx), color=colors[g], lw=1.4)
    ax.set_xlabel("Digital factor allocation (DFA)")
    ax.set_ylabel("Regional coordinated development (RCD)")
    ax.legend(frameon=False, loc="upper left")
    ax.text(0.02, 0.95, "(a)", transform=ax.transAxes, fontsize=11,
            fontweight="bold", va="top")
    ax.grid(True, linestyle="--", linewidth=0.4, color="#D5D5D5")

    ax = axes[1]
    tab = pd.read_csv(TAB / "table4_threshold.csv")
    row = tab[tab["q"] == "ln_pgdp"].iloc[0]
    vals = [row["beta_low"], row["beta_high"]]
    errs = [1.96 * row["se_low"], 1.96 * row["se_high"]]
    ax.errorbar([0, 1], vals, yerr=errs, fmt="o", color="black",
                capsize=5, markersize=6, lw=1.2)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Below threshold\n($\\ln pgdp \\leq 10.589$)",
                        "Above threshold\n($\\ln pgdp > 10.589$)"])
    ax.axhline(0, color="#999999", lw=0.7, ls=":")
    ax.set_ylabel("Estimated coefficient of DFA")
    ax.text(0.02, 0.95, "(b)", transform=ax.transAxes, fontsize=11,
            fontweight="bold", va="top")
    ax.grid(True, axis="y", linestyle="--", linewidth=0.4, color="#D5D5D5")
    fig.tight_layout()
    save(fig, "fig3_scatter_regimes")


def lr_curve():
    df = pd.read_csv(DATA / "analysis_panel.csv").sort_values(
        ["province", "year"]).reset_index(drop=True)
    controls = ["gov", "ln_fdi", "ln_dens", "private"]
    q = "ln_pgdp"
    ids = df["province"]
    y = df["rcd"] - df.groupby("province")["rcd"].transform("mean")
    C = np.column_stack([
        (df[c] - df.groupby("province")[c].transform("mean")).values
        for c in controls])
    x = (df["dfa"] - df.groupby("province")["dfa"].transform("mean")).values
    grid = np.quantile(df[q], np.linspace(0.10, 0.90, 100))
    ss = []
    for g in grid:
        i = (df[q].values <= g).astype(float)
        x1 = df["dfa"] * i
        x1 = (x1 - x1.groupby(df["province"]).transform("mean")).values
        x2 = df["dfa"] * (1 - i)
        x2 = (x2 - x2.groupby(df["province"]).transform("mean")).values
        X = np.column_stack([x1, x2, C])
        b = np.linalg.lstsq(X, y, rcond=None)[0]
        e = y - X @ b
        ss.append(float(e @ e))
    ss = np.array(ss)
    gamma = grid[np.argmin(ss)]
    sigma2 = ss.min() / (len(df) - 7)
    lr = (ss - ss.min()) / sigma2

    fig, ax = plt.subplots(figsize=(5.2, 3.6))
    ax.plot(grid, lr, color="#1F618D", lw=1.5)
    ax.axhline(7.35, color="#C0392B", ls="--", lw=1.0, label="95% critical value")
    ax.axvline(gamma, color="black", ls=":", lw=1.0)
    ax.set_xlabel("Threshold candidate for ln(per capita GDP)")
    ax.set_ylabel("Likelihood-ratio statistic")
    ax.set_ylim(0, max(20, np.percentile(lr, 99) * 1.1))
    ax.legend(frameon=False, loc="upper right")
    ax.grid(True, linestyle="--", linewidth=0.4, color="#D5D5D5")
    ax.text(0.02, 0.95, f"$\\hat{{\\gamma}}$ = {gamma:.3f}",
            transform=ax.transAxes, fontsize=9)
    fig.tight_layout()
    save(fig, "fig4_lr_curve")
    pd.DataFrame({"grid": grid, "lr": lr}).to_csv(
        TAB / "lr_curve.csv", index=False, encoding="utf-8-sig")


def coefficient_forest():
    het = pd.read_csv(TAB / "table5_heterogeneity.csv")
    rob = pd.read_csv(TAB / "table6_robustness.csv")
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 4.2))
    ax = axes[0]
    sub = het[het["fe"] == "two-way"].reset_index(drop=True)
    ypos = np.arange(len(sub))[::-1]
    ax.errorbar(sub["coef"], ypos, xerr=1.96 * sub["se"], fmt="o",
                color="#1F618D", capsize=4, markersize=5)
    ax.axvline(0, color="#999999", lw=0.7, ls=":")
    ax.set_yticks(ypos)
    ax.set_yticklabels(sub["region"])
    ax.set_xlabel("DFA coefficient (two-way FE)")
    ax.set_title("(a) Regional heterogeneity", loc="left", fontsize=9.5,
                 fontweight="bold")
    ax.grid(True, axis="x", linestyle="--", linewidth=0.4, color="#D5D5D5")

    ax = axes[1]
    keep = ["Baseline", "Five-dimension RCD", "Entropy-weighted RCD",
            "Equal-weight DFA", "Excluding municipalities", "2013-2019",
            "Winsorized 1/99"]
    sub = rob[rob["spec"].isin(keep)].copy()
    order = {k: i for i, k in enumerate(keep)}
    sub["ord"] = sub["spec"].map(order)
    sub = sub.sort_values("ord")
    ypos = np.arange(len(sub))[::-1]
    ax.errorbar(sub["coef"], ypos, xerr=1.96 * sub["se"], fmt="o",
                color="#117A65", capsize=4, markersize=5)
    ax.axvline(0, color="#999999", lw=0.7, ls=":")
    ax.set_yticks(ypos)
    ax.set_yticklabels(sub["spec"], fontsize=8)
    ax.set_xlabel("DFA coefficient")
    ax.set_title("(b) Alternative specifications", loc="left", fontsize=9.5,
                 fontweight="bold")
    ax.grid(True, axis="x", linestyle="--", linewidth=0.4, color="#D5D5D5")
    fig.tight_layout()
    save(fig, "fig5_coefficients")


def trends():
    df = pd.read_csv(DATA / "analysis_panel.csv")
    fig, axes = plt.subplots(1, 2, figsize=(9.0, 3.4))
    for reg, sub in df.groupby("region"):
        g = sub.groupby("year")[["dfa", "rcd"]].mean()
        axes[0].plot(g.index, g["dfa"], marker="o", ms=3, lw=1.2, label=reg)
        axes[1].plot(g.index, g["rcd"], marker="o", ms=3, lw=1.2, label=reg)
    axes[0].set_ylabel("DFA (regional mean)")
    axes[1].set_ylabel("RCD (regional mean)")
    for ax, lab in zip(axes, ["(a) DFA", "(b) RCD"]):
        ax.set_xlabel("Year")
        ax.grid(True, linestyle="--", linewidth=0.4, color="#D5D5D5")
        ax.text(0.02, 0.95, lab, transform=ax.transAxes, fontsize=9.5,
                fontweight="bold", va="top")
    axes[0].legend(frameon=False, fontsize=7.5, ncol=2)
    fig.tight_layout()
    save(fig, "fig6_trends")


if __name__ == "__main__":
    framework()
    scatter_threshold()
    lr_curve()
    coefficient_forest()
    trends()
    print("figures saved")
