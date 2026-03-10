from database.db import get_connection

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    PRAGMA foreign_keys = ON
    """)

    # table of players at the club
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS players (
        player_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        member BOOLEAN NOT NULL DEFAULT 0,
        
        points FLOAT NOT NULL DEFAULT 0,
        games_played INTEGER NOT NULL DEFAULT 0
    )
    """)

    # table of semesters
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS semester (
    semester_id INTEGER PRIMARY KEY AUTOINCREMENT,
    semester_name TEXT UNIQUE NOT NULL,
    
    games_played INTEGER NOT NULL DEFAULT 0
    
    )
    """)
    
    # table of sessions
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    semester_id INTEGER NOT NULL,
    session_date TEXT NOT NULL,
    
    games_played INTEGER NOT NULL DEFAULT 0,
    
    FOREIGN KEY(semester_id) REFERENCES semester(semester_id)
    )
    """)
    
    # table of games
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS games (
    games_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,

    player1_id INTEGER NOT NULL,
    player2_id INTEGER NOT NULL,

    winner_id INTEGER NOT NULL,

    FOREIGN KEY(session_id) REFERENCES sessions(session_id),
    FOREIGN KEY(player1_id) REFERENCES players(player_id),
    FOREIGN KEY(player2_id) REFERENCES players(player_id),
    FOREIGN KEY(winner_id) REFERENCES players(player_id)
    )
    """)

    conn.commit()
    conn.close()