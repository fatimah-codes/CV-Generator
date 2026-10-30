"""
app.py — Entry point and session router for CV Studio.

Run with: streamlit run app.py
"""

from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="CV Studio",
    page_icon="✨",
    layout="centered",
    initial_sidebar_state="expanded",
)

import auth
from views import login, questionnaire, review, result
from views.popups import show_ats_guide_popup


# ============================================================
# CSS + Fonts + Animation JS injection
# ============================================================

def _load_styles() -> None:
    """Embed local fonts as base64 @font-face, then inject styles.css."""
    css_path = Path(__file__).parent / "styles.css"
    css_body = css_path.read_text(encoding="utf-8") if css_path.exists() else ""

    fonts_dir = Path(__file__).parent / "assets" / "fonts"
    font_faces: list[str] = []

    epilogue_path = fonts_dir / "Epilogue-Black.woff2"
    if epilogue_path.exists():
        b64 = base64.b64encode(epilogue_path.read_bytes()).decode()
        font_faces.append(f"""@font-face {{
  font-family: 'Epilogue';
  src: url('data:font/woff2;base64,{b64}') format('woff2');
  font-weight: 900;
  font-style: normal;
  font-display: swap;
}}""")

    dmsans_path = fonts_dir / "DMSans-Regular.woff2"
    if dmsans_path.exists():
        b64 = base64.b64encode(dmsans_path.read_bytes()).decode()
        font_faces.append(f"""@font-face {{
  font-family: 'DM Sans';
  src: url('data:font/woff2;base64,{b64}') format('woff2');
  font-weight: 400;
  font-style: normal;
  font-display: swap;
}}""")

    full_css = "\n".join(font_faces) + "\n" + css_body
    st.markdown(f"<style>{full_css}</style>", unsafe_allow_html=True)


_load_styles()


# ============================================================
# Sidebar
# ============================================================

def _sidebar() -> None:
    with st.sidebar:
        st.markdown('<div class="wordmark">cv studio</div>', unsafe_allow_html=True)
        st.caption("ATS-friendly CV generator")
        st.markdown("---")

        if not auth.is_authenticated():
            st.markdown('<span class="pill-badge">locked</span>', unsafe_allow_html=True)
            st.markdown(
                "<small style='color:#475569'>Paste your OpenAI key on the right to begin. "
                "No account or database needed.</small>",
                unsafe_allow_html=True,
            )
            return

        st.markdown('<span class="pill-badge">session active</span>', unsafe_allow_html=True)
        st.markdown(
            "<small style='color:#475569'>Key is in memory only — never saved anywhere.</small>",
            unsafe_allow_html=True,
        )
        st.markdown("<br>**Overview**", unsafe_allow_html=True)

        current_page = st.session_state.get("app_page", "questionnaire")
        step = st.session_state.get("form_step", 1)

        steps = [
            "1. Target role & JD",
            "2. Personal details",
            "3. Summary inputs",
            "4. Work experience",
            "5. Education",
            "6. Projects",
            "7. Skills",
            "8. Finishing touches",
        ]

        for idx, name in enumerate(steps, start=1):
            if current_page == "questionnaire" and step == idx:
                st.markdown(
                    f"<span style='color:#6d28d9;font-weight:700'>→ {name}</span>",
                    unsafe_allow_html=True,
                )
            elif current_page == "questionnaire" and step > idx:
                st.markdown(
                    f"<span style='color:#059669;font-weight:500'>✓ {name}</span>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"<span style='color:#64748b'>&nbsp;&nbsp;{name}</span>",
                    unsafe_allow_html=True,
                )

        review_active = current_page == "review"
        result_active = current_page == "result"

        st.markdown(
            f"<span style='color:{'#6d28d9;font-weight:700' if review_active else '#64748b'}'>"
            f"{'→ ' if review_active else '&nbsp;&nbsp;'}Review answers</span>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<span style='color:{'#6d28d9;font-weight:700' if result_active else '#64748b'}'>"
            f"{'→ ' if result_active else '&nbsp;&nbsp;'}Generated CV & export</span>",
            unsafe_allow_html=True,
        )

        st.markdown("---")

        if st.button("💡 ATS Pro Secrets Guide", type="secondary", use_container_width=True):
            show_ats_guide_popup()

        if current_page == "result":
            if st.button("✏️ Edit answers", type="secondary", use_container_width=True):
                st.session_state["app_page"] = "questionnaire"
                st.session_state["form_step"] = 1
                st.rerun()

        if st.button("🚪 Log out", type="secondary", use_container_width=True):
            auth.logout()
            st.rerun()


_sidebar()


# ============================================================
# Main routing
# ============================================================

def main() -> None:
    if not auth.is_authenticated():
        login.render()
        return

    page = st.session_state.get("app_page", "questionnaire")
    step = st.session_state.get("form_step", 1)

    if page == "result":
        result.render()
    elif page == "review" or step > 8:
        review.render()
    else:
        questionnaire.render()


main()
