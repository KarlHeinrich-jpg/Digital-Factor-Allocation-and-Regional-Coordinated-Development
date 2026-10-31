# -*- coding: utf-8 -*-
"""Spatial diagnostics: contiguity and distance weights, global Moran's I,
and local Moran (LISA) for DFA and RCD.

Outputs
-------
output/spatial/W_rook.npy          row-standardised rook weights (30 x 30)
output/spatial/provinces.csv       province order used by the weights
output/tables/table_moran.csv      global Moran's I by year, index, and W
output/tables/table_lisa_2021.csv  local Moran quadrants for 2021
output/figures/fig_lisa_map.*      LISA cluster map, DFA and RCD, 2013/2021
paper/tables/table8_moran.tex
"""
from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from esda.moran import Moran, Moran_Local
from libpysal.weights import Rook, W
from scipy.spatial.distance import cdist

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "output"
SPAT = OUT / "spatial"
SPAT.mkdir(parents=True, exist_ok=True)

SKILL = Path(r"C:/Users/93529/.agents/skills/yile-paper-style")
sys.path.insert(0, str(SKILL / "scripts"))
sys.path.insert(0, str(ROOT / "src"))
from paper_style import normalize_province  # noqa: E402

YEARS = list(range(2013, 2022))
PERM = 999


# --------------------------------------------------------------------------
# weights
# --------------------------------------------------------------------------
def _strip(name: str) -> str:
    for suf in ("维吾尔自治区", "壮族自治区", "回族自治区", "自治区", "省", "市"):
        if name.endswith(suf):
            return name[: -len(suf)]
    return name


def build_weights(provinces: list[str]) -> tuple[W, W]:
    geo = gpd.read_file(SKILL / "assets" / "geo" / "china_provinces.geojson")
    geo = geo.to_crs(4326)
    geo["province"] = geo["name"].map(_strip)
    geo = geo.set_index("province", drop=True)
    geo = geo.loc[[p for p in geo.index if p in set(provinces)]]

    rook = Rook.from_dataframe(geo, use_index=True)
    ids = {p: i for i, p in enumerate(geo.index)}
    mat = rook.sparse.tolil()
    # Hainan is an island and has no rook neighbour; the conventional fix in
    # China provincial studies is to link it to Guangdong.
    if "海南" in ids and "广东" in ids:
        i, j = ids["海南"], ids["广东"]
        mat[i, j] = 1
        mat[j, i] = 1
    mat = mat.tocsr()
    neighbors = {p: [geo.index[j] for j in mat[i].indices]
                 for i, p in enumerate(geo.index)}
    w_rook = W(neighbors, silence_warnings=True)
    w_rook.transform = "r"

    proj = geo.to_crs("+proj=aea +lat_1=25 +lat_2=47 +lat_0=0 +lon_0=105 "
                      "+datum=WGS84 +units=km +no_defs")
    coords = np.column_stack([proj.geometry.centroid.x, proj.geometry.centroid.y])
    d = cdist(coords, coords, metric="euclidean")
    np.fill_diagonal(d, np.inf)
    nb = {p: [geo.index[j] for j in np.nonzero(np.isfinite(d[i]))[0]]
          for i, p in enumerate(geo.index)}
    w_dist = W(nb, silence_warnings=True)
    for i, p in enumerate(geo.index):
        w_dist.weights[p] = [float(1.0 / d[i, geo.index.get_loc(q)] ** 2)
                             for q in nb[p]]
    w_dist.transform = "r"
    return w_rook, w_dist


# --------------------------------------------------------------------------
# analysis
# --------------------------------------------------------------------------
def global_moran(panel: pd.DataFrame, w: W, weight_name: str) -> pd.DataFrame:
    rows = []
    for var in ("dfa", "rcd"):
        for year in YEARS:
            s = panel[panel["year"] == year].set_index("province").loc[w.id_order, var]
            mi = Moran(s.values, w, permutations=PERM)
            rows.append({
                "index": var.upper(), "weight": weight_name, "year": year,
                "moran": mi.I, "ei": mi.EI, "sd": np.sqrt(mi.VI_norm),
                "z": mi.z_norm, "p": mi.p_norm, "p_sim": mi.p_sim,
            })
    return pd.DataFrame(rows)


