"""
views/result.py — CV generation, preview, ATS analysis, editing, and exports.
"""
from __future__ import annotations

import json, re
import streamlit as st
from auth import get_api_key
from llm.chain import generate_cv, regenerate_section, analyse_ats, CvOutput, AtsAnalysis
from export.pdf import generate_pdf
from export.docx import generate_docx


# ============================================================
# Small helpers
# ============================================================

def _has_cv() -> bool:
    return bool(st.session_state.get("generated_cv"))


def _cv() -> dict:
    return st.session_state.get("generated_cv", {})


def _ats() -> dict | None:
    return st.session_state.get("ats_analysis")


# ============================================================
# CV → HTML preview
# ============================================================

def _cv_html(cv: dict) -> str:
    contact = cv.get("contact", {})
    parts = [contact.get("email",""), contact.get("phone",""),
             contact.get("location",""), contact.get("linkedin",""), contact.get("github","")]
    contact_line = " &nbsp;|&nbsp; ".join(p for p in parts if p)

    html = f"""<div class="cv-preview">
<h1>{contact.get("full_name","")}</h1>
<p class="cv-contact">{contact_line}</p>
"""
    if cv.get("summary"):
        html += f"<h2>Professional Summary</h2><p>{cv['summary']}</p>"

    for job in cv.get("work_experience", []):
        dates = f"{job.get('start_date','')} – {job.get('end_date','')}"
        loc = f", {job['location']}" if job.get("location") else ""
        html += f"""<h2>Experience</h2>
<h3>{job.get("title","")}</h3>
<span class="cv-company">{job.get("company","")}{loc}</span>
<span class="cv-dates">{dates}</span><div style="clear:both"></div><ul>"""
        for b in job.get("bullets",[]):
            if b.strip():
                html += f"<li>{b}</li>"
        html += "</ul>"

    if cv.get("education"):
        html += "<h2>Education</h2>"
    for edu in cv.get("education",[]):
        dates = f"{edu.get('start_date','')} – {edu.get('end_date','')}"
        gpa = f" &nbsp;·&nbsp; GPA: {edu['gpa']}" if edu.get("gpa") else ""
        html += f"<h3>{edu.get('degree','')}</h3><span class='cv-company'>{edu.get('institution','')}{gpa}</span><span class='cv-dates'>{dates}</span><div style='clear:both'></div>"

    if cv.get("projects"):
        html += "<h2>Projects</h2>"
    for proj in cv.get("projects",[]):
        tech = ", ".join(proj.get("tech_stack",[]))
        tech_str = f" <small style='color:#64748b'>[{tech}]</small>" if tech else ""
        outcome = f"<br><small style='color:#059669;font-weight:500'>Outcome: {proj['outcome']}</small>" if proj.get("outcome") else ""
        link = f"<br><a href='{proj['link']}' style='color:#7c3aed;font-size:12px;font-weight:500'>{proj['link']}</a>" if proj.get("link") else ""
        html += f"<h3>{proj.get('name','')}{tech_str}</h3><p>{proj.get('description','')}{outcome}{link}</p>"

    skills = cv.get("skills",{})
    tech_s, tools_s, soft_s = skills.get("technical",[]), skills.get("tools",[]), skills.get("soft_skills",[])
    if tech_s or tools_s or soft_s:
        html += "<h2>Skills</h2>"
        if tech_s:  html += f"<p><strong>Technical:</strong> {', '.join(tech_s)}</p>"
        if tools_s: html += f"<p><strong>Tools:</strong> {', '.join(tools_s)}</p>"
        if soft_s:  html += f"<p><strong>Soft Skills:</strong> {', '.join(soft_s)}</p>"

    certs = cv.get("certifications",[])
    if certs:
        html += "<h2>Certifications</h2><ul>"
        for c in certs:
            line = c.get("name","")
            if c.get("issuer"): line += f" — {c['issuer']}"
            if c.get("year"):   line += f" ({c['year']})"
            html += f"<li>{line}</li>"
        html += "</ul>"

    if cv.get("awards"):
        html += "<h2>Awards</h2><ul>" + "".join(f"<li>{a}</li>" for a in cv["awards"]) + "</ul>"
    if cv.get("languages"):
        html += f"<h2>Languages</h2><p>{', '.join(cv['languages'])}</p>"

    html += "</div>"
    return html


