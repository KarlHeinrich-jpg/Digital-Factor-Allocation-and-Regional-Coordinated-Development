# -*- coding: utf-8 -*-
"""RapidOCR extraction of the four provincial income tables.

RapidOCR reads each printed number as one line, which is much more reliable
than the Windows OCR engine for this font. Output has the same layout as
data/income_ocr_raw_wide.csv.
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd
from rapidocr_onnxruntime import RapidOCR

ROOT = Path(__file__).resolve().parents[1]
TMP = ROOT / ".tmp"
OUT = ROOT / "data"

TABLES = {
    "urban_2020": ("C0623_2020.jpg", list(range(2013, 2020))),
    "rural_2020": ("C0629_2020.jpg", list(range(2013, 2020))),
    "urban_2022": ("C0624_2022.jpg", list(range(2015, 2022))),
    "rural_2022": ("C0630_2022.jpg", list(range(2015, 2022))),
}

PROVS = ["全国", "北京", "天津", "河北", "山西", "内蒙古", "辽宁", "吉林", "黑龙江",
         "上海", "江苏", "浙江", "安徽", "福建", "江西", "山东", "河南", "湖北",
         "湖南", "广东", "广西", "海南", "重庆", "四川", "贵州", "云南", "西藏",
         "陕西", "甘肃", "青海", "宁夏", "新疆"]

ocr = RapidOCR()


def parse_number(t: str) -> float | None:
    s = t.replace("，", "").replace(",", "").replace(" ", "")
    s = s.replace("．", ".").replace("。", ".")
    s = re.sub(r"[^0-9.]", "", s)
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def ocr_table(path: Path, years: list[int]) -> pd.DataFrame:
    res, _ = ocr(str(path))
    boxes = []
    for box, text, score in res:
        xs = [p[0] for p in box]
        ys = [p[1] for p in box]
        boxes.append((float(np.mean(xs)), float(np.mean(ys)), text))

    # header year column centers
    col_centers = []
    for y in years:
        cand = [x for x, yy, t in boxes if yy < 120 and str(y) in t]
        if cand:
            col_centers.append(float(np.mean(cand)))
    if len(col_centers) != len(years):
        # fixed seven-column layout, calibrated on the scans
        col_centers = list(np.linspace(140, 680, len(years)))

    # data rows: cluster y of all text below the header and right of the labels
    data = [(x, y, t) for x, y, t in boxes if y > 120]
    ys = sorted({round(y) for x, y, t in data if re.search(r"\d", t)})
    clusters: list[list[float]] = []
    for y in ys:
        if not clusters or abs(y - np.mean(clusters[-1])) > 9:
            clusters.append([y])
        else:
            clusters[-1].append(y)
    row_centers = [float(np.mean(c)) for c in clusters]
    # keep the 32 densest / evenly spaced rows
    if len(row_centers) > 32:
        row_centers = row_centers[:32]
    if len(row_centers) != 32:
        # fall back to the calibrated first/last province rows
        row_centers = list(np.linspace(150, 1223, 32))

    grid: dict[tuple[int, int], list[tuple[float, str]]] = {}
    for x, y, t in data:
        if not re.search(r"\d", t) and x < 60:
            continue
        ri = int(np.argmin([abs(y - c) for c in row_centers]))
        ci = int(np.argmin([abs(x - c) for c in col_centers]))
        grid.setdefault((ri, ci), []).append((x, t))

    rows = []
    for ri in range(len(row_centers)):
        vals = []
        for ci in range(len(years)):
            toks = [t for _, t in sorted(grid.get((ri, ci), []))]
            v = parse_number(" ".join(toks)) if toks else np.nan
            vals.append(v)
        rows.append(vals)
    df = pd.DataFrame(rows, columns=years)
    df.insert(0, "province", PROVS[:len(df)])
    return df


if __name__ == "__main__":
    out = []
    for name, (fn, years) in TABLES.items():
        df = ocr_table(TMP / fn, years)
        df.insert(0, "table", name)
        out.append(df)
        print("==", name, df.shape)
        print(df.head(4).to_string())
    allt = pd.concat(out, ignore_index=True)
    allt.to_csv(OUT / "income_ocr_raw_wide.csv", index=False, encoding="utf-8-sig")
    print("saved", OUT / "income_ocr_raw_wide.csv")
