"""
utils.py
-----------
Helper functions used by app.py:
  * PDF text extraction (pdfplumber)
  * Resume analysis via the Google Gemini SDK (google-genai)
  * SQLite persistence helpers
  * Misc validation / report-generation helpers
"""

import os
import re
import json
import sqlite3
from datetime import datetime

import pdfplumber
from google import genai

from config import Config

# --------------------------------------------------------------------------
# File validation
# --------------------------------------------------------------------------


def allowed_file(filename: str) -> bool:
    """Return True if the filename has an allowed extension."""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS
    )


# --------------------------------------------------------------------------
# PDF text extraction
# --------------------------------------------------------------------------


def extract_text_from_pdf(filepath: str) -> str:
    """
    Extract all readable text from a PDF resume using pdfplumber.
    Returns a single cleaned string. Raises ValueError if no text found.
    """
    extracted_chunks = []

    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            extracted_chunks.append(page_text)

    full_text = "\n".join(extracted_chunks).strip()

    if not full_text:
        raise ValueError(
            "No readable text could be extracted from this PDF. "
            "It may be a scanned/image-based resume."
        )

    # Collapse excessive whitespace
    full_text = re.sub(r"[ \t]+", " ", full_text)
    full_text = re.sub(r"\n{3,}", "\n\n", full_text)

    return full_text


# --------------------------------------------------------------------------
# Gemini AI analysis
# --------------------------------------------------------------------------

ANALYSIS_PROMPT_TEMPLATE = """
You are an expert technical recruiter, ATS (Applicant Tracking System) specialist,
and career coach. Analyze the following resume text thoroughly and honestly.

Return your ENTIRE response as a single valid JSON object and NOTHING else.
Do not wrap it in markdown code fences. Do not add any commentary before or
after the JSON. Follow this EXACT schema:

{{
  "resume_score": <integer 0-100, overall quality score>,
  "ats_score": <integer 0-100, how well this resume would pass an ATS>,
  "candidate_name": "<best-guess full name found in resume, or 'Not Found'>",
  "experience_summary": "<3-5 sentence professional summary of the candidate>",
  "technical_skills": ["skill1", "skill2", "..."],
  "soft_skills": ["skill1", "skill2", "..."],
  "missing_skills": ["skill1", "skill2", "..."],
  "projects": ["short description of project 1", "short description of project 2"],
  "education": ["degree - institution - year", "..."],
  "certifications": ["certification 1", "..."],
  "experience": [
    {{"role": "Job Title", "company": "Company Name", "duration": "Jan 2022 - Present", "highlights": "One line summary"}}
  ],
  "suggested_job_roles": [
    {{"role": "Job Title", "match_percent": <integer 0-100>}}
  ],
  "salary_estimation": {{
    "currency": "USD",
    "entry_level": "e.g. 45,000 - 60,000",
    "mid_level": "e.g. 65,000 - 90,000",
    "senior_level": "e.g. 95,000 - 130,000",
    "note": "one short disclaimer sentence about estimation accuracy"
  }},
  "career_roadmap": [
    {{"stage": "Short-term (0-6 months)", "action": "advice text"}},
    {{"stage": "Mid-term (6-18 months)", "action": "advice text"}},
    {{"stage": "Long-term (18+ months)", "action": "advice text"}}
  ],
  "resume_improvements": ["actionable improvement 1", "actionable improvement 2", "..."],
  "interview_questions": [
    {{"question": "question text", "category": "Technical|Behavioral|Situational"}}
  ]
}}

Rules:
- If a section cannot be determined from the resume, return an empty array or "Not Found" - never omit a key.
- Keep arrays to a maximum of 8 items each for readability.
- Be realistic and constructive with scores; do not always give high scores.
- Base salary estimation on the apparent role/domain/seniority; keep ranges generic if unclear.

RESUME TEXT:
\"\"\"
{resume_text}
\"\"\"
"""


def _clean_json_response(raw_text: str) -> str:
    """Strip markdown code fences if the model added them despite instructions."""
    text = raw_text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()
    return text


def analyze_resume_with_gemini(resume_text: str) -> dict:
    """
    Send resume text to Gemini and return a parsed dict following the
    ANALYSIS_PROMPT_TEMPLATE schema. Raises RuntimeError on failure.
    """
    if not Config.GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Please add it to your .env file."
        )

    # Trim extremely long resumes to keep prompt size reasonable
    trimmed_text = resume_text[:15000]

    prompt = ANALYSIS_PROMPT_TEMPLATE.format(resume_text=trimmed_text)

    client = genai.Client(api_key=Config.GEMINI_API_KEY)

    try:
        response = client.models.generate_content(
            model=Config.GEMINI_MODEL,
            contents=prompt,
        )
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Gemini API request failed: {exc}") from exc

    raw_text = response.text or ""
    cleaned = _clean_json_response(raw_text)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "Gemini returned an unexpected format and the response "
            "could not be parsed as JSON."
        ) from exc

    return data


