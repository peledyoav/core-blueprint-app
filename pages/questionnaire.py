import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import init_db, get_client_by_token, save_questionnaire, get_questionnaire
from core.analyzer import analyze_client, extract_cv_text
from core.database import save_report

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
        "top3_label": "בחר/י 3 תחומים הדחופים ביותר לשיפור:",
        "lang_toggle": "English",
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
        "top3_label": "Select the 3 most urgent areas to improve:",
        "lang_toggle": "עברית",
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

PART_A_SHORT = {
    "he": ["אתגרי יומיום", "איזון עבודה-חיים", "פיתוח מקצועי", "גמול חומרי",
           "יחסים בעבודה", "ביטחון תעסוקתי", "תרבות ארגונית", "משמעות ומטרה",
           "עניין ומימוש עצמי", "השפעה ויוזמה"],
    "en": ["Daily Challenges", "Work-Life Balance", "Professional Dev.", "Compensation",
           "Work Relationships", "Employment Security", "Culture", "Meaning & Purpose",
           "Self-Actualization", "Influence"],
}

DOMAINS = ["Backend", "Frontend", "Full-Stack", "Data", "AI/ML", "DevOps/Platform",
           "Product", "Architecture", "Security", "אחר / Other"]

SENIORITY_OPTIONS = {
    "he": ["Junior", "Mid", "Senior", "Staff / Principal", "Lead / Manager", "Director+"],
    "en": ["Junior", "Mid", "Senior", "Staff / Principal", "Lead / Manager", "Director+"],
}

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
        .stRadio > div { flex-direction: row-reverse; }
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

    st.title(L["title"])
    st.markdown(f"**{L['welcome']}, {client['name']}**")
    st.markdown(f"*{L['subtitle']}*")
    st.divider()

    with st.form("questionnaire_form"):
        # --- PART A ---
        st.subheader(L["part_a_title"])
        st.caption(L["part_a_desc"])

        part_a = {}
        questions = PART_A_QUESTIONS[lang]
        for i, (key, question) in enumerate(zip(PART_A_KEYS, questions)):
            part_a[key] = st.slider(
                question,
                min_value=1, max_value=10, value=5,
                key=f"part_a_{key}"
            )

        short_labels = PART_A_SHORT[lang]
        top3 = st.multiselect(
            L["top3_label"],
            options=short_labels,
            max_selections=3,
            key="top3"
        )
        part_a["top3"] = top3

        st.divider()

        # --- PART B ---
        st.subheader(L["part_b_title"])
        st.caption(L["part_b_desc"])

        part_b = {}

        if lang == "he":
            part_b["seniority"] = st.selectbox("רמת בכירות נוכחית", SENIORITY_OPTIONS[lang])
            part_b["domain_current"] = st.selectbox("דומיין נוכחי", DOMAINS)
            part_b["domain_desired"] = st.selectbox("דומיין רצוי", DOMAINS)
            part_b["ic_manager"] = st.slider(
                "IC או Manager? (1 = טכני מלא, 10 = ניהול אנשים מלא)",
                1, 10, 5
            )
            part_b["technical_depth"] = st.slider(
                "כמה חשוב לך להישאר 'בחומר הטכני' ביומיום? (1-10)",
                1, 10, 5
            )
            part_b["company_stage"] = st.slider(
                "סטייג' חברה מועדף (1 = Startup מוקדם, 10 = Enterprise גדול)",
                1, 10, 5
            )
            part_b["market_demand"] = st.slider(
                "כמה אתה מרגיש שהכישורים שלך מבוקשים בשוק היום? (1-10)",
                1, 10, 5
            )
            part_b["main_concerns"] = st.multiselect(
                "מה החשש המרכזי שלך לגבי העתיד המקצועי? (עד 2)",
                options=CONCERNS[lang], max_selections=2
            )
            part_b["main_obstacle"] = st.multiselect(
                "מה המכשול העיקרי שמונע ממך לעשות את השינוי? (עד 2)",
                options=OBSTACLES[lang], max_selections=2
            )
            part_b["skills_to_develop"] = st.text_area(
                "אילו כישורים תרצה לפתח ב-12 חודשים הקרובים? (משפט אחד)",
                max_chars=300
            )
            part_b["success_definition"] = st.text_area(
                "מה ייראה לך כהצלחה בסוף התהליך? (משפט אחד)",
                max_chars=300
            )
        else:
            part_b["seniority"] = st.selectbox("Current seniority level", SENIORITY_OPTIONS[lang])
            part_b["domain_current"] = st.selectbox("Current domain", DOMAINS)
            part_b["domain_desired"] = st.selectbox("Desired domain", DOMAINS)
            part_b["ic_manager"] = st.slider(
                "IC or Manager? (1 = fully technical, 10 = people management)",
                1, 10, 5
            )
            part_b["technical_depth"] = st.slider(
                "How important is staying 'in the technical material' daily? (1-10)",
                1, 10, 5
            )
            part_b["company_stage"] = st.slider(
                "Preferred company stage (1 = Early Startup, 10 = Large Enterprise)",
                1, 10, 5
            )
            part_b["market_demand"] = st.slider(
                "How in-demand do you feel your skills are today? (1-10)",
                1, 10, 5
            )
            part_b["main_concerns"] = st.multiselect(
                "What are your main concerns about your professional future? (up to 2)",
                options=CONCERNS[lang], max_selections=2
            )
            part_b["main_obstacle"] = st.multiselect(
                "What is the main obstacle preventing you from making a change? (up to 2)",
                options=OBSTACLES[lang], max_selections=2
            )
            part_b["skills_to_develop"] = st.text_area(
                "What skills would you like to develop in the next 12 months? (one sentence)",
                max_chars=300
            )
            part_b["success_definition"] = st.text_area(
                "What would success look like at the end of the process? (one sentence)",
                max_chars=300
            )

        st.divider()

        # --- CV ---
        st.subheader(L["cv_title"])
        st.caption(L["cv_desc"])
        cv_file = st.file_uploader(
            "CV (PDF / DOCX)" if lang == "en" else "קורות חיים (PDF / DOCX)",
            type=["pdf", "docx"]
        )

        submitted = st.form_submit_button(L["submit"], type="primary", use_container_width=True)

    if submitted:
        cv_text = ""
        if cv_file:
            cv_text = extract_cv_text(cv_file.read(), cv_file.name)

        qid = save_questionnaire(client["id"], part_a, part_b, cv_text)

        with st.spinner("מנתח נתונים..." if lang == "he" else "Analyzing data..."):
            questionnaire = {"part_a": part_a, "part_b": part_b, "cv_text": cv_text}
            report = analyze_client(questionnaire, client)
            save_report(client["id"], qid, report)

        st.success(L["success"])
        st.balloons()


main()
