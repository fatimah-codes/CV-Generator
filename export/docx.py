"""
export/docx.py — ATS-safe DOCX export using python-docx.

Single-column layout, standard heading styles, no tables, no images,
no text boxes — fully readable by ATS parsers.
"""

from __future__ import annotations

import io
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


# ============================================================
# Helpers
# ============================================================

def _set_run_font(run, name: str = "Calibri", size_pt: float = 11) -> None:
    run.font.name = name
    run.font.size = Pt(size_pt)


def _add_horizontal_rule(doc: Document) -> None:
    """Add a thin paragraph border below the last paragraph (HR effect)."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(2)
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "4")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), "CCCCCC")
    pBdr.append(bottom)
    pPr.append(pBdr)


def _section_heading(doc: Document, title: str) -> None:
    """Add a styled section heading with a rule underneath."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(2)
    run = p.add_run(title.upper())
    run.bold = True
    _set_run_font(run, size_pt=10.5)
    run.font.color.rgb = RGBColor(0x20, 0x20, 0x20)
    _add_horizontal_rule(doc)


def _two_col(doc: Document, left: str, right: str, left_bold: bool = False) -> None:
    """Simulate a two-column row using tabs."""
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(1)
    r_left = p.add_run(left)
    r_left.bold = left_bold
    _set_run_font(r_left, size_pt=10.5)
    if right:
        p.add_run("\t")
        r_right = p.add_run(right)
        _set_run_font(r_right, size_pt=9)
        r_right.font.color.rgb = RGBColor(0x80, 0x80, 0x80)
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT  # tab handles alignment


def _body(doc: Document, text: str, size: float = 10.5) -> None:
    p = doc.add_paragraph(text)
    p.paragraph_format.space_after = Pt(2)
    for run in p.runs:
        _set_run_font(run, size_pt=size)


def _bullet(doc: Document, text: str) -> None:
    p = doc.add_paragraph(style="List Bullet")
    run = p.add_run(text)
    _set_run_font(run, size_pt=10.5)
    p.paragraph_format.space_after = Pt(1)


# ============================================================
# Public API
# ============================================================

def generate_docx(cv: dict) -> bytes:
    """
    Build an ATS-safe DOCX from a CV dict.

    Args:
        cv: Dict matching CvOutput schema.

    Returns:
        DOCX bytes ready for st.download_button.
    """
    doc = Document()

    # ---- Page margins ----
    for section in doc.sections:
        section.top_margin = Inches(0.9)
        section.bottom_margin = Inches(0.9)
        section.left_margin = Inches(0.9)
        section.right_margin = Inches(0.9)

    # ---- Name ----
    contact = cv.get("contact", {})
    name_para = doc.add_paragraph()
    name_para.paragraph_format.space_after = Pt(2)
    name_run = name_para.add_run(contact.get("full_name", ""))
    name_run.bold = True
    _set_run_font(name_run, size_pt=22)

    # ---- Contact line ----
    parts = [
        contact.get("email", ""),
        contact.get("phone", ""),
        contact.get("location", ""),
        contact.get("linkedin", ""),
        contact.get("github", ""),
    ]
    contact_line = "  |  ".join(p for p in parts if p)
    if contact_line:
        p = doc.add_paragraph(contact_line)
        p.paragraph_format.space_after = Pt(4)
        for run in p.runs:
            _set_run_font(run, size_pt=9)
            run.font.color.rgb = RGBColor(0x60, 0x60, 0x60)

    # ---- Summary ----
    summary = cv.get("summary", "")
    if summary:
        _section_heading(doc, "Professional Summary")
        _body(doc, summary)

    # ---- Work Experience ----
    jobs = cv.get("work_experience", [])
    if jobs:
        _section_heading(doc, "Experience")
        for job in jobs:
            dates = f"{job.get('start_date', '')} – {job.get('end_date', '')}"
            loc = job.get("location", "")
            right = f"{dates}  {loc}".strip()
            _two_col(doc, job.get("title", ""), right, left_bold=True)

            # Company in italic
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(2)
            r = p.add_run(job.get("company", ""))
            r.italic = True
            _set_run_font(r, size_pt=9.5)
            r.font.color.rgb = RGBColor(0x55, 0x55, 0x55)

            for b in job.get("bullets", []):
                _bullet(doc, b)

            doc.add_paragraph().paragraph_format.space_after = Pt(2)

    # ---- Education ----
    edu_list = cv.get("education", [])
    if edu_list:
        _section_heading(doc, "Education")
        for edu in edu_list:
            dates = f"{edu.get('start_date', '')} – {edu.get('end_date', '')}"
            _two_col(doc, edu.get("degree", ""), dates, left_bold=True)
            gpa_str = f"  GPA: {edu['gpa']}" if edu.get("gpa") else ""
            _body(doc, edu.get("institution", "") + gpa_str, size=9.5)

    # ---- Projects ----
    projects = cv.get("projects", [])
    if projects:
        _section_heading(doc, "Projects")
        for proj in projects:
            p = doc.add_paragraph()
            r = p.add_run(proj.get("name", ""))
            r.bold = True
            _set_run_font(r, size_pt=10.5)

            tech = ", ".join(proj.get("tech_stack", []))
            if tech:
                tr = p.add_run(f"  [{tech}]")
                _set_run_font(tr, size_pt=9)
                tr.font.color.rgb = RGBColor(0x77, 0x77, 0x77)

            _body(doc, proj.get("description", ""))
            if proj.get("outcome"):
                _body(doc, f"Outcome: {proj['outcome']}", size=10)
            if proj.get("link"):
                _body(doc, proj["link"], size=9)
            doc.add_paragraph().paragraph_format.space_after = Pt(2)

    # ---- Skills ----
    skills = cv.get("skills", {})
    tech_s = skills.get("technical", [])
    tools_s = skills.get("tools", [])
    soft_s = skills.get("soft_skills", [])
    if tech_s or tools_s or soft_s:
        _section_heading(doc, "Skills")
        if tech_s:
            p = doc.add_paragraph()
            r = p.add_run("Technical: ")
            r.bold = True
            _set_run_font(r, size_pt=10.5)
            rv = p.add_run(", ".join(tech_s))
            _set_run_font(rv, size_pt=10.5)
        if tools_s:
            p = doc.add_paragraph()
            r = p.add_run("Tools: ")
            r.bold = True
            _set_run_font(r, size_pt=10.5)
            rv = p.add_run(", ".join(tools_s))
            _set_run_font(rv, size_pt=10.5)
        if soft_s:
            p = doc.add_paragraph()
            r = p.add_run("Soft Skills: ")
            r.bold = True
            _set_run_font(r, size_pt=10.5)
            rv = p.add_run(", ".join(soft_s))
            _set_run_font(rv, size_pt=10.5)

    # ---- Certifications ----
    certs = cv.get("certifications", [])
    if certs:
        _section_heading(doc, "Certifications")
        for cert in certs:
            line = cert.get("name", "")
            if cert.get("issuer"):
                line += f" — {cert['issuer']}"
            if cert.get("year"):
                line += f" ({cert['year']})"
            _body(doc, line)

    # ---- Awards ----
    awards = cv.get("awards", [])
    if awards:
        _section_heading(doc, "Awards")
        for a in awards:
            _bullet(doc, a)

    # ---- Languages ----
    langs = cv.get("languages", [])
    if langs:
        _section_heading(doc, "Languages")
        _body(doc, ", ".join(langs))

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
