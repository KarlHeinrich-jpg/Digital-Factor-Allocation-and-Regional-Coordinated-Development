# -*- coding: utf-8 -*-
"""Build a clean editable DOCX from manuscript_md.md.

The MDPI LaTeX PDF remains the primary formatted version. This builder parses
the Markdown companion, inserts real Word tables and figures, converts
citations to author-year text, and formats the document in a simple MDPI-like
style.
"""
from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"
MD = PAPER / "manuscript_md.md"


# ---------------------------------------------------------------- citations
def parse_bib():
    text = (PAPER / "references.bib").read_text(encoding="utf-8")
    entries = {}
    for m in re.finditer(r"@(\w+)\{([^,]+),(.*?)\n\}", text, re.S):
        typ, key, body = m.group(1), m.group(2), m.group(3)
        fields = {}
        for fm in re.finditer(r"(\w+)\s*=\s*\{(.*?)\}(?=,|\s*\n|\s*$)", body, re.S):
            fields[fm.group(1).lower()] = fm.group(2).strip()
        entries[key] = (typ, fields)
    return entries


def surname(author: str) -> str:
    a = author.strip()
    if a.startswith("{") and a.endswith("}"):
        return a[1:-1]
    a = a.strip("{}")
    if "," in a:
        return a.split(",")[0].strip()
    parts = a.split()
    return parts[-1] if parts else a


def cite_short(key, entries):
    typ, f = entries.get(key, ("", {}))
    authors = [x.strip() for x in f.get("author", "").split(" and ") if x.strip()]
    year = f.get("year", "")
    if not authors:
        return f"{key} {year}"
    if len(authors) == 1:
        return f"{surname(authors[0])}, {year}"
    if len(authors) == 2:
        return f"{surname(authors[0])} & {surname(authors[1])}, {year}"
    return f"{surname(authors[0])} et al., {year}"


def replace_citations(text, entries):
    def repl(m):
        keys = [k.strip() for k in m.group(1).split(";")]
        return "(" + "; ".join(cite_short(k.lstrip("@"), entries) for k in keys) + ")"
    return re.sub(r"\[(@[^\]]+)\]", repl, text)


def format_reference(key, entries):
    typ, f = entries.get(key, ("", {}))
    authors = [x.strip() for x in f.get("author", "").split(" and ") if x.strip()]
    # format each author as Surname, I.
    fmta = []
    for a in authors:
        a = a.strip("{}")
        if "," in a:
            sur, rest = [x.strip() for x in a.split(",", 1)]
            initials = " ".join([p[0] + "." for p in rest.replace(".", " ").split() if p])
        else:
            parts = a.split()
            sur = parts[-1] if parts else a
            initials = " ".join([p[0] + "." for p in parts[:-1]])
        fmta.append(f"{sur}, {initials}".strip(", "))
    if len(fmta) > 6:
        auth = ", ".join(fmta[:3]) + " et al."
    elif len(fmta) == 1:
        auth = fmta[0]
    else:
        auth = ", ".join(fmta[:-1]) + ", & " + fmta[-1]
    year = f.get("year", "n.d.")
    title = f.get("title", "").strip()
    journal = f.get("journal", "")
    vol = f.get("volume", "")
    num = f.get("number", "")
    pages = f.get("pages", "")
    pub = f.get("publisher", "")
    note = f.get("note", "")
    out = f"{auth} ({year}). {title}."
    if journal:
        out += f" {journal}"
        if vol:
            out += f", {vol}"
        if num:
            out += f"({num})"
        if pages:
            out += f", {pages}"
        out += "."
    elif pub:
        out += f" {pub}."
    elif note:
        out += f" {note}."
    return out


# ---------------------------------------------------------------- docx helpers
def set_cell_border(cell, **kwargs):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = tcPr.find(qn("w:tcBorders"))
    if tcBorders is None:
        tcBorders = OxmlElement("w:tcBorders")
        tcPr.append(tcBorders)
    for edge in ("top", "bottom", "left", "right"):
        if edge in kwargs:
            el = tcBorders.find(qn(f"w:{edge}"))
            if el is None:
                el = OxmlElement(f"w:{edge}")
                tcBorders.append(el)
            for k, v in kwargs[edge].items():
                el.set(qn(f"w:{k}"), str(v))


def three_line_table(doc, headers, rows, font_size=8.5):
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = True
    hdr = table.rows[0].cells
    for i, h in enumerate(headers):
        hdr[i].text = ""
        p = hdr[i].paragraphs[0]
        run = p.add_run(h)
        run.bold = True
        run.font.size = Pt(font_size)
        run.font.name = "Times New Roman"
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER if i > 0 else WD_ALIGN_PARAGRAPH.LEFT
    for row in rows:
        cells = table.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = ""
            p = cells[i].paragraphs[0]
            run = p.add_run(str(val))
            run.font.size = Pt(font_size)
            run.font.name = "Times New Roman"
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT if i > 0 else WD_ALIGN_PARAGRAPH.LEFT
    # three-line borders
    nrows = len(table.rows)
    for r in range(nrows):
        for c in range(len(headers)):
            borders = {}
            if r == 0:
                borders["top"] = {"val": "single", "sz": 8, "color": "000000"}
                borders["bottom"] = {"val": "single", "sz": 4, "color": "000000"}
            elif r == nrows - 1:
                borders["bottom"] = {"val": "single", "sz": 8, "color": "000000"}
            set_cell_border(table.rows[r].cells[c], **borders)
    return table


def add_page_number(section):
    footer = section.footer
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), "PAGE")
    run._r.append(fld)


