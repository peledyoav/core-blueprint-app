import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import (init_db, get_client_by_token, save_questionnaire,
                           get_questionnaire, save_draft, get_draft, delete_draft, save_report)

st.set_page_config(page_title="CORE Blueprint — שאלון", layout="centered", page_icon="🧭")

init_db()

LABELS = {
    "he": {
        "title": "🧭 שאלון CORE Blueprint",
        "subtitle": "שאלון קריירה אישי — הייטק",
        "welcome": "ברוכ/ה הבא/ה",
        "part_a_title": "חלק א' — שביעות רצון נוכחית",
        "part_a_desc": "דרג/י כל תחום מ-1 (לא מרוצה בכלל) עד 10 (מרוצה מאוד)",
        "part_b_title": "חלק ב' — כיוון מקצועי",
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
        "role_current": "תפקיד/דומיין נוכחי",
        "role_desired": "תפקיד/דומיין רצוי",
    },
    "en": {
        "title": "🧭 CORE Blueprint Questionnaire",
        "subtitle": "Personal Career Questionnaire — High-Tech",
        "welcome": "Welcome",
        "part_a_title": "Part A — Current Satisfaction",
        "part_a_desc": "Rate each area from 1 (very unsatisfied) to 10 (very satisfied)",
        "part_b_title": "Part B — Professional Direction",
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
        "role_current": "Current role / domain",
        "role_desired": "Desired role / domain",
    }
}

PART_A_QUESTIONS = {
    "he": [
        "אתגרי יומיום — עד כמה את/ה מרוצה מהאתגרים, המשימות והאחריות בתפקיד?",
        "איזון עבודה-חיים — עד כמה את/ה מרוצה מהאיזון בין העבודה לחיים האישיים?",
        "פיתוח מקצועי — עד כמה את/ה מרוצה ממסלול הקריירה וההתקדמות שלך?",
        "גמול חומרי — עד כמה את/ה מרוצה מהשכר, הביטחון הכלכלי וההטבות?",
        "יחסים בעבודה — עד כמה את/ה מרוצה מהיחסים עם מנהלים, עמיתים ובעלי עניין?",
        "ביטחון תעסוקתי — עד כמה את/ה מרגיש/ה יציבות ובטחון בתפקיד הנוכחי?",
        "תרבות ארגונית — עד כמה את/ה מרוצה מתרבות הארגון, החדשנות ורווחת העובדים?",
        "משמעות ומטרה — עד כמה את/ה מרגיש/ה שהעבודה שלך משמעותית ומתאימה לערכיך?",
        "עניין ומימוש עצמי — עד כמה את/ה מרגיש/ה שאת/ה מממש/ת את הפוטנציאל שלך?",
        "השפעה ויוזמה — עד כמה את/ה מרגיש/ה שיש לך השפעה ויכולת להוביל שינויים?",
    ],
    "en": [
        "Daily Challenges — How satisfied are you with the challenges, tasks, and responsibilities in your role?",
        "Work-Life Balance — How satisfied are you with the balance between work and personal life?",
        "Professional Development — How satisfied are you with your career path and progress?",
        "Compensation — How satisfied are you with your salary, financial security, and benefits?",
        "Work Relationships — How satisfied are you with your relationships with managers, colleagues, and stakeholders?",
        "Employment Security — How secure and stable do you feel in your current role?",
        "Organizational Culture — How satisfied are you with the organization's culture, innovation, and employee wellbeing?",
        "Meaning & Purpose — How much do you feel your work is meaningful and aligned with your values?",
        "Interest & Self-Actualization — How much do you feel you're realizing your full potential?",
        "Influence & Initiative — How much influence do you feel you have and ability to lead change?",
    ]
}

PART_A_KEYS = ["q1", "q2", "q3", "q4", "q5", "q6", "q7", "q8", "q9", "q10"]

# General fields
FIELDS = {
    "he": [
        "פיתוח תוכנה (Software)",
        "חומרה / אלקטרוניקה (Hardware)",
        "קושחה / מערכות משובצות (Embedded/Firmware)",
        "IT / תשתיות",
        "דאטה ואנליטיקה",
        "בינה מלאכותית / מחקר (AI/ML)",
        "סייבר ואבטחת מידע",
        "מוצר ועיצוב (Product/UX)",
        "פינטק (Fintech)",
        "ביוטק / מדטק (Biotech/MedTech)",
        "ביטחון ואווירונאוטיקה (Defense/Aerospace)",
        "תקשורת וסלקום (Telecom)",
        "ניהול פרויקטים / תוכניות",
        "אחר",
    ],
    "en": [
        "Software Development",
        "Hardware / Electronics",
        "Embedded / Firmware",
        "IT / Infrastructure",
        "Data & Analytics",
        "AI / ML / Research",
        "Cybersecurity",
        "Product & Design (UX)",
        "Fintech",
        "Biotech / MedTech",
        "Defense / Aerospace",
        "Telecom",
        "Project / Program Management",
        "Other",
    ]
}

