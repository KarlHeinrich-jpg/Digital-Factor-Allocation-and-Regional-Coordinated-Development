# -*- coding: utf-8 -*-
"""Appendix B: province-by-year DFA and RCD index values (Tables A2 and A3).

Layout follows the province x year measurement tables used in the reference
papers: one row per province, one column per year, plus the province-level
mean, standard deviation, and the 2013-2021 change.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "paper" / "tables"
OUT.mkdir(parents=True, exist_ok=True)

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

REGIONS = [("East", "Eastern"), ("Central", "Central"),
           ("West", "Western"), ("Northeast", "Northeastern")]

YEARS = list(range(2013, 2022))
NCOL = len(YEARS) + 3  # years + mean + sd + change


def build(df, var, path, caption_label):
    wide = df.pivot(index="province", columns="year", values=var)[YEARS]
    reg = df.drop_duplicates("province").set_index("province")["region"]
    name = pd.Series(EN)

    head = " & ".join(str(y) for y in YEARS)
    lines = [
        r"\begin{tabular}{l" + "r" * NCOL + "}",
        r"\toprule",
        f"Province & {head} & Mean & SD & Change \\\\",
        r"\midrule",
    ]
    first_group = True
    for key, label in REGIONS:
        provs = sorted(reg[reg == key].index, key=lambda p: name[p])
        if not first_group:
            lines.append(r"\midrule")
        first_group = False
        lines.append(rf"\multicolumn{{{NCOL + 1}}}{{l}}{{\textit{{{label}}}}} \\")
        for p in provs:
            v = wide.loc[p]
            cells = " & ".join(f"{x:.3f}" for x in v)
            lines.append(
                f"{name[p]} & {cells} & {v.mean():.3f} & {v.std(ddof=1):.3f} & "
                f"{v[2021] - v[2013]:+.3f} \\\\")

    lines += [r"\midrule"]
    allv = df[var]
    g = df.groupby("year")[var].mean()
    cells = " & ".join(f"{g[y]:.3f}" for y in YEARS)
    lines.append(
        f"National mean & {cells} & {allv.mean():.3f} & {allv.std(ddof=1):.3f} & "
        f"{g[2021] - g[2013]:+.3f} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {path}  ({caption_label})")


def main():
    df = pd.read_csv(DATA / "analysis_panel.csv")
    missing = set(df["province"]) - set(EN)
    assert not missing, missing
    build(df, "dfa", OUT / "tableA2_dfa_values.tex", "DFA")
    build(df, "rcd", OUT / "tableA3_rcd_values.tex", "RCD")


if __name__ == "__main__":
    main()
