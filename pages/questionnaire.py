import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import (init_db, get_client_by_token, save_questionnaire,
                           get_questionnaire, save_draft, get_draft, delete_draft, save_report)
from core.analyzer import analyze_client, extract_cv_text

st.set_page_config(page_title="CORE Blueprint - שאלון", layout="centered", page_icon="🧭")

init_db()

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;600;700;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Heebo', sans-serif;
}
.stApp {
    direction: rtl;
    text-align: right;
    background-color: #f2f2f2;
}
/* RTL for all app content */
.stApp, .stApp * { direction: rtl; text-align: right; }
/* Keep sliders LTR (1 left, 10 right) */
.stSlider, .stSlider * { direction: ltr !important; text-align: left !important; }
/* Labels */
label, .stSelectbox label, .stMultiSelect label,
.stTextArea label, .stTextInput label {
    font-weight: 600 !important;
    color: #0a203d !important;
    display: block;
    text-align: right !important;
}
/* Dropdowns */
.stSelectbox [data-baseweb="select"], .stMultiSelect [data-baseweb="select"] {
    direction: rtl; text-align: right;
}
[data-testid="column"] { direction: rtl; }

/* Buttons */
.stButton > button, .stFormSubmitButton > button {
    background-color: #52c4cd !important;
    color: white !important;
    border: none !important;
    border-radius: 22px !important;
    font-weight: 700 !important;
    font-family: 'Heebo', sans-serif !important;
    padding: 10px 28px !important;
    transition: background 0.2s;
}
.stButton > button:hover, .stFormSubmitButton > button:hover {
    background-color: #0a203d !important;
}

/* Hero */
.hero-card {
    background-color: #0a203d;
    border-radius: 22px;
    padding: 36px 32px 28px 32px;
    text-align: center;
    color: white;
    margin-bottom: 28px;
    box-shadow: 0 8px 32px rgba(10,32,61,0.18);
}
.hero-subtitle {
    font-size: 1rem;
    color: #52c4cd;
    margin-top: 6px;
    font-weight: 400;
}
.hero-welcome {
    font-size: 1.25rem;
    font-weight: 700;
    margin-top: 18px;
    color: #ffffff;
}

/* Section headers */
.section-header {
    background: white;
    border-right: 5px solid #52c4cd;
    border-radius: 12px;
    padding: 13px 18px;
    margin: 28px 0 14px 0;
    font-weight: 700;
    font-size: 1.1rem;
    color: #0a203d;
    box-shadow: 0 2px 10px rgba(10,32,61,0.07);
}

/* Cards / form */
div[data-testid="stForm"] {
    background: white;
    border-radius: 16px;
    padding: 28px;
    box-shadow: 0 2px 16px rgba(10,32,61,0.07);
}

/* Field/role block outside form */
.field-block {
    background: white;
    border-radius: 16px;
    padding: 20px 24px 12px 24px;
    box-shadow: 0 2px 10px rgba(10,32,61,0.06);
    margin-bottom: 16px;
}

.autosave-indicator {
    color: #52c4cd;
    font-size: 0.8rem;
    text-align: left;
    margin-top: 4px;
    font-weight: 600;
}

.footer {
    text-align: center;
    color: #888;
    font-size: 0.78rem;
    margin-top: 48px;
    padding: 20px;
    border-top: 1px solid #d0d0d0;
}

