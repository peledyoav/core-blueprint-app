import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path

_default_db = Path(__file__).parent.parent / "data" / "clients.db"
DB_PATH = Path(os.getenv("DB_PATH", str(_default_db)))


def get_connection():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            token TEXT UNIQUE NOT NULL,
            created_at TEXT DEFAULT (datetime('now')),
            notes TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS questionnaires (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            part_a TEXT NOT NULL,
            part_b TEXT NOT NULL,
            cv_text TEXT,
            submitted_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            questionnaire_id INTEGER NOT NULL,
            track TEXT,
            spider_data TEXT,
            cv_analysis TEXT,
            insights TEXT,
            recommended_directions TEXT,
            syllabus TEXT,
            generated_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (client_id) REFERENCES clients(id),
            FOREIGN KEY (questionnaire_id) REFERENCES questionnaires(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS drafts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL UNIQUE,
            part_a TEXT,
            part_b TEXT,
            updated_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )
    """)

    conn.commit()
    conn.close()


def add_client(name: str, email: str, token: str, notes: str = "") -> int:
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO clients (name, email, token, notes) VALUES (?, ?, ?, ?)",
        (name, email, token, notes)
    )
    client_id = c.lastrowid
    conn.commit()
    conn.close()
    return client_id


def get_client_by_token(token: str) -> dict | None:
    conn = get_connection()
    c = conn.cursor()
    row = c.execute("SELECT * FROM clients WHERE token = ?", (token,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_client_by_id(client_id: int) -> dict | None:
    conn = get_connection()
    c = conn.cursor()
    row = c.execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_clients() -> list[dict]:
    conn = get_connection()
    c = conn.cursor()
    rows = c.execute("""
        SELECT cl.*, q.submitted_at as questionnaire_submitted, r.generated_at as report_generated
        FROM clients cl
        LEFT JOIN questionnaires q ON q.client_id = cl.id
        LEFT JOIN reports r ON r.client_id = cl.id
        ORDER BY cl.created_at DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_questionnaire(client_id: int, part_a: dict, part_b: dict, cv_text: str = "") -> int:
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO questionnaires (client_id, part_a, part_b, cv_text) VALUES (?, ?, ?, ?)",
        (client_id, json.dumps(part_a, ensure_ascii=False), json.dumps(part_b, ensure_ascii=False), cv_text)
    )
    qid = c.lastrowid
    conn.commit()
    conn.close()
    return qid


def get_questionnaire(client_id: int) -> dict | None:
    conn = get_connection()
    c = conn.cursor()
    row = c.execute(
        "SELECT * FROM questionnaires WHERE client_id = ? ORDER BY submitted_at DESC LIMIT 1",
        (client_id,)
    ).fetchone()
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
            (client_id, questionnaire_id, track, spider_data, cv_analysis, insights, recommended_directions, syllabus)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        client_id,
        questionnaire_id,
        report.get("track"),
        json.dumps(report.get("spider_data", {}), ensure_ascii=False),
        report.get("cv_analysis", ""),
        report.get("insights", ""),
        json.dumps(report.get("recommended_directions", []), ensure_ascii=False),
        json.dumps(report.get("syllabus", []), ensure_ascii=False),
    ))
    rid = c.lastrowid
    conn.commit()
    conn.close()
    return rid


def save_draft(client_id: int, part_a: dict, part_b: dict):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO drafts (client_id, part_a, part_b, updated_at)
        VALUES (?, ?, ?, datetime('now'))
        ON CONFLICT(client_id) DO UPDATE SET
            part_a=excluded.part_a,
            part_b=excluded.part_b,
            updated_at=excluded.updated_at
    """, (client_id, json.dumps(part_a, ensure_ascii=False), json.dumps(part_b, ensure_ascii=False)))
    conn.commit()
    conn.close()


def get_draft(client_id: int) -> dict | None:
    conn = get_connection()
    c = conn.cursor()
    row = c.execute("SELECT * FROM drafts WHERE client_id = ?", (client_id,)).fetchone()
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
    c.execute("DELETE FROM drafts WHERE client_id = ?", (client_id,))
    conn.commit()
    conn.close()


def get_report(client_id: int) -> dict | None:
    conn = get_connection()
    c = conn.cursor()
    row = c.execute(
        "SELECT * FROM reports WHERE client_id = ? ORDER BY generated_at DESC LIMIT 1",
        (client_id,)
    ).fetchone()
    conn.close()
    if not row:
        return None
    result = dict(row)
    result["spider_data"] = json.loads(result["spider_data"])
    result["recommended_directions"] = json.loads(result["recommended_directions"])
    result["syllabus"] = json.loads(result["syllabus"])
    return result
