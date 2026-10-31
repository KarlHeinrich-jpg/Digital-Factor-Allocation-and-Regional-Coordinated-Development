# -*- coding: utf-8 -*-
"""Build an editable MDPI-style DOCX companion from the LaTeX manuscript.

The LaTeX PDF remains the primary formatted version. This script converts the
section files to Markdown, replaces the LaTeX tables with pipe tables built
from the result CSVs, runs pandoc with citeproc, and applies basic MDPI-like
styles with python-docx.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pandas as pd
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"
TAB = ROOT / "output" / "tables"
PANDOC = ROOT / ".tmp" / "pandoc_bin" / "pandoc-3.1.11" / "pandoc.exe"

# ---------------------------------------------------------------- md tables
def star(p):
    return "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.10 else ""


def md_table2():
    d = pd.read_csv(TAB / "table2_descriptives.csv")
    names = {"dfa": "DFA index", "rcd": "RCD index", "rcd5": "RCD5 index",
             "rcd_ccd": "RCD-CCD", "income_ratio": "Urban-rural income ratio",
             "gov": "Government intervention", "ln_fdi": "Log FDI per capita",
             "ln_dens": "Log population density", "private": "Private economy vitality",
             "fin_dev": "Financial development", "tech": "Technological investment",
             "ind_struct": "Industrial structure upgrading"}
    out = ["| Variable | N | Mean | SD | Min | Median | Max |",
           "|---|---:|---:|---:|---:|---:|---:|"]
    for _, r in d.iterrows():
        out.append(f"| {names.get(r['var'], r['var'])} | {int(r['n'])} | {r['mean']:.3f} | "
                   f"{r['sd']:.3f} | {r['min']:.3f} | {r['p50']:.3f} | {r['max']:.3f} |")
    return "\n".join(out)


def md_table3():
    d = pd.read_csv(TAB / "table3_baseline.csv")
    coef = {(r["model"], r["var"]): (r["coef"], r["se"], r["p"]) for _, r in d.iterrows()
            if r["var"] != "N"}
    models = ["(1)", "(2)", "(3)", "(4)"]
    out = ["| | (1) | (2) | (3) | (4) |", "|---|---:|---:|---:|---:|",
           "| DFA | " + " | ".join(f"{coef[(m,'dfa')][0]:.3f}{star(coef[(m,'dfa')][2])}"
                                   for m in models) + " |",
           "|  | " + " | ".join(f"({coef[(m,'dfa')][1]:.3f})" for m in models) + " |"]
    for v, lab in [("gov", "Government intervention"), ("ln_fdi", "Log FDI"),
                   ("ln_dens", "Log population density"), ("private", "Private economy")]:
        out.append(f"| {lab} | " + " | ".join(
            f"{coef[(m,v)][0]:.4f}{star(coef[(m,v)][2])}" if (m, v) in coef else ""
            for m in models) + " |")
        out.append("|  | " + " | ".join(
            f"({coef[(m,v)][1]:.4f})" if (m, v) in coef else "" for m in models) + " |")
    out += ["| Controls | No | Yes | Yes | Yes |",
            "| Province FE | Yes | Yes | Yes | Yes |",
            "| Year FE | Yes | Yes | Yes | Yes |",
            "| Region trends | No | No | Yes | No |",
            "| Observations | 270 | 270 | 270 | 270 |"]
    return "\n".join(out)


def md_table4():
    d = pd.read_csv(TAB / "table4_threshold.csv")
    f = pd.read_csv(TAB / "threshold_tests.csv")
    fv = dict(zip(f["threshold_var"], f["F"]))
    labels = {"dfa": "DFA", "ln_pgdp": "ln(per capita GDP)",
              "fin_dev": "Financial development", "tech": "Technological investment",
              "private": "Private economy vitality"}
    a = ["| Threshold variable | γ | 95% CI | F | Bootstrap p |",
         "|---|---:|---|---:|---:|"]
    for _, r in d.iterrows():
        ci = "--" if r["q"] == "fin_dev" else f"[{r['ci_lo']:.3f}, {r['ci_hi']:.3f}]"
        a.append(f"| {labels[r['q']]} | {r['gamma']:.3f} | {ci} | {fv[r['q']]:.2f} | {r['p_boot']:.3f} |")
    b = ["| Threshold variable | Low regime | High regime | Observations (low/high) |",
         "|---|---:|---:|---:|"]
    for _, r in d.iterrows():
        b.append(f"| {labels[r['q']]} | {r['beta_low']:.3f}{star(r['p_low'])} | "
                 f"{r['beta_high']:.3f}{star(r['p_high'])} | {int(r['n_low'])}/{int(r['n_high'])} |")
        b.append(f"|  | ({r['se_low']:.3f}) | ({r['se_high']:.3f}) | |")
    return "\n\n".join(["\n".join(a), "\n".join(b)])


def md_table5():
    d = pd.read_csv(TAB / "table5_heterogeneity.csv")
    out = ["| Region | Two-way FE | Province FE |", "|---|---:|---:|"]
    for reg in ["East", "Central", "West", "Northeast"]:
        row = {r["fe"]: r for _, r in d[d["region"] == reg].iterrows()}
        out.append(f"| {reg} | {row['two-way']['coef']:.3f}{star(row['two-way']['p'])} | "
                   f"{row['province']['coef']:.3f}{star(row['province']['p'])} |")
        out.append(f"|  | ({row['two-way']['se']:.3f}) | ({row['province']['se']:.3f}) |")
    out += ["| Controls | Yes | Yes |", "| Observations | 90/54/99/27 | 90/54/99/27 |"]
    return "\n".join(out)


def md_table6():
    d = pd.read_csv(TAB / "table6_robustness.csv")
    out = ["| Specification | Coefficient | SE | N |", "|---|---:|---:|---:|"]
    for _, r in d.iterrows():
        out.append(f"| {r['spec']} | {r['coef']:.3f}{star(r['p'])} | ({r['se']:.3f}) | {int(r['n'])} |")
    return "\n".join(out)


def md_table7():
    d = pd.read_csv(TAB / "table7_mechanisms.csv")
    names = {"tech": "Technological investment", "fin_dev": "Financial development",
             "ind_struct": "Industrial upgrading", "income_ratio": "Urban-rural income ratio"}
    out = ["| Mediator | DFA → M (two-way FE) | DFA → M (province FE) | M in RCD equation |",
           "|---|---:|---:|---:|"]
    for m in ["tech", "fin_dev", "ind_struct", "income_ratio"]:
        sub = d[d["mediator"] == m]
        tw = sub[sub["fe"] == "two-way"].iloc[0]
        pv = sub[sub["fe"] == "province"].iloc[0]
        eq = sub[sub["fe"] == "RCD equation"]
        eqs = f"{eq.iloc[0]['coef']:.3f}{star(eq.iloc[0]['p'])}" if len(eq) else "--"
        out.append(f"| {names[m]} | {tw['coef']:.3f}{star(tw['p'])} | {pv['coef']:.3f}{star(pv['p'])} | {eqs} |")
        out.append(f"|  | ({tw['se']:.3f}) | ({pv['se']:.3f}) | |")
    out += ["| Controls | Yes | Yes | Yes |", "| Observations | 270 | 270 | 270 |"]
    return "\n".join(out)


def md_tableA1():
    d = pd.read_csv(TAB / "table_weights.csv")
    names = {"dfa_ports_pc": "Internet access ports per capita", "dfa_optical": "Optical cable density",
             "dfa_mobile": "Mobile phone penetration", "dfa_ipv4_pc": "IPv4 addresses per capita",
             "dfa_domain_pc": "Domain names per capita", "dfa_software_gdp": "Software revenue/GDP",
             "dfa_ecom_gdp": "E-commerce sales/GDP", "dfa_ecom_firm": "Share of firms with e-commerce",
             "dfa_website": "Websites per 100 firms", "dfa_info_firm_pc": "Information firms per capita",
             "dfa_dfi_coverage": "DFI coverage breadth", "dfa_dfi_usage": "DFI usage depth",
             "dfa_dfi_digit": "DFI digitization", "dfa_ict_emp": "ICT employment share",
             "dfa_internet": "Internet penetration", "rcd_pgdp": "GDP per capita",
             "rcd_retail_pc": "Retail sales per capita", "rcd_fiscal": "Fiscal self-sufficiency",
             "rcd_income": "Disposable income per capita", "rcd_beds": "Hospital beds per 10,000",
             "rcd_highered": "Higher-education students per 100,000",
             "rcd_social": "Social security spending share", "rcd_urban": "Urbanization rate",
             "rcd_income_ratio": "Urban-rural income ratio (negative)",
             "rcd_unemployment": "Urban unemployment rate (negative)"}
    dim = {"dfa_ports_pc": "Digital infrastructure", "dfa_optical": "Digital infrastructure",
           "dfa_mobile": "Digital infrastructure", "dfa_ipv4_pc": "Digital infrastructure",
           "dfa_domain_pc": "Digital infrastructure", "dfa_software_gdp": "Digital industry",
           "dfa_ecom_gdp": "Digital industry", "dfa_ecom_firm": "Digital industry",
           "dfa_website": "Digital industry", "dfa_info_firm_pc": "Digital industry",
           "dfa_dfi_coverage": "Digital finance", "dfa_dfi_usage": "Digital finance",
           "dfa_dfi_digit": "Digital finance", "dfa_ict_emp": "Digital human capital",
           "dfa_internet": "Digital human capital", "rcd_pgdp": "Economic",
           "rcd_retail_pc": "Economic", "rcd_fiscal": "Economic", "rcd_income": "Social",
           "rcd_beds": "Social", "rcd_highered": "Social", "rcd_social": "Social",
           "rcd_urban": "Urban-rural", "rcd_income_ratio": "Urban-rural",
           "rcd_unemployment": "Urban-rural"}
    out = ["| Dimension | Indicator | Weight |", "|---|---|---:|"]
    for idx, title in [("DFA", "Panel A: DFA"), ("RCD_global10", "Panel B: RCD")]:
        out.append(f"| **{title}** | | |")
        for _, r in d[d["index"] == idx].iterrows():
            out.append(f"| {dim.get(r['indicator'], r['dimension'])} | "
                       f"{names.get(r['indicator'], r['indicator'])} | {r['weight_within']:.3f} |")
    return "\n".join(out)


# ---------------------------------------------------------------- latex -> md
CIT = re.compile(r"\\cite[pt]?\{([^}]+)\}")
REF_MAP = {
    "sec:lit": "2", "sec:data": "3", "sec:results": "4", "sec:discussion": "5",
    "sec:conclusion": "6", "sec:baseline": "4.2", "sec:threshold": "4.3",
    "sec:heterogeneity": "4.4", "sec:robustness": "4.5", "sec:mechanisms": "4.6",
    "sec:limitations": "5.6", "app:weights": "Appendix A",
    "tab:indicators": "1", "tab:descriptives": "2", "tab:baseline": "3",
    "tab:threshold": "4", "tab:heterogeneity": "5", "tab:robustness": "6",
    "tab:mechanisms": "7", "tab:weights": "A1",
    "fig:framework": "1", "fig:maps": "2", "fig:trends": "3", "fig:lr": "4",
    "fig:scatter": "5", "fig:coef": "6",
}


def clean_inline(s: str) -> str:
    maths = []
    def _protect(m):
        maths.append(m.group(0))
        return f"@@MATH{len(maths)-1}@@"
    s = re.sub(r"\$\$.*?\$\$|\$[^$]+\$", _protect, s, flags=re.S)
    s = s.replace(r"\%", "%").replace(r"\&", "&").replace(r"\_", "_")
    s = s.replace(r"\$", "$").replace(r"\#", "#")
    s = s.replace(r"\,", " ").replace(r"\;", " ").replace(r"\!", "")
    s = s.replace(r"\textless", "<").replace(r"\textgreater", ">")
    s = re.sub(r"\\textbf\{([^{}]*)\}", r"**\1**", s)
    s = re.sub(r"\\textit\{([^{}]*)\}", r"*\1*", s)
    s = re.sub(r"\\emph\{([^{}]*)\}", r"*\1*", s)
    s = re.sub(r"\\ref\{([^}]+)\}", lambda m: REF_MAP.get(m.group(1), m.group(1)), s)
    s = CIT.sub(lambda m: "[" + "; ".join("@" + k.strip() for k in m.group(1).split(",")) + "]", s)
    s = re.sub(r"\\citet\{([^}]+)\}", r"@\1", s)
    s = re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?(\{[^{}]*\})?", "", s)
    s = s.replace("~", " ")
    for i, m in enumerate(maths):
        s = s.replace(f"@@MATH{i}@@", m)
    return s


def figure_block(m):
    block = m.group(0)
    imgs = re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", block)
    cap = re.search(r"\\caption\{(.*?)\}\s*\\label", block, re.S)
    caption = clean_inline(cap.group(1)) if cap else ""
    out = []
    for img in imgs:
        img = img.replace(".pdf", ".png")
        out.append(f"![{caption}]({img})")
    return "\n\n".join(out)


def latex_to_md(text: str) -> str:
    # figures
    text = re.sub(r"\\begin\{figure\}.*?\\end\{figure\}", figure_block, text, flags=re.S)
    # display equations
    def eq(m):
        body = m.group(1)
        body = re.sub(r"\\label\{[^}]+\}", "", body)
        return "$$\n" + body.strip() + "\n$$"
    text = re.sub(r"\\begin\{equation\}(.*?)\\end\{equation\}", eq, text, flags=re.S)
    # headings
    text = re.sub(r"\\section\{([^}]*)\}\\label\{[^}]+\}", r"# \1", text)
    text = re.sub(r"\\section\{([^}]*)\}", r"# \1", text)
    text = re.sub(r"\\subsection\{([^}]*)\}\\label\{[^}]+\}", r"## \1", text)
    text = re.sub(r"\\subsection\{([^}]*)\}", r"## \1", text)
    # remove remaining table inputs (tables are inserted as Markdown in build_md)
    text = re.sub(r"\\input\{[^}]+\}", "", text)
    # remove leftover environment commands
    text = re.sub(r"\\(begin|end)\{[^}]+\}", "", text)
    text = clean_inline(text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def build_md() -> str:
    title = "Nonlinear Effects of Digital Factor Allocation on Regional Coordinated Development: Evidence from a Provincial Panel Threshold Model in China"
    abstract = ("China's digital economy has grown rapidly, but whether digital factor allocation promotes regional "
                "coordinated development remains an open question. This study constructs a digital factor allocation "
                "(DFA) index covering digital infrastructure, digital industry, digital finance, and digital human "
                "capital, and a regional coordinated development (RCD) index covering economic, social, and urban-rural "
                "coordination for 30 Chinese provinces from 2013 to 2021. Using the entropy weight method and a Hansen "
                "panel threshold model, this study examines the nonlinear relationship between DFA and RCD. The results "
                "show that DFA is positively associated with RCD: the baseline two-way fixed-effects estimate is 0.241 "
                "(p < 0.05). The association is nonlinear. When per capita GDP exceeds the estimated threshold of 10.589 "
                "(about CNY 39,700), the marginal association rises from 0.506 to 0.677. A financial development threshold "
                "indicates that the marginal association declines at very high levels of financial depth, consistent with "
                "diminishing returns to digital finance. The association is strongest in western provinces, and channel "
                "analysis suggests that industrial upgrading, financial deepening, and technological investment are "
                "plausible mechanisms. These findings imply that digital factor policies should be sequenced with economic "
                "development, tailored to regional absorptive capacity, and accompanied by complementary reforms in "
                "advanced regions.")
    parts = [f"# {title}", "",
             "**Yile Wang**", "",
             "School of Economics, Beijing Technology and Business University, Beijing 102488, China; 2401050128@st.btbu.edu.cn", "",
             "**Abstract**", "", abstract, "",
             "**Keywords:** digital factor allocation; regional coordinated development; threshold effect; absorptive capacity; digital finance; China", ""]
    # Table 1 placeholder: use the LaTeX block rows parsed from sec3
    sec3 = (PAPER / "sec3_data.tex").read_text(encoding="utf-8")
    rows = []
    for ln in sec3.split("\n"):
        if "&" in ln and ln.rstrip().endswith("\\\\"):
            if "multicolumn" in ln or "Dimension & Indicator" in ln:
                continue
            cells = [c.strip() for c in ln.rstrip().rstrip("\\").split("&")]
            if len(cells) == 4:
                rows.append("| " + " | ".join(clean_inline(c) for c in cells) + " |")
    table1 = "\n".join(["| Dimension | Indicator | Definition and unit | Sign |",
                        "|---|---|---|---:|"] + rows)
    table_map = {
        "table2_descriptives.tex": ("Table 2. Descriptive statistics.", md_table2()),
        "table3_baseline.tex": ("Table 3. Baseline estimates of the effect of DFA on RCD.", md_table3()),
        "table4_threshold_a.tex": ("Table 4. Threshold tests.", md_table4()),
        "table5_heterogeneity.tex": ("Table 5. Regional heterogeneity.", md_table5()),
        "table6_robustness.tex": ("Table 6. Robustness checks.", md_table6()),
        "table7_mechanisms.tex": ("Table 7. Channel regressions.", md_table7()),
        "tableA1_weights.tex": ("Table A1. Entropy weights.", md_tableA1()),
    }
    for f in ["sec1_intro.tex", "sec2_lit.tex", "sec3_data.tex", "sec4_results.tex",
              "sec5_discussion.tex", "sec6_conclusion.tex"]:
        raw = (PAPER / f).read_text(encoding="utf-8")
        if f == "sec3_data.tex":
            # replace the entire first table block with Table 1
            start = raw.index("\\begin{table}[htbp]")
            end = raw.index("\\end{table}", start) + len("\\end{table}")
            raw = raw[:start] + "\n\n**Table 1. Indicator systems for DFA and RCD.**\n\n" + table1 + "\n\n" + raw[end:]
        for fn, (cap, tab) in table_map.items():
            if fn in raw:
                # replace the input inside the table block; the wrapper is removed by latex_to_md
                raw = raw.replace(f"\\input{{tables/{fn}}}", f"\n\n**{cap}**\n\n{tab}\n\n")
        parts.append(latex_to_md(raw))
    parts.append("\n# References\n")
    return "\n\n".join(parts)


def make_reference_docx(path: Path):
    doc = Document()
    section = doc.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2.5)
    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(10)
    normal.paragraph_format.line_spacing = 1.15
    normal.paragraph_format.space_after = Pt(6)
    for name, size in [("Title", 16), ("Heading 1", 12), ("Heading 2", 11)]:
        st = styles[name]
        st.font.name = "Times New Roman"
        st.font.size = Pt(size)
        st.font.bold = True
        st.paragraph_format.space_before = Pt(12)
        st.paragraph_format.space_after = Pt(6)
    doc.save(path)


def style_docx(path: Path):
    doc = Document(path)
    for p in doc.paragraphs:
        for r in p.runs:
            r.font.name = "Times New Roman"
    # page numbers in footer
    section = doc.sections[0]
    footer = section.footer
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), "PAGE")
    run._r.append(fld)
    doc.save(path)


if __name__ == "__main__":
    md = build_md()
    (PAPER / "manuscript_md.md").write_text(md, encoding="utf-8")
    ref = PAPER / "reference.docx"
    make_reference_docx(ref)
    out = PAPER / "manuscript_word.docx"
    cmd = [str(PANDOC), str(PAPER / "manuscript_md.md"), "-o", str(out),
           "--citeproc", "--bibliography", str(PAPER / "references.bib"),
           "--reference-doc", str(ref), "--resource-path", str(PAPER)]
    subprocess.run(cmd, check=True)
    style_docx(out)
    print("DOCX written:", out)
