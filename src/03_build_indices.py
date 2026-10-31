# -*- coding: utf-8 -*-
"""Construct the Digital Factor Allocation (DFA) and Regional Coordinated
Development (RCD) indices with the entropy-weight method.

Outputs
-------
data/analysis_panel.csv : 30 provinces x 2013-2021, all indices and raw controls
output/tables/table_weights.csv : Entropy weights by dimension and indicator
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
TAB = ROOT / "output" / "tables"
TAB.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------- load panel
df = pd.read_csv(DATA / "provincial_panel_raw.csv", encoding="utf-8-sig",
                 skiprows=[1, 2, 3])
df["year"] = pd.to_numeric(df["年份"], errors="coerce")
df = df[(df["year"] >= 2013) & (df["year"] <= 2021) &
        (df["省份"] != "西藏")].copy()
df = df.rename(columns={"省份": "province"})
df = df.sort_values(["province", "year"]).reset_index(drop=True)

inc = pd.read_csv(DATA / "income_panel.csv")[["province", "year", "income_ratio",
                                              "urban", "rural"]]
inc = inc.rename(columns={"urban": "urban_filled", "rural": "rural_filled"})
df = df.merge(inc, on=["province", "year"], how="left")

for c in df.columns:
    if c not in ["province"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

# ---------------------------------------------------------------- indicators
df["pop"] = df["年末常住人口(万人)"]
df["gdp"] = df["Gross domestic product"]

df["dfa_ports_pc"] = df["互联网接入端口数"] / df["pop"]
df["dfa_optical"] = df["单位面积长途光缆长度"]
df["dfa_mobile"] = df["移动电话普及率"]
df["dfa_ipv4_pc"] = df["IPv4个数"] / df["pop"]
df["dfa_domain_pc"] = df["域名数"] / df["pop"]
df["dfa_software_gdp"] = df["软件业务收入"] / 10000.0 / df["gdp"]
df["dfa_ecom_gdp"] = df["电子商务交易额"] / df["gdp"]
df["dfa_ecom_firm"] = df["有电子商务交易活动企业比重"]
df["dfa_website"] = df["每百家企业拥有网站数"]
df["dfa_info_firm_pc"] = df["信息化企业数"] / df["pop"]
df["dfa_dfi_coverage"] = df["数字金融覆盖广度指数"]
df["dfa_dfi_usage"] = df["数字金融使用深度指数"]
df["dfa_dfi_digit"] = df["数字金融数字化程度"]
df["dfa_ict_emp"] = df["数字化发展水平"]
df["dfa_internet"] = df["互联网普及率"]

df["rcd_pgdp"] = df["人均国内生产总值"]
df["rcd_retail_pc"] = df["人均社会消费品零售总额"]
df["rcd_fiscal"] = df["财政自给率"]
df["rcd_income"] = df["居民收入水平"]
df["rcd_beds"] = df["每万人拥有医院床位数"]
df["rcd_highered"] = df["每十万人拥有高等教育在校生数"]
df["rcd_social"] = df["社会保障支持强度"]
df["rcd_urban"] = df["城镇化率"]
df["rcd_income_ratio"] = df["income_ratio"]
df["rcd_unemployment"] = df["城镇登记失业率"]
df["rcd_gas"] = df["城市燃气普及率"]
df["rcd_water"] = df["城市用水普及率"]
df["rcd_road"] = df["人均城市道路面积"]
df["rcd_transit"] = df["每万人拥有公共交通车辆数"]
df["rcd_green"] = df["建成区绿化覆盖率"]
df["rcd_forest"] = df["森林覆盖率(%)"]
df["rcd_env_exp"] = df["环保支出占比"]
df["rcd_wastewater"] = df["废水排放强度"]
df["rcd_so2"] = df["二氧化硫排放强度"]
df["rcd_energy"] = df["能源消耗强度"]

DFA_DIMS = {
    "digital infrastructure": ["dfa_ports_pc", "dfa_optical", "dfa_mobile",
                               "dfa_ipv4_pc", "dfa_domain_pc"],
    "digital industry": ["dfa_software_gdp", "dfa_ecom_gdp", "dfa_ecom_firm",
                         "dfa_website", "dfa_info_firm_pc"],
    "digital finance": ["dfa_dfi_coverage", "dfa_dfi_usage", "dfa_dfi_digit"],
    "digital human capital": ["dfa_ict_emp", "dfa_internet"],
}

RCD_DIMS = {
    "economic": ["rcd_pgdp", "rcd_retail_pc", "rcd_fiscal"],
    "social": ["rcd_income", "rcd_beds", "rcd_highered", "rcd_social"],
    "urban-rural": ["rcd_urban", "rcd_income_ratio", "rcd_unemployment"],
    "infrastructure": ["rcd_gas", "rcd_water", "rcd_road", "rcd_transit"],
    "ecology": ["rcd_green", "rcd_forest", "rcd_env_exp", "rcd_wastewater",
                "rcd_so2", "rcd_energy"],
}

NEGATIVE = {"rcd_income_ratio", "rcd_unemployment", "rcd_wastewater",
            "rcd_so2", "rcd_energy"}


def normalize(s: pd.Series, negative: bool = False) -> pd.Series:
    lo, hi = s.quantile(0.01), s.quantile(0.99)
    x = s.clip(lo, hi)
    z = (x - x.min()) / (x.max() - x.min() + 1e-12)
    if negative:
        z = 1 - z
    return z + 1e-4


def entropy_weights(data: pd.DataFrame, cols: list[str]) -> pd.Series:
    Z = pd.DataFrame({c: normalize(data[c], c in NEGATIVE) for c in cols})
    P = Z / Z.sum()
    k = 1 / np.log(len(Z))
    e = -k * (P * np.log(P)).sum()
    d = 1 - e
    return d / d.sum()


def score(data: pd.DataFrame, weights: pd.Series) -> pd.Series:
    Z = pd.DataFrame({c: normalize(data[c], c in NEGATIVE) for c in weights.index})
    return (Z * weights).sum(axis=1)


# ---------------------------------------------------------------- DFA
weights_rows = []
for dim, cols in DFA_DIMS.items():
    w = entropy_weights(df, cols)
    df[f"dfa_dim_{dim}"] = score(df, w)
    for c in cols:
        weights_rows.append({"index": "DFA", "dimension": dim, "indicator": c,
                             "weight_within": w[c]})
# equal dimension weights, so the four factor categories count equally
for dim in DFA_DIMS:
    df[f"dfa_dim_{dim}_n"] = normalize(df[f"dfa_dim_{dim}"])
df["dfa"] = df[[f"dfa_dim_{d}_n" for d in DFA_DIMS]].mean(axis=1)

# ---------------------------------------------------------------- RCD
rcd_w = {}
for dim, cols in RCD_DIMS.items():
    w = entropy_weights(df, cols)
    rcd_w[dim] = w
    df[f"rcd_dim_{dim}"] = score(df, w)
    for c in cols:
        weights_rows.append({"index": "RCD", "dimension": dim, "indicator": c,
                             "weight_within": w[c]})
for dim in RCD_DIMS:
    df[f"rcd_dim_{dim}_n"] = normalize(df[f"rcd_dim_{dim}"])
# Baseline: equal weights across the three core coordination dimensions.
# Subsystem scores are already weighted sums of normalized indicators on a 0-1
# scale, so they are averaged directly (rather than re-normalized, which would
# give each dimension equal variance instead of equal weight).
CORE = ["economic", "social", "urban-rural"]
df["rcd"] = df[[f"rcd_dim_{d}" for d in CORE]].mean(axis=1)
# Extended five-dimension index (robustness)
df["rcd5"] = df[[f"rcd_dim_{d}" for d in RCD_DIMS]].mean(axis=1)
# Global entropy weights over the ten core indicators (robustness)
core_cols = [c for d in CORE for c in RCD_DIMS[d]]
w10 = entropy_weights(df, core_cols)
df["rcd_global10"] = score(df, w10)
for c in core_cols:
    weights_rows.append({"index": "RCD_global10", "dimension": "all",
                         "indicator": c, "weight_within": w10[c]})
# Entropy-weighted composite of the three core dimensions
Zc = pd.DataFrame({d: normalize(df[f"rcd_dim_{d}"]) for d in CORE})
Pc = Zc / Zc.sum()
kc = 1 / np.log(len(Zc))
ec = -kc * (Pc * np.log(Pc)).sum()
wc = (1 - ec) / (1 - ec).sum()
df["rcd3_global"] = (Zc * wc).sum(axis=1)
# Coupling coordination degree across the three core dimensions
U = Zc.clip(lower=1e-4)
k = U.shape[1]
C = k * (U.prod(axis=1) ** (1 / k)) / U.sum(axis=1)
T = U.mean(axis=1)
df["rcd_ccd"] = np.sqrt(C * T)
# Five-dimension CCD (robustness)
U5 = df[[f"rcd_dim_{d}_n" for d in RCD_DIMS]].clip(lower=1e-4)
C5 = 5 * (U5.prod(axis=1) ** (1 / 5)) / U5.sum(axis=1)
df["rcd5_ccd"] = np.sqrt(C5 * U5.mean(axis=1))

# DFA variants for robustness
all_dfa = [c for cols in DFA_DIMS.values() for c in cols]
Zd = pd.DataFrame({c: normalize(df[c]) for c in all_dfa})
df["dfa_equal"] = Zd.mean(axis=1)
Pd = Zd / Zd.sum()
kd = 1 / np.log(len(Zd))
ed = -kd * (Pd * np.log(Pd)).sum()
wd = (1 - ed) / (1 - ed).sum()
df["dfa_entropy"] = (Zd * wd).sum(axis=1)
from sklearn.decomposition import PCA
Zp = (Zd - Zd.mean()) / Zd.std()
pca = PCA(n_components=1).fit(Zp)
df["dfa_pca"] = pca.transform(Zp)[:, 0]
weights_rows += [{"index": "DFA_global_entropy", "dimension": "all",
                   "indicator": c, "weight_within": wd[c]} for c in all_dfa]

# ---------------------------------------------------------------- controls
df["gov"] = df["政府干预强度"]
df["fdi_pc"] = df["人均对外开放水平"]
df["ln_fdi"] = np.log(df["fdi_pc"].clip(lower=1))
df["ln_dens"] = np.log(df["人口密度"])
df["private"] = df["私营经济活力"]
df["fin_dev"] = df["金融发展水平"]
df["tech"] = df["科技投入强度"]
df["ind_struct"] = df["第三产业占GDP比重"] / df["第二产业占比"]
df["ln_pgdp"] = np.log(df["rcd_pgdp"])

REGION = {
    "北京": "East", "天津": "East", "河北": "East", "上海": "East",
    "江苏": "East", "浙江": "East", "福建": "East", "山东": "East",
    "广东": "East", "海南": "East",
    "山西": "Central", "安徽": "Central", "江西": "Central", "河南": "Central",
    "湖北": "Central", "湖南": "Central",
    "内蒙古": "West", "广西": "West", "重庆": "West", "四川": "West",
    "贵州": "West", "云南": "West", "陕西": "West", "甘肃": "West",
    "青海": "West", "宁夏": "West", "新疆": "West",
    "辽宁": "Northeast", "吉林": "Northeast", "黑龙江": "Northeast",
}
df["region"] = df["province"].map(REGION)

out_cols = (["province", "year", "region", "dfa", "rcd", "rcd5", "rcd_ccd",
             "rcd5_ccd", "rcd3_global", "rcd_global10", "dfa_equal",
             "dfa_entropy", "dfa_pca"]
            + [f"dfa_dim_{d}" for d in DFA_DIMS]
            + [f"rcd_dim_{d}" for d in RCD_DIMS]
            + ["income_ratio", "urban_filled", "rural_filled", "gov", "ln_fdi",
               "ln_dens", "private", "fin_dev", "tech", "ind_struct", "ln_pgdp",
               "rcd_pgdp", "rcd_income", "rcd_urban"])
df[out_cols].to_csv(DATA / "analysis_panel.csv", index=False, encoding="utf-8-sig")

wt = pd.DataFrame(weights_rows)
wt.to_csv(TAB / "table_weights.csv", index=False, encoding="utf-8-sig")

print(df.shape)
print(df[["dfa", "rcd", "rcd_ccd"]].describe().round(4).to_string())
print("\ncorr dfa-rcd", round(df["dfa"].corr(df["rcd"]), 4),
      " dfa-ccd", round(df["dfa"].corr(df["rcd_ccd"]), 4))
print("\nweights:")
print(wt.to_string(index=False))
print("\nTop/bottom DFA (2021):")
print(df[df["year"] == 2021][["province", "dfa", "rcd"]]
      .sort_values("dfa", ascending=False).head(6).to_string(index=False))
print(df[df["year"] == 2021][["province", "dfa", "rcd"]]
      .sort_values("dfa").head(6).to_string(index=False))
