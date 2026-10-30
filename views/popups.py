"""
views/popups.py — Interactive animated modal popups for CV Studio.
"""
from __future__ import annotations

import streamlit as st


@st.dialog("💡 ATS Strategy & Action Verbs Guide")
def show_ats_guide_popup() -> None:
    """Animated popup modal providing ATS secrets, keyword strategies, and power verbs."""
    st.markdown('<span class="pill-badge">expert cheatsheet</span>', unsafe_allow_html=True)
    st.markdown("### how ats algorithms score your cv")
    st.markdown(
        "Applicant Tracking Systems (ATS) scan for **exact keyword frequency**, "
        "clean single-column hierarchies, and impact-driven bullet formulas."
    )

    tab_verbs, tab_metrics, tab_keywords = st.tabs([
        "⚡ Power Action Verbs",
        "📈 The Metric Formula",
        "🎯 Keyword Strategy",
    ])

    with tab_verbs:
        st.markdown("**Replace passive words with high-impact verbs:**")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            **Technical & Building:**
            - *Architected*, *Engineered*, *Deployed*
            - *Refactored*, *Automated*, *Scaled*
            - *Implemented*, *Containerized*, *Optimized*
            
            **Leadership & Ownership:**
            - *Spearheaded*, *Directed*, *Orchestrated*
            - *Mentored*, *Pioneered*, *Championed*
            """)
        with col2:
            st.markdown("""
            **Impact & Optimization:**
            - *Maximized*, *Accelerated*, *Slashed*
            - *Consolidated*, *Transformed*, *Negotiated*
            
            **Research & Strategy:**
            - *Benchmarked*, *Forecasted*, *Audited*
            - *Uncovered*, *Formulated*, *Standardized*
            """)

    with tab_metrics:
        st.markdown("**The Winning Bullet Formula (XYZ):**")
        st.info("Accomplished **[X]** as measured by **[Y]**, by doing **[Z]**.")
        st.markdown("""
        **Strong Examples:**
        - *Reduced API latency by 45% (down to 120ms) by designing a multi-layer Redis caching tier.*
        - *Scaled transaction throughput by 3.2x across 12 microservices, supporting 2.5M daily active users.*
        - *Automated CI/CD deployment pipelines, cutting release cycle time from 4 days to 25 minutes.*
        - *Recovered \\$120K in cloud compute waste by benchmarking and right-sizing AWS Kubernetes clusters.*
        """)

    with tab_keywords:
        st.markdown("**How to pick the right keywords:**")
        st.markdown("""
        1. **Mirror the Job Description**: If the posting says *PostgreSQL*, don't just write *relational DB*.
        2. **Standard Headers**: Stick to *Summary*, *Experience*, *Education*, *Skills*.
        3. **No Hidden Tricks**: White text, tables, or text boxes get parsed as junk or discarded by Taleo, Workday, and Greenhouse.
        4. **Our AI engine handles this automatically** when you paste the target JD in Step 1!
        """)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Got it, let's build! →", type="primary", use_container_width=True):
        st.rerun()


@st.dialog("✨ Action Verbs & Metrics Helper")
def show_bullet_helper_popup() -> None:
    """Quick helper popup for drafting achievements."""
    st.markdown("### quick achievement ideas")
    st.markdown("Choose a category to view high-converting bullet starters:")

    category = st.selectbox(
        "Focus Area",
        ["Speed & Performance", "Cost & Cloud Savings", "Scale & Volume", "Team & Mentorship"],
    )

    if category == "Speed & Performance":
        st.markdown("""
        - *Accelerated build times by [X]% by parallelizing test suites in GitHub Actions.*
        - *Optimized slow database queries, boosting page load speeds from [X]s to [Y]s.*
        """)
    elif category == "Cost & Cloud Savings":
        st.markdown("""
        - *Eliminated \\$[X]K in monthly AWS expenses by migrating idle workloads to serverless.*
        - *Negotiated third-party SaaS licenses, saving the department [X]% annually.*
        """)
    elif category == "Scale & Volume":
        st.markdown("""
        - *Supported [X]M peak events per day with 99.99% uptime by implementing Kafka message queues.*
        - *Redesigned search architecture, handling [X]x traffic growth without downtime.*
        """)
    else:
        st.markdown("""
        - *Mentored [X] junior and mid-level engineers, resulting in [Y] promotions within 1 year.*
        - *Established agile code review standards, increasing sprint velocity by [X]%.*
        """)

    if st.button("Close Helper", type="primary", use_container_width=True):
        st.rerun()