# ============================================================
# CV → Markdown / TXT
# ============================================================

def _cv_md(cv: dict) -> str:
    contact = cv.get("contact",{})
    parts = [contact.get("email",""), contact.get("phone",""),
             contact.get("location",""), contact.get("linkedin",""), contact.get("github","")]
    lines = [f"# {contact.get('full_name','')}", " | ".join(p for p in parts if p), ""]

    if cv.get("summary"):
        lines += ["## Professional Summary", cv["summary"], ""]

    if cv.get("work_experience"):
        lines.append("## Experience")
        for j in cv["work_experience"]:
            lines.append(f"### {j.get('title','')} — {j.get('company','')}  ")
            lines.append(f"*{j.get('start_date','')} – {j.get('end_date','')}*  ")
            for b in j.get("bullets",[]): lines.append(f"- {b}")
            lines.append("")

    if cv.get("education"):
        lines.append("## Education")
        for e in cv["education"]:
            gpa = f" · GPA: {e['gpa']}" if e.get("gpa") else ""
            lines.append(f"### {e.get('degree','')} — {e.get('institution','')}{gpa}  ")
            lines.append(f"*{e.get('start_date','')} – {e.get('end_date','')}*")
            lines.append("")

    if cv.get("projects"):
        lines.append("## Projects")
        for p in cv["projects"]:
            tech = ", ".join(p.get("tech_stack",[]))
            lines.append(f"### {p.get('name','')}  [{tech}]")
            lines.append(p.get("description",""))
            if p.get("outcome"): lines.append(f"Outcome: {p['outcome']}")
            if p.get("link"):    lines.append(p["link"])
            lines.append("")

    skills = cv.get("skills",{})
    lines.append("## Skills")
    if skills.get("technical"):  lines.append(f"**Technical:** {', '.join(skills['technical'])}")
    if skills.get("tools"):      lines.append(f"**Tools:** {', '.join(skills['tools'])}")
    if skills.get("soft_skills"): lines.append(f"**Soft Skills:** {', '.join(skills['soft_skills'])}")
    lines.append("")

    if cv.get("certifications"):
        lines.append("## Certifications")
        for c in cv["certifications"]:
            line = c.get("name","")
            if c.get("issuer"): line += f" — {c['issuer']}"
            if c.get("year"):   line += f" ({c['year']})"
            lines.append(f"- {line}")
        lines.append("")

    if cv.get("awards"):
        lines += ["## Awards"] + [f"- {a}" for a in cv["awards"]] + [""]
    if cv.get("languages"):
        lines += ["## Languages", ", ".join(cv["languages"])]

    return "\n".join(lines)


# ============================================================
# ATS panel
# ============================================================