# Specific roles per field (same index as FIELDS)
ROLES_BY_FIELD = {
    "פיתוח תוכנה (Software)": ["Backend", "Frontend", "Full-Stack", "Mobile (iOS/Android)", "QA / Automation", "DevOps / Platform", "Site Reliability (SRE)", "Software Architecture", "אחר / Other"],
    "חומרה / אלקטרוניקה (Hardware)": ["VLSI / ASIC Design", "PCB Design", "Analog / RF", "Digital Design", "Hardware Verification", "System Engineering", "אחר / Other"],
    "קושחה / מערכות משובצות (Embedded/Firmware)": ["Firmware Development", "RTOS / BSP", "Drivers", "Embedded Linux", "Real-Time Systems", "אחר / Other"],
    "IT / תשתיות": ["SysAdmin / IT", "Network Engineering", "Cloud (AWS/Azure/GCP)", "IT Support", "Storage & Backup", "אחר / Other"],
    "דאטה ואנליטיקה": ["Data Engineering", "Data Science", "BI / Analytics", "Data Architecture", "Database Administration", "אחר / Other"],
    "בינה מלאכותית / מחקר (AI/ML)": ["ML Engineering", "AI Research", "Computer Vision", "NLP", "MLOps", "Generative AI", "אחר / Other"],
    "סייבר ואבטחת מידע": ["Penetration Testing / Red Team", "SOC / Blue Team", "AppSec", "Cloud Security", "GRC / Compliance", "אחר / Other"],
    "מוצר ועיצוב (Product/UX)": ["Product Management", "UX / UI Design", "Product Analytics", "Growth", "אחר / Other"],
    "פינטק (Fintech)": ["Backend / API", "Payments", "Risk & Compliance", "Blockchain / Web3", "Trading Systems", "אחר / Other"],
    "ביוטק / מדטק (Biotech/MedTech)": ["Bioinformatics", "Medical Devices Software", "Regulatory Affairs", "Clinical Data", "אחר / Other"],
    "ביטחון ואווירונאוטיקה (Defense/Aerospace)": ["Systems Engineering", "Avionics", "Simulation", "Signal Processing", "Cyber Defense", "אחר / Other"],
    "תקשורת וסלקום (Telecom)": ["Network Engineering", "RF / Wireless", "Core Network", "OSS/BSS", "אחר / Other"],
    "ניהול פרויקטים / תוכניות": ["Project Manager", "Program Manager", "Scrum Master / Agile", "PMO", "אחר / Other"],
    "אחר": ["אחר / Other"],
    # English keys
    "Software Development": ["Backend", "Frontend", "Full-Stack", "Mobile (iOS/Android)", "QA / Automation", "DevOps / Platform", "Site Reliability (SRE)", "Software Architecture", "Other"],
    "Hardware / Electronics": ["VLSI / ASIC Design", "PCB Design", "Analog / RF", "Digital Design", "Hardware Verification", "System Engineering", "Other"],
    "Embedded / Firmware": ["Firmware Development", "RTOS / BSP", "Drivers", "Embedded Linux", "Real-Time Systems", "Other"],
    "IT / Infrastructure": ["SysAdmin / IT", "Network Engineering", "Cloud (AWS/Azure/GCP)", "IT Support", "Storage & Backup", "Other"],
    "Data & Analytics": ["Data Engineering", "Data Science", "BI / Analytics", "Data Architecture", "Database Administration", "Other"],
    "AI / ML / Research": ["ML Engineering", "AI Research", "Computer Vision", "NLP", "MLOps", "Generative AI", "Other"],
    "Cybersecurity": ["Penetration Testing / Red Team", "SOC / Blue Team", "AppSec", "Cloud Security", "GRC / Compliance", "Other"],
    "Product & Design (UX)": ["Product Management", "UX / UI Design", "Product Analytics", "Growth", "Other"],
    "Fintech": ["Backend / API", "Payments", "Risk & Compliance", "Blockchain / Web3", "Trading Systems", "Other"],
    "Biotech / MedTech": ["Bioinformatics", "Medical Devices Software", "Regulatory Affairs", "Clinical Data", "Other"],
    "Defense / Aerospace": ["Systems Engineering", "Avionics", "Simulation", "Signal Processing", "Cyber Defense", "Other"],
    "Telecom": ["Network Engineering", "RF / Wireless", "Core Network", "OSS/BSS", "Other"],
    "Project / Program Management": ["Project Manager", "Program Manager", "Scrum Master / Agile", "PMO", "Other"],
    "Other": ["Other"],
}

