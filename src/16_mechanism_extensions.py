# -*- coding: utf-8 -*-
"""Mechanism extensions: moderation, sub-dimension decomposition, and
regime-specific mediation.

Outputs
-------
output/tables/table_interaction.csv
output/tables/table_subdimensions.csv
output/tables/table_regime_mediation.csv
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from linearmodels.panel import PanelOLS

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
TAB = ROOT / "output" / "tables"

CONTROLS = ["gov", "ln_fdi", "ln_dens", "private"]
DIMS = {
    "digital infrastructure": "Infrastructure",
    "digital industry": "Industry",
    "digital finance": "Finance",
    "digital human capital": "Human capital",
}
MEDIATORS = {"tech": "Technological investment",
             "fin_dev": "Financial development",
             "ind_struct": "Industrial upgrading"}
GAMMA = 10.5893


def load() -> pd.DataFrame:
    df = pd.read_csv(DATA / "analysis_panel.csv")
    for d in DIMS:
        v = df[f"dfa_dim_{d}"]
        df[f"sub_{DIMS[d]}"] = (v - v.min()) / (v.max() - v.min())
    return df


def fe(df, y, xs, twoway=True):
    d = df.dropna(subset=[y] + xs).set_index(["province", "year"])
    mod = PanelOLS(d[y], d[xs], entity_effects=True, time_effects=twoway,
                   drop_absorbed=True)
    return mod.fit(cov_type="clustered", cluster_entity=True)


def row(res, var):
    return {"coef": float(res.params[var]), "se": float(res.std_errors[var]),
            "p": float(res.pvalues[var])}


# ------------------------------------------------------------ moderation
def interactions(df):
    out = []
    for mod in ["ln_pgdp", "fin_dev"]:
        d = df.copy()
        d["mod_c"] = d[mod] - d[mod].mean()
        d["dfa_x_mod"] = d["dfa"] * d["mod_c"]
        res = fe(d, "rcd", ["dfa", "dfa_x_mod", "mod_c"] + CONTROLS)
        out.append({"moderator": mod, "term": "dfa", **row(res, "dfa")})
        out.append({"moderator": mod, "term": "dfa_x_moderator",
                    **row(res, "dfa_x_mod")})
        for q in (0.25, 0.50, 0.75):
            v = np.quantile(d[mod], q)
            me = res.params["dfa"] + res.params["dfa_x_mod"] * (v - d[mod].mean())
            se = np.sqrt(
                res.cov.loc["dfa", "dfa"]
                + (v - d[mod].mean()) ** 2 * res.cov.loc["dfa_x_mod", "dfa_x_mod"]
                + 2 * (v - d[mod].mean()) * res.cov.loc["dfa", "dfa_x_mod"])
            out.append({"moderator": mod, "term": f"marginal_effect_p{int(q*100)}",
                        "coef": float(me), "se": float(se),
                        "p": float(2 * (1 - __import__("scipy").stats.norm.cdf(
                            abs(me / se))))})
    out = pd.DataFrame(out)
    out.to_csv(TAB / "table_interaction.csv", index=False, encoding="utf-8-sig")
    print(out.round(3).to_string(index=False))


# -------------------------------------------------------- sub-dimensions
def _demean(a, ids):
    s = pd.Series(np.asarray(a, dtype=float))
    return (s - s.groupby(ids.values).transform("mean")).values


def _ssr(X, y):
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    e = y - X @ b
    return float(e @ e), b


def _threshold(df, x, q="ln_pgdp", reps=200, seed=20261101):
    """Hansen threshold test for a single regressor, province FE."""
    d = df.dropna(subset=[x, q, "rcd"] + CONTROLS).reset_index(drop=True)
    ids = d["province"]
    y = _demean(d["rcd"], ids)

    def design(g):
        i = (d[q].values <= g).astype(float)
        return np.column_stack([_demean(d[x].values * i, ids),
                                _demean(d[x].values * (1 - i), ids)] +
                               [_demean(d[c], ids) for c in CONTROLS])

    def null():
        return np.column_stack([_demean(d[x], ids)] +
                               [_demean(d[c], ids) for c in CONTROLS])

    grid = np.quantile(d[q], np.linspace(0.10, 0.90, 60))
    X0 = null()
    ssr0, b0 = _ssr(X0, y)
    best = (np.inf, None)
    for g in grid:
        s, _ = _ssr(design(g), y)
        if s < best[0]:
            best = (s, g)
    ssr1, gamma = best
    dfree = len(d) - (X0.shape[1] + 1) - 1
    F = (ssr0 - ssr1) / (ssr1 / dfree)

    rng = np.random.default_rng(seed)
    fitted, resid = X0 @ b0, y - X0 @ b0
    ups = d["province"].unique()
    Fstar = np.empty(reps)
    for r in range(reps):
        signs = pd.Series(rng.choice([-1.0, 1.0], size=len(ups)), index=ups)
        ys = _demean(fitted + resid * signs.loc[d["province"].values].values, ids)
        s0, _ = _ssr(X0, ys)
        bs = min(_ssr(design(g), ys)[0] for g in grid)
        Fstar[r] = (s0 - bs) / (bs / dfree)
    p = float((Fstar >= F).mean())
    X1 = design(gamma)
    beta = np.linalg.lstsq(X1, y, rcond=None)[0]
    return {"gamma": float(gamma), "F": float(F), "p_boot": p,
            "beta_low": float(beta[0]), "beta_high": float(beta[1])}


def subdimensions(df):
    subs = [f"sub_{v}" for v in DIMS.values()]
    out = []
    for s in subs:
        res = fe(df, "rcd", [s] + CONTROLS)
        out.append({"kind": "linear", "variable": s, **row(res, s)})
    res = fe(df, "rcd", subs + CONTROLS)
    for s in subs:
        out.append({"kind": "linear_joint", "variable": s, **row(res, s)})
    lin = pd.DataFrame(out)
    lin.to_csv(TAB / "table_subdimensions.csv", index=False,
               encoding="utf-8-sig")
    print(lin.round(3).to_string(index=False))

    thr = []
    for s in subs:
        r = _threshold(df, s)
        thr.append({"variable": s, **r})
        print(f"  threshold {s:14s} gamma={r['gamma']:.3f} F={r['F']:.2f} "
              f"p={r['p_boot']:.3f} low={r['beta_low']:.3f} "
              f"high={r['beta_high']:.3f}")
    pd.DataFrame(thr).to_csv(TAB / "table_subdimension_threshold.csv",
                             index=False, encoding="utf-8-sig")
    return subs


# -------------------------------------------------- regime mediation
def mediation(df, mediator):
    """Baron-Kenny style paths with a province bootstrap SE on a*b."""
    cols = ["dfa", mediator, "rcd"] + CONTROLS

    def fit_regime(sub):
        res_a = fe(sub, mediator, ["dfa"] + CONTROLS)
        res_b = fe(sub, "rcd", ["dfa", mediator] + CONTROLS)
        a = float(res_a.params["dfa"])
        b = float(res_b.params[mediator])
        c = float(res_b.params["dfa"])
        return a, b, c

    out = []
    for label, sub in (("low", df[df["ln_pgdp"] <= GAMMA]),
                       ("high", df[df["ln_pgdp"] > GAMMA])):
        a, b, c = fit_regime(sub)
        rng = np.random.default_rng(20261101)
        provs = sub["province"].unique()
        boot = []
        for _ in range(300):
            pick = rng.choice(provs, size=len(provs), replace=True)
            frames = []
            for i, p in enumerate(pick):
                tmp = sub[sub["province"] == p].copy()
                tmp["province"] = f"{p}_{i}"
                frames.append(tmp)
            rep = pd.concat(frames, ignore_index=True)
            try:
                aa, bb, _ = fit_regime(rep)
                boot.append(aa * bb)
            except Exception:
                continue
        if boot:
            lo, hi = np.percentile(np.array(boot), [2.5, 97.5])
        else:
            lo = hi = float("nan")
        out.append({"regime": label, "mediator": mediator, "n_prov": len(provs),
                    "n_obs": len(sub), "a": a, "b": b, "direct_c": c,
                    "indirect": a * b, "ci_lo": lo, "ci_hi": hi,
                    "n_boot": len(boot),
                    "sig": bool(boot and lo * hi > 0)})
        print(f"  {label:4s} {mediator:10s} n={len(sub):3d} a={a:8.4f} "
              f"b={b:8.5f} a*b={a*b:9.5f} CI=[{lo:.5f},{hi:.5f}] nb={len(boot)}")
    return out


def main() -> None:
    df = load()
    print("== interactions ==")
    interactions(df)
    print("\n== sub-dimensions ==")
    subs = subdimensions(df)
    print("\n== regime mediation ==")
    rows = []
    for m in MEDIATORS:
        rows += mediation(df, m)
    pd.DataFrame(rows).to_csv(TAB / "table_regime_mediation.csv",
                              index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
