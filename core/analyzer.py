import os
import json
import anthropic
from data.core_blueprint import TRACKS

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are an expert career coach assistant specializing in high-tech professionals in Israel.
You help analyze career questionnaires and CVs to generate personalized coaching insights and session syllabi based on the CORE Blueprint methodology.
Always respond in valid JSON format as specified in the user prompt.
Be specific, empathetic, and actionable. Tailor all insights to the high-tech context."""


def analyze_client(questionnaire: dict, client_info: dict) -> dict:
    part_a = questionnaire["part_a"]
    part_b = questionnaire["part_b"]
    cv_text = questionnaire.get("cv_text", "")

    prompt = f"""
Analyze this high-tech professional's career questionnaire and CV.

CLIENT INFO:
Name: {client_info['name']}

PART A - OCCUPATIONAL SATISFACTION (1-10 scale):
1. Daily challenges & role satisfaction: {part_a.get('q1', 'N/A')}
2. Work-life balance: {part_a.get('q2', 'N/A')}
3. Professional development: {part_a.get('q3', 'N/A')}
4. Compensation & financial wellbeing: {part_a.get('q4', 'N/A')}
5. Workplace relationships: {part_a.get('q5', 'N/A')}
6. Employment security: {part_a.get('q6', 'N/A')}
7. Workplace culture: {part_a.get('q7', 'N/A')}
8. Meaning & purpose: {part_a.get('q8', 'N/A')}
9. Interest & self-actualization: {part_a.get('q9', 'N/A')}
10. Influence & initiative: {part_a.get('q10', 'N/A')}
Top 3 urgent areas to improve: {part_a.get('top3', [])}

PART B - PROFESSIONAL DIRECTION:
1. Seniority level: {part_b.get('seniority', 'N/A')}
2. Current domain: {part_b.get('domain_current', 'N/A')}
3. Desired domain: {part_b.get('domain_desired', 'N/A')}
4. IC vs Manager (1=full IC, 10=full Manager): {part_b.get('ic_manager', 'N/A')}
5. Technical depth importance (1-10): {part_b.get('technical_depth', 'N/A')}
6. Preferred company stage (1=Startup, 10=Enterprise): {part_b.get('company_stage', 'N/A')}
7. Market demand feeling (1-10): {part_b.get('market_demand', 'N/A')}
8. Main concerns: {part_b.get('main_concerns', [])}
9. Main obstacle to change: {part_b.get('main_obstacle', [])}
10. Skills to develop: {part_b.get('skills_to_develop', 'N/A')}
11. Definition of success: {part_b.get('success_definition', 'N/A')}

CV TEXT (if provided):
{cv_text if cv_text else 'No CV provided'}

Based on this data, provide a comprehensive analysis in the following JSON structure:

{{
  "track": "A" or "B",
  "track_reason_he": "explanation in Hebrew why this track was chosen (2-3 sentences)",
  "track_reason_en": "explanation in English why this track was chosen (2-3 sentences)",
  "spider_data": {{
    "daily_challenges": <score 1-10>,
    "work_life_balance": <score 1-10>,
    "professional_development": <score 1-10>,
    "compensation": <score 1-10>,
    "relationships": <score 1-10>,
    "security": <score 1-10>,
    "culture": <score 1-10>,
    "meaning": <score 1-10>,
    "self_actualization": <score 1-10>,
    "influence": <score 1-10>
  }},
  "cv_analysis_he": "CV analysis in Hebrew: current career stage, key strengths visible from CV, career trajectory, market positioning (3-4 sentences). If no CV, write 'לא צורף קורות חיים'",
  "cv_milestones_he": ["milestone 1", "milestone 2", "milestone 3"] or [],
  "energy_batteries": {{
    "connection": <score 1-10, how full is the 'connection' battery>,
    "progress": <score 1-10, how full is the 'progress' battery>,
    "influence": <score 1-10, how full is the 'influence' battery>
  }},
  "insights_he": [
    "Key insight 1 in Hebrew - specific to their situation",
    "Key insight 2 in Hebrew",
    "Key insight 3 in Hebrew",
    "Key insight 4 in Hebrew"
  ],
  "recommended_directions_he": [
    {{
      "title": "Direction title in Hebrew",
      "description": "2-3 sentence description tailored to their profile",
      "fit_score": <1-10>,
      "market_demand": "high/medium/low",
      "timeline": "short-term (3-6 months) / medium-term (6-18 months) / long-term (1-3 years)"
    }},
    {{
      "title": "Direction 2",
      "description": "...",
      "fit_score": <1-10>,
      "market_demand": "high/medium/low",
      "timeline": "..."
    }}
  ],
  "personalized_syllabus": [
    {{
      "session": 1,
      "personalized_focus_he": "Specific focus for THIS client in session 1 (2-3 sentences connecting their data to the session goal)",
      "key_questions_he": ["Question 1 tailored to client", "Question 2", "Question 3"],
      "homework_adaptation_he": "Any adaptation to the standard homework based on their situation"
    }},
    ... (sessions 2-10)
  ]
}}
"""

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=4000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    analysis = json.loads(raw)

    track_key = analysis.get("track", "A")
    track_sessions = TRACKS[track_key]["sessions"]

    syllabus = []
    for i, session_template in enumerate(track_sessions):
        personalized = {}
        if i < len(analysis.get("personalized_syllabus", [])):
            personalized = analysis["personalized_syllabus"][i]

        syllabus.append({
            **session_template,
            "personalized_focus_he": personalized.get("personalized_focus_he", ""),
            "key_questions_he": personalized.get("key_questions_he", []),
            "homework_adaptation_he": personalized.get("homework_adaptation_he", ""),
        })

    return {
        "track": track_key,
        "track_reason_he": analysis.get("track_reason_he", ""),
        "track_reason_en": analysis.get("track_reason_en", ""),
        "spider_data": analysis.get("spider_data", {}),
        "cv_analysis": analysis.get("cv_analysis_he", ""),
        "cv_milestones": analysis.get("cv_milestones_he", []),
        "energy_batteries": analysis.get("energy_batteries", {}),
        "insights": analysis.get("insights_he", []),
        "recommended_directions": analysis.get("recommended_directions_he", []),
        "syllabus": syllabus,
    }


def extract_cv_text(file_bytes: bytes, file_name: str) -> str:
    if file_name.lower().endswith(".pdf"):
        try:
            import PyPDF2
            import io
            reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception:
            return ""
    elif file_name.lower().endswith(".docx"):
        try:
            import docx
            import io
            doc = docx.Document(io.BytesIO(file_bytes))
            return "\n".join(p.text for p in doc.paragraphs)
        except Exception:
            return ""
    return ""
