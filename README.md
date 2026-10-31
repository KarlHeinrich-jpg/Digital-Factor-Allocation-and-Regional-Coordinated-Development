# Digital Factor Allocation and Regional Coordinated Development in China

**Manuscript (target journal: MDPI *Economies*)**

**Title:** Nonlinear Effects of Digital Factor Allocation on Regional Coordinated Development: Evidence from a Provincial Panel Threshold Model in China

**Authors:** Junfeng Wang (School of Marxism, Beijing Technology and Business University), Jiayi Wang (Digital College, Beijing Technology and Business University), Yile Wang (School of Economics, Beijing Technology and Business University; corresponding author)

**Status:** Working paper / manuscript. The paper has not been peer reviewed. Please cite it as a working paper.

---

## What is in this repository

This repository contains the complete reproducibility package for the paper:

- `paper/manuscript_MDPI_Economies.pdf` — formatted manuscript (MDPI LaTeX template, 24 pages, 6 figures, 7 tables).
- `paper/manuscript.tex`, `paper/sec1_intro.tex` … `paper/sec6_conclusion.tex` — LaTeX source.
- `paper/references.bib` — bibliography.
- `paper/Definitions/` — MDPI LaTeX class and logos.
- `paper/figures/` — final figures (PDF vector + PNG 300 dpi). Figure 1 is a black-and-white TikZ flowchart; the source is `fig1_framework_tikz.tex`.
- `paper/tables/` — LaTeX table source.
- `data/analysis_panel.csv` — final province-year panel used in the regressions (30 provinces × 2013–2021, N = 270).
- `data/income_panel.csv` — reconciled urban/rural income panel and urban-rural income ratio.
- `data/provincial_panel_raw.csv` — raw compiled provincial panel.
- `data/panel_360.dta` — Stata version of the 30-province panel.
- `output/tables/*.csv` — all regression tables in machine-readable form.
- `output/figures/*` — generated figure files and map data.
- `src/` — full analysis code, from income OCR and index construction to threshold tests, figures, LaTeX tables, and map generation.

A more detailed Chinese delivery note (data provenance, results, caveats, submission checklist) is in [`README_交付说明.md`](README_交付说明.md).

---

## Research design in brief

- **Sample:** 30 Chinese provincial-level units (Tibet, Hong Kong, Macao, and Taiwan are excluded because of data availability and comparability), 2013–2021, balanced panel with 270 observations. 2013 is the start year because China's unified urban-rural household survey began in 2013.
- **DFA (digital factor allocation):** four dimensions and 15 indicators — digital infrastructure, digital industry, digital finance, and digital human capital. Equal weights across dimensions; entropy weights within each dimension.
- **RCD (regional coordinated development):** three core dimensions and 10 indicators — economic coordination, social coordination, and urban-rural coordination. Equal weights across dimensions; entropy weights within each dimension. Robustness uses a five-dimension RCD, a coupling coordination degree (CCD), and a global entropy-weighted RCD.
- **Method:** two-way fixed-effects baseline plus a Hansen (1999) panel threshold model. The threshold is searched over the inner 80% of the threshold variable; inference uses a cluster wild bootstrap (300 replications) and likelihood-ratio confidence intervals.
- **Controls:** government intervention, log FDI per capita, log population density, and private economy vitality.
- **Mechanisms:** industrial upgrading, financial development, technological investment, and the urban-rural income ratio.

### Data sources

- China Statistical Yearbook (2014–2022)
- China City Statistical Yearbook (2014–2022)
- China Environmental Statistics Yearbook
- Provincial statistical yearbooks
- Peking University Digital Financial Inclusion Index (PKU DFIIC)

The urban/rural income series were extracted from the scanned yearbook tables (China Statistical Yearbook 2020, Tables 6-23 and 6-29; 2022, Tables 6-24 and 6-30) with RapidOCR and reconciled against the accounting identity linking total income, urban income, rural income, and the urbanization rate. A few remaining gaps were filled by linear interpolation within provinces. See `src/01b_ocr_income_rapid.py` and `src/02_build_income_panel.py`.

---

## Key results

