"""
db.py — Data access layer for the Pool League Manager.

All database interaction should go through this module rather than
writing raw SQL scattered through the GUI code. Keeps schema details
in one place and makes future changes (e.g. tweaking Elo K-factor,
adding columns) low-risk.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.utils import calc_elo_change

DB_PATH = Path(__file__).parent / "league.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"

# Points awarded to the winner of a match, added to their running total
# for that semester (semesters_players.points). Bump this if you want
# wins to be worth more than 1 point.
POINTS_PER_WIN = 1

# ---------------------------------------------------------------
# Make sure the database exists and is initialized with schema.sql
# ---------------------------------------------------------------

def init_db(schema_path: Path = SCHEMA_PATH, db_path: Path = DB_PATH):
    """Creates tables, triggers, and views from schema.sql if the database is missing."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found at {schema_path.resolve()}")

    with get_connection(db_path) as conn:
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_script = f.read()
        conn.executescript(schema_script)
    print(f"Database successfully initialized at {db_path.resolve()}")

# ---------------------------------------------------------------
# Helpers for getting a connection and wrapping transactions
# ---------------------------------------------------------------

def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row       # lets you do row["player_id"] instead of row[0]
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def transaction(conn: sqlite3.Connection):
    """Wrap a block of writes in a single commit/rollback so a match record + its two Elo history rows either all succeed or all fail."""
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


# ---------------------------------------------------------------
# Players
# ---------------------------------------------------------------

def add_player(conn, first_name, last_name, is_member=0, starting_elo=1000):
    """Add a new player to the database and return their player_id."""
    with transaction(conn):
        cur = conn.execute(
            "SELECT player_id FROM players WHERE first_name = ? AND last_name = ?", 
            (first_name, last_name)
        )
        row = cur.fetchone()
        
        if row:
            return row["player_id"] if isinstance(row, dict) else row[0]
        
        cur = conn.execute(
            """INSERT INTO players (first_name, last_name, is_member, base_elo, current_elo)
               VALUES (?, ?, ?, ?, ?)""",
            (first_name, last_name, is_member, starting_elo, starting_elo),
        )
        return cur.lastrowid

def get_player(conn, player_id):
    """Fetch a player's record by player_id. Returns a dict or None if not found."""
    row = conn.execute("SELECT * FROM players WHERE player_id = ?", (player_id,)).fetchone()
    return dict(row) if row else None

def list_all_players(conn) -> list[tuple[str, str]]:
    """Return a list of all players, sorted by current Elo descending."""
    rows = conn.execute(
        "SELECT * FROM players ORDER BY current_elo DESC"
    ).fetchall()
    return [dict(r) for r in rows]

def get_pid_from_name(conn, first_name, last_name):
    """Returns the player id of the named player"""
    row = conn.execute("SELECT player_id FROM players WHERE first_name = ? AND last_name = ?", (first_name, last_name)).fetchone()
    return row[0] if row else None

def get_name_from_pid(conn, player_id) -> tuple[str, str]:
    """Returns the first and second name of the player"""
    row = conn.execute("SELECT first_name, last_name FROM players WHERE player_id = ?", (player_id,)).fetchone()
    return (row[0], row[1]) if row else None

def list_active_players(conn):
    """Return a list of all active players, sorted by current Elo descending."""
    rows = conn.execute(
        "SELECT * FROM players WHERE is_active = 1 ORDER BY current_elo DESC"
    ).fetchall()
    return [dict(r) for r in rows]

def is_player_active(conn, player_id) -> bool:
    """Returns True if the player is active"""
    row = conn.execute("SELECT is_active FROM players WHERE player_id = ?", (player_id,)).fetchone()
    return row[0] if row else None

def update_player_active(conn, player_id, active: bool = 1):
    """Update a players active status in the database"""
    with transaction(conn):
        
        conn.execute(f"UPDATE players SET is_active = ? WHERE player_id = ?", (active, player_id))


