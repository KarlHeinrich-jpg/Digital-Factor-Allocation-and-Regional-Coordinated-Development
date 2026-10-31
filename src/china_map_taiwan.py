# -*- coding: utf-8 -*-
"""China provincial choropleth in the style of the Systems 2026 paper.

The layout is a 2 x 2 grid of maps.  Each panel carries

* an italic bold ``<year> EPI Value`` title,
* a five-class green-yellow-orange-red legend,
* a north arrow,
* a 0/170/340 Miles scale bar,
* a South China Sea inset built from Hainan's island polygons.

Usage
-----
    python china_map.py --data assets/data/epi_panel.csv \
        --out assets/previews/fig06_china_epi_4panel.png \
        --years 2003 2010 2015 2020 --value epi --label EPI

The input CSV must contain ``province, year, <value>``.  Province names may be
short (北京) or full (北京市); both are normalised automatically.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Circle, Polygon, Rectangle
from shapely import make_valid
from shapely.geometry import box, Polygon as ShapelyPolygon

from paper_style import (
    BLUE_SEQ, GREEN_SEQ, MAP_BREAKS, MAP_COLORS, MAP_LABELS, apply_style,
    normalize_province, save_figure,
)

HERE = Path(__file__).resolve().parent
ASSETS = Path(r"C:/Users/93529/.agents/skills/yile-paper-style/assets")
GEO_PATH = ASSETS / "geo" / "china_provinces.geojson"
TAIWAN_PATH = HERE / "taiwan_province.geojson"

ALBERS = ("+proj=aea +lat_1=25 +lat_2=47 +lat_0=0 +lon_0=105 "
          "+datum=WGS84 +units=m +no_defs")
MAIN_BOX = (73.0, 17.5, 135.0, 54.0)  # lon/lat clipping for the main map
BORDER = "#4D4D4D"

# Ready-made palettes for the other map figures in the portfolio.
PALETTES = {
    "default": (MAP_COLORS, MAP_BREAKS, MAP_LABELS),
    "blue": (
        ["#DEEBF7", "#9ECAE1", "#4292C6", "#2171B5", "#08306B"],
        [0.0, 0.20, 0.30, 0.40, 0.50, 0.80],
        ["0.00 — 0.20", "0.21 — 0.30", "0.31 — 0.40",
         "0.41 — 0.50", "0.51 — 0.80"],
    ),
    "green": (
        ["#E5F5E0", "#A1D99B", "#41AB5D", "#238B45", "#00441B"],
        [0.0, 0.30, 0.40, 0.50, 0.60, 0.70],
        ["0.00 — 0.30", "0.31 — 0.40", "0.41 — 0.50",
         "0.51 — 0.60", "0.61 — 0.70"],
    ),
}


def _load_geo() -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """Return (main map, full Hainan for inset, Taiwan coastline)."""
    gdf = gpd.read_file(GEO_PATH)
    gdf["province"] = gdf["name"].map(normalize_province)
    if gdf.crs is None:
        gdf = gdf.set_crs(4326)
    else:
        gdf = gdf.to_crs(4326)
    gdf["geometry"] = make_valid(gdf.geometry.values)

    full = gdf.copy()
    hainan = full[full["province"] == "海南省"].copy()

    main = gdf.copy()
    main["geometry"] = main.geometry.intersection(box(*MAIN_BOX))
    main = main[~main.geometry.is_empty].copy()
    main = main.to_crs(ALBERS)

    taiwan = gpd.read_file(TAIWAN_PATH)
    if taiwan.crs is None:
        taiwan = taiwan.set_crs(4326)
    else:
        taiwan = taiwan.to_crs(4326)
    # keep only the Taiwan ring (the clipped file also contains a Fujian segment)
    taiwan = taiwan.to_crs(ALBERS)
    return main, hainan, taiwan


def _class_index(value: float, breaks=None, n_colors: int | None = None) -> int | None:
    if pd.isna(value):
        return None
    brks = list(breaks) if breaks is not None else MAP_BREAKS
    n = n_colors if n_colors is not None else len(MAP_COLORS)
    for i in range(n):
        if value <= brks[i + 1]:
            return i
    return n - 1


def _draw_legend(ax: plt.Axes, colors=None, labels=None, title: str = "EPI",
                 x: float = 0.018, y: float = 0.025,
                 width: float = 0.135, height: float = 0.040,
                 gap: float = 0.008, fontsize: float = 8.2) -> None:
    """Multi-row legend drawn in axes coordinates (top row = lowest class)."""
    colors = list(colors) if colors is not None else MAP_COLORS
    labels = list(labels) if labels is not None else MAP_LABELS
    top = y + (len(colors) - 1) * (height + gap)
    ax.text(x, top + height + 0.015, title, transform=ax.transAxes,
            fontsize=fontsize + 1.2, fontstyle="italic", fontweight="bold",
            ha="left", va="bottom", zorder=30, clip_on=False)
    for i, (color, label) in enumerate(zip(colors, labels)):
        yy = top - i * (height + gap)
        ax.add_patch(Rectangle((x, yy), width, height,
                               transform=ax.transAxes, facecolor=color,
                               edgecolor="#333333", linewidth=0.55,
                               zorder=30, clip_on=False))
        ax.text(x + width + 0.012, yy + height / 2, label,
                transform=ax.transAxes, fontsize=fontsize, fontweight="bold",
                ha="left", va="center", zorder=30, clip_on=False)


def _draw_north_arrow(ax: plt.Axes, x: float = 0.955, y: float = 0.925,
                      r: float = 0.032) -> None:
    """Four-point compass rose with N/E/S/W letters."""
    tr = ax.transAxes
    ax.add_patch(Circle((x, y), r * 0.95, transform=tr, facecolor="white",
                        edgecolor="black", linewidth=0.8, zorder=25,
                        clip_on=False))
    for angle, face in [(90, "black"), (270, "black"), (0, "white"),
                        (180, "white")]:
        a = np.deg2rad(angle)
        tip = (x + r * 1.45 * np.cos(a), y + r * 1.45 * np.sin(a))
        left = (x + r * 0.42 * np.cos(a + np.pi / 2),
                y + r * 0.42 * np.sin(a + np.pi / 2))
        right = (x + r * 0.42 * np.cos(a - np.pi / 2),
                 y + r * 0.42 * np.sin(a - np.pi / 2))
        ax.add_patch(Polygon([left, tip, right], closed=True, transform=tr,
                             facecolor=face, edgecolor="black", linewidth=0.6,
                             zorder=26, clip_on=False))
    for ang, txt in [(90, "N"), (270, "S"), (0, "E"), (180, "W")]:
        a = np.deg2rad(ang)
        ax.text(x + r * 2.0 * np.cos(a), y + r * 2.0 * np.sin(a), txt,
                transform=tr, ha="center", va="center", fontsize=7.5,
                fontweight="bold", zorder=27, clip_on=False)


def _draw_scale_bar(ax: plt.Axes, miles: int = 340,
                    x_frac: float = 0.50, y_frac: float = 0.055,
                    fontsize: float = 7.6) -> None:
    """Scale bar whose length is computed in projected metres."""
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    length_m = miles * 1609.344
    x0 = xmin + x_frac * (xmax - xmin)
    y0 = ymin + y_frac * (ymax - ymin)
    x1 = x0 + length_m
    ax.plot([x0, x1], [y0, y0], color="black", linewidth=1.0, zorder=22,
            solid_capstyle="butt")
    labels = [(0, "0", "left"), (0.5, f"{miles // 2}", "center"),
              (1, f"{miles} Miles", "left")]
    for frac, txt, ha in labels:
        xx = x0 + frac * (x1 - x0)
        ax.plot([xx, xx], [y0, y0 + (ymax - ymin) * 0.012],
                color="black", linewidth=1.0, zorder=22)
        ax.text(xx, y0 + (ymax - ymin) * 0.019, txt, ha=ha, va="bottom",
                fontsize=fontsize, fontweight="bold", zorder=22)


def _draw_inset(ax: plt.Axes, hainan: gpd.GeoDataFrame, colors=None,
                fontsize: float = 6.5) -> None:
    """South China Sea inset with Hainan's islands and a dashed boundary."""
    colors = list(colors) if colors is not None else MAP_COLORS
    inset = ax.inset_axes([0.805, 0.005, 0.175, 0.205])
    hainan.plot(ax=inset, facecolor=colors[min(1, len(colors) - 1)], edgecolor="#333333",
                linewidth=0.25, zorder=2)
    # Simplified nine-dash-line geometry; replace with an official boundary
    # file if the target journal requires a surveyed maritime boundary.
    segments = [
        [(108.7, 18.3), (109.5, 17.2)],
        [(109.8, 15.5), (110.7, 12.8)],
        [(110.9, 10.5), (111.8, 7.5)],
        [(112.5, 5.2), (114.5, 4.2)],
        [(115.5, 3.9), (117.5, 4.2)],
        [(118.5, 4.8), (119.8, 6.2)],
        [(120.3, 7.8), (121.2, 10.0)],
        [(121.6, 12.5), (122.0, 14.5)],
        [(122.0, 16.5), (121.5, 18.5)],
    ]
    for seg in segments:
        xs, ys = zip(*seg)
        inset.plot(xs, ys, color="black", linewidth=0.55,
                   linestyle=(0, (3, 2)), zorder=3)
    inset.set_xlim(105, 123)
    inset.set_ylim(2, 24)
    inset.set_aspect("equal")
    inset.set_xticks([])
    inset.set_yticks([])
    inset.set_xlabel("")
    inset.set_ylabel("")
    for spine in inset.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(0.8)
        spine.set_color("black")



