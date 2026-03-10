from database.db import get_connection

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS players (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        member BOOLEAN NOT NULL DEFAULT 0,
        points FLOAT NOT NULL DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()