# -*- coding: utf-8 -*-
"""Generate the two-panel China maps used in Figure 2.

The map engine is a local copy of the yile-paper-style `china_map.py` with a
Taiwan polygon added (`src/taiwan_province.geojson`) and the South China Sea
inset moved so that it does not cover Taiwan. Taiwan is filled in light gray
because it is not in the estimation sample; Tibet is white for the same reason.

Run from the project root:
    python src/08b_maps.py
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SKILL_SCRIPTS = Path(r"C:/Users/93529/.agents/skills/yile-paper-style/scripts")
sys.path.insert(0, str(SKILL_SCRIPTS))
sys.path.insert(0, str(ROOT / "src"))

from china_map_taiwan import PALETTES, plot_china_panels  # noqa: E402


def main() -> None:
    panel = pd.read_csv(ROOT / "data" / "analysis_panel.csv")
    years = [2013, 2021]
    map_data = panel[panel["year"].isin(years)][
        ["province", "year", "dfa", "rcd"]
    ].copy()
    map_data.to_csv(ROOT / "output" / "figures" / "map_data.csv",
                    index=False, encoding="utf-8-sig")

    out = ROOT / "output" / "figures"

    colors, _, _ = PALETTES["blue"]
    breaks = [0, 0.12, 0.20, 0.28, 0.40, 1.01]
    labels = ["<0.12", "0.12-0.20", "0.20-0.28", "0.28-0.40", ">0.40"]
    fig = plot_china_panels(
        map_data, years, out / "fig2a_dfa_map_2p.png",
        value_col="dfa", legend_title="DFA", title_suffix="DFA",
        ncols=2, figsize=(10.5, 5.0),
        palette=colors, breaks=breaks, labels=labels,
    )
    fig.savefig(out / "fig2a_dfa_map_2p.pdf", bbox_inches="tight")
    plt.close(fig)

    colors, _, _ = PALETTES["green"]
    breaks = [0, 0.20, 0.28, 0.35, 0.45, 0.90]
    labels = ["<0.20", "0.20-0.28", "0.28-0.35", "0.35-0.45", ">0.45"]
    fig = plot_china_panels(
        map_data, years, out / "fig2b_rcd_map_2p.png",
        value_col="rcd", legend_title="RCD", title_suffix="RCD",
        ncols=2, figsize=(10.5, 5.0),
        palette=colors, breaks=breaks, labels=labels,
    )
    fig.savefig(out / "fig2b_rcd_map_2p.pdf", bbox_inches="tight")
    plt.close(fig)

    for name in ["fig2a_dfa_map_2p.pdf", "fig2a_dfa_map_2p.png",
                 "fig2b_rcd_map_2p.pdf", "fig2b_rcd_map_2p.png"]:
        shutil.copy2(out / name, ROOT / "paper" / "figures" / name)

    print("maps written to", out, "and copied to paper/figures")


if __name__ == "__main__":
    main()
