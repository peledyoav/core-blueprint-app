import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import (init_db, get_client_by_token, save_questionnaire,
                           get_questionnaire, save_draft, get_draft, delete_draft, save_report)
from core.analyzer import analyze_client, extract_cv_text

st.set_page_config(page_title="CORE Blueprint - שאלון", layout="centered", page_icon="🧭")
try:
    init_db()
except Exception as _db_err:
    st.error(f"שגיאת חיבור למסד נתונים: {_db_err}")
    st.stop()

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;600;700;900&display=swap');
html, body, [class*="css"] { font-family: 'Heebo', sans-serif; }
.stApp, .stApp * { direction: rtl; text-align: right; }
.stSlider, .stSlider * { direction: ltr !important; text-align: left !important; }
label, .stSelectbox label, .stMultiSelect label,
.stTextArea label, .stTextInput label {
    font-weight: 600 !important; color: #0a203d !important;
    display: block; text-align: right !important;
}
.stSelectbox [data-baseweb="select"], .stMultiSelect [data-baseweb="select"] {
    direction: rtl; text-align: right;
}
[data-testid="column"] { direction: rtl; }

.stButton > button, .stFormSubmitButton > button {
    background-color: #52c4cd !important; color: white !important;
    border: none !important; border-radius: 22px !important;
    font-weight: 700 !important; font-family: 'Heebo', sans-serif !important;
    padding: 10px 28px !important;
}
.stButton > button:hover, .stFormSubmitButton > button:hover {
    background-color: #0a203d !important;
}
.stApp { background-color: #f2f2f2; }

.hero-card {
    background-color: #0a203d; border-radius: 22px;
    padding: 28px 32px; text-align: center; color: white;
    margin-bottom: 24px; box-shadow: 0 8px 32px rgba(10,32,61,0.18);
}
.hero-subtitle { font-size: 1rem; color: #52c4cd; margin-top: 4px; }
.hero-welcome { font-size: 1.2rem; font-weight: 700; margin-top: 12px; }

.section-header {
    background: white; border-right: 5px solid #52c4cd;
    border-radius: 12px; padding: 12px 18px; margin: 24px 0 12px 0;
    font-weight: 700; font-size: 1.05rem; color: #0a203d;
    box-shadow: 0 2px 10px rgba(10,32,61,0.07);
}
.cv-box {
    background: linear-gradient(135deg, #e8f8f9, #f0fdfe);
    border: 2px dashed #52c4cd; border-radius: 16px;
    padding: 20px 24px; margin-bottom: 16px;
}
div[data-testid="stForm"] {
    background: white; border-radius: 16px;
    padding: 24px; box-shadow: 0 2px 16px rgba(10,32,61,0.07);
}
.autosave-indicator {
    color: #52c4cd; font-size: 0.8rem; text-align: left; margin-top: 4px; font-weight: 600;
}
.footer {
    text-align: center; color: #888; font-size: 0.78rem;
    margin-top: 48px; padding: 20px; border-top: 1px solid #d0d0d0;
}
</style>
""", unsafe_allow_html=True)

# ── Labels ─────────────────────────────────────────────────────────────────────
LABELS = {
    "he": {
        "cv_box_title": "העלה/י קורות חיים תחילה - זה חוסך לך שאלות רבות",
        "cv_box_desc": "ה-AI יחלץ מה-CV את התפקיד, הכישורים, הניסיון והמסלול שלך, וישאל רק מה שחסר.",
        "cv_upload": "קורות חיים (PDF או DOCX)",
        "part_a_title": "חלק א - שביעות רצון נוכחית",
        "part_a_desc": "דרג/י כל תחום מ-1 (לא מרוצה כלל) עד 10 (מרוצה מאוד)",
        "part_b_title": "חלק ב - כיוון מקצועי",
        "part_b_desc": "מה שה-CV לא יכול לספר - רק אתה יודע",
        "field_desired": "לאיזה תחום תרצה/י לעבור (או להישאר)?",
        "role_desired": "תפקיד ספציפי רצוי",
        "submit": "שלח שאלון לניתוח",
        "already_submitted": "השאלון שלך כבר נשלח. תודה!",
        "invalid_token": "הקישור אינו תקין. פנה/י למנטור שלך.",
        "success": "השאלון נשלח בהצלחה! תודה רבה.",
        "lang_toggle": "English",
        "autosaved": "נשמר אוטומטית",
        "other_specify": "פרט/י:",
    },
    "en": {
        "cv_box_title": "Upload your CV first - saves you many questions",
        "cv_box_desc": "AI will extract your role, skills, experience, and career arc from the CV, and only ask what's missing.",
        "cv_upload": "Resume / CV (PDF or DOCX)",
        "part_a_title": "Part A - Current Satisfaction",
        "part_a_desc": "Rate each area from 1 (very unsatisfied) to 10 (very satisfied)",
        "part_b_title": "Part B - Professional Direction",
        "part_b_desc": "What your CV can't tell us - only you know",
        "field_desired": "Which field do you want to move to (or stay in)?",
        "role_desired": "Desired specific role",
        "submit": "Submit Questionnaire",
        "already_submitted": "Your questionnaire has already been submitted. Thank you!",
        "invalid_token": "Invalid link. Please contact your mentor.",
        "success": "Questionnaire submitted successfully! Thank you.",
        "lang_toggle": "עברית",
        "autosaved": "Auto-saved",
        "other_specify": "Please specify:",
    }
}

PART_A_QUESTIONS = {
    "he": [
        "אתגרי יומיום - עד כמה את/ה מרוצה מהאתגרים, המשימות והאחריות בתפקיד?",
        "איזון עבודה-חיים - עד כמה את/ה מרוצה מהאיזון בין העבודה לחיים האישיים?",
        "פיתוח מקצועי - עד כמה את/ה מרוצה ממסלול הקריירה וההתקדמות שלך?",
        "גמול חומרי - עד כמה את/ה מרוצה מהשכר, הביטחון הכלכלי וההטבות?",
        "יחסים בעבודה - עד כמה את/ה מרוצה מהיחסים עם מנהלים, עמיתים ובעלי עניין?",
        "ביטחון תעסוקתי - עד כמה את/ה מרגיש/ה יציבות ובטחון בתפקיד הנוכחי?",
        "תרבות ארגונית - עד כמה את/ה מרוצה מתרבות הארגון, החדשנות ורווחת העובדים?",
        "משמעות ומטרה - עד כמה את/ה מרגיש/ה שהעבודה שלך משמעותית ומתאימה לערכיך?",
        "עניין ומימוש עצמי - עד כמה את/ה מרגיש/ה שאת/ה מממש/ת את הפוטנציאל שלך?",
        "השפעה ויוזמה - עד כמה את/ה מרגיש/ה שיש לך השפעה ויכולת להוביל שינויים?",
    ],
    "en": [
        "Daily Challenges - How satisfied are you with the challenges, tasks, and responsibilities in your role?",
        "Work-Life Balance - How satisfied are you with the balance between work and personal life?",
        "Professional Development - How satisfied are you with your career path and progress?",
        "Compensation - How satisfied are you with your salary, financial security, and benefits?",
        "Work Relationships - How satisfied are you with relationships with managers, colleagues, and stakeholders?",
        "Employment Security - How secure and stable do you feel in your current role?",
        "Organizational Culture - How satisfied are you with the organization's culture and employee wellbeing?",
        "Meaning and Purpose - How much do you feel your work is meaningful and aligned with your values?",
        "Interest and Self-Actualization - How much do you feel you're realizing your full potential?",
        "Influence and Initiative - How much influence do you have and ability to lead change?",
    ]
}
PART_A_KEYS = ["q1","q2","q3","q4","q5","q6","q7","q8","q9","q10"]

FIELDS = {
    "he": [
        "פיתוח תוכנה (Software)", "חומרה ואלקטרוניקה (Hardware)",
        "קושחה ומערכות משובצות (Embedded/Firmware)", "IT ותשתיות",
        "דאטה ואנליטיקה", "בינה מלאכותית ומחקר (AI/ML)",
        "סייבר ואבטחת מידע", "מוצר ועיצוב (Product/UX)",
        "פינטק (Fintech)", "ביוטק ומדטק (Biotech/MedTech)",
        "ביטחון ואווירונאוטיקה (Defense/Aerospace)", "תקשורת וסלקום (Telecom)",
        "ניהול פרויקטים ותוכניות", "אחר",
    ],
    "en": [
        "Software Development", "Hardware / Electronics", "Embedded / Firmware",
        "IT / Infrastructure", "Data and Analytics", "AI / ML / Research",
        "Cybersecurity", "Product and Design (UX)", "Fintech", "Biotech / MedTech",
        "Defense / Aerospace", "Telecom", "Project / Program Management", "Other",
    ]
}

OTHER_HE, OTHER_EN = "אחר", "Other"

ROLES_BY_FIELD = {
    "פיתוח תוכנה (Software)": ["Backend","Frontend","Full-Stack","Mobile (iOS/Android)","QA / Automation","DevOps / Platform","Site Reliability (SRE)","Software Architecture",OTHER_HE],
    "חומרה ואלקטרוניקה (Hardware)": ["VLSI / ASIC Design","PCB Design","Analog / RF","Digital Design","Hardware Verification","System Engineering",OTHER_HE],
    "קושחה ומערכות משובצות (Embedded/Firmware)": ["Firmware Development","RTOS / BSP","Drivers","Embedded Linux","Real-Time Systems",OTHER_HE],
    "IT ותשתיות": ["SysAdmin / IT","Network Engineering","Cloud (AWS/Azure/GCP)","IT Support","Storage and Backup",OTHER_HE],
    "דאטה ואנליטיקה": ["Data Engineering","Data Science","BI / Analytics","Data Architecture","Database Administration",OTHER_HE],
    "בינה מלאכותית ומחקר (AI/ML)": ["ML Engineering","AI Research","Computer Vision","NLP","MLOps","Generative AI",OTHER_HE],
    "סייבר ואבטחת מידע": ["Penetration Testing / Red Team","SOC / Blue Team","AppSec","Cloud Security","GRC / Compliance",OTHER_HE],
    "מוצר ועיצוב (Product/UX)": ["Product Management","UX / UI Design","Product Analytics","Growth",OTHER_HE],
    "פינטק (Fintech)": ["Backend / API","Payments","Risk and Compliance","Blockchain / Web3","Trading Systems",OTHER_HE],
    "ביוטק ומדטק (Biotech/MedTech)": ["Bioinformatics","Medical Devices Software","Regulatory Affairs","Clinical Data",OTHER_HE],
    "ביטחון ואווירונאוטיקה (Defense/Aerospace)": ["Systems Engineering","Avionics","Simulation","Signal Processing","Cyber Defense",OTHER_HE],
    "תקשורת וסלקום (Telecom)": ["Network Engineering","RF / Wireless","Core Network","OSS/BSS",OTHER_HE],
    "ניהול פרויקטים ותוכניות": ["Project Manager","Program Manager","Scrum Master / Agile","PMO",OTHER_HE],
    OTHER_HE: [OTHER_HE],
    "Software Development": ["Backend","Frontend","Full-Stack","Mobile (iOS/Android)","QA / Automation","DevOps / Platform","SRE","Software Architecture",OTHER_EN],
    "Hardware / Electronics": ["VLSI / ASIC Design","PCB Design","Analog / RF","Digital Design","Hardware Verification","System Engineering",OTHER_EN],
    "Embedded / Firmware": ["Firmware Development","RTOS / BSP","Drivers","Embedded Linux","Real-Time Systems",OTHER_EN],
    "IT / Infrastructure": ["SysAdmin / IT","Network Engineering","Cloud (AWS/Azure/GCP)","IT Support","Storage and Backup",OTHER_EN],
    "Data and Analytics": ["Data Engineering","Data Science","BI / Analytics","Data Architecture","Database Administration",OTHER_EN],
    "AI / ML / Research": ["ML Engineering","AI Research","Computer Vision","NLP","MLOps","Generative AI",OTHER_EN],
    "Cybersecurity": ["Penetration Testing / Red Team","SOC / Blue Team","AppSec","Cloud Security","GRC / Compliance",OTHER_EN],
    "Product and Design (UX)": ["Product Management","UX / UI Design","Product Analytics","Growth",OTHER_EN],
    "Fintech": ["Backend / API","Payments","Risk and Compliance","Blockchain / Web3","Trading Systems",OTHER_EN],
    "Biotech / MedTech": ["Bioinformatics","Medical Devices Software","Regulatory Affairs","Clinical Data",OTHER_EN],
    "Defense / Aerospace": ["Systems Engineering","Avionics","Simulation","Signal Processing","Cyber Defense",OTHER_EN],
    "Telecom": ["Network Engineering","RF / Wireless","Core Network","OSS/BSS",OTHER_EN],
    "Project / Program Management": ["Project Manager","Program Manager","Scrum Master / Agile","PMO",OTHER_EN],
    OTHER_EN: [OTHER_EN],
}

CONCERNS = {
    "he": ["השפעת ה-AI על התפקיד שלי","פיטורים וחוסר יציבות","תקרת זכוכית","חוסר כיוון ברור","פער כישורים","שחיקה",OTHER_HE],
    "en": ["AI's impact on my role","Layoffs and instability","Glass ceiling","Lack of clear direction","Skills gap","Burnout",OTHER_EN],
}
OBSTACLES = {
    "he": ["פחד מכישלון","אי-בטחון בכישורים","שכר ויציבות","זמן ואנרגיה","לא יודע מה אני רוצה","מחויבות משפחתית",OTHER_HE],
    "en": ["Fear of failure","Skill insecurity","Salary and stability","Time and energy","Don't know what I want","Family commitments",OTHER_EN],
}
GEO_OPTIONS = {
    "he": ["גמיש לחלוטין (כולל ריילוקיישן)","ישראל בלבד - גמיש","אזור ספציפי בישראל","עבודה מהבית בלבד (Remote)"],
    "en": ["Fully flexible (including relocation)","Israel only - flexible","Specific area in Israel","Remote only"],
}
SALARY_OPTIONS = {
    "he": ["עד 20,000","20,000-30,000","30,000-40,000","40,000-55,000","55,000-70,000","70,000+","לא רלוונטי"],
    "en": ["Up to 20K ILS","20K-30K ILS","30K-40K ILS","40K-55K ILS","55K-70K ILS","70K+ ILS","Not relevant"],
}
IC_MANAGER_OPTIONS = {
    "he": ["IC מלא - עומק טכני","IC בכיר עם השפעה","Tech Lead / Architect","Engineering Manager","Director ומעלה","עדיין לא יודע"],
    "en": ["Full IC - technical depth","Senior IC with influence","Tech Lead / Architect","Engineering Manager","Director and above","Not sure yet"],
}


def is_other(val): return val in (OTHER_HE, OTHER_EN)

def resolve_other(val, other_text):
    return other_text.strip() if (is_other(val) and other_text and other_text.strip()) else val

def resolve_list_other(lst, other_text):
    return [other_text.strip() if (s in (OTHER_HE, OTHER_EN) and other_text and other_text.strip()) else s for s in lst]


def collect_draft_data(lang):
    fd = resolve_other(st.session_state.get("field_desired", FIELDS[lang][0]), st.session_state.get("field_desired_other",""))
    rd = resolve_other(st.session_state.get("role_desired", ""), st.session_state.get("role_desired_other",""))
    concerns = resolve_list_other(st.session_state.get("pb_main_concerns",[]), st.session_state.get("pb_concerns_other",""))
    obstacles = resolve_list_other(st.session_state.get("pb_main_obstacle",[]), st.session_state.get("pb_obstacle_other",""))
    part_a = {k: st.session_state.get(f"pa_{k}", 5) for k in PART_A_KEYS}
    part_b = {
        "field_desired": fd, "role_desired": rd,
        "direction_preference": st.session_state.get("pb_direction_pref",""),
        "ic_manager_goal": st.session_state.get("pb_ic_manager_goal",""),
        "company_stage": st.session_state.get("pb_company_stage", 5),
        "energy_givers": st.session_state.get("pb_energy_givers",""),
        "energy_drainers": st.session_state.get("pb_energy_drainers",""),
        "risk_tolerance": st.session_state.get("pb_risk_tolerance", 5),
        "geo_flexibility": st.session_state.get("pb_geo_flexibility",""),
        "learning_hours": st.session_state.get("pb_learning_hours", 5),
        "salary_range": st.session_state.get("pb_salary_range",""),
        "key_achievement": st.session_state.get("pb_key_achievement",""),
        "main_concerns": concerns,
        "main_obstacle": obstacles,
        "skills_to_develop": st.session_state.get("pb_skills_to_develop",""),
        "success_definition": st.session_state.get("pb_success_definition",""),
        "coaching_specific": st.session_state.get("pb_coaching_specific",""),
    }
    return part_a, part_b


def main():
    token = st.query_params.get("token","")
    if "lang" not in st.session_state:
        st.session_state.lang = "he"
    lang = st.session_state.lang
    L = LABELS[lang]
    other_val = OTHER_HE if lang == "he" else OTHER_EN

    col_lang = st.columns([5,1])[1]
    with col_lang:
        if st.button(L["lang_toggle"], key="lang_btn"):
            st.session_state.lang = "en" if lang == "he" else "he"
            st.session_state.draft_loaded = False
            st.rerun()

    if not token:
        st.error(L["invalid_token"]); return
    client = get_client_by_token(token)
    if not client:
        st.error(L["invalid_token"]); return
    if get_questionnaire(client["id"]):
        st.success(L["already_submitted"]); st.balloons(); return

    # ── Logo + Hero ────────────────────────────────────────────────────────────
    logo_path = Path(__file__).parent.parent / "assets" / "logo.png"
    if logo_path.exists():
        col_logo = st.columns([1,2,1])[1]
        with col_logo:
            st.image(str(logo_path), use_container_width=True)

    st.markdown(f"""
    <div class="hero-card">
        <div class="hero-subtitle">From Burnout to Breakthrough in High-Tech</div>
        <div class="hero-welcome">שלום {client['name']}, ברוכ/ה הבא/ה לשאלון האישי שלך</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Restore draft ──────────────────────────────────────────────────────────
    if "draft_loaded" not in st.session_state:
        draft = get_draft(client["id"])
        if draft:
            for k, v in draft["part_a"].items():
                st.session_state[f"pa_{k}"] = v
            pb = draft["part_b"]
            for k in ["direction_preference","ic_manager_goal","company_stage","energy_givers",
                      "energy_drainers","risk_tolerance","geo_flexibility","learning_hours",
                      "salary_range","key_achievement","main_concerns","main_obstacle",
                      "skills_to_develop","success_definition","coaching_specific"]:
                if k in pb:
                    st.session_state[f"pb_{k}"] = pb[k]
            for k in ["field_desired","role_desired"]:
                if k in pb:
                    st.session_state[k] = pb[k]
        st.session_state["draft_loaded"] = True
        st.session_state["interaction_count"] = 0
        st.session_state["cv_uploaded"] = False

    # ── CV Upload (FIRST - outside form) ──────────────────────────────────────
    st.markdown(f'<div class="section-header">📄 {L["cv_box_title"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="cv-box"><p style="margin:0;color:#0a203d;">{L["cv_box_desc"]}</p></div>', unsafe_allow_html=True)
    cv_file = st.file_uploader(L["cv_upload"], type=["pdf","docx"], key="cv_uploader")
    if cv_file:
        st.success("✓ קורות חיים הועלו - ינותחו בעת הגשת השאלון" if lang=="he" else "✓ CV uploaded - will be analyzed on submission")

    # ── PART A ─────────────────────────────────────────────────────────────────
    st.markdown(f'<div class="section-header">📊 {L["part_a_title"]}</div>', unsafe_allow_html=True)
    st.caption(L["part_a_desc"])
    part_a = {}
    for key, question in zip(PART_A_KEYS, PART_A_QUESTIONS[lang]):
        part_a[key] = st.slider(question, min_value=1, max_value=10, value=5, key=f"pa_{key}")

    # ── PART B - desired direction (outside form for reactivity) ───────────────
    st.markdown(f'<div class="section-header">🎯 {L["part_b_title"]}</div>', unsafe_allow_html=True)
    st.caption(L["part_b_desc"])

    col1, col2 = st.columns(2)
    with col1:
        field_desired = st.selectbox(L["field_desired"], FIELDS[lang], key="field_desired")
        if is_other(field_desired):
            st.text_input(L["other_specify"], key="field_desired_other", placeholder="...")
    with col2:
        roles_desired = ROLES_BY_FIELD.get(field_desired, [other_val])
        role_desired = st.selectbox(L["role_desired"], roles_desired, key="role_desired")
        if is_other(role_desired):
            st.text_input(L["other_specify"], key="role_desired_other", placeholder="...")

    # ── Auto-save ──────────────────────────────────────────────────────────────
    st.session_state["interaction_count"] = st.session_state.get("interaction_count", 0) + 1
    if st.session_state["interaction_count"] > 1:
        _a, _b = collect_draft_data(lang)
        save_draft(client["id"], _a, _b)
        st.markdown(f'<div class="autosave-indicator">✓ {L["autosaved"]}</div>', unsafe_allow_html=True)

    # ── PART B - rest (inside form) ────────────────────────────────────────────
    with st.form("questionnaire_form"):
        part_b = {}
        is_he = (lang == "he")

        # Direction details
        part_b["direction_preference"] = st.text_area(
            "מה מושך אותך לכיוון הזה? מה הציפיות שלך ממנו?" if is_he else "What attracts you to this direction? What are your expectations?",
            max_chars=400, key="pb_direction_pref")

        part_b["ic_manager_goal"] = st.selectbox(
            "לאן את/ה רוצה להתפתח מקצועית?" if is_he else "What is your professional growth direction?",
            IC_MANAGER_OPTIONS[lang], key="pb_ic_manager_goal")

        part_b["company_stage"] = st.slider(
            "סטייג' חברה מועדף (1 = Startup מוקדם, 10 = Enterprise גדול)" if is_he else "Preferred company stage (1=Early Startup, 10=Large Enterprise)",
            1, 10, 5, key="pb_company_stage")

        st.divider()

        # Energy - critical for coaching
        st.markdown("**⚡ " + ("מקורות אנרגיה ושחיקה" if is_he else "Energy & Burnout Sources") + "**")
        part_b["energy_givers"] = st.text_area(
            "מה מעניק לך אנרגיה ומוטיבציה בעבודה? (משימות, אינטראקציות, סוג עבודה)" if is_he else "What gives you energy and motivation at work? (tasks, interactions, type of work)",
            max_chars=400, key="pb_energy_givers", placeholder="למשל: פתרון בעיות טכניות מורכבות, עבודה עם לקוחות, הדרכת עמיתים...")

        part_b["energy_drainers"] = st.text_area(
            "מה גורם לך לשחיקה ומרוקן אותך?" if is_he else "What causes burnout and drains you?",
            max_chars=400, key="pb_energy_drainers", placeholder="למשל: ישיבות רבות מדי, חוסר אוטונומיה, חזרתיות...")

        st.divider()

        # Risk & practicalities
        st.markdown("**🎲 " + ("פרקטי ומציאותי" if is_he else "Practical Considerations") + "**")
        part_b["risk_tolerance"] = st.slider(
            "רמת סובלנות לסיכון (1 = ביטחון ויציבות מעל הכל, 10 = אוהב/ת שינויים ואי-ודאות)" if is_he else "Risk tolerance (1 = stability above all, 10 = love change and uncertainty)",
            1, 10, 5, key="pb_risk_tolerance")

        part_b["geo_flexibility"] = st.selectbox(
            "גמישות גיאוגרפית" if is_he else "Geographic flexibility",
            GEO_OPTIONS[lang], key="pb_geo_flexibility")

        part_b["learning_hours"] = st.slider(
            "כמה שעות בשבוע פנוי/ה ללמידה והתפתחות מקצועית?" if is_he else "How many hours per week available for learning and development?",
            0, 20, 5, key="pb_learning_hours")

        part_b["salary_range"] = st.selectbox(
            "ציפיות שכר ברוטו חודשי (₪)" if is_he else "Expected monthly gross salary (ILS)",
            SALARY_OPTIONS[lang], key="pb_salary_range")

        st.divider()

        # Achievement & concerns
        st.markdown("**🏆 " + ("הישגים ואתגרים" if is_he else "Achievements & Challenges") + "**")
        part_b["key_achievement"] = st.text_area(
            "מה ההישג המקצועי שאת/ה הכי גאה/ה בו? למה?" if is_he else "What professional achievement are you most proud of? Why?",
            max_chars=500, key="pb_key_achievement", placeholder="ספר/י על פרויקט, החלטה, או רגע בקריירה שמייצג אותך בצורה הטובה ביותר...")

        concerns_raw = st.multiselect(
            "החששות המרכזיים לגבי העתיד המקצועי (עד 2)" if is_he else "Main concerns about your professional future (up to 2)",
            options=CONCERNS[lang], max_selections=2, key="pb_main_concerns")
        if any(s in (OTHER_HE, OTHER_EN) for s in concerns_raw):
            st.text_input("חשש אחר - פרט/י:" if is_he else "Other concern:", key="pb_concerns_other", placeholder="...")

        obstacles_raw = st.multiselect(
            "המכשול העיקרי שמונע ממך לעשות את השינוי (עד 2)" if is_he else "Main obstacle preventing change (up to 2)",
            options=OBSTACLES[lang], max_selections=2, key="pb_main_obstacle")
        if any(s in (OTHER_HE, OTHER_EN) for s in obstacles_raw):
            st.text_input("מכשול אחר - פרט/י:" if is_he else "Other obstacle:", key="pb_obstacle_other", placeholder="...")

        st.divider()

        # Skills & goals
        st.markdown("**🌱 " + ("מטרות ומה שאתה מחפש" if is_he else "Goals & What You're Looking For") + "**")
        part_b["skills_to_develop"] = st.text_area(
            "אילו כישורים תרצה/י לפתח ב-12 חודשים הקרובים?" if is_he else "Skills to develop in the next 12 months?",
            max_chars=300, key="pb_skills_to_develop")

        part_b["success_definition"] = st.text_area(
            "איך ייראה עבורך הצלחה בסוף התהליך?" if is_he else "What would success look like at the end of the process?",
            max_chars=300, key="pb_success_definition")

        part_b["coaching_specific"] = st.text_area(
            "מה הכי חשוב לך לקבל מהתהליך איתי? מה לא נאמר בשאלון?" if is_he else "What's most important to get from this coaching process? What wasn't covered in the questionnaire?",
            max_chars=400, key="pb_coaching_specific", placeholder="כל מה שחשוב לך שאני אדע...")

        submitted = st.form_submit_button(L["submit"], type="primary", use_container_width=True)

    if submitted:
        fd = resolve_other(st.session_state.get("field_desired",""), st.session_state.get("field_desired_other",""))
        rd = resolve_other(st.session_state.get("role_desired",""), st.session_state.get("role_desired_other",""))
        part_b["field_desired"] = fd
        part_b["role_desired"] = rd
        part_b["main_concerns"] = resolve_list_other(concerns_raw, st.session_state.get("pb_concerns_other",""))
        part_b["main_obstacle"] = resolve_list_other(obstacles_raw, st.session_state.get("pb_obstacle_other",""))

        cv_text = ""
        if cv_file:
            cv_text = extract_cv_text(cv_file.read(), cv_file.name)

        qid = save_questionnaire(client["id"], part_a, part_b, cv_text)

        with st.spinner("מנתח נתונים ובונה את הדוח האישי שלך... (כ-30 שניות)" if lang=="he" else "Analyzing data and building your personal report... (~30 seconds)"):
            questionnaire = {"part_a": part_a, "part_b": part_b, "cv_text": cv_text}
            report = analyze_client(questionnaire, client)
            save_report(client["id"], qid, report)

        delete_draft(client["id"])
        st.success(L["success"])
        st.balloons()

    st.markdown("""
    <div class="footer">
        CORE Blueprint &nbsp;|&nbsp; Yoav Peled Career Coaching<br>
        &copy; 2026 כל הזכויות שמורות ליואב פלד
    </div>
    """, unsafe_allow_html=True)


main()
