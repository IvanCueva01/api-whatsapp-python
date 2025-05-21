import sqlite3
from db import get_connection


def upsert_session(user_id, stage=None):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO sessions (user_id, stage, updated_at) 
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id) DO UPDATE SET stage = excluded.stage, updated_at = CURRENT_TIMESTAMP
    ''', (user_id, stage))
    conn.commit()
    conn.close()


def get_session_stage(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT stage FROM sessions WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None


def save_message(user_id, role, content):
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO messages (user_id, role, content)
            VALUES (?, ?, ?)
        ''', (user_id, role, content))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"Error al guardar el mensaje: {e}")


def get_recent_messages(user_id, limit=6):
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute('''
            SELECT role, content FROM messages 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (user_id, limit))
        rows = c.fetchall()
        conn.close()
        return [{"role": r, "content": c} for r, c in reversed(rows)]
    except sqlite3.Error as e:
        print(f"Error al obtener los mensajes: {e}")
        return []
