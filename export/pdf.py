"""
export/pdf.py — Text-selectable PDF export using fpdf2.

Uses standard fonts for guaranteed ATS text selection.
No images, no tables, no multi-column — single-column ATS-safe layout.
"""

from __future__ import annotations

import os
from fpdf import FPDF, XPos, YPos


def _sanitize_for_pdf(text: str) -> str:
    """Replace problematic Unicode symbols with safe equivalents for PDF."""
    if not text:
        return ""
    replacements = {
        "\u2013": "-",   # en dash
        "\u2014": " - ", # em dash
        "\u2018": "'",   # left single quote
        "\u2019": "'",   # right single quote
        "\u201c": '"',   # left double quote
        "\u201d": '"',   # right double quote
        "\u2022": "-",   # bullet
        "\u2026": "...", # ellipsis
        "\u00a0": " ",   # non-breaking space
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


class CvPDF(FPDF):
    """Custom FPDF subclass with ATS-safe single-column CV layout helpers."""

    LEFT_MARGIN = 20
    RIGHT_MARGIN = 20
    TOP_MARGIN = 20

    def __init__(self) -> None:
        super().__init__(format="A4")
        self.set_margins(self.LEFT_MARGIN, self.TOP_MARGIN, self.RIGHT_MARGIN)
        self.set_auto_page_break(auto=True, margin=20)

        # Attempt to use Windows Arial for full Unicode support, else fall back to Helvetica
        self.font_family_name = "Helvetica"
        arial_regular = "C:/Windows/Fonts/arial.ttf"
        arial_bold = "C:/Windows/Fonts/arialbd.ttf"
        arial_italic = "C:/Windows/Fonts/ariali.ttf"

        if os.path.exists(arial_regular) and os.path.exists(arial_bold):
            try:
                self.add_font("ArialATS", "", arial_regular)
                self.add_font("ArialATS", "B", arial_bold)
                if os.path.exists(arial_italic):
                    self.add_font("ArialATS", "I", arial_italic)
                self.font_family_name = "ArialATS"
            except Exception:
                self.font_family_name = "Helvetica"

        self.add_page()

    # ------------------------------------------------------------------ #
    # Section heading
    # ------------------------------------------------------------------ #
    def section_heading(self, title: str) -> None:
        self.ln(4)
        self.set_font(self.font_family_name, "B", 10)
        self.set_text_color(30, 30, 30)
        clean_title = _sanitize_for_pdf(title.upper())
        self.cell(0, 6, clean_title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        # Thin rule
        self.set_draw_color(180, 180, 180)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(2.5)

    # ------------------------------------------------------------------ #
    # Name header
    # ------------------------------------------------------------------ #
    def name_header(self, name: str, contact_line: str) -> None:
        self.set_font(self.font_family_name, "B", 18)
        self.set_text_color(10, 10, 10)
        self.cell(0, 9, _sanitize_for_pdf(name), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_font(self.font_family_name, "", 9)
        self.set_text_color(90, 90, 90)
        self.cell(0, 5, _sanitize_for_pdf(contact_line), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(3)

    # ------------------------------------------------------------------ #
    # Body text
    # ------------------------------------------------------------------ #
    def body_text(self, text: str, size: int = 10) -> None:
        self.set_font(self.font_family_name, "", size)
        self.set_text_color(30, 30, 30)
        self.multi_cell(0, 5.2, _sanitize_for_pdf(text))
        self.ln(1)

    def bold_text(self, text: str, size: int = 10) -> None:
        self.set_font(self.font_family_name, "B", size)
        self.set_text_color(10, 10, 10)
        self.cell(0, 5.2, _sanitize_for_pdf(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def two_col_row(self, left: str, right: str, bold_left: bool = False) -> None:
        """Print title on left and right-aligned dates."""
        clean_left = _sanitize_for_pdf(left)
        clean_right = _sanitize_for_pdf(right)

        self.set_font(self.font_family_name, "", 9)
        rw = self.get_string_width(clean_right) + 4

        style = "B" if bold_left else ""
        self.set_font(self.font_family_name, style, 10)
        avail = max(10, self.w - self.l_margin - self.r_margin - rw)
        self.set_text_color(10, 10, 10)
        self.cell(avail, 5.2, clean_left)

        self.set_font(self.font_family_name, "", 9)
        self.set_text_color(90, 90, 90)
        self.cell(rw, 5.2, clean_right, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(10, 10, 10)

    def bullet(self, text: str) -> None:
        self.set_font(self.font_family_name, "", 10)
        self.set_text_color(30, 30, 30)
        indent = 6
        bullet_char = "-"
        self.cell(indent, 5.2, bullet_char)
        clean_text = _sanitize_for_pdf(text)
        self.multi_cell(
            self.w - self.l_margin - self.r_margin - indent,
            5.2,
            clean_text,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )


# ============================================================
# Public API
# ============================================================

def generate_pdf(cv: dict) -> bytes:
    """
    Build a text-selectable PDF from a CV dict.

    Args:
        cv: Dict matching CvOutput schema.

    Returns:
        PDF bytes ready for st.download_button.
    """
    pdf = CvPDF()

    # ---- Contact header ----
    contact = cv.get("contact", {})
    name = contact.get("full_name", "")
    parts = [
        contact.get("email", ""),
        contact.get("phone", ""),
        contact.get("location", ""),
        contact.get("linkedin", ""),
        contact.get("github", ""),
    ]
    contact_line = "  |  ".join(p for p in parts if p)
    pdf.name_header(name, contact_line)

    # ---- Summary ----
    summary = cv.get("summary", "")
    if summary:
        pdf.section_heading("Professional Summary")
        pdf.body_text(summary)

    # ---- Work Experience ----
    jobs = cv.get("work_experience", [])
    if jobs:
        pdf.section_heading("Experience")
        for job in jobs:
            dates = f"{job.get('start_date', '')} - {job.get('end_date', '')}"
            loc = job.get("location", "")
            right_col = f"{dates}  {loc}".strip()
            pdf.two_col_row(job.get("title", ""), right_col, bold_left=True)

            company = job.get("company", "")
            if company:
                try:
                    pdf.set_font(pdf.font_family_name, "I", 9)
                except Exception:
                    pdf.set_font(pdf.font_family_name, "", 9)
                pdf.set_text_color(70, 70, 70)
                pdf.cell(0, 4.8, _sanitize_for_pdf(company), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.ln(1)

            for b in job.get("bullets", []):
                pdf.bullet(b)
            pdf.ln(2)

    # ---- Education ----
    edu_list = cv.get("education", [])
    if edu_list:
        pdf.section_heading("Education")
        for edu in edu_list:
            dates = f"{edu.get('start_date', '')} - {edu.get('end_date', '')}"
            pdf.two_col_row(edu.get("degree", ""), dates, bold_left=True)
            pdf.set_font(pdf.font_family_name, "", 9)
            pdf.set_text_color(70, 70, 70)
            gpa_str = f"  GPA: {edu['gpa']}" if edu.get("gpa") else ""
            pdf.cell(0, 4.8, _sanitize_for_pdf(edu.get("institution", "") + gpa_str), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(2)

    # ---- Projects ----
    projects = cv.get("projects", [])
    if projects:
        pdf.section_heading("Projects")
        for proj in projects:
            tech = ", ".join(proj.get("tech_stack", []))
            pdf.bold_text(proj.get("name", ""))
            if tech:
                try:
                    pdf.set_font(pdf.font_family_name, "I", 9)
                except Exception:
                    pdf.set_font(pdf.font_family_name, "", 9)
                pdf.set_text_color(80, 80, 80)
                pdf.cell(0, 4.8, _sanitize_for_pdf(f"Tech: {tech}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.body_text(proj.get("description", ""))
            outcome = proj.get("outcome", "")
            link = proj.get("link", "")
            if outcome:
                pdf.body_text(f"Outcome: {outcome}")
            if link:
                pdf.body_text(f"Link: {link}", size=9)
            pdf.ln(2)

    # ---- Skills ----
    skills = cv.get("skills", {})
    tech = skills.get("technical", [])
    tools = skills.get("tools", [])
    soft = skills.get("soft_skills", [])
    if tech or tools or soft:
        pdf.section_heading("Skills")
        if tech:
            pdf.set_font(pdf.font_family_name, "B", 10)
            pdf.cell(26, 5.2, "Technical:")
            pdf.set_font(pdf.font_family_name, "", 10)
            pdf.cell(0, 5.2, _sanitize_for_pdf(", ".join(tech)), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        if tools:
            pdf.set_font(pdf.font_family_name, "B", 10)
            pdf.cell(26, 5.2, "Tools:")
            pdf.set_font(pdf.font_family_name, "", 10)
            pdf.cell(0, 5.2, _sanitize_for_pdf(", ".join(tools)), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        if soft:
            pdf.set_font(pdf.font_family_name, "B", 10)
            pdf.cell(26, 5.2, "Soft Skills:")
            pdf.set_font(pdf.font_family_name, "", 10)
            pdf.cell(0, 5.2, _sanitize_for_pdf(", ".join(soft)), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(2)

    # ---- Certifications ----
    certs = cv.get("certifications", [])
    if certs:
        pdf.section_heading("Certifications")
        for cert in certs:
            line = cert.get("name", "")
            if cert.get("issuer"):
                line += f" - {cert['issuer']}"
            if cert.get("year"):
                line += f" ({cert['year']})"
            pdf.body_text(line)

    # ---- Awards ----
    awards = cv.get("awards", [])
    if awards:
        pdf.section_heading("Awards")
        for a in awards:
            pdf.bullet(a)

    # ---- Languages ----
    langs = cv.get("languages", [])
    if langs:
        pdf.section_heading("Languages")
        pdf.body_text(", ".join(langs))

    return bytes(pdf.output())
