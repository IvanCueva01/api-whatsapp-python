from db import get_connection


def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            role TEXT, -- 'user' or 'assistant'
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            user_id TEXT PRIMARY KEY,
            stage TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_activity (
            user_id TEXT PRIMARY KEY,
            last_active_timestamp INTEGER,
            last_follow_up_timestamp INTEGER,
            follow_up_stage INTEGER DEFAULT 0,  -- 0: none, 1: first sent, 2: second sent, 3: third sent/max
            meeting_booked_status INTEGER DEFAULT 0, -- 0: No, 1: Yes
            pending_booking_confirmation INTEGER DEFAULT 0 -- 0: No, 1: Yes, expecting user to confirm if they booked
        )
    ''')
    conn.commit()
    conn.close()


if __name__ == '__main__':
    init_db()
    print('Database initialized.')
