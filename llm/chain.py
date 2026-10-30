"""
llm/chain.py — LangChain + OpenAI CV generation pipeline.

Pydantic schemas define the structured output; the LLM chain fills them
from the user's raw questionnaire answers.

SAFETY RULE: The model is instructed never to fabricate facts.
             If data is missing, it omits that field.
"""

from __future__ import annotations

import json
import re
from typing import Optional
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser


# ============================================================
# Pydantic schemas — structured CV output
# ============================================================

class ContactInfo(BaseModel):
    full_name: str = Field(description="Full name of the candidate")
    email: str = Field(description="Email address")
    phone: str = Field(description="Phone number")
    location: str = Field(description="City and country")
    linkedin: Optional[str] = Field(default=None, description="LinkedIn URL or handle")
    github: Optional[str] = Field(default=None, description="GitHub or portfolio URL")


class WorkEntry(BaseModel):
    company: str
    title: str
    start_date: str
    end_date: str  # "Present" if current
    location: Optional[str] = None
    bullets: list[str] = Field(description="3-5 achievement bullets, action verb + metric")


class EducationEntry(BaseModel):
    degree: str
    institution: str
    start_date: str
    end_date: str
    gpa: Optional[str] = None


class ProjectEntry(BaseModel):
    name: str
    tech_stack: list[str]
    description: str
    outcome: Optional[str] = None
    link: Optional[str] = None


class SkillsSection(BaseModel):
    technical: list[str]
    tools: list[str]
    soft_skills: list[str]


class CertificationEntry(BaseModel):
    name: str
    issuer: Optional[str] = None
    year: Optional[str] = None


class CvOutput(BaseModel):
    contact: ContactInfo
    summary: str = Field(description="3-4 sentence professional summary, ATS-optimised")
    work_experience: list[WorkEntry]
    education: list[EducationEntry]
    projects: list[ProjectEntry]
    skills: SkillsSection
    certifications: list[CertificationEntry] = Field(default_factory=list)
    awards: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)


class AtsAnalysis(BaseModel):
    score: int = Field(description="ATS match score 0-100")
    matched_keywords: list[str] = Field(default_factory=list)
    missing_keywords: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(description="3-6 short actionable tips")
    strengths: list[str] = Field(description="2-4 things done well")


# ============================================================
# Generation chain
# ============================================================

CV_SYSTEM_PROMPT = """You are an expert CV writer and ATS specialist. Your task is to
produce a polished, ATS-friendly CV in strict JSON format matching the schema below.

CRITICAL RULES — follow without exception:
1. NEVER invent, fabricate, or embellish any fact: no made-up employers, dates,
   degrees, project names, or metrics. Use ONLY what the user provided.
2. If information is missing or unclear, omit that field or leave it blank — do not guess.
3. Rewrite bullet points using strong action verbs (Led, Built, Reduced, Increased…)
   followed by a measurable result whenever the user supplied numbers or percentages.
   If no metric was given, keep the bullet factual and concise — do not add fake numbers.
4. The professional summary must be 3-4 sentences, written in third person or first person
   consistently, and must incorporate relevant keywords from the job description naturally
   (no keyword stuffing).
5. Keep language professional, clear, and free of clichés.
6. Return ONLY valid JSON — no markdown fences, no extra commentary.

JSON schema you must follow:
{schema}
"""

CV_USER_PROMPT = """Target Role: {target_role}

Job Description (use keywords naturally):
{job_description}

Candidate Data:
{candidate_data}

Return the completed CV as JSON exactly matching the schema. Remember: do not invent any facts."""


ATS_SYSTEM_PROMPT = """You are an ATS (Applicant Tracking System) expert.
Analyse the CV below against the job description and return a JSON object matching this schema:
{schema}

Be specific and actionable in your suggestions. Score conservatively: 70+ is a good match.
Return ONLY valid JSON."""

ATS_USER_PROMPT = """Job Description:
{job_description}

CV Content:
{cv_content}"""


def _make_llm(api_key: str, temperature: float = 0.3) -> ChatOpenAI:
    """Instantiate ChatOpenAI with the session key — never logs the key."""
    return ChatOpenAI(
        api_key=api_key,
        model="gpt-4o-mini",
        temperature=temperature,
    )


