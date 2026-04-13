import streamlit as st
import os
import secrets
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent))

from core.database import (init_db, add_client, update_client, delete_client, reset_client_data,
                           get_all_clients, get_client_by_id, get_questionnaire, get_report, save_report)
from core.analyzer import analyze_client
from core.charts import create_spider_chart, create_energy_bars
from data.core_blueprint import TRACKS

st.set_page_config(
    page_title="CORE Blueprint — מנטור",
    layout="wide",
    page_icon="🧭",
    initial_sidebar_state="expanded",
)

init_db()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;600;700;900&display=swap');

html, body, [class*="css"] { font-family: 'Heebo', sans-serif; }

.stApp, .stApp * { direction: rtl; text-align: right; }
.stSlider, .stSlider * { direction: ltr !important; text-align: left !important; }

/* Sidebar RTL */
[data-testid="stSidebar"] { direction: rtl; }
[data-testid="stSidebar"] * { direction: rtl; text-align: right; }

/* Tabs RTL */
[data-testid="stTabs"] { direction: rtl; }
button[data-baseweb="tab"] { font-family: 'Heebo', sans-serif !important; font-weight: 600; }

/* Metrics */
[data-testid="stMetric"] { direction: rtl; text-align: right; }

/* Expander */
[data-testid="stExpander"] { direction: rtl; }