SENIORITY_OPTIONS = ["Junior", "Mid", "Senior", "Staff / Principal", "Lead / Manager", "Director+"]

CONCERNS = {
    "he": ["השפעת ה-AI על התפקיד שלי", "פיטורים וחוסר יציבות", "תקרת זכוכית",
           "חוסר כיוון ברור", "פער כישורים", "שחיקה"],
    "en": ["AI's impact on my role", "Layoffs & instability", "Glass ceiling",
           "Lack of clear direction", "Skills gap", "Burnout"],
}

OBSTACLES = {
    "he": ["פחד מכישלון", "אי-בטחון בכישורים", "שכר ויציבות", "זמן ואנרגיה",
           "לא יודע מה אני רוצה", "מחויבות משפחתית"],
    "en": ["Fear of failure", "Skill insecurity", "Salary & stability", "Time & energy",
           "Don't know what I want", "Family commitments"],
}


def main():
    token = st.query_params.get("token", "")

    if "lang" not in st.session_state:
        st.session_state.lang = "he"

    lang = st.session_state.lang
    L = LABELS[lang]
    rtl = lang == "he"

    if rtl:
        st.markdown("""
        <style>
        .stApp { direction: rtl; text-align: right; }
        .stSlider { direction: ltr; }
        </style>
        """, unsafe_allow_html=True)

    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button(L["lang_toggle"]):
            st.session_state.lang = "en" if lang == "he" else "he"
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

    # Restore draft into session_state on first load
    if "draft_loaded" not in st.session_state:
        draft = get_draft(client["id"])
        if draft:
            for k, v in draft["part_a"].items():
                st.session_state[f"pa_{k}"] = v
            for k, v in draft["part_b"].items():
                st.session_state[f"pb_{k}"] = v
            st.session_state["field_current"] = draft["part_b"].get("field_current", FIELDS[lang][0])
            st.session_state["field_desired"] = draft["part_b"].get("field_desired", FIELDS[lang][0])
            st.session_state["role_current"] = draft["part_b"].get("role_current", "")
            st.session_state["role_desired"] = draft["part_b"].get("role_desired", "")
        st.session_state["draft_loaded"] = True

    st.title(L["title"])
    st.markdown(f"**{L['welcome']}, {client['name']}**")
    st.markdown(f"*{L['subtitle']}*")
    st.divider()

    # --- Dynamic field/role selectors (outside form for reactivity) ---
    st.subheader(L["part_b_title"])
    st.caption(L["part_b_desc"])

    fields_list = FIELDS[lang]

    col1, col2 = st.columns(2)
    with col1:
        field_current = st.selectbox(L["field_current"], fields_list, key="field_current")
    with col2:
        field_desired = st.selectbox(L["field_desired"], fields_list, key="field_desired")

    roles_current = ROLES_BY_FIELD.get(field_current, ["אחר / Other"])
    roles_desired = ROLES_BY_FIELD.get(field_desired, ["אחר / Other"])

    col3, col4 = st.columns(2)
    with col3:
        role_current = st.selectbox(L["role_current"], roles_current, key="role_current")
    with col4:
        role_desired = st.selectbox(L["role_desired"], roles_desired, key="role_desired")

    st.divider()

    with st.form("questionnaire_form"):
        # --- PART A ---
        st.subheader(L["part_a_title"])
        st.caption(L["part_a_desc"])

        part_a = {}
        questions = PART_A_QUESTIONS[lang]
        for key, question in zip(PART_A_KEYS, questions):
            part_a[key] = st.slider(question, min_value=1, max_value=10, value=5, key=f"pa_{key}")

        st.divider()

        # --- PART B (rest of questions) ---
        part_b = {}

        if lang == "he":
            part_b["seniority"] = st.selectbox("רמת בכירות נוכחית", SENIORITY_OPTIONS, key="pb_seniority")
            part_b["ic_manager"] = st.slider("IC או Manager? (1 = טכני מלא, 10 = ניהול אנשים מלא)", 1, 10, 5, key="pb_ic_manager")
            part_b["technical_depth"] = st.slider("כמה חשוב לך להישאר 'בחומר הטכני' ביומיום? (1-10)", 1, 10, 5, key="pb_technical_depth")
            part_b["company_stage"] = st.slider("סטייג' חברה מועדף (1 = Startup מוקדם, 10 = Enterprise גדול)", 1, 10, 5, key="pb_company_stage")
            part_b["market_demand"] = st.slider("כמה אתה מרגיש שהכישורים שלך מבוקשים בשוק היום? (1-10)", 1, 10, 5, key="pb_market_demand")
            part_b["main_concerns"] = st.multiselect("מה החשש המרכזי שלך לגבי העתיד המקצועי? (עד 2)", options=CONCERNS[lang], max_selections=2, key="pb_main_concerns")
            part_b["main_obstacle"] = st.multiselect("מה המכשול העיקרי שמונע ממך לעשות את השינוי? (עד 2)", options=OBSTACLES[lang], max_selections=2, key="pb_main_obstacle")
            part_b["skills_to_develop"] = st.text_area("אילו כישורים תרצה לפתח ב-12 חודשים הקרובים? (משפט אחד)", max_chars=300, key="pb_skills_to_develop")
            part_b["success_definition"] = st.text_area("מה ייראה לך כהצלחה בסוף התהליך? (משפט אחד)", max_chars=300, key="pb_success_definition")
        else:
            part_b["seniority"] = st.selectbox("Current seniority level", SENIORITY_OPTIONS, key="pb_seniority")
            part_b["ic_manager"] = st.slider("IC or Manager? (1 = fully technical, 10 = people management)", 1, 10, 5, key="pb_ic_manager")
            part_b["technical_depth"] = st.slider("How important is staying 'in the technical material' daily? (1-10)", 1, 10, 5, key="pb_technical_depth")
            part_b["company_stage"] = st.slider("Preferred company stage (1 = Early Startup, 10 = Large Enterprise)", 1, 10, 5, key="pb_company_stage")
            part_b["market_demand"] = st.slider("How in-demand do you feel your skills are today? (1-10)", 1, 10, 5, key="pb_market_demand")
            part_b["main_concerns"] = st.multiselect("Main concerns about your professional future? (up to 2)", options=CONCERNS[lang], max_selections=2, key="pb_main_concerns")
            part_b["main_obstacle"] = st.multiselect("Main obstacle preventing you from making a change? (up to 2)", options=OBSTACLES[lang], max_selections=2, key="pb_main_obstacle")
            part_b["skills_to_develop"] = st.text_area("Skills to develop in the next 12 months? (one sentence)", max_chars=300, key="pb_skills_to_develop")
            part_b["success_definition"] = st.text_area("What would success look like at the end of the process? (one sentence)", max_chars=300, key="pb_success_definition")

        st.divider()

        # --- CV ---
        st.subheader(L["cv_title"])
        st.caption(L["cv_desc"])
        cv_file = st.file_uploader(
            "CV (PDF / DOCX)" if lang == "en" else "קורות חיים (PDF / DOCX)",
            type=["pdf", "docx"]
        )

        col_save, col_submit = st.columns([1, 2])
        with col_save:
            save_btn = st.form_submit_button(
                "💾 שמור טיוטה" if lang == "he" else "💾 Save Draft",
                use_container_width=True
            )
        with col_submit:
            submitted = st.form_submit_button(L["submit"], type="primary", use_container_width=True)

    if save_btn:
        draft_part_b = {
            "field_current": st.session_state.get("field_current", ""),
            "field_desired": st.session_state.get("field_desired", ""),
            "role_current": st.session_state.get("role_current", ""),
            "role_desired": st.session_state.get("role_desired", ""),
        }
        for k in ["seniority", "ic_manager", "technical_depth", "company_stage",
                  "market_demand", "main_concerns", "main_obstacle",
                  "skills_to_develop", "success_definition"]:
            if f"pb_{k}" in st.session_state:
                draft_part_b[k] = st.session_state[f"pb_{k}"]
        draft_part_a = {k: st.session_state.get(f"pa_{k}", 5) for k in PART_A_KEYS}
        save_draft(client["id"], draft_part_a, draft_part_b)
        st.success("✅ הטיוטה נשמרה!" if lang == "he" else "✅ Draft saved!")

    if submitted:
        # Merge field/role from session state into part_b
        part_b["field_current"] = st.session_state.get("field_current", "")
        part_b["field_desired"] = st.session_state.get("field_desired", "")
        part_b["role_current"] = st.session_state.get("role_current", "")
        part_b["role_desired"] = st.session_state.get("role_desired", "")

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


main()
