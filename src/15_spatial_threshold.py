# -*- coding: utf-8 -*-
"""Threshold model with spatial controls.

Specifications
--------------
none  baseline Hansen threshold (province FE)
slx   + W*DFA (spatial lag of the regressor); reported only as a transparency
      check because own DFA and W*DFA are correlated at 0.979 after the
      within transformation, so the two coefficients are not separately
      identified
sem   spatial error model: u = lambda W u + e, estimated by ML
sar   spatial autoregressive model: rho W RCD, estimated by ML

W is the row-standardised rook contiguity matrix from 14_*, for the 30
provinces in the estimation sample. The threshold test for the SEM and SAR
specifications is a cluster wild bootstrap conditional on the estimated
spatial parameter.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SPAT = ROOT / "output" / "spatial"
TAB = ROOT / "output" / "tables"

CONTROLS = ["gov", "ln_fdi", "ln_dens", "private"]
Q = "ln_pgdp"


# ---------------------------------------------------------------- helpers
def demean(a, ids):
    s = pd.Series(np.asarray(a, dtype=float))
    return (s - s.groupby(ids.values).transform("mean")).values


def ssr_fit(X, y):
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    e = y - X @ b
    return float(e @ e), b


def w_apply(vec, W, T, N):
    return (W @ np.asarray(vec, dtype=float).reshape(T, N).T).T.reshape(-1)


def spatial_filter(vec, par, W, T, N):
    """(I - par*W) vec, applied within each year."""
    m = np.asarray(vec, dtype=float).reshape(T, N)
    return (m - par * (m @ W.T)).reshape(-1)


def build(d, gamma, ids):
    i = (d[Q].values <= gamma).astype(float)
    cols = [demean(d["dfa"].values * i, ids),
            demean(d["dfa"].values * (1 - i), ids)]
    cols += [demean(d[c].values, ids) for c in CONTROLS]
    return np.column_stack(cols)


def build_null(d, ids):
    return np.column_stack([demean(d["dfa"].values, ids)] +
                           [demean(d[c].values, ids) for c in CONTROLS])


def search(d, y, grid, ids, Xfun=build):
    best = (np.inf, None, None)
    for g in grid:
        s, b = ssr_fit(Xfun(d, g, ids), y)
        if s < best[0]:
            best = (s, g, b)
    return best


def cluster_se(d, y, X):
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    e = y - X @ b
    prov = d["province"].values
    ups = np.unique(prov)
    n, k = X.shape
    XtX_inv = np.linalg.pinv(X.T @ X)
    meat = np.zeros((k, k))
    for p in ups:
        m = prov == p
        score = X[m].T @ e[m]
        meat += np.outer(score, score)
    adj = len(ups) / (len(ups) - 1) * (n - 1) / (n - k)
    V = XtX_inv @ meat @ XtX_inv * adj
    return b, np.sqrt(np.diag(V))


def wild_bootstrap(d, y, grid, ids, F, Xfun=build, Nfun=build_null,
                   reps=300, seed=20261031):
    rng = np.random.default_rng(seed)
    X0 = Nfun(d, ids)
    ssr0, b0 = ssr_fit(X0, y)
    fitted, resid = X0 @ b0, y - X0 @ b0
    dfree = len(d) - (X0.shape[1] + 1) - 1
    ups = d["province"].unique()
    Fstar = np.empty(reps)
    for r in range(reps):
        signs = pd.Series(rng.choice([-1.0, 1.0], size=len(ups)), index=ups)
        ys = demean(fitted + resid * signs.loc[d["province"].values].values, ids)
        s0, _ = ssr_fit(X0, ys)
        s1, _, _ = search(d, ys, grid, ids, Xfun)
        Fstar[r] = (s0 - s1) / (s1 / dfree)
    return float((Fstar >= F).mean())


# --------------------------------------------------- spatial ML searches
def ml_search(d, y_raw, par_grid, gamma_grid, ids, W, T, N, kind):
    """Profile ML over the spatial parameter and the threshold."""
    lam = np.linalg.eigvals(W).real
    if kind == "sar":
        fit = w_apply(y_raw, W, T, N)
    best = (-np.inf, None, None, None)
    for par in par_grid:
        jac = 1.0 - par * lam
        if np.any(jac <= 1e-8):
            continue
        logdet = T * np.sum(np.log(jac))
        if kind == "sem":
            yf = spatial_filter(y_raw, par, W, T, N)
        else:
            yf = y_raw - par * fit
        yy = demean(yf, ids)
        for g in gamma_grid:
            if kind == "sem":
                X = np.column_stack([
                    demean(spatial_filter(d["dfa"].values * (d[Q].values <= g), par, W, T, N), ids),
                    demean(spatial_filter(d["dfa"].values * (d[Q].values > g), par, W, T, N), ids),
                ] + [demean(spatial_filter(d[c].values, par, W, T, N), ids)
                     for c in CONTROLS])
                N0 = np.column_stack([
                    demean(spatial_filter(d["dfa"].values, par, W, T, N), ids)] +
                    [demean(spatial_filter(d[c].values, par, W, T, N), ids)
                     for c in CONTROLS])
            else:
                X = build(d, g, ids)
                N0 = build_null(d, ids)
            s, b = ssr_fit(X, yy)
            if s <= 0:
                continue
            ll = -len(d) / 2 * np.log(s) + logdet
            if ll > best[0]:
                best = (ll, g, par, yy)
    return best


def sem_design(par, W, T, N):
    """Filtered design matrices for the spatial error model at a fixed lambda."""
    def bf(dd, g, idn):
        cols = [demean(spatial_filter(dd["dfa"].values * (dd[Q].values <= g),
                                      par, W, T, N), idn),
                demean(spatial_filter(dd["dfa"].values * (dd[Q].values > g),
                                      par, W, T, N), idn)]
        cols += [demean(spatial_filter(dd[c].values, par, W, T, N), idn)
                 for c in CONTROLS]
        return np.column_stack(cols)

    def nf(dd, idn):
        cols = [demean(spatial_filter(dd["dfa"].values, par, W, T, N), idn)]
        cols += [demean(spatial_filter(dd[c].values, par, W, T, N), idn)
                 for c in CONTROLS]
        return np.column_stack(cols)

    return bf, nf


def main() -> None:
    panel = pd.read_csv(DATA / "analysis_panel.csv")
    order = pd.read_csv(SPAT / "provinces.csv", header=None)[0].tolist()
    W = np.load(SPAT / "W_rook.npy")

    panel["pi"] = panel["province"].map({p: i for i, p in enumerate(order)})
    panel = panel.sort_values(["year", "pi"]).reset_index(drop=True)
    T, N = panel["year"].nunique(), len(order)
    panel["w_dfa"] = w_apply(panel["dfa"].values, W, T, N)

    d = panel
    ids = d["province"]
    y = demean(d["rcd"].values, ids)
    grid = np.quantile(d[Q], np.linspace(0.10, 0.90, 80))

    within_corr = np.corrcoef(demean(d["dfa"].values, ids),
                              demean(d["w_dfa"].values, ids))[0, 1]
    print(f"within correlation between DFA and W*DFA: {within_corr:.3f}")

    rows = []

    # (1) baseline
    X0 = build_null(d, ids)
    ssr0, _ = ssr_fit(X0, y)
    ssr1, g0, _ = search(d, y, grid, ids)
    dfree = len(d) - (X0.shape[1] + 1) - 1
    F0 = (ssr0 - ssr1) / (ssr1 / dfree)
    p0 = wild_bootstrap(d, y, grid, ids, F0)
    bh, seh = cluster_se(d, y, build(d, g0, ids))
    rows.append({"model": "baseline", "gamma": g0, "spatial_par": np.nan,
                 "F": F0, "p_boot": p0, "beta_low": bh[0], "se_low": seh[0],
                 "beta_high": bh[1], "se_high": seh[1], "n": len(d)})
    print(f"[baseline] gamma={g0:.3f} F={F0:.2f} p={p0:.3f} "
          f"low={bh[0]:.3f}({seh[0]:.3f}) high={bh[1]:.3f}({seh[1]:.3f})")

    # (2) SLX transparency check
    def build_lag(dd, g, idn):
        return np.column_stack([build(dd, g, idn),
                                demean(dd["w_dfa"].values, idn)])

    def null_lag(dd, idn):
        return np.column_stack([demean(dd["dfa"].values, idn),
                                demean(dd["w_dfa"].values, idn)] +
                               [demean(dd[c].values, idn) for c in CONTROLS])

    N0l = null_lag(d, ids)
    ssr0l, _ = ssr_fit(N0l, y)
    ssr1l, gl, _ = search(d, y, grid, ids, build_lag)
    dfreel = len(d) - (N0l.shape[1] + 1) - 1
    Fl = (ssr0l - ssr1l) / (ssr1l / dfreel)
    pl = wild_bootstrap(d, y, grid, ids, Fl, build_lag, null_lag)
    bl, sel = cluster_se(d, y, build_lag(d, gl, ids))
    rows.append({"model": "slx", "gamma": gl, "spatial_par": np.nan,
                 "F": Fl, "p_boot": pl, "beta_low": bl[0], "se_low": sel[0],
                 "beta_high": bl[1], "se_high": sel[1], "n": len(d),
                 "w_dfa": bl[2 + len(CONTROLS)],
                 "se_w_dfa": sel[2 + len(CONTROLS)]})
    print(f"[slx] gamma={gl:.3f} p={pl:.3f} low={bl[0]:.3f}({sel[0]:.3f}) "
          f"high={bl[1]:.3f}({sel[1]:.3f}) "
          f"w_dfa={bl[2 + len(CONTROLS)]:.3f}({sel[2 + len(CONTROLS)]:.3f})")

    # (3) SEM and (4) SAR
    par_grid = np.round(np.arange(-0.60, 0.901, 0.02), 3)
    for kind in ("sem", "sar"):
        ll, gk, pk, yk = ml_search(d, d["rcd"].values, par_grid, grid, ids,
                                   W, T, N, kind)
        if kind == "sem":
            bf, nf = sem_design(pk, W, T, N)
        else:
            bf, nf = build, build_null
        N0 = nf(d, ids)
        ssk1, _ = ssr_fit(bf(d, gk, ids), yk)
        ssk0, _ = ssr_fit(N0, yk)
        dfreek = len(d) - (N0.shape[1] + 1) - 1
        Fk = (ssk0 - ssk1) / (ssk1 / dfreek)
        pk_boot = wild_bootstrap(d, yk, grid, ids, Fk, bf, nf)
        bkk, sekk = cluster_se(d, yk, bf(d, gk, ids))
        rows.append({"model": kind, "gamma": gk, "spatial_par": pk,
                     "F": Fk, "p_boot": pk_boot,
                     "beta_low": bkk[0], "se_low": sekk[0],
                     "beta_high": bkk[1], "se_high": sekk[1], "n": len(d)})
        print(f"[{kind}] gamma={gk:.3f} par={pk:.3f} F={Fk:.2f} "
              f"p={pk_boot:.3f} low={bkk[0]:.3f}({sekk[0]:.3f}) "
              f"high={bkk[1]:.3f}({sekk[1]:.3f})")

    sar = [r for r in rows if r["model"] == "sar"][0]
    rho = sar["spatial_par"]
    Mmat = np.linalg.inv(np.eye(N) - rho * W)
    direct = np.trace(Mmat) / N
    total = 1.0 / (1.0 - rho)
    for regime, beta in (("low", sar["beta_low"]), ("high", sar["beta_high"])):
        print(f"  SAR {regime}: direct={beta * direct:.3f} "
              f"indirect={beta * (total - direct):.3f} total={beta * total:.3f}")

    pd.DataFrame(rows).to_csv(TAB / "table_spatial_threshold.csv",
                              index=False, encoding="utf-8-sig")
    print("within corr dfa/w_dfa:", round(within_corr, 3))


if __name__ == "__main__":
    main()
