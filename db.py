import sqlite3


def get_connection():
    return sqlite3.connect('messages.db')


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_number TEXT,
            user_message TEXT,
            bot_response TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
    conn.commit()
    conn.close()


def save_message(user_number, user_message, bot_response):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO messages (user_number, user_message, bot_response)
            VALUES (?, ?, ?)
        ''', (user_number, user_message, bot_response))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error al guardar el mensaje: {e}")
    finally:
        conn.close()