| Result | Estimate |
|---|---|
| Baseline DFA effect on RCD (two-way FE, full controls) | **0.241** (SE 0.118; p = 0.042) |
| DFA effect excluding municipalities | 0.288 (p = 0.026) |
| DFA effect, 2013–2019 | 0.283 (p = 0.022) |
| Economic-development threshold (ln GDP per capita) | **10.589** (≈ CNY 39,700) |
| DFA coefficient below threshold | **0.506*** |
| DFA coefficient above threshold | **0.677*** |
| Threshold bootstrap p-value | **0.003** |
| Financial-development threshold | 10.045; 0.578*** below, 0.267*** above; p = 0.010 |
| Western region, two-way FE | **0.555*** (p < 0.001) |

The economic-development threshold is the paper's main nonlinear result. The financial-development threshold is based on a small high-regime group (30 observations, mostly Beijing, Shanghai, and Tianjin) and should be interpreted with caution. The five-dimension RCD, CCD, entropy-weighted DFA, and lagged DFA specifications are not significant; the paper reports these results and discusses them as scope conditions. See the manuscript's Limitations section for the sensitivity of the threshold to region-specific trends and year fixed effects.

---

## Reproduce

Python 3.13 with `pandas`, `numpy`, `statsmodels`, `linearmodels`, `matplotlib`, `geopandas`, `rapidocr_onnxruntime`, and `python-docx`; LaTeX with TeX Live 2025 (`pdflatex`, `bibtex`, `xelatex`).

```bash
git clone https://github.com/KarlHeinrich-jpg/Digital-Factor-Allocation-and-Regional-Coordinated-Development.git
cd Digital-Factor-Allocation-and-Regional-Coordinated-Development

# 1. Income OCR and reconciliation (skip if data/income_panel.csv is present)
python src/01b_ocr_income_rapid.py
python src/02_build_income_panel.py

# 2. Construct DFA and RCD indices
python src/03_build_indices.py

# 3. Threshold tests and main result tables
python src/04_threshold_test.py
python src/05_threshold_main.py
python src/07_main_results.py

# 4. Figures and LaTeX tables
python src/08_figures.py
python src/09_make_latex_tables.py

# 5. Rebuild the black-and-white flowchart (TikZ)
cd paper/figures
xelatex fig1_framework_tikz.tex
cd ..

# 6. Compile the manuscript
pdflatex manuscript.tex
bibtex manuscript
pdflatex manuscript.tex
pdflatex manuscript.tex
```

The maps are generated by `src/china_map_taiwan.py`, a local copy of the `yile-paper-style` map script with a Taiwan polygon (`src/taiwan_province.geojson`) added and filled in light gray. Taiwan is shown for cartographic completeness; it is not in the estimation sample.

---

## Notes on the maps and data

- Taiwan is included in the China maps as a light-gray area. It is not assigned a DFA/RCD class because Taiwan is not in the estimation sample; assigning a value would require additional data.
- Tibet is white because it is excluded from the estimation sample.
- The nine-dash line in the South China Sea inset is schematic. For formal submission, replace it with an official boundary file if the journal requires one; do not delete the inset.
- The raw provincial panel is compiled from public official yearbooks. Please check the original yearbook terms of use before redistributing the raw tables.

---

## License

- **Code:** MIT License (`LICENSE`).
- **Data, figures, and manuscript text:** Creative Commons Attribution 4.0 International (CC BY 4.0), unless a source yearbook states otherwise. See `DATA_LICENSE.md`.

If you use the data or code, please cite the manuscript.

## Citation

```bibtex
@unpublished{wang2026digital,
  title  = {Nonlinear Effects of Digital Factor Allocation on Regional Coordinated Development: Evidence from a Provincial Panel Threshold Model in China},
  author = {Wang, Junfeng and Wang, Jiayi and Wang, Yile},
  year   = {2026},
  note   = {Working paper},
  url    = {https://github.com/KarlHeinrich-jpg/Digital-Factor-Allocation-and-Regional-Coordinated-Development}
}
```

## Contact

Corresponding author: Yile Wang, School of Economics, Beijing Technology and Business University, Beijing 100048, China; 2401050128@st.btbu.edu.cn; ORCID 0009-0008-3195-5631.