def plot_china_panels(
    data: pd.DataFrame,
    years: list[int],
    out_path: str | Path,
    value_col: str = "epi",
    legend_title: str = "EPI",
    title_suffix: str = "EPI Value",
    ncols: int = 2,
    figsize: tuple[float, float] | None = None,
    palette=None, breaks=None, labels=None,
) -> plt.Figure:
    """Draw the China map grid and return the matplotlib figure.

    ``palette``/``breaks``/``labels`` override the default EPI five-class ramp;
    use ``PALETTES["blue"]`` or ``PALETTES["green"]`` for DEI/CEI figures.
    """
    apply_style(base=10)
    colors = list(palette) if palette is not None else MAP_COLORS
    brks = list(breaks) if breaks is not None else MAP_BREAKS
    labs = list(labels) if labels is not None else MAP_LABELS
    if len(colors) != len(brks) - 1 or len(labs) != len(colors):
        raise ValueError("Need len(colors) == len(breaks)-1 and len(labels)==len(colors)")
    df = data.copy()
    df["province"] = df["province"].map(normalize_province)
    main, hainan, taiwan = _load_geo()
    union = main.dissolve().geometry.iloc[0]

    nrows = int(np.ceil(len(years) / ncols))
    if figsize is None:
        figsize = (6.15 * ncols, 5.0 * nrows)
    fig, axes = plt.subplots(nrows, ncols, figsize=figsize, dpi=300)
    axes = np.atleast_1d(axes).ravel()

    for ax, year in zip(axes, years):
        sub = df[df["year"] == year][["province", value_col]]
        merged = main.merge(sub, on="province", how="left")
        merged["_class"] = merged[value_col].map(
            lambda v: _class_index(v, brks, len(colors)))
        merged["_face"] = merged["_class"].map(
            lambda i: colors[int(i)] if pd.notna(i) else "#FFFFFF")

        # light halo outside the national boundary
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

        ax.text(0.5, 1.005, f"{year} {title_suffix}", transform=ax.transAxes,
                ha="center", va="bottom", fontsize=18, fontstyle="italic",
                fontweight="bold", clip_on=False)
        _draw_legend(ax, colors=colors, labels=labs, title=legend_title)
        _draw_north_arrow(ax)
        _draw_scale_bar(ax)
        _draw_inset(ax, hainan, colors=colors)

    for ax in axes[len(years):]:
        ax.axis("off")

    fig.subplots_adjust(left=0.005, right=0.995, top=0.975, bottom=0.01,
                        wspace=0.01, hspace=0.18)
    save_figure(fig, out_path)
    return fig


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, help="CSV with province, year, value")
    parser.add_argument("--out", required=True, help="output PNG path")
    parser.add_argument("--years", nargs="+", type=int, default=[2003, 2010, 2015, 2020])
    parser.add_argument("--value", default="epi")
    parser.add_argument("--label", default="EPI")
    parser.add_argument("--suffix", default="EPI Value")
    parser.add_argument("--palette", choices=list(PALETTES), default="default")
    args = parser.parse_args()
    data = pd.read_csv(args.data)
    colors, breaks, labels = PALETTES[args.palette]
    plot_china_panels(data, args.years, args.out, value_col=args.value,
                      legend_title=args.label, title_suffix=args.suffix,
                      palette=colors, breaks=breaks, labels=labels)


if __name__ == "__main__":
    main()
