# -*- coding: utf-8 -*-
"""OCR the provincial urban/rural income tables from China Statistical Yearbook
(2020 and 2022 editions) and assemble a province-year panel.

Tables
------
2020 edition: C0623_2020.jpg (urban, 2013-2019), C0629_2020.jpg (rural, 2013-2019)
2022 edition: C0624_2022.jpg (urban, 2015-2021), C0630_2022.jpg (rural, 2015-2021)

Output: data/income_ocr_raw.csv  (province, year, urban, rural, source)
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd
import winocr
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
TMP = ROOT / ".tmp"
OUT = ROOT / "data"

TABLES = {
    "urban_2020": ("C0623_2020.jpg", list(range(2013, 2020))),
    "rural_2020": ("C0629_2020.jpg", list(range(2013, 2020))),
    "urban_2022": ("C0624_2022.jpg", list(range(2015, 2022))),
    "rural_2022": ("C0630_2022.jpg", list(range(2015, 2022))),
}


def _clean_num(tokens: list[str]) -> float | None:
    # The table prints one decimal; OCR often splits "31194.8" into "31194" + "8"
    if len(tokens) >= 2 and re.fullmatch(r"\d{1,2}", tokens[-1]):
        s = tokens[0] + "." + tokens[-1]
    else:
        s = "".join(tokens)
    s = s.replace("．", ".").replace("。", ".").replace(",", "").replace(" ", "")
    # common OCR confusions in this font
    s = s.replace("O", "0").replace("o", "0").replace("U", "0").replace("u", "0")
    s = s.replace("l", "1").replace("I", "1").replace("t", "1")
    s = re.sub(r"[^0-9.]", "", s)
    if not s:
        return None
    if "." not in s and len(s) >= 4:
        s = s[:-1] + "." + s[-1]
    try:
        return float(s)
    except ValueError:
        return None


def ocr_table(path: Path, years: list[int]) -> pd.DataFrame:
    img = Image.open(path)
    res = winocr.recognize_pil_sync(img, "zh-Hans")
    nums = []
    for ln in res["lines"]:
        for w in ln["words"]:
            t = w["text"]
            if re.search(r"\d", t):
                r = w["bounding_rect"]
                nums.append((r["x"], r["y"], r["width"], r["height"], t))
    # Keep the data region only (below header, right of province names)
    nums = [n for n in nums if n[1] > 120 and n[0] > 60]

    # Row clusters from y positions
    ys = sorted({round(n[1]) for n in nums})
    clusters: list[list[float]] = []
    for y in ys:
        if not clusters or abs(y - np.mean(clusters[-1])) > 9:
            clusters.append([y])
        else:
            clusters[-1].append(y)
    row_centers = sorted(float(np.mean(c)) for c in clusters)

    # Column centers from header positions (x of year labels)
    header = [n for n in nums if n[1] <= 120]
    col_centers = []
    for y in years:
        cand = [n for n in header if str(y)[:2] in n[4] or str(y) in n[4]]
        if cand:
            col_centers.append(float(np.mean([c[0] + c[2] / 2 for c in cand])))
    if len(col_centers) != len(years):
        # fall back to equally spaced columns over the data area
        xs = [n[0] for n in nums]
        col_centers = list(np.linspace(min(xs) + 20, max(xs) + 20, len(years)))

    grid: dict[tuple[int, int], list[tuple[float, str]]] = {}
    for x, y, w, h, t in nums:
        ri = int(np.argmin([abs(y - c) for c in row_centers]))
        ci = int(np.argmin([abs(x + w / 2 - c) for c in col_centers]))
        grid.setdefault((ri, ci), []).append((x, t))

    provs = ["全国"] + ["北京","天津","河北","山西","内蒙古","辽宁","吉林","黑龙江","上海",
             "江苏","浙江","安徽","福建","江西","山东","河南","湖北","湖南","广东","广西",
             "海南","重庆","四川","贵州","云南","西藏","陕西","甘肃","青海","宁夏","新疆"]
    rows = []
    for ri in range(len(row_centers)):
        vals = []
        for ci in range(len(years)):
            toks = [t for _, t in sorted(grid.get((ri, ci), []))]
            vals.append(_clean_num(toks) if toks else np.nan)
        rows.append(vals)
    df = pd.DataFrame(rows, columns=years)
    df.insert(0, "province", provs[:len(df)])
    return df


if __name__ == "__main__":
    out = []
    for name, (fn, years) in TABLES.items():
        df = ocr_table(TMP / fn, years)
        df.insert(0, "table", name)
        out.append(df)
        print(name, df.shape)
        print(df.head(3).to_string())
    allt = pd.concat(out)
    allt.to_csv(OUT / "income_ocr_raw_wide.csv", index=False, encoding="utf-8-sig")
    print("saved", OUT / "income_ocr_raw_wide.csv")