/* Buttons */
.stButton > button {
    background-color: #52c4cd !important;
    color: white !important;
    border: none !important;
    border-radius: 22px !important;
    font-weight: 700 !important;
    font-family: 'Heebo', sans-serif !important;
}
.stButton > button:hover { background-color: #0a203d !important; }

/* Headers and text */
h1, h2, h3, h4 { color: #0a203d; font-family: 'Heebo', sans-serif !important; }

/* Background */
.stApp { background-color: #f2f2f2; }

/* Cards */
[data-testid="stExpander"] { background: white; border-radius: 12px; }
</style>
""", unsafe_allow_html=True)


def _get_secret(key, default=""):
    try:
        return st.secrets.get(key) or os.getenv(key, default)
    except Exception:
        return os.getenv(key, default)

MENTOR_PASSWORD = _get_secret("MENTOR_PASSWORD", "core2024")
BASE_URL = _get_secret("BASE_URL", "http://localhost:8501")

PHASE_COLORS = {
    "Audit": "#EF553B",
    "Core": "#636EFA",
    "Resilience": "#00CC96",
    "Impact": "#AB63FA",
}


def check_auth():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if not st.session_state.authenticated:
        st.title("🧭 CORE Blueprint")
        st.subheader("כניסה למנטור")
        pwd = st.text_input("סיסמה", type="password")
        if st.button("כניסה", type="primary"):
            if pwd == MENTOR_PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("סיסמה שגויה")
        st.stop()


def sidebar():
    with st.sidebar:
        st.title("🧭 CORE Blueprint")
        st.caption("מנטור Dashboard")
        st.divider()
        page = st.radio(
            "ניווט",
            ["👥 לקוחות", "➕ לקוח חדש"],
            label_visibility="collapsed"
        )
        st.divider()
        if st.button("יציאה", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()
    return page


def page_clients():
    st.title("👥 לקוחות")
    clients = get_all_clients()

    if not clients:
        st.info("אין לקוחות עדיין. הוסף לקוח חדש.")
        return

    seen_ids = set()
    unique_clients = []
    for c in clients:
        if c["id"] not in seen_ids:
            seen_ids.add(c["id"])
            unique_clients.append(c)

    for client in unique_clients:
        has_questionnaire = bool(client.get("questionnaire_submitted"))
        has_report = bool(client.get("report_generated"))

        status = "✅ דוח מוכן" if has_report else ("⏳ ממתין לניתוח" if has_questionnaire else "📋 ממתין לשאלון")
        color = "#00CC96" if has_report else ("#FFA15A" if has_questionnaire else "#636EFA")

        with st.expander(f"**{client['name']}** — {client['email']} — {status}"):
            col1, col2 = st.columns([2, 1])
            with col1:
                token = client["token"]
                questionnaire_url = f"{BASE_URL}/questionnaire?token={token}"
                st.markdown(f"**קישור שאלון ללקוח:**")
                st.code(questionnaire_url)
            with col2:
                if has_report:
                    if st.button("צפה בדוח", key=f"view_{client['id']}", type="primary"):
                        st.session_state.view_client_id = client["id"]
                        st.rerun()
                elif has_questionnaire:
                    if st.button("צור דוח", key=f"gen_{client['id']}", type="secondary"):
                        with st.spinner("מנתח נתונים..."):
                            q = get_questionnaire(client["id"])
                            c = get_client_by_id(client["id"])
                            report = analyze_client(q, c)
                            save_report(client["id"], q["id"], report)
                        st.success("הדוח נוצר!")
                        st.rerun()

            # Edit / Delete
            with st.popover("✏️ עריכה / מחיקה"):
                st.markdown("**עריכת פרטי לקוח:**")
                new_name = st.text_input("שם", value=client["name"], key=f"edit_name_{client['id']}")
                new_email = st.text_input("אימייל", value=client["email"], key=f"edit_email_{client['id']}")
                new_notes = st.text_area("הערות", value=client.get("notes",""), key=f"edit_notes_{client['id']}")
                if st.button("💾 שמור שינויים", key=f"save_{client['id']}", type="primary"):
                    update_client(client["id"], new_name, new_email, new_notes)
                    st.success("עודכן!")
                    st.rerun()
                st.divider()
                st.markdown("**איפוס נתוני שאלון ודוח:**")
                st.caption("מוחק את השאלון והדוח - הלקוח יוכל למלא מחדש. הפרטים האישיים נשמרים.")
                confirm_reset = st.checkbox(f"אני מאשר איפוס נתוני {client['name']}", key=f"confirm_reset_{client['id']}")
                if confirm_reset:
                    if st.button("🔄 אפס נתונים", key=f"reset_{client['id']}", type="secondary"):
                        reset_client_data(client["id"])
                        if st.session_state.get("view_client_id") == client["id"]:
                            del st.session_state["view_client_id"]
                        st.success("הנתונים אופסו. הלקוח יכול למלא שאלון מחדש.")
                        st.rerun()

                st.divider()
                st.markdown("**מחיקת לקוח מלאה:**")
                st.caption("מוחק את הלקוח וכל הנתונים שלו לצמיתות.")
                confirm = st.checkbox(f"אני מאשר מחיקה מלאה של {client['name']}", key=f"confirm_{client['id']}")
                if confirm:
                    if st.button("🗑️ מחק לקוח לצמיתות", key=f"delete_{client['id']}", type="secondary"):
                        delete_client(client["id"])
                        if st.session_state.get("view_client_id") == client["id"]:
                            del st.session_state["view_client_id"]
                        st.success("הלקוח נמחק.")
                        st.rerun()

    if "view_client_id" in st.session_state:
        st.divider()
        show_client_report(st.session_state.view_client_id)


def show_client_report(client_id: int):
    client = get_client_by_id(client_id)
    report = get_report(client_id)

    if not report:
        st.warning("אין דוח זמין ללקוח זה.")
        return

    track_key = report["track"]
    track = TRACKS[track_key]

    st.title(f"📊 דוח — {client['name']}")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        st.metric("מסלול מומלץ", track["name_he"])
    with col2:
        if report.get("track_reason_he"):
            st.info(report["track_reason_he"])
    with col3:
        if st.button("🔄 צור דוח מחדש", key=f"regen_{client_id}"):
            with st.spinner("מנתח מחדש..."):
                q = get_questionnaire(client_id)
                rep = analyze_client(q, client)
                save_report(client_id, q["id"], rep)
            st.success("הדוח עודכן!")
            st.rerun()

    tabs = st.tabs(["📋 סיכום", "📈 פרופיל", "💪 SWOT", "🎯 כיוונים", "⚡ פעולות", "📚 משאבים", "🗺️ סילבוס"])

    # ── TAB 1: Executive Summary ───────────────────────────────────────────────
    with tabs[0]:
        if report.get("executive_summary_he"):
            st.info(report["executive_summary_he"])

        cv_profile = report.get("cv_profile", {})
        if cv_profile:
            col1, col2, col3 = st.columns(3)
            with col1:
                yrs = cv_profile.get("years_total_experience")
                st.metric("שנות ניסיון", f"{yrs}" if yrs else "N/A")
            with col2:
                st.metric("שלב קריירה", cv_profile.get("career_stage_he", "N/A"))
            with col3:
                st.metric("מסלול מומלץ", track["name_he"])

            if cv_profile.get("key_technical_skills"):
                st.markdown("**כישורים טכניים מרכזיים:**")
                skills_str = " • ".join(cv_profile["key_technical_skills"])
                st.markdown(f"<p style='color:#52c4cd;font-weight:600'>{skills_str}</p>", unsafe_allow_html=True)

            if cv_profile.get("market_positioning_he"):
                st.markdown("**מיקום בשוק:**")
                st.write(cv_profile["market_positioning_he"])

        if report.get("market_analysis_he"):
            st.markdown("**ניתוח שוק:**")
            st.write(report["market_analysis_he"])

    # ── TAB 2: Profile ─────────────────────────────────────────────────────────
    with tabs[1]:
        col1, col2 = st.columns([3, 2])
        with col1:
            spider = report.get("spider_data", {})
            if spider:
                fig = create_spider_chart(spider, client["name"])
                st.plotly_chart(fig, use_container_width=True)
        with col2:
            batteries = report.get("energy_batteries", {})
            if batteries:
                fig2 = create_energy_bars(batteries)
                st.plotly_chart(fig2, use_container_width=True)

        cv_profile = report.get("cv_profile", {})
        if report.get("cv_analysis") and report["cv_analysis"] != "לא צורף קורות חיים":
            st.subheader("ניתוח קורות חיים")
            st.write(report["cv_analysis"])
            if cv_profile.get("career_trajectory_he"):
                st.markdown(f"**מסלול קריירה:** {cv_profile['career_trajectory_he']}")
            if cv_profile.get("personal_brand_he"):
                st.markdown(f"**מיתוג אישי:** {cv_profile['personal_brand_he']}")
            if cv_profile.get("brand_gaps_he"):
                st.markdown(f"**מה חסר במיתוג:** {cv_profile['brand_gaps_he']}")
            milestones = report.get("cv_milestones", [])
            if milestones:
                st.markdown("**אבני דרך עיקריות:**")
                for m in milestones:
                    st.markdown(f"• {m}")

        insights = report.get("insights", [])
        if insights:
            st.subheader("תובנות מרכזיות")
            for i, insight in enumerate(insights, 1):
                st.markdown(f"**{i}.** {insight}" if isinstance(insight, str) else f"**{i}.** {str(insight)}")

    # ── TAB 3: SWOT ────────────────────────────────────────────────────────────
    with tabs[2]:
        swot = report.get("swot", {})
        if swot:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### 💪 חוזקות")
                for s in swot.get("strengths_he", []):
                    st.markdown(f"✅ {s}")
                st.markdown("### 🌱 הזדמנויות")
                for s in swot.get("opportunities_he", []):
                    st.markdown(f"🚀 {s}")
            with col2:
                st.markdown("### ⚠️ חולשות")
                for s in swot.get("weaknesses_he", []):
                    st.markdown(f"🔸 {s}")
                st.markdown("### 🌩️ איומים")
                for s in swot.get("threats_he", []):
                    st.markdown(f"⚡ {s}")
        else:
            st.info("SWOT יהיה זמין בדוח הבא")

    # ── TAB 4: Directions ──────────────────────────────────────────────────────
    with tabs[3]:
        directions = report.get("recommended_directions", [])
        for d in directions:
            title = d.get("title_he") or d.get("title", "")
            desc = d.get("description_he") or d.get("description", "")
            with st.expander(f"**{title}** — התאמה: {d.get('fit_score','?')}/10", expanded=True):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("התאמה", f"{d.get('fit_score','?')}/10")
                with col2:
                    demand = d.get("market_demand","")
                    demand_he = {"high":"גבוהה","medium":"בינונית","low":"נמוכה"}.get(demand, demand)
                    st.metric("ביקוש שוק", demand_he)
                with col3:
                    st.metric("שכר צפוי (₪)", d.get("salary_range_ils","N/A"))
                with col4:
                    risk = d.get("risk_level","")
                    risk_he = {"high":"גבוה","medium":"בינוני","low":"נמוך"}.get(risk, risk)
                    st.metric("רמת סיכון", risk_he)

                st.write(desc)

                if d.get("why_good_fit_he"):
                    st.markdown(f"**למה מתאים לך:** {d['why_good_fit_he']}")
                if d.get("timeline_he"):
                    st.caption(f"⏱️ ציר זמן: {d['timeline_he']}")

                col_r, col_w = st.columns(2)
                with col_r:
                    if d.get("reward_he"):
                        st.success(f"**פוטנציאל:** {d['reward_he']}")
                with col_w:
                    if d.get("risk_he"):
                        st.warning(f"**סיכון:** {d['risk_he']}")

                if d.get("skills_gap_he"):
                    st.markdown("**פערי כישורים לסגירה:**")
                    for sk in d["skills_gap_he"]:
                        st.markdown(f"• {sk}")
                    if d.get("bridge_plan_he"):
                        st.markdown(f"**תוכנית סגירת פערים:** {d['bridge_plan_he']}")

                st.markdown("**תוכנית 30/60/90 יום:**")
                col30, col60, col90 = st.columns(3)
                with col30:
                    st.markdown("**30 יום**")
                    for a in d.get("plan_30_days_he",[]):
                        st.markdown(f"• {a}")
                with col60:
                    st.markdown("**60 יום**")
                    for a in d.get("plan_60_days_he",[]):
                        st.markdown(f"• {a}")
                with col90:
                    st.markdown("**90 יום**")
                    for a in d.get("plan_90_days_he",[]):
                        st.markdown(f"• {a}")

    # ── TAB 5: Quick Wins & Action Plan ───────────────────────────────────────
    with tabs[4]:
        quick_wins = report.get("quick_wins", [])
        if quick_wins:
            st.subheader("⚡ ניצחונות מהירים - לעשות עכשיו")
            for i, w in enumerate(quick_wins, 1):
                st.markdown(f"**{i}.** {w}")
            st.divider()

        networking = report.get("networking", {})
        if networking:
            st.subheader("🤝 רשת קשרים מקצועית")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**קהילות מומלצות:**")
                for c in networking.get("communities", []):
                    st.markdown(f"• {c}")
            with col2:
                st.markdown("**אירועים ומפגשים:**")
                for e in networking.get("events", []):
                    st.markdown(f"• {e}")
            with col3:
                st.markdown("**אונליין:**")
                for o in networking.get("online", []):
                    st.markdown(f"• {o}")

    # ── TAB 6: Resources ───────────────────────────────────────────────────────
    with tabs[5]:
        resources = report.get("resources", {})
        if resources:
            courses = resources.get("courses", [])
            if courses:
                st.subheader("🎓 קורסים מומלצים")
                for c in courses:
                    with st.container(border=True):
                        st.markdown(f"**{c.get('name','')}** — {c.get('platform','')}")
                        if c.get("why_he"):
                            st.caption(c["why_he"])

            books = resources.get("books", [])
            if books:
                st.subheader("📖 ספרים מומלצים")
                for b in books:
                    with st.container(border=True):
                        st.markdown(f"**{b.get('title','')}** — {b.get('author','')}")
                        if b.get("why_he"):
                            st.caption(b["why_he"])

            certs = resources.get("certifications", [])
            if certs:
                st.subheader("🏅 הסמכות מומלצות")
                for cert in certs:
                    name = cert.get("name","") if isinstance(cert, dict) else str(cert)
                    why = cert.get("why_he","") if isinstance(cert, dict) else ""
                    st.markdown(f"• **{name}**" + (f" - {why}" if why else ""))

    # ── TAB 7: Syllabus ────────────────────────────────────────────────────────
    with tabs[6]:
        st.subheader(f"סילבוס מותאם אישית — {track['name_he']}")
        syllabus = report.get("syllabus", [])
        for session in syllabus:
            phase = session.get("phase", "")
            session_num = session.get("session", "")
            title = session.get("title_he", "")
            with st.expander(f"מפגש {session_num} | {phase} | {title}"):
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.markdown(f"**מטרה:** {session.get('goal_he', '')}")
                    st.markdown(f"**שיעורי בית:** {session.get('homework_he', '')}")
                    if session.get("homework_adaptation_he"):
                        st.info(f"התאמה אישית: {session['homework_adaptation_he']}")
                with col2:
                    if session.get("personalized_focus_he"):
                        st.markdown("**מיקוד מותאם:**")
                        st.info(session["personalized_focus_he"])
                    for q in session.get("key_questions_he", []):
                        st.markdown(f"• {q}")
                tools = session.get("tools", [])
                if tools:
                    st.markdown("**כלים:** " + " | ".join(tools))

    if st.button("← חזרה לרשימה"):
        del st.session_state.view_client_id
        st.rerun()


def page_new_client():
    st.title("➕ הוספת לקוח חדש")

    with st.form("new_client_form"):
        name = st.text_input("שם מלא *")
        email = st.text_input("אימייל *")
        notes = st.text_area("הערות (אופציונלי)")
        submitted = st.form_submit_button("צור לקוח ושלח קישור", type="primary")

    if submitted:
        if not name or not email:
            st.error("שם ואימייל הם שדות חובה.")
            return
        token = secrets.token_urlsafe(24)
        try:
            client_id = add_client(name, email, token, notes)
            questionnaire_url = f"{BASE_URL}/questionnaire?token={token}"
            st.success(f"לקוח **{name}** נוצר בהצלחה!")
            st.markdown("**קישור לשאלון (שלח ללקוח):**")
            st.code(questionnaire_url)
            st.info("העתק את הקישור ושלח ללקוח באימייל או בוואטסאפ.")
        except Exception as e:
            if "UNIQUE constraint" in str(e):
                st.error("כתובת האימייל כבר קיימת במערכת.")
            else:
                st.error(f"שגיאה: {e}")


def main():
    check_auth()
    page = sidebar()

    if page == "👥 לקוחות":
        page_clients()
    elif page == "➕ לקוח חדש":
        page_new_client()


main()
