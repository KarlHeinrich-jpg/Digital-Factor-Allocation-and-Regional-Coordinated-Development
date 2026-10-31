# -*- coding: utf-8 -*-
"""Endogeneity and specification checks that do not require external instruments.

1. Oster (2019) bounds: how strong would selection on unobservables have to be
   to drive the DFA coefficient to zero?
2. Randomisation inference for the threshold: permute DFA within year and
   compare the observed Hansen F statistic with its permutation distribution.

No external instrument is available for DFA (the panel contains no historical
telecommunications, terrain, or distance-to-backbone variables), so a proper
2SLS or Caner-Hansen IV threshold estimate cannot be constructed from these
data.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
TAB = ROOT / "output" / "tables"

CONTROLS = ["gov", "ln_fdi", "ln_dens", "private"]
EXTRA = ["tech", "ind_struct", "fin_dev"]
Q = "ln_pgdp"


def demean(a, ids):
    s = pd.Series(np.asarray(a, dtype=float))
    return (s - s.groupby(ids.values).transform("mean")).values


def ols_fe(d, y, xs, ids, year_fe=True):
    """Two-way (or province-only) FE by explicit demeaning."""
    Y = demean(d[y], ids)
    if year_fe:
        Y = pd.Series(Y) - pd.Series(Y).groupby(d["year"].values).transform("mean")
        Y = Y.values
    Xs = []
    for x in xs:
        v = demean(d[x], ids)
        if year_fe:
            v = (pd.Series(v) - pd.Series(v).groupby(d["year"].values)
                 .transform("mean")).values
        Xs.append(v)
    X = np.column_stack(Xs)
    b = np.linalg.lstsq(X, Y, rcond=None)[0]
    e = Y - X @ b
    ssr = float(e @ e)
    sst = float(((Y - Y.mean()) ** 2).sum())
    return b, 1 - ssr / sst, ssr, Y, X


def oster(short_beta, short_r2, long_beta, long_r2, rmax_delta=1.3):
    rmax = min(1.0, rmax_delta * long_r2)
    denom = long_r2 - short_r2
    beta_star = long_beta - (short_beta - long_beta) * (rmax - long_r2) / denom
    d_star = long_beta * denom / ((short_beta - long_beta) * (rmax - long_r2))
    return beta_star, d_star, rmax


def main() -> None:
    d = pd.read_csv(DATA / "analysis_panel.csv")
    ids = d["province"]

    # short: no controls; long: baseline controls; full: baseline + extra
    bs, r2s, *_ = ols_fe(d, "rcd", ["dfa"], ids)
    bl, r2l, *_ = ols_fe(d, "rcd", ["dfa"] + CONTROLS, ids)
    bf, r2f, *_ = ols_fe(d, "rcd", ["dfa"] + CONTROLS + EXTRA, ids)
    # province FE only (the threshold-model analogue)
    bp, r2p, *_ = ols_fe(d, "rcd", ["dfa"], ids, year_fe=False)
    bpf, r2pf, *_ = ols_fe(d, "rcd", ["dfa"] + CONTROLS, ids, year_fe=False)

    rows = []
    for label, b0, r0, b1, r1 in [
        ("two-way FE, controls", float(bs[0]), r2s, float(bl[0]), r2l),
        ("province FE, controls", float(bp[0]), r2p, float(bpf[0]), r2pf),
        ("two-way FE, controls + extra", float(bl[0]), r2l, float(bf[0]), r2f),
    ]:
        beta_star, d_star, rmax = oster(b0, r0, b1, r1)
        rows.append({"spec": label, "beta_short": b0, "r2_short": r0,
                     "beta_long": b1, "r2_long": r1, "r_max": rmax,
                     "beta_star": beta_star, "delta_star": d_star})
        print(f"{label:32s} short={b0:.3f}(R2={r0:.3f}) long={b1:.3f}"
              f"(R2={r1:.3f}) beta*={beta_star:.3f} delta*={d_star:.2f}")
    pd.DataFrame(rows).to_csv(TAB / "table_oster.csv", index=False,
                              encoding="utf-8-sig")

    # ------------------------------------------------ randomisation inference
    # Placebo: if the threshold reflects the true development ordering, then
    # randomly reassigning income levels across provinces within each year
    # should destroy it. DFA and RCD are left untouched, so the placebo does
    # not reintroduce the common national trend through the regressor.
    y = demean(d["rcd"], ids)
    grid = np.quantile(d[Q], np.linspace(0.10, 0.90, 60))

    def design(dd, g):
        i = (dd[Q].values <= g).astype(float)
        return np.column_stack([demean(dd["dfa"].values * i, ids),
                                demean(dd["dfa"].values * (1 - i), ids)] +
                               [demean(dd[c], ids) for c in CONTROLS])

    X0 = np.column_stack([demean(d["dfa"], ids)] +
                         [demean(d[c], ids) for c in CONTROLS])
    ssr0, _ = _ssr(X0, y)
    ssr1 = min(_ssr(design(d, g), y)[0] for g in grid)
    dfree = len(d) - (X0.shape[1] + 1) - 1
    F_obs = (ssr0 - ssr1) / (ssr1 / dfree)

    rng = np.random.default_rng(20261101)
    reps = 499
    Fp = np.empty(reps)
    gammas = np.empty(reps)
    d2 = d.copy()
    for r in range(reps):
        d2[Q] = (d2.groupby("year")[Q]
                 .transform(lambda s: rng.permutation(s.values)))
        best = (np.inf, None)
        for g in grid:
            s, _ = _ssr(design(d2, g), y)
            if s < best[0]:
                best = (s, g)
        Fp[r] = (ssr0 - best[0]) / (best[0] / dfree)
        gammas[r] = best[1]

    p_perm = float((Fp >= F_obs).mean())
    print(f"\nrandomisation inference: F_obs={F_obs:.2f}  "
          f"perm mean={Fp.mean():.2f}  p95={np.percentile(Fp, 95):.2f}  "
          f"p_perm={p_perm:.3f}")
    print(f"permuted gamma: median={np.median(gammas):.3f} "
          f"iqr=[{np.percentile(gammas, 25):.3f},"
          f"{np.percentile(gammas, 75):.3f}]")
    pd.DataFrame({"F": Fp, "gamma": gammas}).to_csv(
        TAB / "table_randomization.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame([{"F_obs": F_obs, "p_perm": p_perm,
                   "perm_mean": float(Fp.mean()),
                   "perm_p95": float(np.percentile(Fp, 95)),
                   "reps": reps}]).to_csv(
        TAB / "table_randomization_summary.csv", index=False,
        encoding="utf-8-sig")


def _ssr(X, y):
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    e = y - X @ b
    return float(e @ e), b


if __name__ == "__main__":
    main()
