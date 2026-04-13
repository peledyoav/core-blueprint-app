import os
import json
import requests
from data.core_blueprint import TRACKS


def _get_api_key():
    try:
        import streamlit as st
        key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
    except Exception:
        key = os.getenv("GROQ_API_KEY")
    if not key:
        raise Exception("GROQ_API_KEY not set in secrets")
    return key


def _call_llm(prompt: str, max_tokens: int = 8000) -> str:
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
    resp = requests.post(url, headers=headers, json=payload, timeout=180)
    if not resp.ok:
        try:
            err = resp.json()
            msg = err.get("error", {}).get("message", resp.text[:300])
        except Exception:
            msg = resp.text[:300]
        try:
            import streamlit as st
            st.error(f"LLM error {resp.status_code}: {msg}")
        except Exception:
            pass
        raise Exception(f"LLM error {resp.status_code}")
    return resp.json()["choices"][0]["message"]["content"]


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

    prompt = f"""Analyze this high-tech professional's complete career data and produce a comprehensive coaching report.

CLIENT: {client_info['name']}

=== PART A: SATISFACTION SCORES (1=very low, 10=very high) ===
1. Daily challenges & role fit: {part_a.get('q1','N/A')}
2. Work-life balance: {part_a.get('q2','N/A')}
3. Professional development: {part_a.get('q3','N/A')}
4. Compensation & financial wellbeing: {part_a.get('q4','N/A')}
5. Workplace relationships: {part_a.get('q5','N/A')}
6. Employment security: {part_a.get('q6','N/A')}
7. Organizational culture: {part_a.get('q7','N/A')}
8. Meaning & purpose: {part_a.get('q8','N/A')}
9. Self-actualization & interest: {part_a.get('q9','N/A')}
10. Influence & initiative: {part_a.get('q10','N/A')}

=== PART B: PROFESSIONAL DIRECTION ===
Desired field: {part_b.get('field_desired','N/A')}
Desired role: {part_b.get('role_desired','N/A')}
Direction attraction: {part_b.get('direction_preference','N/A')}
IC/Manager goal: {part_b.get('ic_manager_goal','N/A')}
Preferred company stage (1=Startup, 10=Enterprise): {part_b.get('company_stage','N/A')}
Energy givers: {part_b.get('energy_givers','N/A')}
Energy drainers: {part_b.get('energy_drainers','N/A')}
Risk tolerance (1=stability, 10=loves risk): {part_b.get('risk_tolerance','N/A')}
Geographic flexibility: {part_b.get('geo_flexibility','N/A')}
Learning hours/week available: {part_b.get('learning_hours','N/A')}
Salary expectation (ILS/month gross): {part_b.get('salary_range','N/A')}
Key achievement: {part_b.get('key_achievement','N/A')}
Main concerns: {part_b.get('main_concerns',[])}
Main obstacles: {part_b.get('main_obstacle',[])}
Skills to develop: {part_b.get('skills_to_develop','N/A')}
Success definition: {part_b.get('success_definition','N/A')}
Additional coaching goal: {part_b.get('coaching_specific','N/A')}

=== CV / RESUME TEXT ===
{cv_text if cv_text else "No CV provided - infer from questionnaire data only"}

=== INSTRUCTIONS ===
1. Extract from CV (if provided): exact years of experience, career progression, technical skills, company types/sizes, key projects, salary indicators
2. If no CV: infer what you can from questionnaire data
3. Assess: market positioning in Israeli tech market 2025, personal brand strength, competitive advantages
4. Provide brutally honest, highly specific insights - NOT generic advice
5. All recommended directions must be realistic for THIS person given their profile
6. 30/60/90 day plans must be concrete and actionable (specific tasks, not vague goals)
7. Resources must be specific (actual course names, real Israeli tech communities)
8. Salary ranges must reflect Israeli market reality 2025

Produce the following JSON (respond with ONLY valid JSON, no markdown):

{{
  "track": "A or B (A=Career Change, B=Resilience/Optimization in current path)",
  "track_reason_he": "2-3 sentences why this track in Hebrew",

  "executive_summary_he": "Comprehensive 4-5 sentence executive summary of this person's career situation, key strengths, main challenge, and recommended path. Be specific and personal, not generic.",

  "spider_data": {{
    "daily_challenges": {part_a.get('q1',5)},
    "work_life_balance": {part_a.get('q2',5)},
    "professional_development": {part_a.get('q3',5)},
    "compensation": {part_a.get('q4',5)},
    "relationships": {part_a.get('q5',5)},
    "security": {part_a.get('q6',5)},
    "culture": {part_a.get('q7',5)},
    "meaning": {part_a.get('q8',5)},
    "self_actualization": {part_a.get('q9',5)},
    "influence": {part_a.get('q10',5)}
  }},

  "cv_profile": {{
    "years_total_experience": <number or null>,
    "career_stage_he": "Junior/Mid/Senior/Staff/Principal/Manager/Director - with Hebrew context",
    "key_technical_skills": ["skill1", "skill2", "skill3", "...up to 8"],
    "key_soft_skills": ["skill1", "skill2", "...up to 5"],
    "companies_profile_he": "Description of company types worked at and what it says about them",
    "career_trajectory_he": "Career arc description - is it linear, pivoting, accelerating, stalling?",
    "personal_brand_he": "What does this CV say about them as a professional? What's their brand?",
    "brand_gaps_he": "What's missing or weak in their CV/brand that needs strengthening?",
    "market_positioning_he": "How are they positioned in Israeli tech market 2025? Demand level for their profile?"
  }},

  "energy_batteries": {{
    "connection": <1-10, based on relationships score and energy_givers/drainers>,
    "progress": <1-10, based on development + self-actualization scores>,
    "influence": <1-10, based on influence score and IC/manager data>
  }},

  "swot": {{
    "strengths_he": ["Strength 1 - specific to their profile", "Strength 2", "Strength 3", "Strength 4"],
    "weaknesses_he": ["Weakness 1 - honest and specific", "Weakness 2", "Weakness 3"],
    "opportunities_he": ["Opportunity 1 in Israeli market", "Opportunity 2", "Opportunity 3"],
    "threats_he": ["Threat 1 to their career", "Threat 2", "Threat 3"]
  }},

  "market_analysis_he": "3-4 sentences: specific assessment of their market position in Israeli tech 2025. Include demand for their skills, salary benchmarks for their profile, and market trends affecting their field.",

  "insights_he": [
    "Insight 1: Deep, specific, personal - something they might not have seen themselves",
    "Insight 2: About their energy/burnout pattern",
    "Insight 3: About their career direction vs. their actual strengths",
    "Insight 4: About an opportunity or risk they should know"
  ],

  "recommended_directions": [
    {{
      "title_he": "Direction name in Hebrew",
      "description_he": "2-3 sentence description tailored to their specific profile",
      "why_good_fit_he": "Why specifically THIS person is suited for this direction based on their data",
      "fit_score": <1-10>,
      "market_demand": "high/medium/low",
      "market_demand_reason_he": "Why this demand level in Israeli market 2025",
      "salary_range_ils": "e.g. 35,000-50,000",
      "timeline_he": "Realistic timeline for this person to transition/achieve",
      "skills_gap_he": ["Specific missing skill 1", "Specific missing skill 2"],
      "bridge_plan_he": "Concrete plan to close the skills gap",
      "risk_level": "high/medium/low",
      "reward_level": "high/medium/low",
      "risk_he": "What could go wrong / cost of pursuing this",
      "reward_he": "What's the upside / best case scenario",
      "plan_30_days_he": ["Concrete action 1 this month", "Action 2", "Action 3"],
      "plan_60_days_he": ["Action 1 by month 2", "Action 2"],
      "plan_90_days_he": ["Action 1 by month 3", "Action 2"]
    }},
    {{
      "title_he": "Direction 2",
      "description_he": "...",
      "why_good_fit_he": "...",
      "fit_score": <1-10>,
      "market_demand": "high/medium/low",
      "market_demand_reason_he": "...",
      "salary_range_ils": "...",
      "timeline_he": "...",
      "skills_gap_he": [],
      "bridge_plan_he": "...",
      "risk_level": "high/medium/low",
      "reward_level": "high/medium/low",
      "risk_he": "...",
      "reward_he": "...",
      "plan_30_days_he": [],
      "plan_60_days_he": [],
      "plan_90_days_he": []
    }}
  ],

  "quick_wins_he": [
    "Action to take THIS WEEK - specific and immediate",
    "Second quick win - something achievable in 2 weeks",
    "Third quick win - builds momentum"
  ],

  "networking_he": {{
    "communities": ["Specific Israeli tech community 1 (with why)", "Community 2"],
    "events": ["Specific event/meetup in Israel relevant to their field", "Event 2"],
    "online": ["Specific LinkedIn group or Slack relevant to them", "Online resource 2"]
  }},

  "resources": {{
    "courses": [
      {{"name": "Specific course name", "platform": "Coursera/Udemy/LinkedIn Learning/etc", "why_he": "Why this course for this person specifically"}},
      {{"name": "Course 2", "platform": "...", "why_he": "..."}}
    ],
    "books": [
      {{"title": "Book title", "author": "Author name", "why_he": "Why this book for them"}},
      {{"title": "Book 2", "author": "...", "why_he": "..."}}
    ],
    "certifications": [
      {{"name": "Certification name", "why_he": "Why this cert for their goals"}}
    ]
  }},

  "recommended_roles": [
    {{
      "title_he": "Job title in Hebrew (e.g. מנהל מוצר, ארכיטקט פתרונות)",
      "timeframe": "short",
      "reasoning_he": "2-3 sentences: why specifically THIS person should pursue this role based on their profile, skills, and market data",
      "salary_range_ils": "e.g. 30,000-45,000",
      "description_he": "1-2 sentences what this role involves in Israeli market"
    }},
    {{
      "title_he": "Role 2",
      "timeframe": "short",
      "reasoning_he": "...",
      "salary_range_ils": "...",
      "description_he": "..."
    }},
    {{
      "title_he": "Role 3",
      "timeframe": "short",
      "reasoning_he": "...",
      "salary_range_ils": "...",
      "description_he": "..."
    }},
    {{
      "title_he": "Role 4 - longer horizon",
      "timeframe": "long",
      "reasoning_he": "...",
      "salary_range_ils": "...",
      "description_he": "..."
    }},
    {{
      "title_he": "Role 5 - longer horizon",
      "timeframe": "long",
      "reasoning_he": "...",
      "salary_range_ils": "...",
      "description_he": "..."
    }}
  ],

  "cv_analysis": "3-4 sentences CV analysis in Hebrew. If no CV: 'לא צורף קורות חיים'",
  "cv_milestones": ["Key milestone from CV 1", "Milestone 2", "Milestone 3"],

  "personalized_syllabus": [
    {{
      "session": 1,
      "personalized_focus_he": "What specifically to focus on in session 1 FOR THIS CLIENT",
      "key_questions_he": ["Question tailored to their data", "Question 2", "Question 3"],
      "homework_adaptation_he": "Specific homework adaptation for this client"
    }}
  ]
}}"""

    raw = _call_llm(prompt, max_tokens=8000).strip()

    # Clean JSON
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0]
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0]
    raw = raw.strip()

    analysis = json.loads(raw)

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
