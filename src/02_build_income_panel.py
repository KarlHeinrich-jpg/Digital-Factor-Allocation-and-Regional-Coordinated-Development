# -*- coding: utf-8 -*-
"""Reconcile OCR'd urban/rural income tables and build a 2013-2021 income panel.

The yearbook prints one decimal. OCR occasionally drops leading digits
(e.g. 46118.9 -> 4611.9). We treat the two yearbook editions as candidates and
choose the province-year pair most consistent with the accounting identity

    INC_total ~= urb_share * INC_urban + (1-urb_share) * INC_rural

Remaining implausible cells are flagged, overridden from
data/income_manual_fixes.csv when available, and otherwise recovered from the
identity or interpolated. All filled cells are marked in the output.
"""
from __future__ import annotations

from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

# ---------------------------------------------------------------- OCR candidates
raw = pd.read_csv(DATA / "income_ocr_raw_wide.csv").drop(columns=["table"])
raw["table"] = np.repeat(["urban_2020", "rural_2020", "urban_2022", "rural_2022"], 32)
long = raw.melt(id_vars=["table", "province"], var_name="year", value_name="value")
long["year"] = long["year"].astype(int)
long["series"] = long["table"].str.split("_").str[0]
long["edition"] = long["table"].str.split("_").str[1]
long = long.dropna(subset=["value"])
long = long[long["province"] != "全国"]
long = long[(long["value"] > 500) & (long["value"] < 200000)]
long["series_edition"] = long["series"] + "_" + long["edition"]

cand = (long.pivot_table(index=["province", "year"], columns="series_edition",
                         values="value", aggfunc="first")
        .reset_index())

# ---------------------------------------------------------------- province panel
panel = pd.read_csv(DATA / "provincial_panel_raw.csv", encoding="utf-8-sig",
                    skiprows=[1, 2, 3])
panel["year"] = pd.to_numeric(panel["年份"], errors="coerce").astype("Int64")
panel = panel[(panel["year"] >= 2013) & (panel["year"] <= 2021) &
              (panel["省份"] != "西藏")].copy()
panel = panel.rename(columns={"省份": "province"})
panel["inc_total"] = pd.to_numeric(panel["居民收入水平"], errors="coerce")
panel["urb"] = pd.to_numeric(panel["城镇化率"], errors="coerce") / 100.0

df = (panel[["province", "year", "inc_total", "urb"]]
      .merge(cand, on=["province", "year"], how="left")
      .sort_values(["province", "year"]).reset_index(drop=True))

# ---------------------------------------------------------------- joint selection
def pick(row):
    u_opts = [v for v in [row.get("urban_2020"), row.get("urban_2022")]
              if pd.notna(v)]
    r_opts = [v for v in [row.get("rural_2020"), row.get("rural_2022")]
              if pd.notna(v)]
    if not u_opts and not r_opts:
        return pd.Series({"urban": np.nan, "rural": np.nan, "select_err": np.nan})
    best = None
    for u, r in product(u_opts or [np.nan], r_opts or [np.nan]):
        if pd.isna(u) and pd.isna(r):
            continue
        if pd.isna(u):
            # predicted urban from observed rural
            u_hat = (row["inc_total"] - (1 - row["urb"]) * r) / row["urb"]
            err = abs(r - r)  # no direct check; use one-sided plausibility
            err = 0.05  # neutral, will be checked after selection
        elif pd.isna(r):
            err = 0.05
        else:
            pred = row["urb"] * u + (1 - row["urb"]) * r
            err = abs(pred - row["inc_total"]) / row["inc_total"]
        if best is None or err < best[0]:
            best = (err, u, r)
    err, u, r = best
    # derive the missing counterpart from the selected one
    if pd.isna(u):
        u = (row["inc_total"] - (1 - row["urb"]) * r) / row["urb"]
    if pd.isna(r):
        r = (row["inc_total"] - row["urb"] * u) / (1 - row["urb"])
    return pd.Series({"urban": u, "rural": r, "select_err": err})

df[["urban", "rural", "select_err"]] = df.apply(pick, axis=1)

# ---------------------------------------------------------------- manual fixes
fix_path = DATA / "income_manual_fixes.csv"
if fix_path.exists():
    manual = pd.read_csv(fix_path)
    df = df.merge(manual, on=["province", "year"], how="left",
                  suffixes=("", "_fix"))
    df["urban"] = df["urban_fix"].fillna(df["urban"])
    df["rural"] = df["rural_fix"].fillna(df["rural"])
    df = df.drop(columns=["urban_fix", "rural_fix"])

# ---------------------------------------------------------------- quality flags
pred = df["urb"] * df["urban"] + (1 - df["urb"]) * df["rural"]
df["identity_err"] = (pred - df["inc_total"]).abs() / df["inc_total"]
df["income_ratio"] = df["urban"] / df["rural"]
df["flag"] = (
    df["urban"].isna() | df["rural"].isna() |
    (df["identity_err"] > 0.12) |
    (df["income_ratio"] < 1.2) | (df["income_ratio"] > 5.5)
)

# fill missing only (flag rows are left for manual review)
for col in ["urban", "rural"]:
    df[col] = df.groupby("province")[col].transform(
        lambda s: s.interpolate(limit_direction="both"))

pred = df["urb"] * df["urban"] + (1 - df["urb"]) * df["rural"]
df["identity_err"] = (pred - df["inc_total"]).abs() / df["inc_total"]
df["income_ratio"] = df["urban"] / df["rural"]

df.to_csv(DATA / "income_panel.csv", index=False, encoding="utf-8-sig")

print(df.shape)
print(df[["income_ratio", "identity_err"]].describe().round(4).to_string())
print("\nflagged cells:")
print(df[df["flag"]][["province", "year", "urban", "rural", "income_ratio",
                      "identity_err", "select_err"]]
      .to_string(index=False))