def _render_ats(ats: dict) -> None:
    score = ats.get("score", 0)
    color = "#059669" if score >= 70 else "#d97706" if score >= 50 else "#dc2626"

    st.markdown(f"""
<div class="ats-panel">
  <div class="pill-badge">ats match score</div>
  <div style="display:flex;align-items:baseline;gap:12px;margin:8px 0 16px">
    <span class="ats-score-number" style="color:{color}">{score}</span>
    <span style="font-size:22px;color:#64748b;font-weight:700">/ 100</span>
  </div>
</div>""", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        matched = ats.get("matched_keywords", [])
        if matched:
            st.markdown("**✅ Matched keywords:**")
            st.markdown(" ".join(f'<span class="pill-badge" style="background:#ecfdf5;border-color:#a7f3d0;color:#065f46">{kw}</span>' for kw in matched[:14]), unsafe_allow_html=True)
    with c2:
        missing = ats.get("missing_keywords", [])
        if missing:
            st.markdown("**⚠️ Keywords to consider:**")
            st.markdown(" ".join(f'<span class="pill-badge" style="background:#fffbeb;border-color:#fde68a;color:#92400e">{kw}</span>' for kw in missing[:10]), unsafe_allow_html=True)

    if ats.get("strengths"):
        st.markdown("<br>**🌟 CV Strengths:**", unsafe_allow_html=True)
        for s in ats["strengths"]: st.markdown(f"- {s}")
    if ats.get("suggestions"):
        st.markdown("<br>**💡 Actionable Tips to Rank Higher:**", unsafe_allow_html=True)
        for tip in ats["suggestions"]: st.markdown(f"- {tip}")


# ============================================================
# Section editor / re-generator
# ============================================================

def _edit_panel(cv_dict: dict, candidate_data: dict, api_key: str) -> None:
    st.markdown("---")
    st.markdown('<span class="pill-badge">interactive editor</span>', unsafe_allow_html=True)
    st.markdown("### edit or regenerate sections")

    tab_edit, tab_ai = st.tabs(["✍️  Edit Text Directly", "🤖  Regenerate Section with AI"])

    with tab_edit:
        new_summary = st.text_area("Professional Summary", value=cv_dict.get("summary",""), height=110, key="edit_summary")

        with st.expander("Work Experience Achievements"):
            for j_idx, job in enumerate(cv_dict.get("work_experience",[])):
                st.markdown(f"**{job.get('title','')} at {job.get('company','')}**")
                edited = st.text_area(f"Achievements (one per line)",
                    value="\n".join(job.get("bullets",[])), height=100, key=f"ebullets_{j_idx}")
                job["bullets"] = [b.strip() for b in edited.split("\n") if b.strip()]

        with st.expander("Skills Categories"):
            skills = cv_dict.get("skills",{})
            new_tech  = st.text_input("Technical Skills (comma-separated)", value=", ".join(skills.get("technical",[])),  key="edit_tech")
            new_tools = st.text_input("Tools & Platforms (comma-separated)", value=", ".join(skills.get("tools",[])),      key="edit_tools")
            new_soft  = st.text_input("Soft Skills (comma-separated)",       value=", ".join(skills.get("soft_skills",[])),key="edit_soft")

        if st.button("💾 Save Changes to Preview", type="primary", key="save_edits"):
            cv_dict["summary"] = new_summary
            cv_dict.setdefault("skills",{})
            cv_dict["skills"]["technical"]  = [s.strip() for s in new_tech.split(",")  if s.strip()]
            cv_dict["skills"]["tools"]      = [s.strip() for s in new_tools.split(",") if s.strip()]
            cv_dict["skills"]["soft_skills"]= [s.strip() for s in new_soft.split(",")  if s.strip()]
            st.session_state["generated_cv"] = cv_dict
            st.toast("✅ Saved! Preview updated instantly.", icon="🎉")
            st.rerun()

    with tab_ai:
        st.caption("Ask AI to rewrite just one specific section while keeping all other sections unchanged.")
        c1, c2 = st.columns([2, 1])
        with c1:
            section = st.selectbox("Choose section to rewrite", ["summary","work_experience","skills","projects"],
                format_func=lambda s: s.replace("_"," ").title(), key="regen_sel")
        with c2:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            regen = st.button("↻ Regenerate with AI", type="primary", use_container_width=True, key="regen_btn")

        if regen:
            with st.spinner(f"Rewriting {section.replace('_',' ')}…"):
                try:
                    updates = regenerate_section(api_key, section, cv_dict, candidate_data)
                    st.session_state["generated_cv"].update(updates)
                    st.toast(f"✅ {section.replace('_', ' ').title()} updated!", icon="✨")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Could not regenerate: {exc}")


# ============================================================
# Main render
# ============================================================

def render() -> None:
    api_key = get_api_key()
    candidate_data = st.session_state.get("form_data", {})

    # ---- Generate if not yet done ----
    if not _has_cv():
        st.markdown('<span class="pill-badge">ai generation in progress</span>', unsafe_allow_html=True)
        st.markdown("## building your ats-optimised cv…")
        st.caption("The AI is restructuring your experience into strong action-verb bullets and natural keywords. No facts are invented.")

        with st.spinner("Crafting your professional CV with AI…"):
            try:
                cv_obj: CvOutput = generate_cv(api_key, candidate_data)
                st.session_state["generated_cv"] = cv_obj.model_dump()
                st.session_state["just_generated"] = True
            except Exception as exc:
                st.error(f"❌ Generation failed: {exc}\n\nIf rate-limited, wait a moment and refresh. If the key expired, log out and try again.")
                if st.button("← Back to review", type="secondary"):
                    st.session_state["app_page"] = "review"
                    st.rerun()
                return

        jd = candidate_data.get("job_description","")
        if jd.strip():
            with st.spinner("Analyzing keyword density & ATS match…"):
                try:
                    ats_obj: AtsAnalysis = analyse_ats(api_key, st.session_state["generated_cv"], jd)
                    st.session_state["ats_analysis"] = ats_obj.model_dump()
                except Exception:
                    st.session_state["ats_analysis"] = None

        st.rerun()

    # ---- Trigger celebration on initial generation ----
    if st.session_state.get("just_generated"):
        st.balloons()
        st.toast("🎉 Your ATS-ready CV is complete!", icon="✨")
        st.session_state["just_generated"] = False

    # ---- Display ----
    cv_dict = _cv()
    contact = cv_dict.get("contact", {})
    name = contact.get("full_name","your cv").lower()

    st.markdown('<span class="pill-badge">complete</span>', unsafe_allow_html=True)
    st.markdown(f"## {name}")

    ca, cb, _ = st.columns([1, 1, 3])
    with ca:
        if st.button("← Back to form", type="secondary"):
            st.session_state.pop("generated_cv", None)
            st.session_state.pop("ats_analysis", None)
            st.session_state["app_page"] = "questionnaire"
            st.session_state["form_step"] = 1
            st.rerun()
    with cb:
        if st.button("↺ Regenerate all", type="secondary"):
            st.session_state.pop("generated_cv", None)
            st.session_state.pop("ats_analysis", None)
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Live preview
    st.markdown("### live document preview")
    st.markdown(_cv_html(cv_dict), unsafe_allow_html=True)

    # ATS panel
    ats_data = _ats()
    if ats_data:
        st.markdown("<br>", unsafe_allow_html=True)
        _render_ats(ats_data)
    elif not candidate_data.get("job_description","").strip():
        st.info("💡 Tip: Paste a job description in Step 1 to unlock an ATS match score and keyword gap analysis.")

    # Editor / regeneration
    _edit_panel(cv_dict, candidate_data, api_key)

    # Downloads
    st.markdown("---")
    st.markdown('<span class="pill-badge">instant download</span>', unsafe_allow_html=True)
    st.markdown("### export your cv")

    slug = contact.get("full_name","cv").lower().replace(" ","_")
    d1, d2, d3 = st.columns(3)

    with d1:
        try:
            pdf_bytes = generate_pdf(cv_dict)
            st.download_button("⬇ Download PDF", data=pdf_bytes, file_name=f"{slug}_cv.pdf",
                               mime="application/pdf", use_container_width=True)
        except Exception as exc:
            st.error(f"PDF error: {exc}")

    with d2:
        try:
            docx_bytes = generate_docx(cv_dict)
            st.download_button("⬇ Download DOCX", data=docx_bytes, file_name=f"{slug}_cv.docx",
                               mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                               use_container_width=True)
        except Exception as exc:
            st.error(f"DOCX error: {exc}")

    with d3:
        md_text = _cv_md(cv_dict)
        st.download_button("⬇ Download TXT / MD", data=md_text.encode("utf-8"),
                           file_name=f"{slug}_cv.md", mime="text/markdown",
                           use_container_width=True)

    st.caption("🔒 Single-column layout. PDF text is selectable and machine-readable (zero tables/images) for 100% ATS pass-through.")
