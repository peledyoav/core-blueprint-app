import os
import re
import json
import time
import requests
from datetime import date
from data.core_blueprint import TRACKS


def _calc_years_experience(cv_text: str) -> int | None:
    """Find the earliest plausible year in CV work history and compute experience to today."""
    if not cv_text:
        return None
    current_year = date.today().year
    # Find all 4-digit years between 1970 and current year
    years = [int(y) for y in re.findall(r'\b(19[7-9]\d|20[0-2]\d)\b', cv_text)
             if int(y) <= current_year]
    if not years:
        return None
    earliest = min(years)
    return current_year - earliest


def _get_api_key():
    try:
        import streamlit as st
        key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
    except Exception:
        key = os.getenv("GROQ_API_KEY")
    if not key:
        raise Exception("GROQ_API_KEY not set in secrets")
    return key


def _call_llm(prompt: str, max_tokens: int = 7000) -> str:
    api_key = _get_api_key()
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": 0.7
    }
    for attempt in range(3):
        resp = requests.post(url, headers=headers, json=payload, timeout=180)
        if resp.ok:
            return resp.json()["choices"][0]["message"]["content"]
        # Rate limit — wait and retry
        if resp.status_code == 429:
            try:
                wait = float(resp.json()["error"]["message"].split("try again in ")[1].split("s")[0])
            except Exception:
                wait = 60
            wait = min(wait + 2, 65)  # small buffer, cap at 65s
            try:
                import streamlit as st
                st.info(f"מגבלת קצב Groq — ממתין {int(wait)} שניות ומנסה שוב...")
            except Exception:
                pass
            time.sleep(wait)
            continue
        # Other error
        try:
            msg = resp.json().get("error", {}).get("message", resp.text[:300])
        except Exception:
            msg = resp.text[:300]
        raise Exception(f"LLM error {resp.status_code}: {msg}")
    raise Exception("LLM rate limit: נסה שוב בעוד דקה")


SYSTEM_PROMPT = """You are Israel's top career advisor for high-tech professionals, combining deep expertise in:
- Israeli tech market dynamics (2024-2025): salaries, demand by role/field, layoff trends, AI impact
- Career psychology and coaching methodology
- Technical career paths across all high-tech domains
- The CORE Blueprint coaching framework

You produce brutally honest, highly specific, actionable analysis. You never give generic advice.
You always respond in valid JSON format exactly as specified. All text fields marked _he should be in Hebrew."""


