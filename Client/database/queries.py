from database.db import get_connection


# Functions for players table
def add_player(name):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("INSERT OR IGNORE INTO players (name) VALUES (?)", (name,))
    conn.commit()
    conn.close()
    
def make_member(name):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE players SET member = 1 WHERE name = ?",(name,))
    
    if cursor.rowcount == 0:
        print(f"No player found with name: {name}")
    else:
        print(f"{name} is now a member")
        
    conn.commit()
    conn.close()

def remove_member(name):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE players SET member = 0 WHERE name = ?",(name,))
    
    if cursor.rowcount == 0:
        print(f"No player found with name: {name}")
    else:
        print(f"{name} is now not a member")
        
    conn.commit()
    conn.close()
    
def get_player(name):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM players WHERE name = ?", (name,))
    rows = cursor.fetchall()
    
    return rows

def get_player_games(name):
    id_ = get_player_id_by_name(name)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM games WHERE player1_id = ? OR player2_id = ?", (id_, id_))

    return cursor.fetchall()

def get_members():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM players WHERE member = ?", (1,))
    rows = cursor.fetchall()
    
    names = [row[0] for row in rows]
    return names

def get_all_players():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM players")
    rows = cursor.fetchall()

    names = [row[0] for row in rows]
    return names


# Functions to add objects to table
def add_semester(semester_name):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("INSERT OR IGNORE INTO semester (semester_name) VALUES (?)", (semester_name,))
    conn.commit()
    
    semester_id = cursor.lastrowid
    conn.close()
    
    return semester_id
    
def add_session(semester_id, session_date):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO sessions (semester_id, session_date) VALUES (?, ?)",
        (semester_id, session_date)
    )    
    conn.commit()
    
    session_id = cursor.lastrowid
    conn.close()
    
    return session_id
    
def add_game(session_id, player1_id, player2_id, winner_id):
    conn = get_connection()
    cursor = conn.cursor()

    # Insert the game
    cursor.execute("""
        INSERT INTO games (session_id, player1_id, player2_id, winner_id, points_to_winner)
        VALUES (?, ?, ?, ?, ?)
    """, (session_id, player1_id, player2_id, winner_id, 1))

    # Increment winner's points and wins
    cursor.execute("""
        UPDATE players
        SET points = points + 1,
            games_played = games_played + 1
        WHERE player_id = ?
    """, (winner_id,))
    
    cursor.execute("""
        UPDATE players
        SET wins = wins + 1
        WHERE player_id = ?
    """, (winner_id,))
    
    # increment games played of loser aswell
    cursor.execute("""
        UPDATE players
        SET games_played = games_played + 1
        WHERE player_id = ?
    """, (player2_id,))

    # Update the number of games in the session
    cursor.execute("""
        UPDATE sessions
        SET games_played = games_played + 1
        WHERE session_id = ?
    """, (session_id,))

    # Update the number of games in the semester
    cursor.execute("""
        UPDATE semester
        SET games_played = games_played + 1
        WHERE semester_id = (
            SELECT semester_id FROM sessions WHERE session_id = ?
        )
    """, (session_id,))

    conn.commit()
    conn.close()
    
    
# Functions to get ids
def get_semester_id_by_name(semester_name):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT semester_id FROM semester WHERE semester_name = ?", (semester_name,))
    result = cursor.fetchone()
    
    conn.close()
    
    return result[0]

def get_session_id_by_name(session_name):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT session_id FROM session WHERE session_name = ?", (session_name,))
    result = cursor.fetchone()
    
    conn.close()
    
    return result[0]
    
def get_player_id_by_name(player_name):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT player_id FROM players WHERE name = ?", (player_name,))
    result = cursor.fetchone()
    
    conn.close()
    
    return result[0]  # the player's id