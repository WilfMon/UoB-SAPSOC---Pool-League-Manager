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
    """
    Get all infomation about a player from name
    """

    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM players WHERE name = ?", (name,))
    rows = cursor.fetchall()
    
    return rows

def get_player_games(name):
    player_id = get_player_id_by_name(name)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM games WHERE player1_id = ? OR player2_id = ?", (player_id, player_id))

    return cursor.fetchall()

def get_player_points(player_id, semester_id):
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT COALESCE(SUM(g.points_to_winner), 0)
        FROM games g
        JOIN sessions s   ON g.session_id = s.session_id
        JOIN semester sem ON s.semester_id = sem.semester_id
        WHERE g.winner_id = ?
          AND sem.semester_id = ?
    """, (player_id, semester_id))
    
    return cursor.fetchone()[0]

def get_player_num_games_played(player_id):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT games_played FROM players WHERE player_id = ?", (player_id,))
    
    return cursor.fetchone()[0]

def get_player_elo(player_id):
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT elo FROM players WHERE player_id = ?
    """, (player_id,))
    
    return cursor.fetchone()[0]

def get_members():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM players WHERE member = ?", (1,))
    rows = cursor.fetchall()
    
    names = [row[0] for row in rows]
    return names

def get_all_players_name():
    """
    Get all the players names
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM players")
    rows = cursor.fetchall()

    names = [row[0] for row in rows]
    return names

def get_all_players_id():
    """
    Get all the players ids
    """
    
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT player_id FROM players")
    rows = cursor.fetchall()

    ids = [row[0] for row in rows]
    return ids

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
    
def get_elo_change(winner_id, loser_id):
    from utils.utils import calc_elo_change
    
    # for new players
    if winner_id == None:
        winner_elo = 1000.0
        winner_games_played = 0
    else:
        winner_elo = get_player_elo(winner_id)
        winner_games_played = get_player_num_games_played(winner_id)
    
    if loser_id == None:
        loser_elo = 1000.0
        loser_games_played = 0
    else:
        loser_elo = get_player_elo(loser_id)
        loser_games_played = get_player_num_games_played(loser_id)
    
    return calc_elo_change(winner_elo, loser_elo, winner_games_played, loser_games_played)
    
def add_game(session_id, player1_id, player2_id, winner_id):
    
    conn = get_connection()
    cursor = conn.cursor()

    # figure out points to add onto winner
    loser_id = player2_id
    
    points_to_add = 1
    
    semster_id = get_semester_id_from_session_id(session_id)
    
    winner_points = get_player_points(winner_id, semster_id)
    loser_points = get_player_points(loser_id, semster_id)
    
    if loser_points - winner_points >= 10: # check if winner was 10 or more points behind loser
        points_to_add = 1 + loser_points * 0.1 # add 10% of losers points onto winners take
        
    # figure out elo updates
    winner_elo_change, loser_elo_change = get_elo_change(winner_id, loser_id)

    # Insert the game
    cursor.execute("""
        INSERT INTO games (
            session_id, 
            player1_id, 
            player2_id, 
            winner_id, 
            points_to_winner,
            elo_to_winner,
            elo_to_loser
            )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (session_id, player1_id, player2_id, winner_id, points_to_add, winner_elo_change, loser_elo_change))

    # Increment winner's points, wins and elo
    cursor.execute("""
        UPDATE players
        SET points = points + ?,
            games_played = games_played + 1,
            wins = wins + 1,
            elo = elo + ?
        WHERE player_id = ?
    """, (points_to_add, winner_elo_change, winner_id))
    
    # increment games played of loser and elo aswell
    cursor.execute("""
        UPDATE players
        SET games_played = games_played + 1, elo = elo + ?
        WHERE player_id = ?
    """, (loser_elo_change, loser_id))

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

def get_semester_id_from_session_id(session_id):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT semester_id FROM sessions WHERE session_id = ?;", (session_id,))
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
    
    if result == None:
        return None
    
    return result[0]  # the player's id