def parse_pipe(lines):
    rows = []
    for ln in lines:
        ln = ln.strip()
        if not ln.startswith("|"):
            continue
        cells = [c.strip() for c in ln.strip("|").split("|")]
        if all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
            continue
        rows.append(cells)
    return rows


def clean_math(s):
    repl = {
        "\\alpha": "α", "\\beta": "β", "\\gamma": "γ", "\\delta": "δ",
        "\\mu": "μ", "\\varepsilon": "ε", "\\epsilon": "ε", "\\sum": "Σ",
        "\\cdot": "·", "\\leq": "≤", "\\geq": "≥", "\\ln": "ln",
        "\\left": "", "\\right": "", "\\,": " ", "\\;": " ", "\\!": "",
        "\\hat{y}": "ŷ", "\\prime": "′", "\\mathrm": "",
    }
    s = re.sub(r"\frac\{([^{}]*)\}\{([^{}]*)\}", r"()/()", s)
    for k, v in repl.items():
        s = s.replace(k, v)
    s = s.replace("{", "").replace("}", "")
    s = re.sub(r"\\[a-zA-Z]+", "", s)
    return s.strip()


# ---------------------------------------------------------------- build
def main():
    entries = parse_bib()
    md = MD.read_text(encoding="utf-8")
    md = md.replace(chr(92)*2+"[2pt]", "").replace(chr(92)*2+"[8pt]", "")
    md = md.replace(chr(92)+"[2pt]", "").replace(chr(92)+"[8pt]", "")
    md = re.sub(r"\$\$(.*?)\$\$",
                lambda m: "\n\n" + clean_math(m.group(1)) + "\n\n", md, flags=re.S)
    md = re.sub(r"\$([^$]+)\$", lambda m: clean_math(m.group(1)), md)
    md = re.sub(r"^\s*\[(?:htbp|H|!htbp|tbp)\]\s*$", "", md, flags=re.M)
    blocks = re.split(r"\n\s*\n", md)
    doc = Document()
    section = doc.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    for attr in ["top_margin", "bottom_margin", "left_margin", "right_margin"]:
        setattr(section, attr, Cm(2.5))
    add_page_number(section)

    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(10)
    normal.paragraph_format.line_spacing = 1.15
    normal.paragraph_format.space_after = Pt(6)
    normal.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    for name, size in [("Title", 16), ("Heading 1", 12), ("Heading 2", 11)]:
        st = styles[name]
        st.font.name = "Times New Roman"
        st.font.size = Pt(size)
        st.font.bold = True
        st.font.color.rgb = RGBColor(0, 0, 0)
        st.paragraph_format.space_before = Pt(12)
        st.paragraph_format.space_after = Pt(6)

    i = 0
    table_flags = {}
    while i < len(blocks):
        b = blocks[i].strip()
        if not b:
            i += 1
            continue
        if b.startswith("# "):
            txt = b[2:].strip()
            p = doc.add_paragraph(txt, style="Title")
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        elif b.startswith("## "):
            doc.add_heading(b[3:].strip(), level=2)
        elif b.startswith("![") and "](" in b:
            m = re.match(r"!\[(.*?)\]\((.*?)\)", b, re.S)
            cap, path = m.group(1), m.group(2)
            img = PAPER / path
            if img.exists():
                doc.add_picture(str(img), width=Cm(16))
                doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(cap)
            r.italic = True
            r.font.size = Pt(9)
            r.font.name = "Times New Roman"
        elif b.startswith("**Table ") and b.endswith("**"):
            cap = b.strip("*").strip()
            p = doc.add_paragraph()
            r = p.add_run(cap)
            r.bold = True
            r.font.size = Pt(9)
            # gather following pipe blocks
            j = i + 1
            while j < len(blocks) and not blocks[j].strip().startswith("|"):
                j += 1
            if j < len(blocks):
                pipe_lines = []
                while j < len(blocks) and all(
                        (not ln.strip()) or ln.strip().startswith("|")
                        for ln in blocks[j].split("\n")):
                    pipe_lines += blocks[j].split("\n")
                    j += 1
                rows = parse_pipe(pipe_lines)
                if rows:
                    three_line_table(doc, rows[0], rows[1:])
                i = j
                continue
        elif b.startswith("|"):
            rows = parse_pipe(b.split(chr(10)))
            if rows:
                three_line_table(doc, rows[0], rows[1:])
        elif b.startswith("$$") and b.endswith("$$"):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(clean_math(b.strip("$").strip()))
            r.italic = True
            r.font.name = "Times New Roman"
        elif b == "**Abstract**":
            p = doc.add_paragraph()
            r = p.add_run("Abstract")
            r.bold = True
            r.font.size = Pt(11)
        elif b.startswith("**Keywords:**"):
            p = doc.add_paragraph()
            r = p.add_run("Keywords: ")
            r.bold = True
            p.add_run(b.split("**Keywords:**", 1)[1].strip())
        else:
            txt = replace_citations(b, entries)
            txt = re.sub(r"\$([^$]+)\$", lambda m: clean_math(m.group(1)), txt)
            txt = txt.replace("**", "")
            txt = re.sub(r"(?<!\*)\*(?!\*)", "", txt)
            p = doc.add_paragraph(txt)
        i += 1

    # references
    doc.add_heading("References", level=2)
    seen = set()
    for m in re.finditer(r"\[(@[^\]]+)\]", md):
        for k in m.group(1).split(";"):
            seen.add(k.strip().lstrip("@"))
    for key in sorted(seen, key=lambda k: format_reference(k, entries).lower()):
        p = doc.add_paragraph()
        r = p.add_run(format_reference(key, entries))
        r.font.size = Pt(9)

    out = PAPER / "manuscript_word.docx"
    doc.save(out)
    print("saved", out)


if __name__ == "__main__":
    main()