def generate_cv(api_key: str, candidate_data: dict) -> CvOutput:
    """
    Run the CV-generation chain.

    Args:
        api_key: User's OpenAI key (session only, never stored).
        candidate_data: Dict of all questionnaire answers.

    Returns:
        CvOutput Pydantic object.
    """
    llm = _make_llm(api_key)
    parser = JsonOutputParser(pydantic_object=CvOutput)

    prompt = ChatPromptTemplate.from_messages([
        ("system", CV_SYSTEM_PROMPT),
        ("human", CV_USER_PROMPT),
    ])

    chain = prompt | llm | parser

    schema_str = json.dumps(CvOutput.model_json_schema(), indent=2)

    raw = chain.invoke({
        "schema": schema_str,
        "target_role": candidate_data.get("target_role", "Not specified"),
        "job_description": candidate_data.get("job_description", "Not provided"),
        "candidate_data": json.dumps(candidate_data, indent=2, ensure_ascii=False),
    })

    # raw is already a dict from JsonOutputParser; validate with Pydantic
    return CvOutput.model_validate(raw)


def regenerate_section(api_key: str, section: str, current_cv: dict, candidate_data: dict) -> dict:
    """
    Regenerate a single CV section without touching others.

    Returns the updated dict for that section only.
    """
    llm = _make_llm(api_key)

    section_prompts = {
        "summary": "Rewrite only the professional summary. Return JSON: {\"summary\": \"...\"}",
        "work_experience": "Rewrite only the work_experience bullets. Return JSON: {\"work_experience\": [...]}",
        "skills": "Rewrite only the skills section. Return JSON: {\"skills\": {...}}",
        "projects": "Rewrite only the projects section. Return JSON: {\"projects\": [...]}",
    }

    instruction = section_prompts.get(section, f"Rewrite only the '{section}' section.")

    messages = [
        ("system", "You are an expert CV writer. " + instruction +
                   " NEVER invent facts. Use only the provided data. Return ONLY valid JSON."),
        ("human", f"Current CV data:\n{json.dumps(current_cv, indent=2)}\n\nCandidate raw data:\n{json.dumps(candidate_data, indent=2)}\n\nJob Description:\n{candidate_data.get('job_description', '')}"),
    ]

    prompt = ChatPromptTemplate.from_messages(messages)
    chain = prompt | llm

    response = chain.invoke({})
    text = response.content.strip()

    # Strip possible markdown fences
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    return json.loads(text)


def analyse_ats(api_key: str, cv_data: dict, job_description: str) -> AtsAnalysis:
    """
    Analyse the generated CV against the job description.

    Returns an AtsAnalysis Pydantic object.
    """
    if not job_description.strip():
        return AtsAnalysis(
            score=0,
            suggestions=["Paste a job description for keyword analysis."],
            strengths=["CV structure looks good."],
        )

    llm = _make_llm(api_key, temperature=0.1)
    parser = JsonOutputParser(pydantic_object=AtsAnalysis)

    prompt = ChatPromptTemplate.from_messages([
        ("system", ATS_SYSTEM_PROMPT),
        ("human", ATS_USER_PROMPT),
    ])

    chain = prompt | llm | parser
    schema_str = json.dumps(AtsAnalysis.model_json_schema(), indent=2)

    cv_text = _cv_to_plain_text(cv_data)

    raw = chain.invoke({
        "schema": schema_str,
        "job_description": job_description,
        "cv_content": cv_text,
    })

    return AtsAnalysis.model_validate(raw)


# ============================================================
# Internal helpers
# ============================================================

def _cv_to_plain_text(cv: dict) -> str:
    """Convert the CV dict to a plain-text blob for ATS analysis."""
    lines: list[str] = []
    c = cv.get("contact", {})
    lines.append(c.get("full_name", ""))
    lines.append(cv.get("summary", ""))

    for job in cv.get("work_experience", []):
        lines.append(f"{job.get('title')} at {job.get('company')}")
        for b in job.get("bullets", []):
            lines.append(f"- {b}")

    for edu in cv.get("education", []):
        lines.append(f"{edu.get('degree')} — {edu.get('institution')}")

    for proj in cv.get("projects", []):
        lines.append(f"Project: {proj.get('name')} — {proj.get('description')}")

    sk = cv.get("skills", {})
    lines.append("Technical: " + ", ".join(sk.get("technical", [])))
    lines.append("Tools: " + ", ".join(sk.get("tools", [])))

    for cert in cv.get("certifications", []):
        lines.append(f"Cert: {cert.get('name')}")

    return "\n".join(filter(None, lines))
