# -*- coding: utf-8 -*-
"""Hansen (1999) panel threshold tests with a cluster wild bootstrap.

The function searches a single threshold over the inner 80% of the threshold
variable, computes Hansen's F statistic, and obtains a bootstrap p-value by
generating y* = fitted + e* with province-level Rademacher weights.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def demean(a: pd.Series, ids: pd.Series) -> np.ndarray:
    s = a.astype(float).copy()
    return (s - s.groupby(ids).transform("mean")).values


def design(d: pd.DataFrame, x: str, controls: list[str], q: str, gamma: float,
           ids: pd.Series) -> np.ndarray:
    i = (d[q].values <= gamma).astype(float)
    cols = [demean(d[x] * i, ids), demean(d[x] * (1 - i), ids)]
    cols += [demean(d[c], ids) for c in controls]
    return np.column_stack(cols)


def ssr(X: np.ndarray, y: np.ndarray) -> tuple[float, np.ndarray]:
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    e = y - X @ b
    return float(e @ e), b


def hansen_test(df: pd.DataFrame, y: str, x: str, q: str, controls: list[str],
                reps: int = 300, seed: int = 20261031) -> dict:
    d = df.dropna(subset=[y, x, q] + controls).reset_index(drop=True)
    ids = d["province"]
    yd = demean(d[y], ids)
    X0 = np.column_stack([demean(d[x], ids)] +
                         [demean(d[c], ids) for c in controls])
    ssr0, b0 = ssr(X0, yd)
    grid = np.quantile(d[q], np.linspace(0.10, 0.90, 80))
    Xgrid = [design(d, x, controls, q, g, ids) for g in grid]
    best = (np.inf, None, None)
    for g, X1 in zip(grid, Xgrid):
        s, b = ssr(X1, yd)
        if s < best[0]:
            best = (s, g, b)
    ssr1, gamma, beta = best
    n, k = X0.shape
    dfree = len(d) - (k + 1) - 1
    F = (ssr0 - ssr1) / (ssr1 / dfree)

    rng = np.random.default_rng(seed)
    fitted = X0 @ b0
    resid = yd - fitted
    prov = d["province"].values
    ups = np.unique(prov)
    Fstar = np.empty(reps)
    for r in range(reps):
        signs = pd.Series(rng.choice([-1.0, 1.0], size=len(ups)), index=ups)
        e_star = resid * signs.loc[prov].values
        y_star = pd.Series(fitted + e_star)
        yd_star = demean(y_star, ids)
        s0, _ = ssr(X0, yd_star)
        best_s = np.inf
        for X1 in Xgrid:
            s, _ = ssr(X1, yd_star)
            if s < best_s:
                best_s = s
        Fstar[r] = (s0 - best_s) / (best_s / dfree)
    pval = float((Fstar >= F).mean())
    return {"y": y, "x": x, "threshold_var": q, "gamma": float(gamma),
            "F": float(F), "p_boot": pval, "ssr0": ssr0, "ssr1": ssr1,
            "beta_low": beta[0], "beta_high": beta[1], "n": len(d),
            "reps": reps}


if __name__ == "__main__":
    df = pd.read_csv(DATA / "analysis_panel.csv").sort_values(
        ["province", "year"]).reset_index(drop=True)
    df["rcd3"] = df[["rcd_dim_economic", "rcd_dim_social",
                     "rcd_dim_urban-rural"]].mean(axis=1)
    controls = ["gov", "ln_fdi", "ln_dens", "private"]
    specs = [
        ("rcd3", "dfa", "dfa"),
        ("rcd3", "dfa", "fin_dev"),
        ("rcd3", "dfa", "tech"),
        ("rcd3", "dfa", "ln_pgdp"),
        ("rcd3", "dfa", "private"),
    ]
    rows = []
    for y, x, q in specs:
        res = hansen_test(df, y, x, q, controls, reps=300)
        rows.append(res)
        print(res)
    pd.DataFrame(rows).to_csv(ROOT / "output" / "tables" /
                              "threshold_tests.csv", index=False,
                              encoding="utf-8-sig")
