# -*- coding: utf-8 -*-
"""Produce the main tables for the paper.

Tables
------
table2_descriptives.csv
table3_baseline.csv
table4_threshold.csv
table5_heterogeneity.csv
table6_robustness.csv
table7_mechanisms.csv
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from linearmodels.panel import PanelOLS

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
TAB = ROOT / "output" / "tables"
TAB.mkdir(parents=True, exist_ok=True)

CONTROLS = ["gov", "ln_fdi", "ln_dens", "private"]
CORE = ["dfa", "rcd", "rcd5", "rcd_ccd"]


def load() -> pd.DataFrame:
    df = pd.read_csv(DATA / "analysis_panel.csv").sort_values(
        ["province", "year"]).reset_index(drop=True)
    df["trend"] = (df["year"] - df["year"].mean()) / df["year"].std()
    for r in ["Central", "West", "Northeast"]:
        df[f"trend_{r}"] = df["trend"] * (df["region"] == r)
    return df


def panel_fe(df: pd.DataFrame, y: str, xs: list[str], twoway: bool = True,
             cluster: bool = True):
    d = df.dropna(subset=[y] + xs).set_index(["province", "year"])
    mod = PanelOLS(d[y], d[xs], entity_effects=True, time_effects=twoway,
                   drop_absorbed=True)
    res = mod.fit(cov_type="clustered" if cluster else "unadjusted",
                  cluster_entity=cluster)
    return res


def stars(p: float) -> str:
    return "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.10 else ""


def baseline_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    specs = [
        ("(1)", "rcd", ["dfa"], True),
        ("(2)", "rcd", ["dfa"] + CONTROLS, True),
        ("(3)", "rcd", ["dfa"] + CONTROLS +
         ["trend", "trend_Central", "trend_West", "trend_Northeast"], True),
        ("(4)", "rcd5", ["dfa"] + CONTROLS, True),
    ]
    for label, y, xs, twoway in specs:
        res = panel_fe(df, y, xs, twoway=twoway)
        for v in ["dfa"] + CONTROLS:
            if v in res.params.index:
                rows.append({"model": label, "outcome": y, "var": v,
                             "coef": res.params[v], "se": res.std_errors[v],
                             "p": res.pvalues[v], "star": stars(res.pvalues[v]),
                             "n": int(res.nobs), "r2": res.rsquared})
        rows.append({"model": label, "outcome": y, "var": "N",
                     "coef": np.nan, "se": np.nan, "p": np.nan, "star": "",
                     "n": int(res.nobs), "r2": res.rsquared})
    return pd.DataFrame(rows)


def demean(a: pd.Series, ids: pd.Series) -> np.ndarray:
    s = pd.Series(np.asarray(a, float).ravel())
    s.index = ids.index
    return (s - s.groupby(ids).transform("mean")).values


def cluster_se(X, e, ids):
    XtX_inv = np.linalg.pinv(X.T @ X)
    meat = np.zeros((X.shape[1], X.shape[1]))
    idv = ids.values
    for i in np.unique(idv):
        Xi, ei = X[idv == i], e[idv == i]
        z = Xi.T @ ei
        meat += np.outer(z, z)
    n = X.shape[0]
    V = XtX_inv @ meat @ XtX_inv * n / (n - 1)
    return np.sqrt(np.diag(V))


def threshold_fe(df: pd.DataFrame, y: str, x: str, q: str,
                 controls=CONTROLS, grid_q=(0.10, 0.90), grid_n=80):
    d = df.dropna(subset=[y, x, q] + controls).reset_index(drop=True)
    ids = d["province"]
    yd = demean(d[y], ids)
    C = np.column_stack([demean(d[c], ids) for c in controls])
    X0 = np.column_stack([demean(d[x], ids), C])
    b0 = np.linalg.lstsq(X0, yd, rcond=None)[0]
    ssr0 = float((yd - X0 @ b0) @ (yd - X0 @ b0))
    grid = np.quantile(d[q], np.linspace(*grid_q, grid_n))
    best = (np.inf, None, None)
    for g in grid:
        i = (d[q].values <= g).astype(float)
        X1 = np.column_stack([demean(d[x] * i, ids),
                              demean(d[x] * (1 - i), ids), C])
        b = np.linalg.lstsq(X1, yd, rcond=None)[0]
        e = yd - X1 @ b
        s = float(e @ e)
        if s < best[0]:
            best = (s, g, b)
    ssr1, gamma, beta = best
    i = (d[q].values <= gamma).astype(float)
    X1 = np.column_stack([demean(d[x] * i, ids),
                          demean(d[x] * (1 - i), ids), C])
    beta = np.linalg.lstsq(X1, yd, rcond=None)[0]
    e = yd - X1 @ beta
    se = cluster_se(X1, e, ids)
    lr = np.array([((ssr0 if False else 0) or 0) for _ in grid])
    # LR over the grid
    lrs = []
    for g in grid:
        i = (d[q].values <= g).astype(float)
        Xg = np.column_stack([demean(d[x] * i, ids),
                              demean(d[x] * (1 - i), ids), C])
        bg = np.linalg.lstsq(Xg, yd, rcond=None)[0]
        eg = yd - Xg @ bg
        lrs.append((float(eg @ eg) - ssr1) / (ssr1 / (len(d) - X1.shape[1])))
    lrs = np.array(lrs)
    ok = grid[lrs <= 7.35]
    ci = (float(ok.min()), float(ok.max())) if len(ok) else (np.nan, np.nan)
    return {"y": y, "x": x, "q": q, "gamma": gamma, "ci_lo": ci[0],
            "ci_hi": ci[1], "beta_low": beta[0], "se_low": se[0],
            "p_low": 2 * (1 - _norm_cdf(abs(beta[0] / se[0]))),
            "beta_high": beta[1], "se_high": se[1],
            "p_high": 2 * (1 - _norm_cdf(abs(beta[1] / se[1]))),
            "n_low": int((d[q] <= gamma).sum()),
            "n_high": int((d[q] > gamma).sum()), "n": len(d),
            "ssr0": ssr0, "ssr1": ssr1}


def _norm_cdf(x):
    from math import erf, sqrt
    return 0.5 * (1 + erf(x / sqrt(2)))


def threshold_table(df: pd.DataFrame) -> pd.DataFrame:
    # bootstrap p-values are read from the earlier 04 output
    boot = pd.read_csv(TAB / "threshold_tests.csv")
    pvals = dict(zip(boot["threshold_var"], boot["p_boot"]))
    rows = []
    for q in ["dfa", "ln_pgdp", "fin_dev", "tech", "private"]:
        r = threshold_fe(df, "rcd", "dfa", q)
        r["p_boot"] = float(pvals.get(q, np.nan))
        rows.append(r)
    return pd.DataFrame(rows)


def heterogeneity_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for reg in ["East", "Central", "West", "Northeast"]:
        sub = df[df["region"] == reg]
        for twoway in [True, False]:
            res = panel_fe(sub, "rcd", ["dfa"] + CONTROLS, twoway=twoway)
            rows.append({"region": reg, "fe": "two-way" if twoway else "province",
                         "coef": res.params["dfa"], "se": res.std_errors["dfa"],
                         "p": res.pvalues["dfa"], "star": stars(res.pvalues["dfa"]),
                         "n": int(res.nobs)})
    return pd.DataFrame(rows)


def robustness_table(df: pd.DataFrame) -> pd.DataFrame:
    specs = []

    def add(name, y, x, note="", twoway=True, sample=None, extra=None):
        specs.append((name, y, x, note, twoway, sample, extra))

    add("Baseline", "rcd", "dfa")
    add("Five-dimension RCD", "rcd5", "dfa")
    add("CCD of core dimensions", "rcd_ccd", "dfa")
    add("Entropy-weighted RCD", "rcd3_global", "dfa")
    add("Equal-weight DFA", "rcd", "dfa_equal")
    add("Entropy-weighted DFA", "rcd", "dfa_entropy")
    add("Excluding municipalities", "rcd", "dfa",
        sample=lambda d: d[~d["province"].isin(["北京", "上海", "天津", "重庆"])])
    add("2013-2019", "rcd", "dfa", sample=lambda d: d[d["year"] <= 2019])
    add("Additional controls", "rcd", "dfa", extra=["tech", "ind_struct", "fin_dev"])
    add("Province FE only", "rcd", "dfa", twoway=False)

    rows = []
    for name, y, x, note, twoway, sample, extra in specs:
        d = sample(df) if sample else df
        xs = [x] + CONTROLS + (extra or [])
        res = panel_fe(d, y, xs, twoway=twoway)
        rows.append({"spec": name, "coef": res.params[x],
                     "se": res.std_errors[x], "p": res.pvalues[x],
                     "star": stars(res.pvalues[x]), "n": int(res.nobs)})
    # lagged DFA
    d = df.copy()
    d["dfa_l1"] = d.groupby("province")["dfa"].shift(1)
    res = panel_fe(d, "rcd", ["dfa_l1"] + CONTROLS)
    rows.append({"spec": "Lagged DFA", "coef": res.params["dfa_l1"],
                 "se": res.std_errors["dfa_l1"], "p": res.pvalues["dfa_l1"],
                 "star": stars(res.pvalues["dfa_l1"]), "n": int(res.nobs)})
    # winsorized outcome and regressor
    d = df.copy()
    for c in ["rcd", "dfa"]:
        lo, hi = d[c].quantile(0.01), d[c].quantile(0.99)
        d[c] = d[c].clip(lo, hi)
    res = panel_fe(d, "rcd", ["dfa"] + CONTROLS)
    rows.append({"spec": "Winsorized 1/99", "coef": res.params["dfa"],
                 "se": res.std_errors["dfa"], "p": res.pvalues["dfa"],
                 "star": stars(res.pvalues["dfa"]), "n": int(res.nobs)})
    return pd.DataFrame(rows)


def mechanism_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for m in ["tech", "fin_dev", "ind_struct", "income_ratio"]:
        for twoway in [True, False]:
            res = panel_fe(df, m, ["dfa"] + [c for c in CONTROLS if c != m],
                           twoway=twoway)
            rows.append({"mediator": m, "fe": "two-way" if twoway else "province",
                         "coef": res.params["dfa"],
                         "se": res.std_errors["dfa"], "p": res.pvalues["dfa"],
                         "star": stars(res.pvalues["dfa"]), "n": int(res.nobs)})
    for m in ["tech", "fin_dev", "ind_struct"]:
        xs = ["dfa", m] + [c for c in CONTROLS if c != m]
        res = panel_fe(df, "rcd", xs)
        rows.append({"mediator": m, "fe": "RCD equation", "coef": res.params[m],
                     "se": res.std_errors[m], "p": res.pvalues[m],
                     "star": stars(res.pvalues[m]), "n": int(res.nobs)})
    return pd.DataFrame(rows)


def descriptive_table(df: pd.DataFrame) -> pd.DataFrame:
    vars_ = ["dfa", "rcd", "rcd5", "rcd_ccd", "income_ratio", "gov",
             "ln_fdi", "ln_dens", "private", "fin_dev", "tech", "ind_struct"]
    rows = []
    for v in vars_:
        s = df[v].dropna()
        rows.append({"var": v, "n": len(s), "mean": s.mean(), "sd": s.std(),
                     "min": s.min(), "p50": s.median(), "max": s.max()})
    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = load()
    descriptive_table(df).to_csv(TAB / "table2_descriptives.csv", index=False,
                                 encoding="utf-8-sig")
    baseline_table(df).to_csv(TAB / "table3_baseline.csv", index=False,
                              encoding="utf-8-sig")
    threshold_table(df).to_csv(TAB / "table4_threshold.csv", index=False,
                               encoding="utf-8-sig")
    heterogeneity_table(df).to_csv(TAB / "table5_heterogeneity.csv", index=False,
                                   encoding="utf-8-sig")
    robustness_table(df).to_csv(TAB / "table6_robustness.csv", index=False,
                                encoding="utf-8-sig")
    mechanism_table(df).to_csv(TAB / "table7_mechanisms.csv", index=False,
                               encoding="utf-8-sig")
    print("tables saved")
    print(pd.read_csv(TAB / "table4_threshold.csv").round(3).to_string(index=False))
    print("\n", pd.read_csv(TAB / "table6_robustness.csv").round(3).to_string(index=False))
