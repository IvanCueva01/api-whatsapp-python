from db import get_connection


def user_exists(phone):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT has_started FROM users WHERE phone = ?", (phone,))
    result = cursor.fetchone()
    conn.close()
    return result and result[0] == 1


def mark_user_started(phone):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(''' 
        INSERT INTO users (phone, has_started) VALUES (?, 1)
        ON CONFLICT(phone) DO UPDATE SET has_started = 1
    ''', (phone,))
    conn.commit()
    conn.close()
