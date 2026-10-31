# -*- coding: utf-8 -*-
"""Figure 2: six maps in a 3 x 2 grid, DFA on the left and RCD on the right,
for 2013, 2017, and 2021 (layout follows the reference paper's Figure 2).
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, r"C:/Users/93529/.agents/skills/yile-paper-style/scripts")
from china_map_taiwan import (  # noqa: E402
    BORDER, PALETTES, _draw_inset, _draw_legend, _draw_north_arrow,
    _draw_scale_bar, _load_geo,
)

DATA = ROOT / "data"
FIG = ROOT / "output" / "figures"
YEARS = [2013, 2017, 2021]
DFA_BREAKS = [0, 0.12, 0.20, 0.28, 0.40, 1.01]
DFA_LABELS = ["<0.12", "0.12-0.20", "0.20-0.28", "0.28-0.40", ">0.40"]
RCD_BREAKS = [0, 0.20, 0.28, 0.35, 0.45, 0.90]
RCD_LABELS = ["<0.20", "0.20-0.28", "0.28-0.35", "0.35-0.45", ">0.45"]
SPEC = {
    "DFA": ("dfa", PALETTES["blue"][0], DFA_BREAKS, DFA_LABELS),
    "RCD": ("rcd", PALETTES["green"][0], RCD_BREAKS, RCD_LABELS),
}


def short_name(full: str) -> str:
    for suf in ("维吾尔自治区", "壮族自治区", "回族自治区", "自治区", "省", "市"):
        if full.endswith(suf):
            return full[: -len(suf)]
    return full


def class_face(value, colors, breaks):
    if pd.isna(value):
        return "#FFFFFF"
    for i in range(len(colors)):
        if value <= breaks[i + 1]:
            return colors[i]
    return colors[-1]


def main() -> None:
    panel = pd.read_csv(DATA / "analysis_panel.csv")
    main_geo, hainan, taiwan = _load_geo()
    geo_names = gpd.read_file(
        r"C:/Users/93529/.agents/skills/yile-paper-style/assets/geo/china_provinces.geojson")["name"]
    full_of = {short_name(n): n for n in geo_names}
    union = main_geo.dissolve().geometry.iloc[0]

    fig, axes = plt.subplots(3, 2, figsize=(9.6, 12.8), dpi=300)
    tags = "abcdef"
    k = 0
    for row, year in enumerate(YEARS):
        for col, name in enumerate(["DFA", "RCD"]):
            var, colors, breaks, labels = SPEC[name]
            title = name
            ax = axes[row, col]
            sub = panel[panel["year"] == year][["province", var]].copy()
            sub["prov_full"] = sub["province"].map(full_of)
            merged = main_geo.merge(sub[["prov_full", var]], left_on="province",
                                    right_on="prov_full", how="left")
            merged["_face"] = merged[var].map(
                lambda v: class_face(v, colors, breaks))

            gpd.GeoSeries([union.buffer(14000)], crs=main_geo.crs).plot(
                ax=ax, color="none", edgecolor="#D5D5D5", linewidth=1.4, zorder=1)
            merged.plot(ax=ax, color=merged["_face"], edgecolor=BORDER,
                        linewidth=0.55, zorder=2)
            gpd.GeoSeries([union], crs=main_geo.crs).plot(
                ax=ax, color="none", edgecolor="black", linewidth=0.95, zorder=4)
            if len(taiwan):
                taiwan.plot(ax=ax, color="#D9D9D9", edgecolor=BORDER,
                            linewidth=0.55, zorder=3)

            minx, miny, maxx, maxy = main_geo.total_bounds
            ax.set_xlim(minx - 0.01 * (maxx - minx), maxx + 0.08 * (maxx - minx))
            ax.set_ylim(miny - 0.16 * (maxy - miny), maxy + 0.06 * (maxy - miny))
            ax.set_aspect("equal")
            ax.axis("off")
            ax.text(0.5, 1.005, f"({tags[k]}) {year} {title}",
                    transform=ax.transAxes, ha="center", va="bottom",
                    fontsize=15, fontstyle="italic", fontweight="bold",
                    clip_on=False)
            _draw_north_arrow(ax, r=0.030)
            _draw_scale_bar(ax)
            _draw_inset(ax, hainan, colors=colors)
            _draw_legend(ax, colors=colors, labels=labels, title=title,
                         width=0.115, height=0.030, gap=0.008, fontsize=10.0)
            k += 1

    fig.subplots_adjust(left=0.005, right=0.995, top=0.975, bottom=0.005,
                        wspace=0.01, hspace=0.115)
    out = FIG / "fig_maps_6"
    for ext in (".png", ".pdf"):
        fig.savefig(out.with_suffix(ext), bbox_inches="tight", facecolor="white")
        shutil.copy2(out.with_suffix(ext),
                     ROOT / "paper" / "figures" / f"fig_maps_6{ext}")
    plt.close(fig)
    print("six-panel map saved")


if __name__ == "__main__":
    main()
