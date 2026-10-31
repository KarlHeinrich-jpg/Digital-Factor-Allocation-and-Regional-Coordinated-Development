# -*- coding: utf-8 -*-
"""Threshold estimates for sub-dimensions of digital factor allocation."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from importlib import import_module  # noqa: E402

t = import_module("04_threshold_test")
m = import_module("05_threshold_main")

df = m.load()
df["rcd3"] = df[["rcd_dim_economic", "rcd_dim_social",
                 "rcd_dim_urban-rural"]].mean(axis=1)
df["rcd_econ"] = df["rcd_dim_economic"]
df["rcd5"] = df[["rcd_dim_economic", "rcd_dim_social", "rcd_dim_urban-rural",
                 "rcd_dim_infrastructure", "rcd_dim_ecology"]].mean(axis=1)

specs = [
    ("rcd_econ", "dfa_dim_digital human capital", "tech"),
    ("rcd3", "dfa_dim_digital human capital", "tech"),
    ("rcd_econ", "dfa_dim_digital infrastructure", "tech"),
    ("rcd_econ", "dfa", "tech"),
    ("rcd_econ", "dfa_dim_digital finance", "ln_pgdp"),
    ("rcd5", "dfa", "tech"),
]
rows = []
for y, x, q in specs:
    # patch the estimator to use the requested outcome and regressor
    src = m.estimate.__code__
    d = df.dropna(subset=[y, x, q] + m.CONTROLS).reset_index(drop=True)
    ids = d["province"]
    yd = m.demean(d[y], ids)
    C = m.control_matrix(d, ids)
    X0 = np.column_stack([m.demean(d[x], ids), C])
    ssr0, b0 = m.ols(X0, yd)
    grid = np.quantile(d[q], np.linspace(0.20, 0.80, 61))
    Xg = [np.column_stack([m.demean(d[x] * (d[q].values <= g), ids),
                           m.demean(d[x] * (d[q].values > g), ids)]) for g in grid]
    ssv = np.array([m.ols(np.column_stack([X, C]), yd)[0] for X in Xg])
    j = int(np.argmin(ssv))
    gamma, ssr1 = float(grid[j]), float(ssv[j])
    X1 = np.column_stack([Xg[j], C])
    beta = m.ols(X1, yd)[1]
    e = yd - X1 @ beta
    se = m.cluster_se(X1, e, ids)
    n, k = X1.shape
    F = (ssr0 - ssr1) / (ssr1 / (n - k))
    lr = (ssv - ssr1) / (ssr1 / (n - k))
    ci = grid[lr <= 7.35]
    ci_lo, ci_hi = (float(ci.min()), float(ci.max())) if len(ci) else (np.nan, np.nan)

    rng = np.random.default_rng(20261031)
    fitted = X0 @ b0
    resid = yd - fitted
    prov = d["province"].values
    ups = np.unique(prov)
    Fstar = np.empty(500)
    for r in range(500):
        signs = pd.Series(rng.choice([-1.0, 1.0], size=len(ups)), index=ups)
        ystar = pd.Series(fitted + resid * signs.loc[prov].values)
        yd_star = m.demean(ystar, ids)
        s0, _ = m.ols(X0, yd_star)
        ss = np.array([m.ols(np.column_stack([X, C]), yd_star)[0] for X in Xg])
        Fstar[r] = (s0 - ss.min()) / (ss.min() / (n - k))
    pboot = float((Fstar >= F).mean())

    rows.append({"y": y, "x": x, "q": q, "gamma": gamma, "gamma_lo": ci_lo,
                 "gamma_hi": ci_hi, "beta_low": beta[0], "se_low": se[0],
                 "beta_high": beta[1], "se_high": se[1], "F": F,
                 "p_boot": pboot, "n_low": int((d[q] <= gamma).sum()),
                 "n_high": int((d[q] > gamma).sum())})
    print({k: (round(v, 4) if isinstance(v, float) else v)
           for k, v in rows[-1].items()})

out = pd.DataFrame(rows)
out.to_csv(ROOT / "output" / "tables" / "threshold_subdims.csv",
           index=False, encoding="utf-8-sig")
print("saved")
