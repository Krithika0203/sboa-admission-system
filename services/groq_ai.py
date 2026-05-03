"""
services/groq_ai.py
All 7 AI features powered by Groq API.
Works on: local (.env), Hugging Face Spaces (secrets), Streamlit Cloud (st.secrets),
          Docker (-e flag), Railway/Render/Heroku (env vars).
"""
import os, json, re
from groq import Groq
from dotenv import load_dotenv

# Load .env for local development
load_dotenv()

def _get_api_key() -> str:
    # Hugging Face Spaces injects secrets as OS environment variables
    # This works for: HF Spaces, Docker, Railway, Render, local .env
    key = os.environ.get("GROQ_API_KEY", "").strip()
    if not key:
        key = os.getenv("GROQ_API_KEY", "").strip()
    return key

client = Groq(api_key=_get_api_key())

def _chat(messages: list, model: str = SMART_MODEL, temperature: float = 0.3, max_tokens: int = 800) -> str:
    """Base wrapper around groq chat completions — always reads key fresh."""
    # Re-read key each call so manual key input from sidebar takes effect
    current_key = _get_api_key()
    if not current_key:
        raise ValueError("GROQ_API_KEY not set. Paste your key in the sidebar.")
    fresh_client = Groq(api_key=current_key)
    response = fresh_client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content


def _parse_json(text: str) -> dict:
    """Strip markdown fences and parse JSON safely."""
    clean = re.sub(r"```json|```", "", text).strip()
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        return {"error": "Could not parse AI response", "raw": text}


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE 1 — AI Chatbot (24/7 Admission Assistant)
# ─────────────────────────────────────────────────────────────────────────────
SCHOOL_KNOWLEDGE = {
    "fees": {
        "LKG": "₹25,000/year", "UKG": "₹25,000/year",
        "Class 1-5": "₹30,000/year", "Class 6-8": "₹35,000/year",
        "Class 9-10": "₹40,000/year", "Class 11-12": "₹45,000/year",
    },
    "eligibility": {
        "LKG": "Age 3.5–4.5 years as of June 1",
        "Class 1": "Age 5.5–6.5 years, must have completed LKG",
    },
    "admission_dates": "Applications open: Jan 15 – Feb 28. Results: March 15.",
    "documents_required": [
        "Birth certificate", "Aadhar card (child + parents)",
        "Previous class marksheet", "Transfer certificate",
        "Passport-size photos (4)", "Residence proof",
    ],
    "schools": "13 SBOA schools across Tamil Nadu.",
    "contact": "admissions@sboa.edu.in | 044-2345-6789",
}

