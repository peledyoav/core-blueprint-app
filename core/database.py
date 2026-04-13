import psycopg2
import psycopg2.extras
import json
import os

def _get_db_url():
    try:
        import streamlit as st
        return st.secrets.get("DATABASE_URL") or os.getenv("DATABASE_URL")
    except Exception:
        return os.getenv("DATABASE_URL")


def get_connection():
    conn = psycopg2.connect(_get_db_url())
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            token TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT NOW(),
            notes TEXT DEFAULT ''
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS questionnaires (
            id SERIAL PRIMARY KEY,
            client_id INTEGER NOT NULL REFERENCES clients(id),
            part_a TEXT NOT NULL,
            part_b TEXT NOT NULL,
            cv_text TEXT DEFAULT '',
            submitted_at TIMESTAMP DEFAULT NOW()
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id SERIAL PRIMARY KEY,
            client_id INTEGER NOT NULL REFERENCES clients(id),
            questionnaire_id INTEGER NOT NULL REFERENCES questionnaires(id),
            track TEXT,
            spider_data TEXT,
            cv_analysis TEXT,
            insights TEXT,
            recommended_directions TEXT,
            syllabus TEXT,
            report_data TEXT DEFAULT '',
            generated_at TIMESTAMP DEFAULT NOW()
        )
    """)
    # Add report_data column to existing tables if missing
    c.execute("""
        ALTER TABLE reports ADD COLUMN IF NOT EXISTS report_data TEXT DEFAULT ''
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS drafts (
            id SERIAL PRIMARY KEY,
            client_id INTEGER NOT NULL UNIQUE REFERENCES clients(id),
            part_a TEXT,
            part_b TEXT,
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)

    conn.commit()
    c.close()
    conn.close()


def _dictrow(row):
    return dict(row) if row else None


def update_client(client_id: int, name: str, email: str, notes: str = ""):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "UPDATE clients SET name=%s, email=%s, notes=%s WHERE id=%s",
        (name, email, notes, client_id)
    )
    conn.commit()
    c.close()
    conn.close()


def delete_client(client_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM drafts WHERE client_id=%s", (client_id,))
    c.execute("DELETE FROM reports WHERE client_id=%s", (client_id,))
    c.execute("DELETE FROM questionnaires WHERE client_id=%s", (client_id,))
    c.execute("DELETE FROM clients WHERE id=%s", (client_id,))
    conn.commit()
    c.close()
    conn.close()


def add_client(name: str, email: str, token: str, notes: str = "") -> int:
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO clients (name, email, token, notes) VALUES (%s, %s, %s, %s) RETURNING id",
        (name, email, token, notes)
    )
    client_id = c.fetchone()[0]
    conn.commit()
    c.close()
    conn.close()
    return client_id


def get_client_by_token(token: str) -> dict | None:
    conn = get_connection()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    c.execute("SELECT * FROM clients WHERE token = %s", (token,))
    row = c.fetchone()
    c.close()
    conn.close()
    return _dictrow(row)


def get_client_by_id(client_id: int) -> dict | None:
    conn = get_connection()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    c.execute("SELECT * FROM clients WHERE id = %s", (client_id,))
    row = c.fetchone()
    c.close()
    conn.close()
    return _dictrow(row)


def get_all_clients() -> list[dict]:
    conn = get_connection()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    c.execute("""
        SELECT cl.*, q.submitted_at as questionnaire_submitted, r.generated_at as report_generated
        FROM clients cl
        LEFT JOIN questionnaires q ON q.client_id = cl.id
        LEFT JOIN reports r ON r.client_id = cl.id
        ORDER BY cl.created_at DESC
    """)
    rows = c.fetchall()
    c.close()
    conn.close()
    return [dict(r) for r in rows]


def save_questionnaire(client_id: int, part_a: dict, part_b: dict, cv_text: str = "") -> int:
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO questionnaires (client_id, part_a, part_b, cv_text) VALUES (%s, %s, %s, %s) RETURNING id",
        (client_id, json.dumps(part_a, ensure_ascii=False), json.dumps(part_b, ensure_ascii=False), cv_text)
    )
    qid = c.fetchone()[0]
    conn.commit()
    c.close()
    conn.close()
    return qid


def get_questionnaire(client_id: int) -> dict | None:
    conn = get_connection()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    c.execute(
        "SELECT * FROM questionnaires WHERE client_id = %s ORDER BY submitted_at DESC LIMIT 1",
        (client_id,)
    )
    row = c.fetchone()
    c.close()
    conn.close()
    if not row:
        return None
    result = dict(row)
    result["part_a"] = json.loads(result["part_a"])
    result["part_b"] = json.loads(result["part_b"])
    return result


def save_report(client_id: int, questionnaire_id: int, report: dict) -> int:
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO reports
            (client_id, questionnaire_id, track, spider_data, cv_analysis, insights,
             recommended_directions, syllabus, report_data)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
    """, (
        client_id,
        questionnaire_id,
        report.get("track"),
        json.dumps(report.get("spider_data", {}), ensure_ascii=False),
        report.get("cv_analysis", ""),
        json.dumps(report.get("insights", []), ensure_ascii=False),
        json.dumps(report.get("recommended_directions", []), ensure_ascii=False),
        json.dumps(report.get("syllabus", []), ensure_ascii=False),
        json.dumps(report, ensure_ascii=False),
    ))
    rid = c.fetchone()[0]
    conn.commit()
    c.close()
    conn.close()
    return rid


def save_draft(client_id: int, part_a: dict, part_b: dict):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO drafts (client_id, part_a, part_b, updated_at)
        VALUES (%s, %s, %s, NOW())
        ON CONFLICT (client_id) DO UPDATE SET
            part_a = EXCLUDED.part_a,
            part_b = EXCLUDED.part_b,
            updated_at = EXCLUDED.updated_at
    """, (client_id, json.dumps(part_a, ensure_ascii=False), json.dumps(part_b, ensure_ascii=False)))
    conn.commit()
    c.close()
    conn.close()


def get_draft(client_id: int) -> dict | None:
    conn = get_connection()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    c.execute("SELECT * FROM drafts WHERE client_id = %s", (client_id,))
    row = c.fetchone()
    c.close()
    conn.close()
    if not row:
        return None
    result = dict(row)
    result["part_a"] = json.loads(result["part_a"]) if result["part_a"] else {}
    result["part_b"] = json.loads(result["part_b"]) if result["part_b"] else {}
    return result


def delete_draft(client_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM drafts WHERE client_id = %s", (client_id,))
    conn.commit()
    c.close()
    conn.close()


def get_report(client_id: int) -> dict | None:
    conn = get_connection()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    c.execute(
        "SELECT * FROM reports WHERE client_id = %s ORDER BY generated_at DESC LIMIT 1",
        (client_id,)
    )
    row = c.fetchone()
    c.close()
    conn.close()
    if not row:
        return None
    result = dict(row)
    # If full report_data is stored, use it (includes all fields)
    if result.get("report_data"):
        return json.loads(result["report_data"])
    # Fallback for old records
    def safe_json(val, default):
        if not val:
            return default
        try:
            return json.loads(val)
        except Exception:
            return default
    result["spider_data"] = safe_json(result.get("spider_data"), {})
    result["recommended_directions"] = safe_json(result.get("recommended_directions"), [])
    result["syllabus"] = safe_json(result.get("syllabus"), [])
    result["insights"] = safe_json(result.get("insights"), [])
    return result