def lisa(panel: pd.DataFrame, w: dict[str, W]) -> pd.DataFrame:
    rows = []
    for side, var in (("a", "dfa"), ("b", "rcd")):
        for year in (2013, 2021):
            s = panel[panel["year"] == year].set_index("province").loc[w["rook"].id_order, var]
            mi = Moran_Local(s.values, w["rook"], permutations=PERM)
            for p, q, pv in zip(w["rook"].id_order, mi.q, mi.p_sim):
                # q: 1 HH, 2 LH, 3 LL, 4 HL
                label = {1: "HH", 2: "LH", 3: "LL", 4: "HL"}[int(q)]
                rows.append({"index": var.upper(), "year": year,
                             "province": p, "quadrant": label,
                             "p_sim": float(pv),
                             "cluster": label if pv < 0.10 else "NS"})
    return pd.DataFrame(rows)


LISA_COLORS = {"HH": "#B2182B", "LL": "#2166AC", "LH": "#92C5DE",
               "HL": "#F4A582", "NS": "#EFEFEF"}


def lisa_map(ls: pd.DataFrame) -> None:
    """2 x 2 LISA cluster map: rows DFA/RCD, columns 2013/2021."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from china_map_taiwan import (_draw_inset, _draw_legend, _draw_north_arrow,
                                  _draw_scale_bar, _load_geo, BORDER)

    geo = gpd.read_file(SKILL / "assets" / "geo" / "china_provinces.geojson")
    full_of = {_strip(n): n for n in geo["name"]}

    main, hainan, taiwan = _load_geo()
    union = main.dissolve().geometry.iloc[0]

    fig, axes = plt.subplots(2, 2, figsize=(10.6, 9.4), dpi=300)
    panels = [("DFA", 2013), ("DFA", 2021), ("RCD", 2013), ("RCD", 2021)]
    for ax, (idx, year) in zip(axes.ravel(), panels):
        sub = ls[(ls["index"] == idx) & (ls["year"] == year)][
            ["province", "cluster"]].copy()
        sub["prov"] = sub["province"].map(full_of)
        merged = main.merge(sub[["prov", "cluster"]], left_on="province",
                            right_on="prov", how="left")
        merged["_face"] = merged["cluster"].map(LISA_COLORS).fillna("#FFFFFF")

        gpd.GeoSeries([union.buffer(14000)], crs=main.crs).plot(
            ax=ax, color="none", edgecolor="#D5D5D5", linewidth=1.4, zorder=1)
        merged.plot(ax=ax, color=merged["_face"], edgecolor=BORDER,
                    linewidth=0.55, zorder=2)
        gpd.GeoSeries([union], crs=main.crs).plot(
            ax=ax, color="none", edgecolor="black", linewidth=0.95, zorder=4)
        if len(taiwan):
            taiwan.plot(ax=ax, color="#D9D9D9", edgecolor=BORDER,
                        linewidth=0.55, zorder=3)

        minx, miny, maxx, maxy = main.total_bounds
        ax.set_xlim(minx - 0.01 * (maxx - minx), maxx + 0.08 * (maxx - minx))
        ax.set_ylim(miny - 0.16 * (maxy - miny), maxy + 0.06 * (maxy - miny))
        ax.set_aspect("equal")
        ax.axis("off")
        tag = "abcd"[panels.index((idx, year))]
        ax.text(0.5, 1.005, f"({tag}) {idx}, {year}", transform=ax.transAxes,
                ha="center", va="bottom", fontsize=15, fontstyle="italic",
                fontweight="bold", clip_on=False)
        _draw_north_arrow(ax, r=0.030)
        _draw_scale_bar(ax)
        _draw_inset(ax, hainan, colors=["#EFEFEF"])

    order = ["HH", "LL", "LH", "HL", "NS"]
    labels = ["High-High", "Low-Low", "Low-High", "High-Low", "Not significant"]
    from matplotlib.patches import Patch
    handles = [Patch(facecolor=LISA_COLORS[k], edgecolor="#333333",
                     linewidth=0.55) for k in order]
    fig.legend(handles, labels, loc="lower center", ncol=5, frameon=False,
               title="LISA cluster", title_fontsize=11, fontsize=10,
               bbox_to_anchor=(0.5, -0.005), handlelength=1.5,
               columnspacing=1.4)

    fig.subplots_adjust(left=0.005, right=0.995, top=0.965, bottom=0.075,
                        wspace=0.01, hspace=0.06)
    out = OUT / "figures" / "fig_lisa_map"
    fig.savefig(out.with_suffix(".png"), bbox_inches="tight", facecolor="white")
    fig.savefig(out.with_suffix(".pdf"), bbox_inches="tight", facecolor="white")
    plt.close(fig)
    for ext in (".png", ".pdf"):
        (ROOT / "paper" / "figures").mkdir(parents=True, exist_ok=True)
        import shutil
        shutil.copy2(out.with_suffix(ext), ROOT / "paper" / "figures" /
                     f"fig_lisa_map{ext}")
    print("LISA map written")


def latex_moran(m: pd.DataFrame) -> None:
    lines = [r"\begin{tabular}{llrrrrrrrrr}", r"\toprule",
             r"Index & W & \multicolumn{9}{c}{Global Moran's $I$ by year} \\",
             r"\cmidrule(lr){3-11}",
             r" & & " + " & ".join(str(y) for y in YEARS) + r" \\",
             r"\midrule"]
    names = {"rook": "Rook contiguity", "dist": "Inverse distance"}
    for idx in ("DFA", "RCD"):
        for wn in ("rook", "dist"):
            sub = m[(m["index"] == idx) & (m["weight"] == wn)].set_index("year")
            cells = []
            for y in YEARS:
                r = sub.loc[y]
                star = "***" if r["p_sim"] < 0.01 else "**" if r["p_sim"] < 0.05 \
                    else "*" if r["p_sim"] < 0.10 else ""
                cells.append(f"{r['moran']:.3f}{star}")
            lines.append(f"{idx} & {names[wn]} & " + " & ".join(cells) + r" \\")
        if idx == "DFA":
            lines.append(r"\midrule")
    lines += [r"\bottomrule", r"\end{tabular}"]
    (ROOT / "paper" / "tables" / "table8_moran.tex").write_text(
        "\n".join(lines), encoding="utf-8")


def main() -> None:
    panel = pd.read_csv(DATA / "analysis_panel.csv")
    provinces = sorted(panel["province"].unique(), key=lambda p: list(
        panel["province"].unique()).index(p))

    w_rook, w_dist = build_weights(provinces)
    print("rook neighbours:", {k: len(v) for k, v in w_rook.neighbors.items()})
    np.save(SPAT / "W_rook.npy", w_rook.full()[0])
    pd.Series(w_rook.id_order).to_csv(SPAT / "provinces.csv", index=False,
                                      header=False, encoding="utf-8-sig")

    m = pd.concat([global_moran(panel, w_rook, "rook"),
                   global_moran(panel, w_dist, "dist")])
    m.to_csv(OUT / "tables" / "table_moran.csv", index=False, encoding="utf-8-sig")
    print(m[m["year"].isin([2013, 2021])].to_string(index=False))
    latex_moran(m)

    ls = lisa(panel, {"rook": w_rook})
    ls.to_csv(OUT / "tables" / "table_lisa.csv", index=False, encoding="utf-8-sig")
    print(ls[ls["year"] == 2021].to_string(index=False))
    lisa_map(ls)


if __name__ == "__main__":
    main()