def chatbot_reply(user_message: str, history: list, language: str = "English") -> str:
    """Feature 1: Multilingual 24/7 admission chatbot."""
    lang_instruction = {
        "English": "Reply in clear English.",
        "Hindi": "हिंदी में उत्तर दें।",
        "Tamil": "தமிழில் பதில் கூறுங்கள்.",
    }.get(language, "Reply in English.")

    system = f"""You are a friendly admission assistant for SBOA Schools.
{lang_instruction}

School knowledge base:
{json.dumps(SCHOOL_KNOWLEDGE, indent=2)}

Rules:
- Answer ONLY admission-related questions.
- Be concise and warm.
- If unsure, say "Please contact admissions@sboa.edu.in".
- Never make up fees or dates not in the knowledge base.
"""
    messages = [{"role": "system", "content": system}]
    for h in history[-6:]:          # keep last 3 turns
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": user_message})

    return _chat(messages, model=SMART_MODEL, temperature=0.4, max_tokens=400)


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE 2 — OCR + Document AI (parse birth cert / marksheet text)
# ─────────────────────────────────────────────────────────────────────────────
def parse_document(raw_text: str, doc_type: str) -> dict:
    """Feature 2: Extract structured data from OCR text using Groq."""
    templates = {
        "birth_certificate": """{
  "student_name": "",
  "date_of_birth": "YYYY-MM-DD",
  "gender": "",
  "father_name": "",
  "mother_name": "",
  "place_of_birth": "",
  "registration_number": ""
}""",
        "marksheet": """{
  "student_name": "",
  "class": "",
  "school_name": "",
  "year": "",
  "subjects": [{"name": "", "marks_obtained": 0, "max_marks": 0}],
  "total_marks": 0,
  "percentage": 0,
  "grade": ""
}""",
        "aadhar": """{
  "name": "",
  "dob": "YYYY-MM-DD",
  "gender": "",
  "aadhar_number": "XXXX-XXXX-XXXX",
  "address": ""
}""",
    }

    prompt = f"""Extract structured data from this {doc_type}.
Return ONLY valid JSON — no explanation, no markdown.

Document text:
{raw_text}

JSON template to fill:
{templates.get(doc_type, '{}')}
"""
    result = _chat([{"role": "user", "content": prompt}], model=FAST_MODEL, temperature=0, max_tokens=600)
    return _parse_json(result)


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE 3 — Auto Form Filling
# ─────────────────────────────────────────────────────────────────────────────
def auto_fill_form(doc_data: dict, form_fields: list) -> dict:
    """Feature 3: Map extracted doc data to application form fields."""
    prompt = f"""Map this document data to the application form fields.
Return ONLY valid JSON — keys must match the form fields exactly.
If a field cannot be filled, use null.

Document data:
{json.dumps(doc_data, indent=2)}

Form fields to fill:
{json.dumps(form_fields, indent=2)}

Rules:
- Dates must be DD/MM/YYYY
- Do not invent information
- "student_name" from "name" or "student_name" in doc data
"""
    result = _chat([{"role": "user", "content": prompt}], model=FAST_MODEL, temperature=0, max_tokens=500)
    return _parse_json(result)


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE 4 — Document Validation
# ─────────────────────────────────────────────────────────────────────────────
REQUIRED_DOCS = {
    "LKG": ["birth_certificate", "aadhar", "photos"],
    "Class 1": ["birth_certificate", "aadhar", "photos"],
    "Class 6": ["birth_certificate", "aadhar", "marksheet", "transfer_certificate", "photos"],
    "Class 9": ["birth_certificate", "aadhar", "marksheet", "transfer_certificate", "photos"],
    "Class 11": ["birth_certificate", "aadhar", "marksheet", "transfer_certificate", "photos"],
}

