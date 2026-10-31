# -*- coding: utf-8 -*-
"""Main threshold estimates.

Specification
-------------
RCD3_it = mu_i + beta1 DFA_it I(q_it <= gamma) + beta2 DFA_it I(q_it > gamma)
          + delta' Controls_it + region-specific linear trends + e_it

Province fixed effects; region-specific linear trends; standard errors
clustered by province. The threshold and its confidence interval are obtained
by grid search and the likelihood-ratio inversion of Hansen (1999).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
TAB = ROOT / "output" / "tables"
TAB.mkdir(parents=True, exist_ok=True)

CONTROLS = ["gov", "ln_fdi", "ln_dens", "private"]


def load() -> pd.DataFrame:
    df = pd.read_csv(DATA / "analysis_panel.csv").sort_values(
        ["province", "year"]).reset_index(drop=True)
    df["rcd3"] = df[["rcd_dim_economic", "rcd_dim_social",
                     "rcd_dim_urban-rural"]].mean(axis=1)
    df["trend"] = (df["year"] - df["year"].mean()) / df["year"].std()
    for r in ["Central", "West", "Northeast"]:
        df[f"trend_{r}"] = df["trend"] * (df["region"] == r)
    return df


def demean(a: pd.Series, ids: pd.Series) -> np.ndarray:
    s = pd.Series(np.asarray(a, float).ravel())
    s.index = ids.index
    return (s - s.groupby(ids).transform("mean")).values


def control_matrix(d: pd.DataFrame, ids: pd.Series) -> np.ndarray:
    cols = [demean(d[c], ids) for c in CONTROLS]
    cols += [demean(d[c], ids) for c in ["trend", "trend_Central",
                                         "trend_West", "trend_Northeast"]]
    return np.column_stack(cols)


def regime_matrix(d: pd.DataFrame, q: str, gamma: float,
                  ids: pd.Series) -> np.ndarray:
    i = (d[q].values <= gamma).astype(float)
    return np.column_stack([demean(d["dfa"] * i, ids),
                            demean(d["dfa"] * (1 - i), ids)])


def ols(X: np.ndarray, y: np.ndarray) -> tuple[float, np.ndarray]:
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    e = y - X @ b
    return float(e @ e), b


def cluster_se(X: np.ndarray, e: np.ndarray, ids: pd.Series) -> np.ndarray:
    XtX_inv = np.linalg.pinv(X.T @ X)
    meat = np.zeros((X.shape[1], X.shape[1]))
    idv = ids.values
    for i in np.unique(idv):
        Xi, ei = X[idv == i], e[idv == i]
        s = Xi.T @ ei
        meat += np.outer(s, s)
    n, k = X.shape
    V = XtX_inv @ meat @ XtX_inv * n / (n - 1)
    return np.sqrt(np.diag(V))


def estimate(df: pd.DataFrame, q: str, reps: int = 500, seed: int = 20261031,
             grid_n: int = 100) -> dict:
    d = df.dropna(subset=["rcd3", "dfa", q] + CONTROLS).reset_index(drop=True)
    ids = d["province"]
    y = demean(d["rcd3"], ids)
    C = control_matrix(d, ids)
    X0 = np.column_stack([demean(d["dfa"], ids), C])
    ssr0, b0 = ols(X0, y)
    grid = np.quantile(d[q], np.linspace(0.10, 0.90, grid_n))
    Xg = [regime_matrix(d, q, g, ids) for g in grid]
    ssv = np.array([ols(np.column_stack([X, C]), y)[0] for X in Xg])
    j = int(np.argmin(ssv))
    gamma, ssr1 = float(grid[j]), float(ssv[j])
    X1 = np.column_stack([Xg[j], C])
    beta = ols(X1, y)[1]
    e = y - X1 @ beta
    se = cluster_se(X1, e, ids)
    n, k = X1.shape
    sigma2 = ssr1 / (n - k)
    F = (ssr0 - ssr1) / sigma2

    # likelihood-ratio confidence interval
    lr = (ssv - ssr1) / sigma2
    ci = grid[lr <= 7.35]
    ci_lo, ci_hi = (float(ci.min()), float(ci.max())) if len(ci) else (np.nan, np.nan)

    # cluster wild bootstrap for the threshold test
    rng = np.random.default_rng(seed)
    fitted = X0 @ b0
    resid = y - fitted
    prov = d["province"].values
    ups = np.unique(prov)
    Fstar = np.empty(reps)
    for r in range(reps):
        signs = pd.Series(rng.choice([-1.0, 1.0], size=len(ups)), index=ups)
        ystar = pd.Series(fitted + resid * signs.loc[prov].values)
        yd = demean(ystar, ids)
        s0, _ = ols(X0, yd)
        ss = np.array([ols(np.column_stack([X, C]), yd)[0] for X in Xg])
        Fstar[r] = (s0 - ss.min()) / (ss.min() / (n - k))
    pboot = float((Fstar >= F).mean())

    return {
        "threshold_var": q, "gamma": gamma, "gamma_lo": ci_lo, "gamma_hi": ci_hi,
        "F": F, "p_boot": pboot, "beta_low": beta[0], "se_low": se[0],
        "beta_high": beta[1], "se_high": se[1], "ssr0": ssr0, "ssr1": ssr1,
        "n": n, "reps": reps,
        "controls": {c: (beta[2 + i], se[2 + i]) for i, c in enumerate(CONTROLS)},
    }


if __name__ == "__main__":
    df = load()
    rows = []
    for q in ["dfa", "ln_pgdp", "fin_dev", "tech", "private"]:
        res = estimate(df, q, reps=500)
        rows.append({k: v for k, v in res.items() if k != "controls"})
        print({k: (round(v, 4) if isinstance(v, float) else v)
               for k, v in res.items() if k != "controls"})
    out = pd.DataFrame(rows)
    out.to_csv(TAB / "threshold_estimates.csv", index=False, encoding="utf-8-sig")
    print("\nsaved", TAB / "threshold_estimates.csv")