# ---------------------------------------------------------------
# Semesters
# ---------------------------------------------------------------

def create_semester(conn, name, start_date, player_ids=None):
    """
    Create a semester and optionally seed semesters_players with each player's current Elo as their starting point for the semester (points start at 0).
    If semester with the same name already exists then don't add a new one, return the id of that semester
    """
    with transaction(conn):
        # 1. Check if a semester with this name already exists
        cur = conn.execute(
            "SELECT semester_id FROM semesters WHERE name = ?", 
            (name,)
        )
        row = cur.fetchone()
        
        if row:
            # Return existing semester ID without re-inserting or re-seeding players
            return row["semester_id"] if isinstance(row, dict) else row[0]

        # 2. Insert new semester if it does not exist
        cur = conn.execute(
            "INSERT INTO semesters (name, start_date) VALUES (?, ?)",
            (name, start_date),
        )
        semester_id = cur.lastrowid

        # 3. Seed initial player states
        if player_ids:
            for pid in player_ids:
                player = get_player(conn, pid)
                conn.execute(
                    """INSERT INTO semesters_players (semester_id, player_id, starting_elo, points)
                       VALUES (?, ?, ?, 0)""",
                    (semester_id, pid, player["current_elo"]),
                )

        return semester_id


def add_player_to_semester(conn, semester_id, player_id):
    """Seed a single player into an already-created semester (e.g. someone who joins partway
    through), using their current Elo as their starting point. No-ops if they're already in it,
    so it's safe to call defensively before crediting points."""
    with transaction(conn):
        player = get_player(conn, player_id)
        conn.execute(
            """INSERT OR IGNORE INTO semesters_players (semester_id, player_id, starting_elo, points)
               VALUES (?, ?, ?, 0)""",
            (semester_id, player_id, player["current_elo"]),
        )


def get_semester_id_for_round(conn, round_id):
    """Look up which semester a round belongs to, via its session."""
    row = conn.execute(
        """SELECT s.semester_id
           FROM rounds r
           JOIN sessions s ON r.session_id = s.session_id
           WHERE r.round_id = ?""",
        (round_id,),
    ).fetchone()
    return row[0] if row else None


def _award_semester_point(conn, semester_id, player_id, points=POINTS_PER_WIN):
    """Add points to a player's semester total, seeding their semesters_players row first
    if they somehow aren't in it yet (e.g. joined the semester late)."""
    add_player_to_semester(conn, semester_id, player_id)
    conn.execute(
        """UPDATE semesters_players
           SET points = points + ?
           WHERE semester_id = ? AND player_id = ?""",
        (points, semester_id, player_id),
    )


# ---------------------------------------------------------------
# Sessions / attendance / rounds
# ---------------------------------------------------------------

def create_session(conn, semester_id, session_date, attendee_ids):
    """Create a session and record attendance for each player in attendee_ids."""
    with transaction(conn):
        # check if session already exists
        cur = conn.execute(
            "SELECT session_id FROM sessions WHERE session_date = ?", 
            (session_date,)
        )
        row = cur.fetchone()
        
        if row:
            return row["session_id"] if isinstance(row, dict) else row[0]
        
        cur = conn.execute(
            "INSERT INTO sessions (semester_id, session_date) VALUES (?, ?)",
            (semester_id, session_date),
        )
        session_id = cur.lastrowid
        conn.executemany(
            "INSERT INTO session_attendance (session_id, player_id) VALUES (?, ?)",
            [(session_id, pid) for pid in attendee_ids],
        )
        return session_id
    
def add_session_attendance(conn, session_id, player_id):
    """Add a single player's attendance to an existing session."""
    with transaction(conn):
        conn.execute(
            "INSERT INTO session_attendance (session_id, player_id) VALUES (?, ?)",
            (session_id, player_id),
        )


def create_round(conn, session_id, round_number):
    """Create a round within a session."""
    with transaction(conn):
        cur = conn.execute(
            "INSERT INTO rounds (session_id, round_number) VALUES (?, ?)",
            (session_id, round_number),
        )
        return cur.lastrowid