def validate_document(raw_text: str, doc_type: str, class_applying: str = "Class 1") -> dict:
    """Feature 4: Validate uploaded document for completeness and authenticity."""
    checklist = REQUIRED_DOCS.get(class_applying, REQUIRED_DOCS["Class 1"])

    prompt = f"""Validate this {doc_type} document for a school admission.

Document text:
{raw_text}

Check:
1. Does it look like a real {doc_type}?
2. Are all important fields present (name, date, signatures/seals mentioned)?
3. Is the document likely valid or suspicious?

Return ONLY valid JSON:
{{
  "is_valid": true/false,
  "confidence_score": 0-100,
  "document_type_confirmed": true/false,
  "issues": ["list any problems"],
  "missing_fields": ["fields not found"],
  "recommendation": "accept / reject / manual_review"
}}
"""
    result = _chat([{"role": "user", "content": prompt}], model=FAST_MODEL, temperature=0, max_tokens=400)
    return _parse_json(result)


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE 5 — Fraud / Duplicate Detection
# ─────────────────────────────────────────────────────────────────────────────
def detect_fraud(new_app: dict, existing_apps: list) -> dict:
    """Feature 5: Detect duplicate or fraudulent applications."""
    prompt = f"""Detect if this new application is a duplicate or fraudulent.

New application:
{json.dumps(new_app, indent=2)}

Sample of existing applications:
{json.dumps(existing_apps[:30], indent=2)}

Check for:
- Same student name + DOB (allow spelling variations)
- Same parent phone or email across different student names
- Applying to many schools same day
- Inconsistencies (age vs class applied)

Return ONLY valid JSON:
{{
  "is_duplicate": true/false,
  "is_suspicious": true/false,
  "confidence": 0-100,
  "matched_id": "app_id or null",
  "flags": ["list of red flags"],
  "reason": "brief explanation"
}}
"""
    result = _chat([{"role": "user", "content": prompt}], model=SMART_MODEL, temperature=0, max_tokens=350)
    return _parse_json(result)


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE 6 — Applicant Scoring (Smart Prioritization)
# ─────────────────────────────────────────────────────────────────────────────
def score_applicant(application: dict) -> dict:
    """Feature 6: Hybrid rule-based + AI scoring for admission priority."""
    score = 0
    breakdown = []

    # Rule-based scoring
    dist = application.get("distance_km", 10)
    if dist <= 1:   score += 30; breakdown.append({"criteria": "Distance ≤1 km",  "points": 30})
    elif dist <= 3: score += 20; breakdown.append({"criteria": "Distance ≤3 km",  "points": 20})
    elif dist <= 5: score += 10; breakdown.append({"criteria": "Distance ≤5 km",  "points": 10})

    if application.get("has_sibling"):
        score += 25; breakdown.append({"criteria": "Sibling studying", "points": 25})

    pct = application.get("percentage", 0)
    if pct >= 90:   score += 20; breakdown.append({"criteria": "Marks ≥90%", "points": 20})
    elif pct >= 75: score += 12; breakdown.append({"criteria": "Marks ≥75%", "points": 12})

    if application.get("is_ews"):
        score += 10; breakdown.append({"criteria": "EWS quota",       "points": 10})
    if application.get("is_staff_child"):
        score += 15; breakdown.append({"criteria": "Staff child",     "points": 15})

    # AI bonus (max 20 pts)
    prompt = f"""A student is applying to SBOA school. Rule-based score so far: {score}/85.

Application details:
{json.dumps(application, indent=2)}

Consider:
- Special achievements (sports, arts, Olympiad)
- Single-parent household
- Any notable circumstances

Award 0–20 BONUS points and write a short admin note.

Return ONLY valid JSON:
{{
  "bonus_points": 0,
  "bonus_reason": "",
  "recommendation": "high_priority / medium / low",
  "admin_note": "one sentence for admin"
}}
"""
    ai_result = _parse_json(
        _chat([{"role": "user", "content": prompt}], model=SMART_MODEL, temperature=0.2, max_tokens=250)
    )

    bonus = min(int(ai_result.get("bonus_points", 0)), 20)
    final_score = min(score + bonus, 100)
    breakdown.append({"criteria": "AI bonus: " + ai_result.get("bonus_reason", ""), "points": bonus})

    return {
        "final_score": final_score,
        "rule_score": score,
        "ai_bonus": bonus,
        "breakdown": breakdown,
        "recommendation": ai_result.get("recommendation", "medium"),
        "admin_note": ai_result.get("admin_note", ""),
    }


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE 7 — Analytics & Forecasting
# ─────────────────────────────────────────────────────────────────────────────
def generate_forecast(current_stats: dict) -> dict:
    """Feature 7: AI-powered demand forecasting and drop-off analysis."""
    prompt = f"""Analyze this SBOA school admission data and provide actionable forecasts.

Current season statistics:
{json.dumps(current_stats, indent=2)}

Provide analysis as ONLY valid JSON:
{{
  "demand_forecast": {{
    "expected_total_applications": 0,
    "confidence": "high/medium/low",
    "peak_week": "e.g. Feb 15-22",
    "schools_filling_fast": []
  }},
  "drop_off_analysis": {{
    "highest_drop_off_stage": "",
    "drop_off_percentage": 0,
    "suggested_fix": ""
  }},
  "conversion_forecast": {{
    "predicted_rate_percent": 0,
    "trend": "improving/declining/stable"
  }},
  "alerts": ["list of urgent items needing attention"],
  "recommendations": ["list of 3-5 actionable steps for admin"]
}}
"""
    result = _chat([{"role": "user", "content": prompt}], model=SMART_MODEL, temperature=0.3, max_tokens=700)
    return _parse_json(result)
