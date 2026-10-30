"""
views/login.py — Animated login gate with privacy notice.
"""
from __future__ import annotations

import streamlit as st
from auth import validate_key, store_key


def render() -> None:
    # Animated hero section with rich contrast
    st.markdown("""
<div style="text-align:center; padding: 2rem 0 1.2rem;">
  <div class="wordmark" style="font-size:36px; display:block; margin-bottom:14px;">cv studio ✦</div>
  <span class="pill-badge">ai-powered ats resume generator</span>
  <h1 style="margin-top:14px;">let's build your cv</h1>
  <p style="color:#475569; font-size:16px; max-width:480px; margin:10px auto 0; font-weight:500;">
    Paste your OpenAI key to enter. We'll craft an ATS-optimised, machine-readable CV in under 2 minutes — no account, no tracking.
  </p>
</div>
""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        key_input = st.text_input(
            "OpenAI API Key",
            type="password",
            placeholder="sk-...",
            help="Starts with sk-. Required to generate your CV.",
            key="login_key_input",
            label_visibility="visible",
        )

        enter = st.button("Enter the studio →", type="primary", use_container_width=True)

        st.markdown(
            "<small style='display:block;text-align:center;margin-top:12px;"
            "color:#64748b;font-weight:500;'>🔒 Your key stays strictly in this session memory — "
            "never saved to disk, logs, or databases.</small>",
            unsafe_allow_html=True,
        )

        if enter:
            key = key_input.strip()
            if not key:
                st.error("Please paste your OpenAI API key first.")
                return
            with st.spinner("Validating key with OpenAI…"):
                ok, err = validate_key(key)
            if ok:
                store_key(key)
                st.toast("Key validated successfully! Welcome to CV Studio.", icon="🎉")
                st.rerun()
            else:
                st.error(f"❌ {err}")

    st.markdown("<br>", unsafe_allow_html=True)

    with st.expander("🔑  Where do I get an API key?"):
        st.markdown(
            "1. Visit [platform.openai.com/api-keys](https://platform.openai.com/api-keys)\n"
            "2. Sign in → **Create new secret key**\n"
            "3. Copy the key (starts with `sk-`) and paste it above.\n\n"
            "You need an active OpenAI account with API billing enabled."
        )

    with st.expander("✨  What does CV Studio do?"):
        st.markdown("""
- **8-step guided form** — captures your background, metrics, and career goals
- **Action-verb rewriting** — transforms dull tasks into high-converting impact bullets
- **Target keyword injection** — pulls core skills directly from the pasted job description
- **ATS match scoring** — measures your keyword coverage and flags missing competencies
- **Multi-format export** — single-column selectable PDF, editable DOCX, and Markdown
- **Interactive section editor** — tweak text directly or regenerate individual sections
""")