# ---------------------------------------------------------------
# Matches — the core "live update" operation
# ---------------------------------------------------------------

def record_match(
    conn,
    round_id,
    player1_id,
    player2_id,
    winner_id=None,
    override_p1_elo=None,
    override_p2_elo=None,
):
    """
    Record a match result and update both players' Elo live.\n
    Also credits the winner with POINTS_PER_WIN semester points (byes and
    undecided matches award none).\n
    Supports override_p1_elo/override_p2_elo for recalculating historic chains.
    """
    with transaction(conn):
        p1 = get_player(conn, player1_id)
        p1_elo = override_p1_elo if override_p1_elo is not None else p1["current_elo"]
        
        # Update the semester standings with points first
        if winner_id is not None:
            semester_id = get_semester_id_for_round(conn, round_id)
            if semester_id is not None:
                _award_semester_point(conn, semester_id, winner_id)
                
        if player2_id is None:
            conn.execute(
                """INSERT INTO matches
                       (round_id, player1_id, player2_id, winner_id,
                        player1_elo_before, player1_elo_after)
                   VALUES (?, ?, NULL, NULL, ?, ?)""",
                (round_id, player1_id, p1_elo, p1_elo),
            )
            return None

        p2 = get_player(conn, player2_id)
        p2_elo = override_p2_elo if override_p2_elo is not None else p2["current_elo"]
        
        if winner_id == player1_id:
            chg1, chg2 = calc_elo_change(p1_elo, p2_elo)
        if winner_id == player2_id:
            chg2, chg1 = calc_elo_change(p2_elo, p1_elo)
            
        new1 = p1_elo + chg1
        new2 = p2_elo + chg2

        cur = conn.execute(
            """INSERT INTO matches
                   (round_id, player1_id, player2_id, winner_id,
                    player1_elo_before, player2_elo_before,
                    player1_elo_after, player2_elo_after)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                round_id,
                player1_id,
                player2_id,
                winner_id,
                p1_elo,
                p2_elo,
                new1,
                new2,
            ),
        )
        match_id = cur.lastrowid

        # Trigger trg_sync_player_elo will sync current_elo automatically
        conn.execute(
            """INSERT INTO elo_history (player_id, match_id, elo_before, elo_after, elo_change)
               VALUES (?, ?, ?, ?, ?)""",
            (player1_id, match_id, p1_elo, new1, new1 - p1_elo),
        )
        conn.execute(
            """INSERT INTO elo_history (player_id, match_id, elo_before, elo_after, elo_change)
               VALUES (?, ?, ?, ?, ?)""",
            (player2_id, match_id, p2_elo, new2, new2 - p2_elo),
        )

        return match_id
    
def recalculate_all_elo(conn):
    """Wipes all Elo history and semester points and recalculates every match in the
    system chronologically starting from base_elo / 0 points."""
    with transaction(conn):
        # 1. Reset all players to their base_elo
        conn.execute("UPDATE players SET current_elo = base_elo")
        
        # 2. Clear out elo_history
        conn.execute("DELETE FROM elo_history")

        # 2b. Reset semester points — they'll be rebuilt as matches are replayed below
        conn.execute("UPDATE semesters_players SET points = 0")

        # 3. Fetch all matches ordered strictly by match_id, along with which
        #    semester each one belongs to (needed to credit points correctly)
        matches = conn.execute(
            """
            SELECT m.match_id, m.round_id, m.player1_id, m.player2_id, m.winner_id,
                   s.semester_id
            FROM matches m
            JOIN rounds r ON m.round_id = r.round_id
            JOIN sessions s ON r.session_id = s.session_id
            ORDER BY m.match_id ASC
            """
        ).fetchall() # made it only sort by match_id as a bugfix

        # 4. In-memory rating tracker seeded with base_elo
        players = conn.execute("SELECT player_id, base_elo FROM players").fetchall()
        elo_map = {p["player_id"]: p["base_elo"] for p in players}

        # 5. Replay matches and update database
        for m in matches:
            p1_id = m["player1_id"]
            p2_id = m["player2_id"]
            winner_id = m["winner_id"]
            match_id = m["match_id"]
            semester_id = m["semester_id"]

            p1_before = elo_map[p1_id]

            if p2_id is None:
                # Bye match — no Elo change, no points
                conn.execute(
                    """UPDATE matches 
                       SET player1_elo_before = ?, player1_elo_after = ?
                       WHERE match_id = ?""",
                    (p1_before, p1_before, match_id),
                )
                continue

            p2_before = elo_map[p2_id]
            
            if winner_id == p1_id:
                chg1, chg2 = calc_elo_change(p1_before, p2_before)
            if winner_id == p2_id:
                chg2, chg1 = calc_elo_change(p2_before, p1_before)
                
            new1 = p1_before + chg1
            new2 = p2_before + chg2

            # Update match record with recalculated values
            conn.execute(
                """UPDATE matches 
                   SET player1_elo_before = ?, player2_elo_before = ?,
                       player1_elo_after = ?, player2_elo_after = ?
                   WHERE match_id = ?""",
                (p1_before, p2_before, new1, new2, match_id),
            )

            # Re-insert history rows (fires trigger to update players.current_elo)
            conn.execute(
                """INSERT INTO elo_history (player_id, match_id, elo_before, elo_after, elo_change)
                   VALUES (?, ?, ?, ?, ?)""",
                (p1_id, match_id, p1_before, new1, new1 - p1_before),
            )
            conn.execute(
                """INSERT INTO elo_history (player_id, match_id, elo_before, elo_after, elo_change)
                   VALUES (?, ?, ?, ?, ?)""",
                (p2_id, match_id, p2_before, new2, new2 - p2_before),
            )

            # Re-credit the semester point for this win
            if winner_id is not None and semester_id is not None:
                _award_semester_point(conn, semester_id, winner_id)

            # Update working ratings
            elo_map[p1_id] = new1
            elo_map[p2_id] = new2


def edit_match_winner(conn, match_id, new_winner_id):
    """Edits a match winner and triggers a full system-wide Elo + points recalculation."""
    with transaction(conn):
        conn.execute(
            "UPDATE matches SET winner_id = ? WHERE match_id = ?",
            (new_winner_id, match_id),
        )
        recalculate_all_elo(conn)


def delete_match(conn, match_id):
    """Deletes a match and triggers a full system-wide Elo + points recalculation."""
    with transaction(conn):
        conn.execute("DELETE FROM matches WHERE match_id = ?", (match_id,))
        recalculate_all_elo(conn)


def get_match_id(conn, p1_id, p2_id, round_id):
    """Returns the match_id of the match played by these two players in this round"""
    with transaction(conn):
        row = conn.execute(
            "SELECT match_id FROM matches WHERE player1_id = ? AND player2_id = ? AND round_id = ?", 
            (p1_id, p2_id, round_id)
        ).fetchone()
        
    return row[0] if row else None


# ---------------------------------------------------------------
# Standings / reporting
# ---------------------------------------------------------------

def get_semester_standings(conn, semester_id):
    """Return a list of players and their stats for a given semester, ordered by points, wins, and current Elo."""
    rows = conn.execute(
        """SELECT * FROM v_semester_standings
           WHERE semester_id = ?
           ORDER BY points DESC, wins DESC, current_elo DESC""",
        (semester_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def get_player_elo_timeline(conn, player_id):
    """Return a list of Elo history records for a given player, ordered by date."""
    rows = conn.execute(
        "SELECT * FROM v_player_elo_timeline WHERE player_id = ? ORDER BY recorded_at",
        (player_id,),
    ).fetchall()
    return [dict(r) for r in rows]

if __name__ == "__main__":
    # Running 'python db.py' directly will initialize the database
    init_db()