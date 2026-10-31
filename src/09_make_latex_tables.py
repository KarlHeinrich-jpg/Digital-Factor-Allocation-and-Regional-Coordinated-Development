# -*- coding: utf-8 -*-
"""Convert result CSVs into booktabs LaTeX tables for the manuscript."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TAB = ROOT / "output" / "tables"
OUT = ROOT / "paper" / "tables"
OUT.mkdir(parents=True, exist_ok=True)


def star(p):
    return "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.10 else ""


def f3(x, dec=3):
    return f"{x:.{dec}f}"


def tex_escape(s):
    return s.replace("_", r"\_").replace("%", r"\%")


def table2():
    d = pd.read_csv(TAB / "table2_descriptives.csv")
    names = {
        "dfa": "DFA index", "rcd": "RCD index", "rcd5": "RCD5 index",
        "rcd_ccd": "RCD coupling coordination", "income_ratio": "Urban-rural income ratio",
        "gov": "Government intervention", "ln_fdi": "Log FDI per capita",
        "ln_dens": "Log population density", "private": "Private economy vitality",
        "fin_dev": "Financial development", "tech": "Technological investment",
        "ind_struct": "Industrial structure upgrading",
    }
    lines = [r"\begin{tabular}{lrrrrrr}", r"\toprule",
             r"Variable & N & Mean & SD & Min & Median & Max \\", r"\midrule"]
    for _, r in d.iterrows():
        lines.append(f"{names.get(r['var'], tex_escape(r['var']))} & {int(r['n'])} & "
                     f"{f3(r['mean'])} & {f3(r['sd'])} & {f3(r['min'])} & "
                     f"{f3(r['p50'])} & {f3(r['max'])} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    (OUT / "table2_descriptives.tex").write_text("\n".join(lines), encoding="utf-8")


def table3():
    d = pd.read_csv(TAB / "table3_baseline.csv")
    coef = {}
    for _, r in d.iterrows():
        if r["var"] == "N":
            continue
        key = (r["model"], r["var"])
        coef[key] = (r["coef"], r["se"], r["p"])
    models = ["(1)", "(2)", "(3)", "(4)"]
    lines = [r"\begin{tabular}{lrrrr}", r"\toprule",
             r" & (1) & (2) & (3) & (4) \\", r"\midrule",
             r"DFA & " + " & ".join(
                 f"{f3(coef[(m,'dfa')][0])}{star(coef[(m,'dfa')][2])}" for m in models) + r" \\",
             r" & " + " & ".join(f"({f3(coef[(m,'dfa')][1])})" for m in models) + r" \\[2pt]"]
    for v, label in [("gov", "Government intervention"), ("ln_fdi", "Log FDI"),
                     ("ln_dens", "Log population density"), ("private", "Private economy")]:
        lines.append(label + " & " + " & ".join(
            f"{f3(coef[(m,v)][0],5 if v=='private' else 4)}{star(coef[(m,v)][2])}" if (m, v) in coef else ""
            for m in models) + r" \\")
        lines.append(r" & " + " & ".join(
            f"({f3(coef[(m,v)][1])})" if (m, v) in coef else "" for m in models) + r" \\[2pt]")
    lines += [r"Controls & No & Yes & Yes & Yes \\",
              r"Province FE & Yes & Yes & Yes & Yes \\",
              r"Year FE & Yes & Yes & Yes & Yes \\",
              r"Region trends & No & No & Yes & No \\",
              r"Observations & 270 & 270 & 270 & 270 \\",
              r"\bottomrule", r"\end{tabular}"]
    (OUT / "table3_baseline.tex").write_text("\n".join(lines), encoding="utf-8")


def table4():
    d = pd.read_csv(TAB / "table4_threshold.csv")
    ftab = pd.read_csv(TAB / "threshold_tests.csv")
    fvals = dict(zip(ftab["threshold_var"], ftab["F"]))
    labels = {"dfa": "DFA", "ln_pgdp": "ln(per capita GDP)", "fin_dev": "Financial development",
              "tech": "Technological investment", "private": "Private economy vitality"}
    a = [r"\begin{tabular}{lcccc}", r"\toprule",
         r"Threshold variable & $\hat{\gamma}$ & 95\% CI & $F$ & Bootstrap $p$ \\", r"\midrule"]
    for _, r in d.iterrows():
        ci = "--" if r["q"] == "fin_dev" else f"[{f3(r['ci_lo'])}, {f3(r['ci_hi'])}]"
        a.append(f"{labels[r['q']]} & {f3(r['gamma'])} & {ci} & "
                 f"{f3(fvals[r['q']],2)} & {f3(r['p_boot'])} \\\\")
    a += [r"\bottomrule", r"\end{tabular}"]
    b = [r"\begin{tabular}{lccc}", r"\toprule",
         r"Threshold variable & Low regime & High regime & Observations (low/high) \\", r"\midrule"]
    for _, r in d.iterrows():
        b.append(f"{labels[r['q']]} & {f3(r['beta_low'])}{star(r['p_low'])} & "
                 f"{f3(r['beta_high'])}{star(r['p_high'])} & {int(r['n_low'])}/{int(r['n_high'])} \\\\")
        b.append(f" & ({f3(r['se_low'])}) & ({f3(r['se_high'])}) & \\\\[2pt]")
    b += [r"\bottomrule", r"\end{tabular}"]
    (OUT / "table4_threshold_a.tex").write_text("\n".join(a), encoding="utf-8")
    (OUT / "table4_threshold_b.tex").write_text("\n".join(b), encoding="utf-8")


def table5():
    d = pd.read_csv(TAB / "table5_heterogeneity.csv")
    regions = ["East", "Central", "West", "Northeast"]
    lines = [r"\begin{tabular}{lcc}", r"\toprule",
             r"Region & Two-way FE & Province FE \\", r"\midrule"]
    for reg in regions:
        row = {}
        for _, r in d[d["region"] == reg].iterrows():
            row[r["fe"]] = (r["coef"], r["se"], r["p"], int(r["n"]))
        lines.append(f"{reg} & {f3(row['two-way'][0])}{star(row['two-way'][2])} & "
                     f"{f3(row['province'][0])}{star(row['province'][2])} \\\\")
        lines.append(f" & ({f3(row['two-way'][1])}) & ({f3(row['province'][1])}) \\\\[2pt]")
    lines += [r"Controls & Yes & Yes \\", r"Observations & 90/54/99/27 & 90/54/99/27 \\",
              r"\bottomrule", r"\end{tabular}"]
    (OUT / "table5_heterogeneity.tex").write_text("\n".join(lines), encoding="utf-8")


def table6():
    d = pd.read_csv(TAB / "table6_robustness.csv")
    lines = [r"\begin{tabular}{lccc}", r"\toprule",
             r"Specification & Coefficient & SE & N \\", r"\midrule"]
    for _, r in d.iterrows():
        lines.append(f"{r['spec']} & {f3(r['coef'])}{star(r['p'])} & "
                     f"({f3(r['se'])}) & {int(r['n'])} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    (OUT / "table6_robustness.tex").write_text("\n".join(lines), encoding="utf-8")


def table7():
    d = pd.read_csv(TAB / "table7_mechanisms.csv")
    names = {"tech": "Technological investment", "fin_dev": "Financial development",
             "ind_struct": "Industrial upgrading", "income_ratio": "Urban-rural income ratio"}
    lines = [r"\begin{tabular}{lccc}", r"\toprule",
             r"Mediator & DFA $\to$ M (two-way FE) & DFA $\to$ M (province FE) & M in RCD equation \\",
             r"\midrule"]
    for m in ["tech", "fin_dev", "ind_struct", "income_ratio"]:
        sub = d[d["mediator"] == m]
        tw = sub[sub["fe"] == "two-way"].iloc[0]
        pv = sub[sub["fe"] == "province"].iloc[0]
        eq = sub[sub["fe"] == "RCD equation"]
        eqs = f"{f3(eq.iloc[0]['coef'])}{star(eq.iloc[0]['p'])}" if len(eq) else "--"
        lines.append(f"{names[m]} & {f3(tw['coef'])}{star(tw['p'])} & "
                     f"{f3(pv['coef'])}{star(pv['p'])} & {eqs} \\\\")
        lines.append(f" & ({f3(tw['se'])}) & ({f3(pv['se'])}) & \\\\[2pt]")
    lines += [r"Controls & Yes & Yes & Yes \\", r"Observations & 270 & 270 & 270 \\",
              r"\bottomrule", r"\end{tabular}"]
    (OUT / "table7_mechanisms.tex").write_text("\n".join(lines), encoding="utf-8")


def table_weights():
    d = pd.read_csv(TAB / "table_weights.csv")
    names = {
        "dfa_ports_pc": "Internet access ports per capita",
        "dfa_optical": "Optical cable density",
        "dfa_mobile": "Mobile phone penetration",
        "dfa_ipv4_pc": "IPv4 addresses per capita",
        "dfa_domain_pc": "Domain names per capita",
        "dfa_software_gdp": "Software revenue/GDP",
        "dfa_ecom_gdp": "E-commerce sales/GDP",
        "dfa_ecom_firm": "Share of firms with e-commerce",
        "dfa_website": "Websites per 100 firms",
        "dfa_info_firm_pc": "Information firms per capita",
        "dfa_dfi_coverage": "DFI coverage breadth",
        "dfa_dfi_usage": "DFI usage depth",
        "dfa_dfi_digit": "DFI digitization",
        "dfa_ict_emp": "ICT employment share",
        "dfa_internet": "Internet penetration",
        "rcd_pgdp": "GDP per capita",
        "rcd_retail_pc": "Retail sales per capita",
        "rcd_fiscal": "Fiscal self-sufficiency",
        "rcd_income": "Disposable income per capita",
        "rcd_beds": "Hospital beds per 10,000",
        "rcd_highered": "Higher-education students per 100,000",
        "rcd_social": "Social security spending share",
        "rcd_urban": "Urbanization rate",
        "rcd_income_ratio": "Urban-rural income ratio (negative)",
        "rcd_unemployment": "Urban unemployment rate (negative)",
    }
    dim_map = {
        "dfa_ports_pc": "Digital infrastructure", "dfa_optical": "Digital infrastructure",
        "dfa_mobile": "Digital infrastructure", "dfa_ipv4_pc": "Digital infrastructure",
        "dfa_domain_pc": "Digital infrastructure",
        "dfa_software_gdp": "Digital industry", "dfa_ecom_gdp": "Digital industry",
        "dfa_ecom_firm": "Digital industry", "dfa_website": "Digital industry",
        "dfa_info_firm_pc": "Digital industry",
        "dfa_dfi_coverage": "Digital finance", "dfa_dfi_usage": "Digital finance",
        "dfa_dfi_digit": "Digital finance",
        "dfa_ict_emp": "Digital human capital", "dfa_internet": "Digital human capital",
        "rcd_pgdp": "Economic", "rcd_retail_pc": "Economic", "rcd_fiscal": "Economic",
        "rcd_income": "Social", "rcd_beds": "Social", "rcd_highered": "Social",
        "rcd_social": "Social", "rcd_urban": "Urban-rural",
        "rcd_income_ratio": "Urban-rural", "rcd_unemployment": "Urban-rural",
    }
    lines = [r"\begin{tabular}{llc}", r"\toprule",
             r"Dimension & Indicator & Weight \\", r"\midrule"]
    lines.append(r"\multicolumn{3}{l}{\textit{Panel A: DFA (equal weights across four dimensions)}} \\")
    for _, r in d[d["index"] == "DFA"].iterrows():
        dim = dim_map.get(r["indicator"], r["dimension"])
        lines.append(f"{dim} & {names.get(r['indicator'], tex_escape(r['indicator']))} & "
                     f"{f3(r['weight_within'])} \\\\")
    lines.append(r"\midrule")
    lines.append(r"\multicolumn{3}{l}{\textit{Panel B: RCD (global entropy weights)}} \\")
    for _, r in d[d["index"] == "RCD_global10"].iterrows():
        dim = dim_map.get(r["indicator"], r["dimension"])
        lines.append(f"{dim} & {names.get(r['indicator'], tex_escape(r['indicator']))} & "
                     f"{f3(r['weight_within'])} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    (OUT / "tableA1_weights.tex").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    for fn in [table2, table3, table4, table5, table6, table7, table_weights]:
        fn()
    print("LaTeX tables written")