def analyze_client(questionnaire: dict, client_info: dict) -> dict:
    part_a = questionnaire["part_a"]
    part_b = questionnaire["part_b"]
    cv_text = questionnaire.get("cv_text", "")

    # Cap CV text to avoid blowing token budget
    cv_snippet = (cv_text[:3000] + "\n[truncated]") if len(cv_text) > 3000 else (cv_text or "No CV provided")

    # Pre-compute years of experience from CV dates (overrides LLM guessing)
    computed_yrs = _calc_years_experience(cv_text)
    yrs_note = (f"VERIFIED years_total_experience={computed_yrs} (computed from earliest date in CV to today — use this exact number, ignore any years mentioned in profile text)"
                if computed_yrs else "Calculate years_total_experience from earliest date in CV to today, do NOT use numbers mentioned in profile text")

    prompt = f"""Career analysis for Israeli high-tech professional. Respond ONLY with valid JSON, no markdown.
Today: {date.today().strftime('%Y-%m-%d')}
{yrs_note}

CLIENT: {client_info['name']}
SCORES (1-10): challenges={part_a.get('q1','?')} balance={part_a.get('q2','?')} development={part_a.get('q3','?')} compensation={part_a.get('q4','?')} relationships={part_a.get('q5','?')} security={part_a.get('q6','?')} culture={part_a.get('q7','?')} meaning={part_a.get('q8','?')} actualization={part_a.get('q9','?')} influence={part_a.get('q10','?')}
DESIRED: field={part_b.get('field_desired','?')} role={part_b.get('role_desired','?')} direction={part_b.get('direction_preference','?')} ic_manager={part_b.get('ic_manager_goal','?')} company_stage={part_b.get('company_stage','?')} risk={part_b.get('risk_tolerance','?')} geo={part_b.get('geo_flexibility','?')} learning_hrs={part_b.get('learning_hours','?')} salary={part_b.get('salary_range','?')}
ENERGY: givers={part_b.get('energy_givers','?')} drainers={part_b.get('energy_drainers','?')}
GOALS: achievement={part_b.get('key_achievement','?')} concerns={part_b.get('main_concerns',[])} obstacles={part_b.get('main_obstacle',[])} skills_wanted={part_b.get('skills_to_develop','?')} success={part_b.get('success_definition','?')} coaching_goal={part_b.get('coaching_specific','?')}
CV: {cv_snippet}

RULES:
- All _he fields in Hebrew; be specific and personal, never generic
- recommended_directions: provide exactly 3, each with full 30/60/90 plan
- recommended_roles: 5 roles (first 3 timeframe="short" achievable <12mo, last 2 timeframe="long" 1-3yr)
- Salary ranges: Israeli market 2025 reality
- Resources: real course names, real Israeli communities

JSON schema:
{{
  "track": "A or B",
  "track_reason_he": "2-3 sentences",
  "executive_summary_he": "4-5 specific sentences",
  "spider_data": {{"daily_challenges":{part_a.get('q1',5)},"work_life_balance":{part_a.get('q2',5)},"professional_development":{part_a.get('q3',5)},"compensation":{part_a.get('q4',5)},"relationships":{part_a.get('q5',5)},"security":{part_a.get('q6',5)},"culture":{part_a.get('q7',5)},"meaning":{part_a.get('q8',5)},"self_actualization":{part_a.get('q9',5)},"influence":{part_a.get('q10',5)}}},
  "cv_profile": {{"years_total_experience":{computed_yrs if computed_yrs else "null"},"career_stage_he":"","key_technical_skills":[],"key_soft_skills":[],"companies_profile_he":"","career_trajectory_he":"","personal_brand_he":"","brand_gaps_he":"","market_positioning_he":""}},
  "energy_batteries": {{"connection":5,"progress":5,"influence":5}},
  "swot": {{"strengths_he":["s1","s2","s3","s4"],"weaknesses_he":["w1","w2","w3"],"opportunities_he":["o1","o2","o3"],"threats_he":["t1","t2","t3"]}},
  "market_analysis_he": "3-4 sentences",
  "insights_he": ["insight1","insight2","insight3","insight4"],
  "recommended_directions": [
    {{
      "title_he":"","description_he":"","why_good_fit_he":"",
      "fit_score":8,"market_demand":"high","market_demand_reason_he":"",
      "salary_range_ils":"","timeline_he":"",
      "skills_gap_he":["skill1","skill2"],"bridge_plan_he":"",
      "risk_level":"medium","reward_level":"high","risk_he":"","reward_he":"",
      "plan_30_days_he":["action1","action2","action3"],
      "plan_60_days_he":["action1","action2"],
      "plan_90_days_he":["action1","action2"]
    }},
    {{"title_he":"","description_he":"","why_good_fit_he":"","fit_score":7,"market_demand":"medium","market_demand_reason_he":"","salary_range_ils":"","timeline_he":"","skills_gap_he":[],"bridge_plan_he":"","risk_level":"low","reward_level":"medium","risk_he":"","reward_he":"","plan_30_days_he":[],"plan_60_days_he":[],"plan_90_days_he":[]}},
    {{"title_he":"","description_he":"","why_good_fit_he":"","fit_score":6,"market_demand":"high","market_demand_reason_he":"","salary_range_ils":"","timeline_he":"","skills_gap_he":[],"bridge_plan_he":"","risk_level":"medium","reward_level":"high","risk_he":"","reward_he":"","plan_30_days_he":[],"plan_60_days_he":[],"plan_90_days_he":[]}}
  ],
  "recommended_roles": [
    {{"title_he":"","timeframe":"short","reasoning_he":"2-3 sentences why this fits this person","salary_range_ils":"","description_he":""}},
    {{"title_he":"","timeframe":"short","reasoning_he":"","salary_range_ils":"","description_he":""}},
    {{"title_he":"","timeframe":"short","reasoning_he":"","salary_range_ils":"","description_he":""}},
    {{"title_he":"","timeframe":"long","reasoning_he":"","salary_range_ils":"","description_he":""}},
    {{"title_he":"","timeframe":"long","reasoning_he":"","salary_range_ils":"","description_he":""}}
  ],
  "quick_wins_he": ["win1 this week","win2 in 2 weeks","win3 builds momentum"],
  "networking_he": {{"communities":["c1","c2"],"events":["e1","e2"],"online":["o1","o2"]}},
  "resources": {{
    "courses":[{{"name":"","platform":"","why_he":""}},{{"name":"","platform":"","why_he":""}}],
    "books":[{{"title":"","author":"","why_he":""}},{{"title":"","author":"","why_he":""}}],
    "certifications":[{{"name":"","why_he":""}}]
  }},
  "cv_analysis": "3-4 sentences or 'לא צורף קורות חיים'",
  "cv_milestones": ["m1","m2","m3"],
  "personalized_syllabus": [
    {{"session":1,"personalized_focus_he":"","key_questions_he":["q1","q2","q3"],"homework_adaptation_he":""}},
    {{"session":2,"personalized_focus_he":"","key_questions_he":["q1","q2"],"homework_adaptation_he":""}},
    {{"session":3,"personalized_focus_he":"","key_questions_he":["q1","q2"],"homework_adaptation_he":""}},
    {{"session":4,"personalized_focus_he":"","key_questions_he":["q1","q2"],"homework_adaptation_he":""}},
    {{"session":5,"personalized_focus_he":"","key_questions_he":["q1","q2"],"homework_adaptation_he":""}},
    {{"session":6,"personalized_focus_he":"","key_questions_he":["q1","q2"],"homework_adaptation_he":""}},
    {{"session":7,"personalized_focus_he":"","key_questions_he":["q1","q2"],"homework_adaptation_he":""}},
    {{"session":8,"personalized_focus_he":"","key_questions_he":["q1","q2"],"homework_adaptation_he":""}},
    {{"session":9,"personalized_focus_he":"","key_questions_he":["q1","q2"],"homework_adaptation_he":""}},
    {{"session":10,"personalized_focus_he":"","key_questions_he":["q1","q2"],"homework_adaptation_he":""}}
  ]
}}"""

    def _extract_json(text: str) -> dict:
        """Try multiple strategies to extract valid JSON from LLM output."""
        text = text.strip()
        # Strip markdown code fences
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        # Find outermost { ... }
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            text = text[start:end + 1]
        return json.loads(text)

    # Try up to 2 times in case LLM returns malformed JSON
    raw = None
    last_err = None
    for attempt in range(2):
        try:
            raw = _call_llm(prompt, max_tokens=7000).strip()
            analysis = _extract_json(raw)
            break
        except (json.JSONDecodeError, ValueError) as e:
            last_err = e
            if attempt == 1:
                try:
                    import streamlit as st
                    st.error(f"הניתוח החזיר פורמט לא תקין (ניסיון {attempt+1}/2). נסה שוב.")
                except Exception:
                    pass
                raise Exception(f"LLM returned invalid JSON after 2 attempts: {e}") from e

    # Merge with CORE Blueprint syllabus template
    track_key = analysis.get("track", "A")
    if track_key not in TRACKS:
        track_key = "A"
    track_sessions = TRACKS[track_key]["sessions"]

    syllabus = []
    personalized = analysis.get("personalized_syllabus", [])
    for i, session_template in enumerate(track_sessions):
        p = personalized[i] if i < len(personalized) else {}
        syllabus.append({
            **session_template,
            "personalized_focus_he": p.get("personalized_focus_he", ""),
            "key_questions_he": p.get("key_questions_he", []),
            "homework_adaptation_he": p.get("homework_adaptation_he", ""),
        })

    return {
        "track": track_key,
        "track_reason_he": analysis.get("track_reason_he", ""),
        "executive_summary_he": analysis.get("executive_summary_he", ""),
        "spider_data": analysis.get("spider_data", {}),
        "cv_profile": analysis.get("cv_profile", {}),
        "energy_batteries": analysis.get("energy_batteries", {}),
        "swot": analysis.get("swot", {}),
        "market_analysis_he": analysis.get("market_analysis_he", ""),
        "insights": analysis.get("insights_he", []),
        "recommended_directions": analysis.get("recommended_directions", []),
        "recommended_roles": analysis.get("recommended_roles", []),
        "quick_wins": analysis.get("quick_wins_he", []),
        "networking": analysis.get("networking_he", {}),
        "resources": analysis.get("resources", {}),
        "cv_analysis": analysis.get("cv_analysis", ""),
        "cv_milestones": analysis.get("cv_milestones", []),
        "syllabus": syllabus,
    }


def extract_cv_text(file_bytes: bytes, file_name: str) -> str:
    if file_name.lower().endswith(".pdf"):
        try:
            import PyPDF2, io
            reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception:
            return ""
    elif file_name.lower().endswith(".docx"):
        try:
            import docx, io
            doc = docx.Document(io.BytesIO(file_bytes))
            return "\n".join(p.text for p in doc.paragraphs)
        except Exception:
            return ""
    return ""
