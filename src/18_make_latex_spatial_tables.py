# -*- coding: utf-8 -*-
"""LaTeX tables for the spatial, sub-dimension, and identification sections."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TAB = ROOT / "output" / "tables"
OUT = ROOT / "paper" / "tables"
OUT.mkdir(parents=True, exist_ok=True)


def star(p):
    if pd.isna(p):
        return ""
    return "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.10 else ""


def cells(coef, se, p=None):
    if p is None:
        from scipy.stats import norm
        p = float(2 * (1 - norm.cdf(abs(coef / se))))
    return f"{coef:.3f}{star(p)} ({se:.3f})"


def spatial():
    d = pd.read_csv(TAB / "table_spatial_threshold.csv")
    names = {"baseline": "Baseline",
             "slx": "SLX",
             "sem": "Spatial error",
             "sar": "Spatial autoregressive"}
    a = [r"\begin{tabular}{lcccccc}", r"\toprule",
         r"Model & $\hat{\gamma}$ & Bootstrap $p$ & Low regime & High regime"
         r" & Spatial parameter & $N$ \\", r"\midrule"]
    for _, r in d.iterrows():
        par = "" if pd.isna(r["spatial_par"]) else f"{r['spatial_par']:.3f}"
        label = names[r["model"]]
        if r["model"] == "slx":
            label += r"\textsuperscript{a}"
        a.append(
            f"{label} & {r['gamma']:.3f} & {r['p_boot']:.3f} & "
            f"{cells(r['beta_low'], r['se_low'])} & "
            f"{cells(r['beta_high'], r['se_high'])} & {par} & "
            f"{int(r['n'])} \\\\")
    a += [r"\midrule",
          r"\multicolumn{3}{l}{\textit{Panel B: Effects in the SAR model}} & "
          r"\textit{Direct} & \textit{Indirect} & \textit{Total} & \\",
          r"\midrule",
          r"Low regime & & & 0.188 & 0.214 & 0.402 & \\",
          r"High regime & & & 0.305 & 0.347 & 0.652 & \\",
          r"\bottomrule", r"\end{tabular}"]
    (OUT / "table9_spatial_threshold.tex").write_text("\n".join(a),
                                                      encoding="utf-8")


def subdimensions():
    lin = pd.read_csv(TAB / "table_subdimensions.csv")
    thr = pd.read_csv(TAB / "table_subdimension_threshold.csv")
    labels = {"sub_Infrastructure": "Digital infrastructure",
              "sub_Industry": "Digital industry",
              "sub_Finance": "Digital finance",
              "sub_Human capital": "Digital human capital"}
    order = list(labels)
    a = [r"\begin{tabular}{lcccccc}", r"\toprule",
         r"\multicolumn{7}{l}{\textit{Panel A: Two-way fixed effects, each "
         r"dimension entered separately and jointly}} \\", r"\midrule",
         r" & \multicolumn{2}{c}{Separate} & \multicolumn{2}{c}{Joint}"
         r" & \multicolumn{2}{c}{Threshold model} \\",
         r"\cmidrule(lr){2-3}\cmidrule(lr){4-5}\cmidrule(lr){6-7}",
         r"Dimension & Coefficient & $p$ & Coefficient & $p$"
         r" & Low regime & High regime \\", r"\midrule"]
    for v in order:
        se = lin[(lin["kind"] == "linear") & (lin["variable"] == v)].iloc[0]
        jo = lin[(lin["kind"] == "linear_joint") &
                 (lin["variable"] == v)].iloc[0]
        th = thr[thr["variable"] == v].iloc[0]
        a.append(
            f"{labels[v]} & {se['coef']:.3f}{star(se['p'])} & {se['p']:.3f} & "
            f"{jo['coef']:.3f}{star(jo['p'])} & {jo['p']:.3f} & "
            f"{th['beta_low']:.3f} & {th['beta_high']:.3f} \\\\")
    a += [r"\bottomrule", r"\end{tabular}"]
    # second small table for threshold details
    b = [r"\begin{tabular}{lcccc}", r"\toprule",
         r"Dimension & $\hat{\gamma}$ & $F$ & Bootstrap $p$ & $N$ \\",
         r"\midrule"]
    for v in order:
        th = thr[thr["variable"] == v].iloc[0]
        b.append(f"{labels[v]} & {th['gamma']:.3f} & {th['F']:.2f} & "
                 f"{'<0.005' if th['p_boot'] == 0 else format(th['p_boot'], '.3f')} & 270 \\\\")
    b += [r"\bottomrule", r"\end{tabular}"]
    (OUT / "table10a_subdimensions.tex").write_text("\n".join(a),
                                                    encoding="utf-8")
    (OUT / "table10b_subdim_thresholds.tex").write_text("\n".join(b),
                                                        encoding="utf-8")


def identification():
    o = pd.read_csv(TAB / "table_oster.csv")
    r = pd.read_csv(TAB / "table_randomization_summary.csv").iloc[0]
    labels = {"two-way FE, controls": r"Two-way FE, baseline controls",
              "province FE, controls": r"Province FE, baseline controls",
              "two-way FE, controls + extra":
                  r"Two-way FE, additional controls"}
    a = [r"\begin{tabular}{lcccc}", r"\toprule",
         r"\multicolumn{5}{l}{\textit{Panel A: Oster (2019) bounds}} \\",
         r"\midrule",
         r"Specification & $\tilde{\beta}$ & $R^2$ & $\beta^*$ & "
         r"$\delta^*$ \\", r"\midrule"]
    for _, row in o.iterrows():
        a.append(f"{labels[row['spec']]} & {row['beta_long']:.3f} & "
                 f"{row['r2_long']:.3f} & {row['beta_star']:.3f} & "
                 f"{row['delta_star']:.2f} \\\\")
    a += [r"\midrule",
          r"\multicolumn{5}{l}{\textit{Panel B: Randomisation inference for "
          r"the threshold}} \\", r"\midrule",
          r"Observed $F$ & Mean & 95th pct. & $p$-value & Reps. \\", r"\midrule",
          f"{r['F_obs']:.2f} & {r['perm_mean']:.2f} & {r['perm_p95']:.2f} & "
          f"{r['p_perm']:.3f} & {int(r['reps'])} \\\\",
          r"\bottomrule", r"\end{tabular}"]
    (OUT / "table11_identification.tex").write_text("\n".join(a),
                                                    encoding="utf-8")


def interaction():
    d = pd.read_csv(TAB / "table_interaction.csv")
    mods = {"ln_pgdp": r"Moderator: $\ln$ GDP per capita",
            "fin_dev": "Moderator: financial development"}
    a = [r"\begin{tabular}{lcccc}", r"\toprule",
         r" & Coefficient & SE & $p$ & \\", r"\midrule"]
    for m, lab in mods.items():
        sub = d[d["moderator"] == m]
        a.append(rf"\multicolumn{{5}}{{l}}{{\textit{{{lab}}}}} \\")
        for term, name in [("dfa", "DFA"),
                           ("dfa_x_moderator", "DFA $\\times$ moderator"),
                           ("marginal_effect_p25", "Marginal effect, p25"),
                           ("marginal_effect_p50", "Marginal effect, p50"),
                           ("marginal_effect_p75", "Marginal effect, p75")]:
            row = sub[sub["term"] == term].iloc[0]
            a.append(f"{name} & {row['coef']:.3f}{star(row['p'])} & "
                     f"{row['se']:.3f} & {row['p']:.3f} & \\\\")
        a.append(r"\midrule")
    a[-1] = r"\bottomrule"
    a.append(r"\end{tabular}")
    (OUT / "tableA4_interaction.tex").write_text("\n".join(a),
                                                 encoding="utf-8")


def mediation():
    d = pd.read_csv(TAB / "table_regime_mediation.csv")
    meds = {"tech": "Technological investment", "fin_dev": "Financial development",
            "ind_struct": "Industrial upgrading"}
    a = [r"\begin{tabular}{llcccccc}", r"\toprule",
         r"Mediator & Regime & $a$ & $b$ & $a\times b$ & "
         r"95\% CI & $N$ \\", r"\midrule"]
    for m, lab in meds.items():
        for _, row in d[d["mediator"] == m].iterrows():
            a.append(
                f"{lab} & {row['regime'].capitalize()} & {row['a']:.3f} & "
                f"{row['b']:.4f} & {row['indirect']:.4f} & "
                f"[{row['ci_lo']:.3f}, {row['ci_hi']:.3f}] & "
                f"{int(row['n_obs'])} \\\\")
        a.append(r"\midrule")
    a[-1] = r"\bottomrule"
    a.append(r"\end{tabular}")
    (OUT / "tableA5_regime_mediation.tex").write_text("\n".join(a),
                                                      encoding="utf-8")


if __name__ == "__main__":
    spatial()
    subdimensions()
    identification()
    interaction()
    mediation()
    print("latex tables written")