# --------------------------------------------------------------------------
# Database helpers
# --------------------------------------------------------------------------


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the analyses table if it does not already exist."""
    conn = get_db_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            candidate_name TEXT,
            resume_score INTEGER,
            ats_score INTEGER,
            analysis_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def save_analysis(filename: str, analysis: dict) -> int:
    """Persist an analysis result and return its new row id."""
    conn = get_db_connection()
    cursor = conn.execute(
        """
        INSERT INTO analyses (filename, candidate_name, resume_score, ats_score, analysis_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            filename,
            analysis.get("candidate_name", "Not Found"),
            int(analysis.get("resume_score", 0) or 0),
            int(analysis.get("ats_score", 0) or 0),
            json.dumps(analysis),
            datetime.utcnow().isoformat(),
        ),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


def get_analysis(analysis_id: int):
    """Fetch a single analysis row by id, or None if not found."""
    conn = get_db_connection()
    row = conn.execute(
        "SELECT * FROM analyses WHERE id = ?", (analysis_id,)
    ).fetchone()
    conn.close()
    if row is None:
        return None
    result = dict(row)
    result["analysis"] = json.loads(result["analysis_json"])
    return result


def get_all_analyses(limit: int = 20):
    """Fetch the most recent analyses for the dashboard history list."""
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT id, filename, candidate_name, resume_score, ats_score, created_at "
        "FROM analyses ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


# --------------------------------------------------------------------------
# Report generation (plain-text downloadable report)
# --------------------------------------------------------------------------


def generate_text_report(analysis: dict, filename: str) -> str:
    """Build a human-readable plain-text report string for download."""
    lines = []
    line = lines.append

    line("=" * 70)
    line("        AI RESUME ANALYZER - DETAILED ANALYSIS REPORT")
    line("=" * 70)
    line(f"Original File     : {filename}")
    line(f"Generated On      : {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    line(f"Candidate Name    : {analysis.get('candidate_name', 'Not Found')}")
    line(f"Resume Score      : {analysis.get('resume_score', 'N/A')} / 100")
    line(f"ATS Score         : {analysis.get('ats_score', 'N/A')} / 100")
    line("-" * 70)

    line("\nEXPERIENCE SUMMARY")
    line(analysis.get("experience_summary", "Not Found"))

    line("\nTECHNICAL SKILLS")
    for s in analysis.get("technical_skills", []) or []:
        line(f"  - {s}")

    line("\nSOFT SKILLS")
    for s in analysis.get("soft_skills", []) or []:
        line(f"  - {s}")

    line("\nMISSING SKILLS")
    for s in analysis.get("missing_skills", []) or []:
        line(f"  - {s}")

    line("\nPROJECTS")
    for p in analysis.get("projects", []) or []:
        line(f"  - {p}")

    line("\nEDUCATION")
    for e in analysis.get("education", []) or []:
        line(f"  - {e}")

    line("\nCERTIFICATIONS")
    for c in analysis.get("certifications", []) or []:
        line(f"  - {c}")

    line("\nWORK EXPERIENCE")
    for exp in analysis.get("experience", []) or []:
        line(
            f"  - {exp.get('role', '')} at {exp.get('company', '')} "
            f"({exp.get('duration', '')}): {exp.get('highlights', '')}"
        )

    line("\nSUGGESTED JOB ROLES")
    for role in analysis.get("suggested_job_roles", []) or []:
        line(f"  - {role.get('role', '')} ({role.get('match_percent', 0)}% match)")

    salary = analysis.get("salary_estimation", {}) or {}
    line("\nSALARY ESTIMATION")
    line(f"  Currency     : {salary.get('currency', 'N/A')}")
    line(f"  Entry Level  : {salary.get('entry_level', 'N/A')}")
    line(f"  Mid Level    : {salary.get('mid_level', 'N/A')}")
    line(f"  Senior Level : {salary.get('senior_level', 'N/A')}")
    line(f"  Note         : {salary.get('note', '')}")

    line("\nCAREER ROADMAP")
    for stage in analysis.get("career_roadmap", []) or []:
        line(f"  [{stage.get('stage', '')}] {stage.get('action', '')}")

    line("\nRESUME IMPROVEMENTS")
    for imp in analysis.get("resume_improvements", []) or []:
        line(f"  - {imp}")

    line("\nPOTENTIAL INTERVIEW QUESTIONS")
    for q in analysis.get("interview_questions", []) or []:
        line(f"  [{q.get('category', '')}] {q.get('question', '')}")

    line("\n" + "=" * 70)
    line("Report generated by AI Resume Analyzer & Career Assistant")
    line("=" * 70)

    return "\n".join(lines)
