"""
views/questionnaire.py — 8-step guided CV form.

All answers persist in st.session_state["form_data"].
Back/Next navigation never loses any data.
"""
from __future__ import annotations

import streamlit as st
from typing import Any
from views.popups import show_ats_guide_popup, show_bullet_helper_popup

TOTAL_STEPS = 8


# ============================================================
# Helpers
# ============================================================

def _init_state() -> None:
    """Initialise session keys if they don't exist yet."""
    defaults: dict[str, Any] = {
        "form_step": 1,
        "form_data": {
            "target_role": "",
            "job_description": "",
            "full_name": "", "email": "", "phone": "",
            "location": "", "linkedin": "", "github": "",
            "years_experience": 0,
            "key_strengths": "", "career_goal": "",
            "work_experience": [],
            "education": [],
            "projects": [],
            "technical_skills": [], "tool_skills": [], "soft_skills": [],
            "certifications": [],
            "awards": "", "languages": [],
        },
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _d() -> dict:
    return st.session_state["form_data"]


def _step() -> int:
    return st.session_state.get("form_step", 1)


def _go(step: int) -> None:
    st.session_state["form_step"] = step
    st.rerun()


def _header(step: int, title: str) -> None:
    col_t, col_btn = st.columns([3, 1])
    with col_t:
        st.markdown(
            f'<span class="pill-badge">step {step} of {TOTAL_STEPS}</span>',
            unsafe_allow_html=True,
        )
        st.markdown(f"## {title}")
    with col_btn:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        if st.button("💡 ATS Guide", type="secondary", use_container_width=True, key=f"guide_hdr_{step}"):
            show_ats_guide_popup()

    st.progress(step / TOTAL_STEPS)
    st.markdown("<br>", unsafe_allow_html=True)


def _nav(step: int, can_next: bool = True, next_label: str = "Next →") -> None:
    c1, c2, _ = st.columns([1, 1, 3])
    with c1:
        if step > 1 and st.button("← Back", type="secondary", use_container_width=True, key=f"back_{step}"):
            _go(step - 1)
    with c2:
        if can_next:
            if st.button(next_label, type="primary", use_container_width=True, key=f"next_{step}"):
                st.toast(f"Step {step} saved!", icon="✨")
                _go(step + 1)


# ============================================================
# Step renderers
# ============================================================

def _step1() -> None:
    _header(1, "let's tailor your cv")
    d = _d()
    d["target_role"] = st.text_input(
        "Target role *",
        value=d["target_role"],
        placeholder="e.g. Senior Software Engineer",
    )
    d["job_description"] = st.text_area(
        "Job description (paste to boost ATS score — optional)",
        value=d["job_description"],
        placeholder="Paste the full job posting here for automatic keyword matching…",
        height=200,
    )
    st.caption("💡 Pasting the JD lets us inject the exact right keywords naturally — no keyword stuffing.")
    ok = bool(d["target_role"].strip())
    if not ok:
        st.warning("Please enter your target role to continue.")
    _nav(1, can_next=ok)


def _step2() -> None:
    _header(2, "tell us about you")
    d = _d()
    c1, c2 = st.columns(2)
    with c1:
        d["full_name"] = st.text_input("Full name *", value=d["full_name"], placeholder="Jane Smith")
        d["email"] = st.text_input("Email *", value=d["email"], placeholder="jane@example.com")
        d["phone"] = st.text_input("Phone *", value=d["phone"], placeholder="+1 555 000 0000")
    with c2:
        d["location"] = st.text_input("City / Country *", value=d["location"], placeholder="London, UK")
        d["linkedin"] = st.text_input("LinkedIn (optional)", value=d["linkedin"], placeholder="linkedin.com/in/janesmith")
        d["github"] = st.text_input("GitHub / Portfolio (optional)", value=d["github"], placeholder="github.com/janesmith")
    st.caption("ℹ️ ATS-safe — no photo, DOB, marital status, or protected characteristics.")
    ok = all(d[f].strip() for f in ["full_name", "email", "phone", "location"])
    if not ok:
        st.warning("Please fill in all required fields (*) to continue.")
    _nav(2, can_next=ok)


def _step3() -> None:
    _header(3, "your professional story")
    d = _d()
    d["years_experience"] = st.number_input(
        "Years of professional experience *",
        min_value=0, max_value=60,
        value=int(d["years_experience"]),
    )
    d["key_strengths"] = st.text_area(
        "Key strengths (comma-separated) *",
        value=d["key_strengths"],
        placeholder="e.g. Python, distributed systems, cloud architecture, team leadership",
        height=80,
    )
    d["career_goal"] = st.text_area(
        "Career goal / what you want in your next role *",
        value=d["career_goal"],
        placeholder="e.g. Lead backend engineering at a growth-stage fintech company…",
        height=100,
    )
    st.caption("🤖 We'll use these to craft an ATS-tailored professional summary.")
    ok = all([d["key_strengths"].strip(), d["career_goal"].strip()])
    if not ok:
        st.warning("Please fill in all required fields to continue.")
    _nav(3, can_next=ok)


def _blank_job() -> dict:
    return {"title": "", "company": "", "location": "", "start_date": "", "end_date": "", "bullets": ["", "", ""]}


def _validate_jobs(jobs: list) -> bool:
    if not jobs:
        return False
    for j in jobs:
        if not (j.get("title") and j.get("company") and j.get("start_date") and j.get("end_date")):
            return False
        if len([b for b in j.get("bullets", []) if b.strip()]) < 3:
            return False
    return True


def _step4() -> None:
    _header(4, "tell us about your work")
    d = _d()
    if not d["work_experience"]:
        d["work_experience"].append(_blank_job())

    col_h1, col_h2 = st.columns([3, 2])
    with col_h1:
        st.markdown("**Add each role:** Include measurable achievements (numbers, %, impact).")
    with col_h2:
        if st.button("✨ Open Achievement Ideas", type="secondary", use_container_width=True, key="open_helper_s4"):
            show_bullet_helper_popup()

    to_delete = []
    for i, job in enumerate(d["work_experience"]):
        label = f"Role {i+1}: {job.get('title', '') or '(untitled)'}"
        with st.expander(label, expanded=(i == len(d["work_experience"]) - 1)):
            c1, c2 = st.columns(2)
            with c1:
                job["title"] = st.text_input("Job title *", value=job["title"], key=f"jt_{i}", placeholder="Software Engineer")
                job["company"] = st.text_input("Company *", value=job["company"], key=f"jc_{i}", placeholder="Acme Corp")
                job["location"] = st.text_input("Location", value=job.get("location", ""), key=f"jl_{i}", placeholder="New York, NY")
            with c2:
                job["start_date"] = st.text_input("Start date *", value=job.get("start_date", ""), key=f"js_{i}", placeholder="Jan 2022")
                job["end_date"] = st.text_input("End date *", value=job.get("end_date", ""), key=f"je_{i}", placeholder="Dec 2023 or Present")

            st.markdown("**Achievements** (3–5 bullets — include numbers, %, impact):")
            bullets = list(job.get("bullets", ["", "", ""]))
            while len(bullets) < 3:
                bullets.append("")
            for bi in range(5):
                lbl = f"Achievement {bi+1}" + (" *" if bi < 3 else " (optional)")
                val = bullets[bi] if bi < len(bullets) else ""
                new_val = st.text_area(lbl, value=val, key=f"jb_{i}_{bi}",
                                       placeholder="e.g. Reduced API latency by 40% via Redis caching tier", height=68)
                if bi < len(bullets):
                    bullets[bi] = new_val
                else:
                    bullets.append(new_val)
            job["bullets"] = [b for b in bullets if b.strip()]

            if len(d["work_experience"]) > 1:
                if st.button(f"🗑 Remove role {i+1}", type="secondary", key=f"delj_{i}"):
                    to_delete.append(i)

    for idx in sorted(to_delete, reverse=True):
        d["work_experience"].pop(idx)
        st.rerun()

    if st.button("+ Add another role", type="secondary", key="add_job"):
        d["work_experience"].append(_blank_job())
        st.rerun()

    ok = _validate_jobs(d["work_experience"])
    if not ok:
        st.warning("Each role needs a title, company, dates, and at least 3 achievements.")
    _nav(4, can_next=ok)


def _blank_edu() -> dict:
    return {"degree": "", "institution": "", "start_date": "", "end_date": "", "gpa": ""}


def _step5() -> None:
    _header(5, "your education")
    d = _d()
    if not d["education"]:
        d["education"].append(_blank_edu())

    to_delete = []
    for i, edu in enumerate(d["education"]):
        label = f"Degree {i+1}: {edu.get('degree', '') or '(untitled)'}"
        with st.expander(label, expanded=(i == len(d["education"]) - 1)):
            c1, c2 = st.columns(2)
            with c1:
                edu["degree"] = st.text_input("Degree / Qualification *", value=edu["degree"], key=f"ed_{i}", placeholder="BSc Computer Science")
                edu["institution"] = st.text_input("Institution *", value=edu["institution"], key=f"ei_{i}", placeholder="University of Oxford")
            with c2:
                edu["start_date"] = st.text_input("Start year *", value=edu.get("start_date", ""), key=f"es_{i}", placeholder="2018")
                edu["end_date"] = st.text_input("End year *", value=edu.get("end_date", ""), key=f"ee_{i}", placeholder="2022")
                edu["gpa"] = st.text_input("GPA / Grade (optional)", value=edu.get("gpa", ""), key=f"eg_{i}", placeholder="3.8 / 4.0")
            if len(d["education"]) > 1:
                if st.button(f"🗑 Remove degree {i+1}", type="secondary", key=f"dele_{i}"):
                    to_delete.append(i)

    for idx in sorted(to_delete, reverse=True):
        d["education"].pop(idx)
        st.rerun()

    if st.button("+ Add another degree", type="secondary", key="add_edu"):
        d["education"].append(_blank_edu())
        st.rerun()

    ok = all(e.get("degree") and e.get("institution") and e.get("start_date") and e.get("end_date") for e in d["education"])
    if not ok:
        st.warning("Please fill in all required education fields.")
    _nav(5, can_next=ok)


def _step6() -> None:
    _header(6, "your projects")
    d = _d()
    st.caption("Optional — add personal, academic, or open-source projects to showcase technical versatility.")

    to_delete = []
    for i, proj in enumerate(d["projects"]):
        label = f"Project {i+1}: {proj.get('name', '') or '(untitled)'}"
        with st.expander(label, expanded=(i == len(d["projects"]) - 1)):
            c1, c2 = st.columns(2)
            with c1:
                proj["name"] = st.text_input("Project name *", value=proj["name"], key=f"pn_{i}", placeholder="Inventory Tracker")
                ts = proj.get("tech_stack", [])
                ts_str = ", ".join(ts) if isinstance(ts, list) else ts
                proj["tech_stack"] = st.text_input("Tech stack (comma-separated) *", value=ts_str, key=f"pt_{i}", placeholder="Python, FastAPI, PostgreSQL")
            with c2:
                proj["link"] = st.text_input("Link (optional)", value=proj.get("link", ""), key=f"pl_{i}")
                proj["outcome"] = st.text_input("Outcome / impact", value=proj.get("outcome", ""), key=f"po_{i}", placeholder="Reduced inventory errors by 25%")
            proj["description"] = st.text_area("What it does *", value=proj.get("description", ""), key=f"pd_{i}", height=80, placeholder="A web app that…")
            if st.button(f"🗑 Remove project {i+1}", type="secondary", key=f"delp_{i}"):
                to_delete.append(i)

    for idx in sorted(to_delete, reverse=True):
        d["projects"].pop(idx)
        st.rerun()

    if st.button("+ Add a project", type="secondary", key="add_proj"):
        d["projects"].append({"name": "", "tech_stack": [], "description": "", "outcome": "", "link": ""})
        st.rerun()

    # Normalise tech_stack to list
    for proj in d["projects"]:
        ts = proj.get("tech_stack", "")
        if isinstance(ts, str):
            proj["tech_stack"] = [t.strip() for t in ts.split(",") if t.strip()]

    _nav(6)


TECH_OPTIONS = ["Python","JavaScript","TypeScript","Java","C++","C#","Go","Rust",
    "SQL","NoSQL","HTML","CSS","React","Next.js","Vue","Angular","Node.js",
    "FastAPI","Django","Flask","Spring Boot","Machine Learning","Deep Learning",
    "NLP","Data Analysis","Pandas","NumPy","TensorFlow","PyTorch","Scikit-learn",
    "Docker","Kubernetes","AWS","GCP","Azure","Terraform","Linux","Bash",
    "REST APIs","GraphQL","LangChain","Streamlit"]

TOOL_OPTIONS = ["Git","GitHub","GitLab","Jira","Confluence","Slack","Figma",
    "VS Code","IntelliJ","Postman","Jupyter","Tableau","Power BI","Excel",
    "Notion","Trello","Asana","Jenkins","GitHub Actions","CircleCI","Airflow",
    "dbt","Snowflake","BigQuery","Redis","Elasticsearch","MongoDB","PostgreSQL","MySQL"]

SOFT_OPTIONS = ["Communication","Teamwork","Leadership","Problem Solving",
    "Adaptability","Time Management","Critical Thinking","Mentoring",
    "Presentation","Stakeholder Management","Cross-functional Collaboration",
    "Project Management","Agile / Scrum"]

LANG_OPTIONS = ["English","Spanish","French","German","Mandarin","Arabic",
    "Hindi","Portuguese","Japanese","Russian","Italian","Korean"]


def _step7() -> None:
    _header(7, "your skills")
    d = _d()

    st.markdown("**Technical skills**")
    selected_tech = [s for s in d["technical_skills"] if s in TECH_OPTIONS]
    d["technical_skills"] = st.multiselect("Select or type", TECH_OPTIONS, default=selected_tech, key="ms_tech", placeholder="Choose or type…")
    custom_tech = st.text_input("Add custom technical skills (comma-separated)", key="ct_tech",
        value=", ".join(s for s in d["technical_skills"] if s not in TECH_OPTIONS))
    d["technical_skills"] = list(dict.fromkeys(d["technical_skills"] + [t.strip() for t in custom_tech.split(",") if t.strip()]))

    st.markdown("<br>**Tools & platforms**", unsafe_allow_html=True)
    selected_tools = [s for s in d["tool_skills"] if s in TOOL_OPTIONS]
    d["tool_skills"] = st.multiselect("Select or type", TOOL_OPTIONS, default=selected_tools, key="ms_tools", placeholder="Choose…")
    custom_tools = st.text_input("Add custom tools (comma-separated)", key="ct_tools",
        value=", ".join(s for s in d["tool_skills"] if s not in TOOL_OPTIONS))
    d["tool_skills"] = list(dict.fromkeys(d["tool_skills"] + [t.strip() for t in custom_tools.split(",") if t.strip()]))

    st.markdown("<br>**Soft skills**", unsafe_allow_html=True)
    selected_soft = [s for s in d["soft_skills"] if s in SOFT_OPTIONS]
    d["soft_skills"] = st.multiselect("Select", SOFT_OPTIONS, default=selected_soft, key="ms_soft", placeholder="Choose…")
    custom_soft = st.text_input("Add custom soft skills (comma-separated)", key="ct_soft",
        value=", ".join(s for s in d["soft_skills"] if s not in SOFT_OPTIONS))
    d["soft_skills"] = list(dict.fromkeys(d["soft_skills"] + [s.strip() for s in custom_soft.split(",") if s.strip()]))

    ok = bool(d["technical_skills"] or d["tool_skills"])
    if not ok:
        st.warning("Please add at least one technical skill or tool.")
    _nav(7, can_next=ok)


def _step8() -> None:
    _header(8, "the finishing touches")
    d = _d()
    st.caption("All optional — add what's relevant to your background.")

    st.markdown("**Certifications**")
    to_delete = []
    for i, cert in enumerate(d["certifications"]):
        c1, c2, c3, c4 = st.columns([3, 2, 1, 0.5])
        with c1:
            cert["name"] = st.text_input("Name", value=cert.get("name", ""), key=f"cen_{i}", placeholder="AWS Solutions Architect")
        with c2:
            cert["issuer"] = st.text_input("Issuer", value=cert.get("issuer", ""), key=f"cei_{i}", placeholder="Amazon Web Services")
        with c3:
            cert["year"] = st.text_input("Year", value=cert.get("year", ""), key=f"cey_{i}", placeholder="2023")
        with c4:
            if st.button("🗑", type="secondary", key=f"delc_{i}"):
                to_delete.append(i)
    for idx in sorted(to_delete, reverse=True):
        d["certifications"].pop(idx)
        st.rerun()
    if st.button("+ Add certification", type="secondary", key="add_cert"):
        d["certifications"].append({"name": "", "issuer": "", "year": ""})
        st.rerun()

    st.markdown("<br>**Awards / Honours** (one per line)", unsafe_allow_html=True)
    d["awards"] = st.text_area("Awards", value=d.get("awards", ""), key="awards_in",
        placeholder="Dean's List 2021\nHackathon Winner – FinHacks 2022", height=80, label_visibility="collapsed")

    st.markdown("<br>**Languages**", unsafe_allow_html=True)
    selected_langs = [l for l in d.get("languages", []) if l in LANG_OPTIONS]
    d["languages"] = st.multiselect("Languages spoken", LANG_OPTIONS, default=selected_langs, key="ms_langs", placeholder="Select…")
    custom_langs = st.text_input("Other languages (comma-separated)", key="ct_langs",
        value=", ".join(l for l in d.get("languages", []) if l not in LANG_OPTIONS))
    d["languages"] = list(dict.fromkeys(d["languages"] + [l.strip() for l in custom_langs.split(",") if l.strip()]))

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, _ = st.columns([1, 1, 3])
    with c1:
        if st.button("← Back", type="secondary", use_container_width=True, key="back_8"):
            _go(7)
    with c2:
        if st.button("Review →", type="primary", use_container_width=True, key="review_go"):
            st.toast("Questionnaire completed! Reviewing answers…", icon="🎉")
            st.session_state["form_step"] = TOTAL_STEPS + 1
            st.rerun()


# ============================================================
# Main render entry point
# ============================================================

def render() -> None:
    _init_state()
    step_map = {1: _step1, 2: _step2, 3: _step3, 4: _step4,
                5: _step5, 6: _step6, 7: _step7, 8: _step8}
    step = _step()
    if step in step_map:
        step_map[step]()
