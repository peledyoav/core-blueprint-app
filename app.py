import streamlit as st
import os
import secrets
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent))

from core.database import init_db, add_client, get_all_clients, get_client_by_id, get_questionnaire, get_report
from core.charts import create_spider_chart, create_energy_bars
from data.core_blueprint import TRACKS

st.set_page_config(
    page_title="CORE Blueprint — מנטור",
    layout="wide",
    page_icon="🧭",
    initial_sidebar_state="expanded",
)

init_db()

MENTOR_PASSWORD = os.getenv("MENTOR_PASSWORD", "core2024")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8501")

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

    col1, col2 = st.columns([1, 1])
    with col1:
        st.metric("מסלול מומלץ", track["name_he"])
    with col2:
        st.info(report["track_reason_he"])

    tab1, tab2, tab3, tab4 = st.tabs(["📈 פרופיל", "🔍 תובנות", "🗺️ כיוונים", "📋 סילבוס"])

    with tab1:
        col1, col2 = st.columns([3, 2])
        with col1:
            fig = create_spider_chart(report["spider_data"], client["name"])
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig2 = create_energy_bars(report.get("energy_batteries", {}))
            st.plotly_chart(fig2, use_container_width=True)

        if report.get("cv_analysis"):
            st.subheader("ניתוח קורות חיים")
            st.write(report["cv_analysis"])
            milestones = report.get("cv_milestones", [])
            if milestones:
                st.subheader("אבני דרך עיקריות")
                for m in milestones:
                    st.markdown(f"• {m}")

    with tab2:
        st.subheader("תובנות מרכזיות")
        insights = report.get("insights", [])
        for i, insight in enumerate(insights, 1):
            st.markdown(f"**{i}.** {insight}")

    with tab3:
        st.subheader("כיווני פיתוח מומלצים")
        directions = report.get("recommended_directions", [])
        for d in directions:
            with st.container(border=True):
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.markdown(f"### {d.get('title', '')}")
                    st.write(d.get("description", ""))
                with col2:
                    st.metric("התאמה", f"{d.get('fit_score', 0)}/10")
                with col3:
                    demand = d.get("market_demand", "")
                    demand_he = {"high": "גבוהה", "medium": "בינונית", "low": "נמוכה"}.get(demand, demand)
                    st.metric("ביקוש שוק", demand_he)
                st.caption(f"⏱️ {d.get('timeline', '')}")

    with tab4:
        st.subheader(f"סילבוס מותאם אישית — {track['name_he']}")
        syllabus = report.get("syllabus", [])

        for session in syllabus:
            phase = session.get("phase", "")
            color = PHASE_COLORS.get(phase, "#636EFA")
            session_num = session.get("session", "")
            title = session.get("title_he", "")

            with st.expander(f"מפגש {session_num} | {phase} | {title}"):
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.markdown(f"**מטרה:** {session.get('goal_he', '')}")
                    st.markdown(f"**הכנה ללקוח:** {session.get('homework_he', '')}")
                    if session.get("homework_adaptation_he"):
                        st.markdown(f"**התאמה אישית לשיעורי בית:** {session['homework_adaptation_he']}")
                with col2:
                    if session.get("personalized_focus_he"):
                        st.markdown("**מיקוד מותאם אישית:**")
                        st.info(session["personalized_focus_he"])
                    key_questions = session.get("key_questions_he", [])
                    if key_questions:
                        st.markdown("**שאלות מפתח למפגש:**")
                        for q in key_questions:
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
