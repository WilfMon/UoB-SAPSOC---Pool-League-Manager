from .db import get_connection

""" Functions for adding to the databse """
def add_player(name, dest="league.db"):
    conn = get_connection(dest)
    cursor = conn.cursor()
    
    cursor.execute("INSERT OR IGNORE INTO players (name) VALUES (?)", (name,))
    conn.commit()
    conn.close()
    

def add_semester(semester_name, dest="league.db"):
    conn = get_connection(dest)
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT OR IGNORE INTO semester (semester_name) VALUES (?)",
        (semester_name,)
    )
    conn.commit()
    
    semester_id = cursor.lastrowid
    conn.close()
    
    return semester_id
    

def add_session(semester_id, session_date, dest="league.db"):
    conn = get_connection(dest)
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO sessions (semester_id, session_date) VALUES (?, ?)",
        (semester_id, session_date)
    )    
    conn.commit()
    
    session_id = cursor.lastrowid
    conn.close()
    
    return session_id


def add_game(session_id, player1_id, player2_id, winner_id, dest="league.db"):
    conn = get_connection(dest)
    cursor = conn.cursor()

    loser_id = player2_id
    points_to_add = 1
    
    semester_id = get_semester_id_from_session_id(session_id, dest)
    
    winner_points = get_player_points(winner_id, semester_id, dest)
    loser_points = get_player_points(loser_id, semester_id, dest)
    
    if loser_points - winner_points >= 10:
        points_to_add = 1 + loser_points * 0.1
        
    winner_elo_change, loser_elo_change = get_elo_change(
        winner_id, loser_id, dest
    )

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
    """, (
        session_id,
        player1_id,
        player2_id,
        winner_id,
        points_to_add,
        winner_elo_change,
        loser_elo_change
    ))

    cursor.execute("""
        UPDATE players
        SET points = points + ?,
            games_played = games_played + 1,
            wins = wins + 1,
            elo = elo + ?
        WHERE player_id = ?
    """, (points_to_add, winner_elo_change, winner_id))
    
    cursor.execute("""
        UPDATE players
        SET games_played = games_played + 1,
            elo = elo + ?
        WHERE player_id = ?
    """, (loser_elo_change, loser_id))

    cursor.execute("""
        UPDATE sessions
        SET games_played = games_played + 1
        WHERE session_id = ?
    """, (session_id,))

    cursor.execute("""
        UPDATE semester
        SET games_played = games_played + 1
        WHERE semester_id = (
            SELECT semester_id FROM sessions WHERE session_id = ?
        )
    """, (session_id,))

    conn.commit()
    conn.close()


""" Functions for updating existing values in the database """
def make_member(name, dest="league.db"):
    conn = get_connection(dest)
    cursor = conn.cursor()
    
    cursor.execute("UPDATE players SET member = 1 WHERE name = ?", (name,))
    
    if cursor.rowcount == 0:
        print(f"No player found with name: {name}")
    else:
        print(f"{name} is now a member")
        
    conn.commit()
    conn.close()


def remove_member(name, dest="league.db"):
    conn = get_connection(dest)
    cursor = conn.cursor()
    
    cursor.execute("UPDATE players SET member = 0 WHERE name = ?", (name,))
    
    if cursor.rowcount == 0:
        print(f"No player found with name: {name}")
    else:
        print(f"{name} is now not a member")
        
    conn.commit()
    conn.close()
    

""" Functions for retriving data from the database """
def get_player(name, dest="league.db") -> list:
    conn = get_connection(dest)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM players WHERE name = ?", (name,))
    rows = cursor.fetchall()
    
    conn.close()
    return rows


def get_player_games(name, dest="league.db") -> list:
    player_id = get_player_id_from_name(name, dest)

    conn = get_connection(dest)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM games WHERE player1_id = ? OR player2_id = ?",
        (player_id, player_id)
    )

    rows = cursor.fetchall()
    conn.close()
    return rows


def get_player_points(player_id, semester_id, dest="league.db") -> float:
    conn = get_connection(dest)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT COALESCE(SUM(g.points_to_winner), 0)
        FROM games g
        JOIN sessions s   ON g.session_id = s.session_id
        JOIN semester sem ON s.semester_id = sem.semester_id
        WHERE g.winner_id = ?
          AND sem.semester_id = ?
    """, (player_id, semester_id))
    
    result = cursor.fetchone()[0]
    conn.close()
    return result


def get_player_num_games_played(player_id, dest="league.db") -> int:
    conn = get_connection(dest)
    cursor = conn.cursor()
    
    cursor.execute("SELECT games_played FROM players WHERE player_id = ?", (player_id,))
    result = cursor.fetchone()[0]
    
    conn.close()
    return result


def get_player_elo(player_id, dest="league.db") -> float:
    conn = get_connection(dest)
    cursor = conn.cursor()
    
    cursor.execute("SELECT elo FROM players WHERE player_id = ?", (player_id,))
    result = cursor.fetchone()[0]
    
    conn.close()
    return result


def get_members(dest="league.db") -> list[str]:
    conn = get_connection(dest)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM players WHERE member = ?", (1,))
    rows = cursor.fetchall()
    
    conn.close()
    return [row[0] for row in rows]


def get_all_players_name(dest="league.db") -> list[str]:
    conn = get_connection(dest)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM players")
    rows = cursor.fetchall()

    conn.close()
    return [row[0] for row in rows]


def get_all_players_id(dest="league.db") -> list[int]:
    conn = get_connection(dest)
    cursor = conn.cursor()

    cursor.execute("SELECT player_id FROM players")
    rows = cursor.fetchall()

    conn.close()
    return [row[0] for row in rows]
    

def get_elo_change(winner_id, loser_id, dest="league.db") -> tuple[float, float]:
    from utils.utils import calc_elo_change
    
    if winner_id is None:
        winner_elo = 1000.0
        winner_games_played = 0
    else:
        winner_elo = get_player_elo(winner_id, dest)
        winner_games_played = get_player_num_games_played(winner_id, dest)
    
    if loser_id is None:
        loser_elo = 1000.0
        loser_games_played = 0
    else:
        loser_elo = get_player_elo(loser_id, dest)
        loser_games_played = get_player_num_games_played(loser_id, dest)
    
    return calc_elo_change(
        winner_elo,
        loser_elo,
        winner_games_played,
        loser_games_played
    )
    

# Functions to get ids
def get_semester_id_from_name(semester_name, dest="league.db") -> int:
    conn = get_connection(dest)
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT semester_id FROM semester WHERE semester_name = ?",
        (semester_name,)
    )
    result = cursor.fetchone()
    
    conn.close()
    return result[0]


def get_semester_id_from_session_id(session_id, dest="league.db") -> int:
    conn = get_connection(dest)
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT semester_id FROM sessions WHERE session_id = ?",
        (session_id,)
    )
    result = cursor.fetchone()
    
    conn.close()
    return result[0]


def get_session_id_from_name(session_name, dest="league.db") -> int:
    conn = get_connection(dest)
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT session_id FROM session WHERE session_name = ?",
        (session_name,)
    )
    result = cursor.fetchone()
    
    conn.close()
    return result[0]
    

def get_player_id_from_name(player_name, dest="league.db") -> int:
    conn = get_connection(dest)
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT player_id FROM players WHERE name = ?",
        (player_name,)
    )
    result = cursor.fetchone()
    
    conn.close()
    
    if result is None:
        return None
    
    return result[0]