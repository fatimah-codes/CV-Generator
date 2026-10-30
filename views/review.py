"""
views/review.py — Pre-generation answer review screen.
"""
from __future__ import annotations

import streamlit as st
from views.popups import show_ats_guide_popup


def _section(title: str, content: str) -> None:
    with st.expander(title, expanded=False):
        st.markdown(content)


def render() -> None:
    col_t, col_btn = st.columns([3, 1])
    with col_t:
        st.markdown('<span class="pill-badge">final review</span>', unsafe_allow_html=True)
        st.markdown("## almost there — review your answers")
    with col_btn:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        if st.button("💡 ATS Guide", type="secondary", use_container_width=True, key="rev_guide_btn"):
            show_ats_guide_popup()

    st.markdown(
        "Check everything below before generating your CV. "
        "Go back to any step to make instant changes."
    )
    st.markdown("<br>", unsafe_allow_html=True)

    d = st.session_state.get("form_data", {})

    _section("🎯 Target role",
        f"**Role:** {d.get('target_role', '')}  \n"
        f"**JD:** {'✅ Provided (Keywords will be tailored)' if d.get('job_description','').strip() else '— not provided'}")

    _section("👤 Personal details",
        f"**Name:** {d.get('full_name','')}  \n"
        f"**Email:** {d.get('email','')}  \n"
        f"**Phone:** {d.get('phone','')}  \n"
        f"**Location:** {d.get('location','')}  \n"
        f"**LinkedIn:** {d.get('linkedin','') or '—'}  \n"
        f"**GitHub:** {d.get('github','') or '—'}")

    _section("📝 Summary inputs",
        f"**Years of experience:** {d.get('years_experience',0)}  \n"
        f"**Key strengths:** {d.get('key_strengths','')}  \n"
        f"**Career goal:** {d.get('career_goal','')}")

    jobs = d.get("work_experience", [])
    if jobs:
        lines = []
        for j in jobs:
            lines.append(f"**{j.get('title','')}** at {j.get('company','')} ({j.get('start_date','')} – {j.get('end_date','')})")
            for b in j.get("bullets", []):
                if b.strip():
                    lines.append(f"  - {b}")
        _section("💼 Work experience", "\n\n".join(lines))

    edu = d.get("education", [])
    if edu:
        lines = [
            f"**{e.get('degree','')}** — {e.get('institution','')} ({e.get('start_date','')}–{e.get('end_date','')})"
            + (f"  GPA: {e['gpa']}" if e.get("gpa") else "")
            for e in edu
        ]
        _section("🎓 Education", "\n\n".join(lines))

    projects = d.get("projects", [])
    if projects:
        lines = [f"**{p.get('name','')}** — {p.get('description','')[:80]}…"
                 for p in projects if p.get("name")]
        _section("🛠 Projects", "\n\n".join(lines) if lines else "_None_")

    _section("⚡ Skills",
        f"**Technical:** {', '.join(d.get('technical_skills',[]))}  \n"
        f"**Tools:** {', '.join(d.get('tool_skills',[]))}  \n"
        f"**Soft skills:** {', '.join(d.get('soft_skills',[]))}")

    extras = []
    certs = [c.get("name","") for c in d.get("certifications",[]) if c.get("name")]
    if certs:
        extras.append(f"**Certifications:** {', '.join(certs)}")
    if d.get("awards","").strip():
        extras.append(f"**Awards:** {d['awards']}")
    if d.get("languages"):
        extras.append(f"**Languages:** {', '.join(d['languages'])}")
    if extras:
        _section("🏅 Extras", "\n\n".join(extras))

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")

    c1, c2, _ = st.columns([1, 1, 2])
    with c1:
        if st.button("← Back to form", type="secondary", use_container_width=True):
            st.session_state["form_step"] = 8
            st.session_state["app_page"] = "questionnaire"
            st.rerun()
    with c2:
        if st.button("✨ Generate my CV", type="primary", use_container_width=True):
            st.session_state["app_page"] = "result"
            st.rerun()