/* Sliders accent */
.stSlider [data-baseweb="slider"] [data-testid="stThumbValue"] {
    color: #0a203d;
}
</style>
""", unsafe_allow_html=True)

# ── Labels ─────────────────────────────────────────────────────────────────────
LABELS = {
    "he": {
        "part_a_title": "חלק א - שביעות רצון נוכחית",
        "part_a_desc": "דרג/י כל תחום מ-1 (לא מרוצה כלל) עד 10 (מרוצה מאוד)",
        "part_b_title": "חלק ב - כיוון מקצועי",
        "part_b_desc": "שאלות ספציפיות לאנשי הייטק",
        "cv_title": "קורות חיים (אופציונלי)",
        "cv_desc": "העלה/י קורות חיים לניתוח מעמיק יותר (PDF או DOCX)",
        "submit": "שלח שאלון",
        "already_submitted": "השאלון שלך כבר נשלח. תודה!",
        "invalid_token": "הקישור אינו תקין. פנה/י למנטור שלך.",
        "success": "השאלון נשלח בהצלחה! תודה רבה.",
        "lang_toggle": "English",
        "field_current": "תחום עיסוק נוכחי",
        "field_desired": "תחום עיסוק רצוי",
        "role_current": "תפקיד ספציפי - נוכחי",
        "role_desired": "תפקיד ספציפי - רצוי",
        "autosaved": "נשמר אוטומטית",
        "other_specify": "פרט/י:",
    },
    "en": {
        "part_a_title": "Part A - Current Satisfaction",
        "part_a_desc": "Rate each area from 1 (very unsatisfied) to 10 (very satisfied)",
        "part_b_title": "Part B - Professional Direction",
        "part_b_desc": "High-tech specific questions",
        "cv_title": "Resume / CV (optional)",
        "cv_desc": "Upload your CV for deeper analysis (PDF or DOCX)",
        "submit": "Submit Questionnaire",
        "already_submitted": "Your questionnaire has already been submitted. Thank you!",
        "invalid_token": "Invalid link. Please contact your mentor.",
        "success": "Questionnaire submitted successfully! Thank you.",
        "lang_toggle": "עברית",
        "field_current": "Current field",
        "field_desired": "Desired field",
        "role_current": "Current specific role",
        "role_desired": "Desired specific role",
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

PART_A_KEYS = ["q1", "q2", "q3", "q4", "q5", "q6", "q7", "q8", "q9", "q10"]

FIELDS = {
    "he": [
        "פיתוח תוכנה (Software)",
        "חומרה ואלקטרוניקה (Hardware)",
        "קושחה ומערכות משובצות (Embedded/Firmware)",
        "IT ותשתיות",
        "דאטה ואנליטיקה",
        "בינה מלאכותית ומחקר (AI/ML)",
        "סייבר ואבטחת מידע",
        "מוצר ועיצוב (Product/UX)",
        "פינטק (Fintech)",
        "ביוטק ומדטק (Biotech/MedTech)",
        "ביטחון ואווירונאוטיקה (Defense/Aerospace)",
        "תקשורת וסלקום (Telecom)",
        "ניהול פרויקטים ותוכניות",
        "אחר",
    ],
    "en": [
        "Software Development",
        "Hardware / Electronics",
        "Embedded / Firmware",
        "IT / Infrastructure",
        "Data and Analytics",
        "AI / ML / Research",
        "Cybersecurity",
        "Product and Design (UX)",
        "Fintech",
        "Biotech / MedTech",
        "Defense / Aerospace",
        "Telecom",
        "Project / Program Management",
        "Other",
    ]
}

OTHER_HE = "אחר"
OTHER_EN = "Other"

ROLES_BY_FIELD = {
    "פיתוח תוכנה (Software)": ["Backend", "Frontend", "Full-Stack", "Mobile (iOS/Android)", "QA / Automation", "DevOps / Platform", "Site Reliability (SRE)", "Software Architecture", OTHER_HE],
    "חומרה ואלקטרוניקה (Hardware)": ["VLSI / ASIC Design", "PCB Design", "Analog / RF", "Digital Design", "Hardware Verification", "System Engineering", OTHER_HE],
    "קושחה ומערכות משובצות (Embedded/Firmware)": ["Firmware Development", "RTOS / BSP", "Drivers", "Embedded Linux", "Real-Time Systems", OTHER_HE],
    "IT ותשתיות": ["SysAdmin / IT", "Network Engineering", "Cloud (AWS/Azure/GCP)", "IT Support", "Storage and Backup", OTHER_HE],
    "דאטה ואנליטיקה": ["Data Engineering", "Data Science", "BI / Analytics", "Data Architecture", "Database Administration", OTHER_HE],
    "בינה מלאכותית ומחקר (AI/ML)": ["ML Engineering", "AI Research", "Computer Vision", "NLP", "MLOps", "Generative AI", OTHER_HE],
    "סייבר ואבטחת מידע": ["Penetration Testing / Red Team", "SOC / Blue Team", "AppSec", "Cloud Security", "GRC / Compliance", OTHER_HE],
    "מוצר ועיצוב (Product/UX)": ["Product Management", "UX / UI Design", "Product Analytics", "Growth", OTHER_HE],
    "פינטק (Fintech)": ["Backend / API", "Payments", "Risk and Compliance", "Blockchain / Web3", "Trading Systems", OTHER_HE],
    "ביוטק ומדטק (Biotech/MedTech)": ["Bioinformatics", "Medical Devices Software", "Regulatory Affairs", "Clinical Data", OTHER_HE],
    "ביטחון ואווירונאוטיקה (Defense/Aerospace)": ["Systems Engineering", "Avionics", "Simulation", "Signal Processing", "Cyber Defense", OTHER_HE],
    "תקשורת וסלקום (Telecom)": ["Network Engineering", "RF / Wireless", "Core Network", "OSS/BSS", OTHER_HE],
    "ניהול פרויקטים ותוכניות": ["Project Manager", "Program Manager", "Scrum Master / Agile", "PMO", OTHER_HE],
    OTHER_HE: [OTHER_HE],
    "Software Development": ["Backend", "Frontend", "Full-Stack", "Mobile (iOS/Android)", "QA / Automation", "DevOps / Platform", "Site Reliability (SRE)", "Software Architecture", OTHER_EN],
    "Hardware / Electronics": ["VLSI / ASIC Design", "PCB Design", "Analog / RF", "Digital Design", "Hardware Verification", "System Engineering", OTHER_EN],
    "Embedded / Firmware": ["Firmware Development", "RTOS / BSP", "Drivers", "Embedded Linux", "Real-Time Systems", OTHER_EN],
    "IT / Infrastructure": ["SysAdmin / IT", "Network Engineering", "Cloud (AWS/Azure/GCP)", "IT Support", "Storage and Backup", OTHER_EN],
    "Data and Analytics": ["Data Engineering", "Data Science", "BI / Analytics", "Data Architecture", "Database Administration", OTHER_EN],
    "AI / ML / Research": ["ML Engineering", "AI Research", "Computer Vision", "NLP", "MLOps", "Generative AI", OTHER_EN],
    "Cybersecurity": ["Penetration Testing / Red Team", "SOC / Blue Team", "AppSec", "Cloud Security", "GRC / Compliance", OTHER_EN],
    "Product and Design (UX)": ["Product Management", "UX / UI Design", "Product Analytics", "Growth", OTHER_EN],
    "Fintech": ["Backend / API", "Payments", "Risk and Compliance", "Blockchain / Web3", "Trading Systems", OTHER_EN],
    "Biotech / MedTech": ["Bioinformatics", "Medical Devices Software", "Regulatory Affairs", "Clinical Data", OTHER_EN],
    "Defense / Aerospace": ["Systems Engineering", "Avionics", "Simulation", "Signal Processing", "Cyber Defense", OTHER_EN],
    "Telecom": ["Network Engineering", "RF / Wireless", "Core Network", "OSS/BSS", OTHER_EN],
    "Project / Program Management": ["Project Manager", "Program Manager", "Scrum Master / Agile", "PMO", OTHER_EN],
    OTHER_EN: [OTHER_EN],
}

SENIORITY_OPTIONS = {
    "he": ["Junior", "Mid", "Senior", "Staff / Principal", "Lead / Manager", "Director+"],
    "en": ["Junior", "Mid", "Senior", "Staff / Principal", "Lead / Manager", "Director+"],
}

CONCERNS = {
    "he": ["השפעת ה-AI על התפקיד שלי", "פיטורים וחוסר יציבות", "תקרת זכוכית",
           "חוסר כיוון ברור", "פער כישורים", "שחיקה", OTHER_HE],
    "en": ["AI's impact on my role", "Layoffs and instability", "Glass ceiling",
           "Lack of clear direction", "Skills gap", "Burnout", OTHER_EN],
}

OBSTACLES = {
    "he": ["פחד מכישלון", "אי-בטחון בכישורים", "שכר ויציבות", "זמן ואנרגיה",
           "לא יודע מה אני רוצה", "מחויבות משפחתית", OTHER_HE],
    "en": ["Fear of failure", "Skill insecurity", "Salary and stability", "Time and energy",
           "Don't know what I want", "Family commitments", OTHER_EN],
}


def is_other(val, lang):
    return val in (OTHER_HE, OTHER_EN)


def resolve_other(val, other_text):
    """Replace 'Other/אחר' with the typed free text if provided."""
    if not other_text or not other_text.strip():
        return val
    return other_text.strip()


def resolve_list_other(selections, other_text):
    """In a list of selections, replace Other with free text."""
    result = []
    for s in selections:
        if s in (OTHER_HE, OTHER_EN):
            if other_text and other_text.strip():
                result.append(other_text.strip())
            else:
                result.append(s)
        else:
            result.append(s)
    return result


def collect_draft_data(lang):
    other = OTHER_HE if lang == "he" else OTHER_EN

    fc = st.session_state.get("field_current", FIELDS[lang][0])
    fc = resolve_other(fc, st.session_state.get("field_current_other", ""))

    fd = st.session_state.get("field_desired", FIELDS[lang][0])
    fd = resolve_other(fd, st.session_state.get("field_desired_other", ""))

    rc = st.session_state.get("role_current", "")
    rc = resolve_other(rc, st.session_state.get("role_current_other", ""))

    rd = st.session_state.get("role_desired", "")
    rd = resolve_other(rd, st.session_state.get("role_desired_other", ""))

    concerns = st.session_state.get("pb_main_concerns", [])
    concerns = resolve_list_other(concerns, st.session_state.get("pb_concerns_other", ""))

    obstacles = st.session_state.get("pb_main_obstacle", [])
    obstacles = resolve_list_other(obstacles, st.session_state.get("pb_obstacle_other", ""))

    part_a = {k: st.session_state.get(f"pa_{k}", 5) for k in PART_A_KEYS}
    part_b = {
        "field_current": fc,
        "field_desired": fd,
        "role_current": rc,
        "role_desired": rd,
        "seniority": st.session_state.get("pb_seniority", SENIORITY_OPTIONS[lang][0]),
        "ic_manager": st.session_state.get("pb_ic_manager", 5),
        "technical_depth": st.session_state.get("pb_technical_depth", 5),
        "company_stage": st.session_state.get("pb_company_stage", 5),
        "main_concerns": concerns,
        "main_obstacle": obstacles,
        "skills_to_develop": st.session_state.get("pb_skills_to_develop", ""),
        "success_definition": st.session_state.get("pb_success_definition", ""),
    }
    return part_a, part_b


def main():
    token = st.query_params.get("token", "")

    if "lang" not in st.session_state:
        st.session_state.lang = "he"

    lang = st.session_state.lang
    L = LABELS[lang]
    other_val = OTHER_HE if lang == "he" else OTHER_EN

    col_lang = st.columns([5, 1])[1]
    with col_lang:
        if st.button(L["lang_toggle"], key="lang_btn"):
            st.session_state.lang = "en" if lang == "he" else "he"
            st.session_state.draft_loaded = False
            st.rerun()

    if not token:
        st.error(L["invalid_token"])
        return

    client = get_client_by_token(token)
    if not client:
        st.error(L["invalid_token"])
        return

    existing = get_questionnaire(client["id"])
    if existing:
        st.success(L["already_submitted"])
        st.balloons()
        return

    # ── Logo + Hero ────────────────────────────────────────────────────────────
    logo_path = Path(__file__).parent.parent / "assets" / "logo.png"
    if logo_path.exists():
        col_logo = st.columns([1, 2, 1])[1]
        with col_logo:
            st.image(str(logo_path), use_container_width=True)

    st.markdown(f"""
    <div class="hero-card">
        <div class="hero-subtitle">From Burnout to Breakthrough in High-Tech</div>
        <div class="hero-welcome">שלום {client['name']}, ברוכ/ה הבא/ה לשאלון האישי שלך</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Restore draft on first load ────────────────────────────────────────────
    if "draft_loaded" not in st.session_state:
        draft = get_draft(client["id"])
        if draft:
            for k, v in draft["part_a"].items():
                st.session_state[f"pa_{k}"] = v
            pb = draft["part_b"]
            for k in ["seniority", "ic_manager", "technical_depth", "company_stage",
                      "market_demand", "main_concerns", "main_obstacle",
                      "skills_to_develop", "success_definition"]:
                if k in pb:
                    st.session_state[f"pb_{k}"] = pb[k]
            if "field_current" in pb:
                st.session_state["field_current"] = pb["field_current"]
            if "field_desired" in pb:
                st.session_state["field_desired"] = pb["field_desired"]
            if "role_current" in pb:
                st.session_state["role_current"] = pb["role_current"]
            if "role_desired" in pb:
                st.session_state["role_desired"] = pb["role_desired"]
        st.session_state["draft_loaded"] = True
        st.session_state["interaction_count"] = 0

    # ── PART A ─────────────────────────────────────────────────────────────────
    st.markdown(f'<div class="section-header">📊 {L["part_a_title"]}</div>', unsafe_allow_html=True)
    st.caption(L["part_a_desc"])

    part_a = {}
    for key, question in zip(PART_A_KEYS, PART_A_QUESTIONS[lang]):
        part_a[key] = st.slider(question, min_value=1, max_value=10, value=5, key=f"pa_{key}")

    # ── PART B - field/role (outside form for reactivity) ─────────────────────
    st.markdown(f'<div class="section-header">🎯 {L["part_b_title"]}</div>', unsafe_allow_html=True)
    st.caption(L["part_b_desc"])

    fields_list = FIELDS[lang]
    col1, col2 = st.columns(2)
    with col1:
        field_current = st.selectbox(L["field_current"], fields_list, key="field_current")
        if is_other(field_current, lang):
            st.text_input(L["other_specify"], key="field_current_other", placeholder="...")
    with col2:
        field_desired = st.selectbox(L["field_desired"], fields_list, key="field_desired")
        if is_other(field_desired, lang):
            st.text_input(L["other_specify"], key="field_desired_other", placeholder="...")

    roles_current = ROLES_BY_FIELD.get(field_current, [other_val])
    roles_desired = ROLES_BY_FIELD.get(field_desired, [other_val])

    col3, col4 = st.columns(2)
    with col3:
        role_current = st.selectbox(L["role_current"], roles_current, key="role_current")
        if is_other(role_current, lang):
            st.text_input(L["other_specify"], key="role_current_other", placeholder="...")
    with col4:
        role_desired = st.selectbox(L["role_desired"], roles_desired, key="role_desired")
        if is_other(role_desired, lang):
            st.text_input(L["other_specify"], key="role_desired_other", placeholder="...")

    # ── Auto-save on every interaction ────────────────────────────────────────
    st.session_state["interaction_count"] = st.session_state.get("interaction_count", 0) + 1
    if st.session_state["interaction_count"] > 1:
        _a, _b = collect_draft_data(lang)
        save_draft(client["id"], _a, _b)
        st.markdown(f'<div class="autosave-indicator">✓ {L["autosaved"]}</div>', unsafe_allow_html=True)

    # ── PART B - rest (inside form) ────────────────────────────────────────────
    with st.form("questionnaire_form"):
        part_b = {}

        if lang == "he":
            part_b["seniority"] = st.selectbox("רמת בכירות נוכחית", SENIORITY_OPTIONS["he"], key="pb_seniority")
            part_b["ic_manager"] = st.slider("IC או Manager? (1 = טכני מלא, 10 = ניהול אנשים מלא)", 1, 10, 5, key="pb_ic_manager")
            part_b["technical_depth"] = st.slider("כמה חשוב לך להישאר בחומר הטכני ביומיום? (1-10)", 1, 10, 5, key="pb_technical_depth")
            part_b["company_stage"] = st.slider("סטייג' חברה מועדף (1 = Startup מוקדם, 10 = Enterprise גדול)", 1, 10, 5, key="pb_company_stage")
            concerns_raw = st.multiselect("מה החשש המרכזי שלך לגבי העתיד המקצועי? (עד 2)", options=CONCERNS["he"], max_selections=2, key="pb_main_concerns")
            if OTHER_HE in concerns_raw:
                st.text_input("חשש אחר - פרט/י:", key="pb_concerns_other", placeholder="...")

            obstacles_raw = st.multiselect("מה המכשול העיקרי שמונע ממך לעשות את השינוי? (עד 2)", options=OBSTACLES["he"], max_selections=2, key="pb_main_obstacle")
            if OTHER_HE in obstacles_raw:
                st.text_input("מכשול אחר - פרט/י:", key="pb_obstacle_other", placeholder="...")

            part_b["skills_to_develop"] = st.text_area("אילו כישורים תרצה לפתח ב-12 חודשים הקרובים?", max_chars=300, key="pb_skills_to_develop")
            part_b["success_definition"] = st.text_area("מה ייראה לך כהצלחה בסוף התהליך?", max_chars=300, key="pb_success_definition")
        else:
            part_b["seniority"] = st.selectbox("Current seniority level", SENIORITY_OPTIONS["en"], key="pb_seniority")
            part_b["ic_manager"] = st.slider("IC or Manager? (1 = fully technical, 10 = people management)", 1, 10, 5, key="pb_ic_manager")
            part_b["technical_depth"] = st.slider("How important is staying in the technical material daily? (1-10)", 1, 10, 5, key="pb_technical_depth")
            part_b["company_stage"] = st.slider("Preferred company stage (1 = Early Startup, 10 = Large Enterprise)", 1, 10, 5, key="pb_company_stage")
            concerns_raw = st.multiselect("Main concerns about your professional future? (up to 2)", options=CONCERNS["en"], max_selections=2, key="pb_main_concerns")
            if OTHER_EN in concerns_raw:
                st.text_input("Other concern - please specify:", key="pb_concerns_other", placeholder="...")

            obstacles_raw = st.multiselect("Main obstacle preventing you from making a change? (up to 2)", options=OBSTACLES["en"], max_selections=2, key="pb_main_obstacle")
            if OTHER_EN in obstacles_raw:
                st.text_input("Other obstacle - please specify:", key="pb_obstacle_other", placeholder="...")

            part_b["skills_to_develop"] = st.text_area("Skills to develop in the next 12 months?", max_chars=300, key="pb_skills_to_develop")
            part_b["success_definition"] = st.text_area("What would success look like at the end of the process?", max_chars=300, key="pb_success_definition")

        st.divider()

        # CV
        st.markdown(f"**{L['cv_title']}**")
        st.caption(L["cv_desc"])
        cv_file = st.file_uploader(
            "CV (PDF / DOCX)" if lang == "en" else "קורות חיים (PDF / DOCX)",
            type=["pdf", "docx"]
        )

        submitted = st.form_submit_button(L["submit"], type="primary", use_container_width=True)

    if submitted:
        # Resolve all "Other" free-text values
        fc = st.session_state.get("field_current", "")
        part_b["field_current"] = resolve_other(fc, st.session_state.get("field_current_other", ""))

        fd = st.session_state.get("field_desired", "")
        part_b["field_desired"] = resolve_other(fd, st.session_state.get("field_desired_other", ""))

        rc = st.session_state.get("role_current", "")
        part_b["role_current"] = resolve_other(rc, st.session_state.get("role_current_other", ""))

        rd = st.session_state.get("role_desired", "")
        part_b["role_desired"] = resolve_other(rd, st.session_state.get("role_desired_other", ""))

        part_b["main_concerns"] = resolve_list_other(
            concerns_raw, st.session_state.get("pb_concerns_other", ""))
        part_b["main_obstacle"] = resolve_list_other(
            obstacles_raw, st.session_state.get("pb_obstacle_other", ""))

        cv_text = ""
        if cv_file:
            cv_text = extract_cv_text(cv_file.read(), cv_file.name)

        qid = save_questionnaire(client["id"], part_a, part_b, cv_text)

        with st.spinner("מנתח נתונים..." if lang == "he" else "Analyzing data..."):
            questionnaire = {"part_a": part_a, "part_b": part_b, "cv_text": cv_text}
            report = analyze_client(questionnaire, client)
            save_report(client["id"], qid, report)

        delete_draft(client["id"])
        st.success(L["success"])
        st.balloons()

    # ── Footer ─────────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="footer">
        CORE Blueprint &nbsp;|&nbsp; Yoav Peled Career Coaching<br>
        &copy; 2026 כל הזכויות שמורות ליואב פלד
    </div>
    """, unsafe_allow_html=True)


main()
