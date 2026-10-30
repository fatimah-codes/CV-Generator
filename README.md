# CV Studio 📄

**CV Studio** is a minimal, local Streamlit web application that guides users step-by-step through building an ATS-optimised (Applicant Tracking System) CV using LangChain and OpenAI (`gpt-4o-mini`).

All processing is 100% local (`localhost:8501`). Your OpenAI API key and CV data stay strictly in browser memory (`st.session_state`) during your session and are **never saved to disk, logs, environment files, or any external database**.

---

## 🌟 Key Features

1. **API-Key "Login" Gate**
   - Masked input with instant test call validation (`client.models.list()`).
   - Friendly error handling (invalid key, rate limit, network failure).
   - Sidebar session indicator and single-click **Log out** action that purges session state.
   - Complete multi-user isolation across concurrent browser sessions.

2. **8-Step Guided Questionnaire**
   - **Step 1:** Target role & optional job description (for natural keyword matching).
   - **Step 2:** Personal details (name, email, phone, location, LinkedIn, GitHub — no photos, DOB, or marital status).
   - **Step 3:** Professional summary inputs (experience, key strengths, career goal).
   - **Step 4:** Repeatable work experience (company, title, dates, location, and 3–5 impact-driven achievement bullets).
   - **Step 5:** Repeatable education entries (degree, institution, dates, GPA).
   - **Step 6:** Repeatable project entries (name, tech stack, description, outcome, link).
   - **Step 7:** Skills (technical, tools, soft skills with preset chips + custom tag inputs).
   - **Step 8:** Finishing touches (certifications, awards, languages).
   - Field validations, Back/Next navigation, and progress indicator.
   - Comprehensive **Review Screen** before generation.

3. **LangChain + OpenAI Generation Engine**
   - Structured JSON output with strict Pydantic schemas (`CvOutput`, `AtsAnalysis`).
   - Bullet rewriting using strong action verbs and quantified impact metrics.
   - Natural keyword injection from the target job description (no stuffing).
   - **Anti-Hallucination Safety Rule**: Never fabricates employers, dates, degrees, or metrics. Missing fields are omitted cleanly.
   - Built-in ATS keyword match scoring, missing keyword analysis, and actionable quality suggestions.

4. **Single-Column ATS-Safe Output & Exports**
   - Clean, standard section headings (Summary, Experience, Education, Projects, Skills, Certifications).
   - No complex tables, no icons, no columns, no text boxes.
   - **Live in-app preview**.
   - **Export to PDF**: Text-selectable, ATS-readable (built with `fpdf2`).
   - **Export to DOCX**: Word-compatible standard document (built with `python-docx`).
   - **Export to Markdown / TXT**: Plain text format.
   - **Section Editing & Regeneration**: Edit section text directly or trigger AI single-section rewriting (summary, experience, skills, or projects).

5. **Minimal Creative-Studio Design**
   - Palette: Pale lavender (`#f0eefa`), surface (`#dfe4f2`), pills/inputs (`#f7f8fa`), text/dark (`#080909`).
   - Typography: **Epilogue Black (900)** headlines and **DM Sans Regular (400)** body loaded with local WOFF2 files and Google Fonts with `font-synthesis: none`.
   - Responsive layout adapting smoothly to desktop and mobile screens (≤ 700px).

---

## 🚀 Quickstart

### 1. Prerequisites
- Python 3.10+
- An OpenAI API Key (starts with `sk-...`)

### 2. Install Dependencies
```bash
cd cv-studio
pip install -r requirements.txt
```

### 3. Launch App
```bash
streamlit run app.py
```

The app will open automatically in your browser at `http://localhost:8501`.

---

## 📂 Project Structure

```text
cv-studio/
├── app.py                  # Main entry point & session router
├── auth.py                 # OpenAI API key validation & session cleanup
├── requirements.txt        # Python package dependencies
├── styles.css              # Creative-studio CSS theme & typography
├── README.md               # Documentation & setup guide
├── pages/
│   ├── __init__.py
│   ├── login.py            # API key login gate & privacy notices
│   ├── questionnaire.py    # 8-step form with state persistence
│   ├── review.py           # Pre-generation answer review
│   └── result.py           # Live CV preview, ATS score, editor & exporters
├── llm/
│   ├── __init__.py
│   └── chain.py            # LangChain chains, Pydantic schemas, & ATS analyzer
├── export/
│   ├── __init__.py
│   ├── pdf.py              # Text-selectable single-column PDF builder
│   └── docx.py             # ATS-safe DOCX builder
└── assets/
    └── fonts/              # Local WOFF2 copies of Epilogue Black & DM Sans
```

---

## 🔒 Security & Privacy

- **Zero Persistence**: Your API key and personal data are kept strictly in memory in `st.session_state`.
- **No Disk Writes**: Nothing is ever saved to `.env`, local files, logs, or databases.
- **Immediate Cleanup**: Clicking **Log out** in the sidebar immediately wipes all session memory.
