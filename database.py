import sqlite3


DB_NAME = "notes_app.db"


def create_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def create_note(title: str, content: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO notes (title, content) VALUES (?, ?)", (title, content))
    conn.commit()
    note_id = cursor.lastrowid
    cursor.execute("SELECT id, title, content, created_at FROM notes WHERE id = ?", (note_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def create_user(username: str, password: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        user_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        conn.close()
        return None
    conn.close()
    return user_id

def get_user(username: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_notes():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, content, created_at FROM notes ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_note(note_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, content, created_at FROM notes WHERE id = ?", (note_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def update_note(note_id: int, title: str, content: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE notes SET title = ?, content = ? WHERE id = ?", (title, content, note_id))
    conn.commit()
    cursor.execute("SELECT id, title, content, created_at FROM notes WHERE id = ?", (note_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def delete_note(note_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    conn.commit()
    deleted = cursor.rowcount
    conn.close()
    return deleted

if __name__ == "__main__":
    create_database()
    print("Database and table created successfully.")