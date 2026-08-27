"""
db.py — Data access layer for the Pool League Manager.

All database interaction should go through this module rather than
writing raw SQL scattered through the GUI code.
"""

import apsw
import apsw.ext

from contextlib import contextmanager
from pathlib import Path
from collections.abc import Callable

import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.utils import calc_elo_change


DB_PATH = Path(__file__).parent / "league.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"

POINTS_PER_WIN = 1

ACTIONS = {
        apsw.SQLITE_INSERT: "INSERT",
        apsw.SQLITE_UPDATE: "UPDATE",
        apsw.SQLITE_DELETE: "DELETE",
    }

# ---------------------------------------------------------------
# Database / connection
# ---------------------------------------------------------------

def init_db(schema_path: Path = SCHEMA_PATH, db_path: Path = DB_PATH):
    """Creates tables, triggers, and views from schema.sql if the database is missing."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found at {schema_path.resolve()}")

    with get_connection(db_path) as conn:
        with open(schema_path, "r", encoding="utf-8") as f:
            conn.execute(f.read())

    print(f"Database successfully initialized at {db_path.resolve()}")
    
    
def listen(conn, callback: Callable):
    """Register the database update hook on an existing connection."""
    conn.setupdatehook(callback)


def get_connection(db_path: Path = DB_PATH) -> apsw.Connection:
    conn = apsw.Connection(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def transaction(conn):
    """Wrap a block of writes in a transaction."""
    already_in_transaction = conn.getautocommit() == False

    if already_in_transaction:
        yield conn
        return

    try:
        conn.execute("BEGIN")
        yield conn
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise


def _rows_as_dicts(conn, sql, params=()):
    """Execute a query and return its results as dictionaries."""
    info = apsw.ext.query_info(conn, sql, bindings=params)
    columns = [col[0] for col in info.description]

    return [
        dict(zip(columns, row))
        for row in conn.execute(sql, params)
    ]



# ---------------------------------------------------------------
# Players
# ---------------------------------------------------------------

def add_player(conn, first_name, last_name, is_member=0, starting_elo=1000):
    """Add a new player to the database and return their player_id."""
    with transaction(conn):
        row = conn.execute(
            "SELECT player_id FROM players WHERE first_name = ? AND last_name = ?",
            (first_name, last_name)
        ).fetchone()

        if row:
            return row[0]

        conn.execute(
            """INSERT INTO players (first_name, last_name, is_member, base_elo, current_elo)
               VALUES (?, ?, ?, ?, ?)""",
            (first_name, last_name, is_member, starting_elo, starting_elo),
        )
        return conn.last_insert_rowid()


def get_player(conn, player_id):
    """Fetch a player's record by player_id. Returns a dict or None."""
    rows = _rows_as_dicts(conn, "SELECT * FROM players WHERE player_id = ?", (player_id,))
    return rows[0] if rows else None


def list_all_players(conn):
    """Return all players sorted by current Elo descending."""
    return _rows_as_dicts(conn, "SELECT * FROM players ORDER BY current_elo DESC")


def get_pid_from_name(conn, first_name, last_name):
    """Return the player ID of the named player."""
    row = conn.execute(
        "SELECT player_id FROM players WHERE first_name = ? AND last_name = ?",
        (first_name, last_name)
    ).fetchone()
    return row[0] if row else None


def get_name_from_pid(conn, player_id):
    """Return the first and last name of a player."""
    row = conn.execute(
        "SELECT first_name, last_name FROM players WHERE player_id = ?",
        (player_id,)
    ).fetchone()
    return row if row else None


def list_active_players(conn):
    """Return all active players sorted by current Elo descending."""
    return _rows_as_dicts(
        conn,
        "SELECT * FROM players WHERE is_active = 1 ORDER BY current_elo DESC"
    )


def is_player_active(conn, player_id):
    """Return True if the player is active."""
    row = conn.execute(
        "SELECT is_active FROM players WHERE player_id = ?",
        (player_id,)
    ).fetchone()
    return row[0] if row else None


def update_player_active(conn, player_id, active=1):
    """Update a player's active status."""
    with transaction(conn):
        conn.execute(
            "UPDATE players SET is_active = ? WHERE player_id = ?",
            (active, player_id)
        )


# ---------------------------------------------------------------
# Semesters
# ---------------------------------------------------------------

def create_semester(conn, name, start_date, player_ids=None):
    """Create a semester and optionally seed its players."""
    with transaction(conn):
        row = conn.execute(
            "SELECT semester_id FROM semesters WHERE name = ?",
            (name,)
        ).fetchone()

        if row:
            return row[0]

        conn.execute(
            "INSERT INTO semesters (name, start_date) VALUES (?, ?)",
            (name, start_date)
        )
        semester_id = conn.last_insert_rowid()

        if player_ids:
            for pid in player_ids:
                player = get_player(conn, pid)
                conn.execute(
                    """INSERT INTO semesters_players
                       (semester_id, player_id, starting_elo, points)
                       VALUES (?, ?, ?, 0)""",
                    (semester_id, pid, player["current_elo"])
                )

        return semester_id


def add_player_to_semester(conn, semester_id, player_id):
    """Add a player to a semester if they aren't already in it."""
    with transaction(conn):
        player = get_player(conn, player_id)
        conn.execute(
            """INSERT OR IGNORE INTO semesters_players
               (semester_id, player_id, starting_elo, points)
               VALUES (?, ?, ?, 0)""",
            (semester_id, player_id, player["current_elo"])
        )


def get_semester_id_for_round(conn, round_id):
    """Look up which semester a round belongs to."""
    row = conn.execute(
        """SELECT s.semester_id
           FROM rounds r
           JOIN sessions s ON r.session_id = s.session_id
           WHERE r.round_id = ?""",
        (round_id,)
    ).fetchone()
    return row[0] if row else None


def _award_semester_point(conn, semester_id, player_id, points=POINTS_PER_WIN):
    """Add points to a player's semester total."""
    add_player_to_semester(conn, semester_id, player_id)
    conn.execute(
        "UPDATE semesters_players SET points = points + ? WHERE semester_id = ? AND player_id = ?",
        (points, semester_id, player_id)
    )


# ---------------------------------------------------------------
# Sessions / attendance / rounds
# ---------------------------------------------------------------

def create_session(conn, semester_id, session_date, attendee_ids):
    """Create a session and record attendance."""
    with transaction(conn):
        row = conn.execute(
            "SELECT session_id FROM sessions WHERE session_date = ?",
            (session_date,)
        ).fetchone()

        if row:
            return row[0]

        conn.execute(
            "INSERT INTO sessions (semester_id, session_date) VALUES (?, ?)",
            (semester_id, session_date)
        )
        session_id = conn.last_insert_rowid()

        conn.executemany(
            "INSERT INTO session_attendance (session_id, player_id) VALUES (?, ?)",
            [(session_id, pid) for pid in attendee_ids]
        )

        return session_id


def add_session_attendance(conn, session_id, player_id):
    """Add a single player's attendance to an existing session."""
    with transaction(conn):
        conn.execute(
            "INSERT INTO session_attendance (session_id, player_id) VALUES (?, ?)",
            (session_id, player_id)
        )


def create_round(conn, session_id, round_number):
    """Create a round within a session."""
    with transaction(conn):
        conn.execute(
            "INSERT INTO rounds (session_id, round_number) VALUES (?, ?)",
            (session_id, round_number)
        )
        return conn.last_insert_rowid()
    

def get_round_id(conn, session_id, round_number) -> int:
    """Get the ID of a round"""
    with transaction(conn):
        row = conn.execute(
            "SELECT round_id FROM rounds WHERE session_id = ? AND round_number = ?",
            (session_id, round_number)
        ).fetchone()
        return row[0] if row else None


def delete_round(conn, round_id):
    """Delete a round."""
    with transaction(conn):
        conn.execute("DELETE FROM rounds WHERE round_id = ?", (round_id,))
        conn.execute("DELETE FROM matches WHERE round_id = ?", (round_id,))
        
        _recalculate_all_elo(conn)


def get_rounds_in_session(conn, session_id):
    """Get the IDs of the rounds in a session"""
    rows = _rows_as_dicts(conn, "SELECT * FROM rounds WHERE session_id = ?", (session_id,))
    return rows[0] if rows else None

# ---------------------------------------------------------------
# Matches
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
    Record a match result and update both players' Elo.

    Also credits the winner with POINTS_PER_WIN semester points.
    """

    with transaction(conn):
        p1 = get_player(conn, player1_id)
        p1_elo = override_p1_elo if override_p1_elo is not None else p1["current_elo"]

        semester_id = get_semester_id_for_round(conn, round_id)

        add_player_to_semester(conn, semester_id, player1_id)

        if player2_id is not None:
            add_player_to_semester(conn, semester_id, player2_id)

        if winner_id is not None and semester_id is not None:
            _award_semester_point(conn, semester_id, winner_id)

        # Bye
        if player2_id is None:
            conn.execute(
                """INSERT INTO matches
                   (round_id, player1_id, player2_id, winner_id,
                    player1_elo_before, player1_elo_after)
                   VALUES (?, ?, NULL, NULL, ?, ?)""",
                (round_id, player1_id, p1_elo, p1_elo)
            )
            return conn.last_insert_rowid()

        p2 = get_player(conn, player2_id)
        p2_elo = override_p2_elo if override_p2_elo is not None else p2["current_elo"]

        if winner_id == player1_id:
            chg1, chg2 = calc_elo_change(p1_elo, p2_elo)
        elif winner_id == player2_id:
            chg2, chg1 = calc_elo_change(p2_elo, p1_elo)
        else:
            chg1 = chg2 = 0

        new1 = p1_elo + chg1
        new2 = p2_elo + chg2

        conn.execute(
            """INSERT INTO matches
               (round_id, player1_id, player2_id, winner_id,
                player1_elo_before, player2_elo_before,
                player1_elo_after, player2_elo_after)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (round_id, player1_id, player2_id, winner_id,
             p1_elo, p2_elo, new1, new2)
        )

        match_id = conn.last_insert_rowid()

        conn.execute(
            """INSERT INTO elo_history
               (player_id, match_id, elo_before, elo_after, elo_change)
               VALUES (?, ?, ?, ?, ?)""",
            (player1_id, match_id, p1_elo, new1, new1 - p1_elo)
        )

        conn.execute(
            """INSERT INTO elo_history
               (player_id, match_id, elo_before, elo_after, elo_change)
               VALUES (?, ?, ?, ?, ?)""",
            (player2_id, match_id, p2_elo, new2, new2 - p2_elo)
        )

        return match_id


def get_match(conn, match_id):
    """Get the info from a match"""
    return _rows_as_dicts(conn, "SELECT * FROM matches WHERE match_id = ?", (match_id,))[0]


def _recalculate_all_elo(conn):
    """Internal recalculation. Assumes a transaction is already active."""

    conn.execute("UPDATE players SET current_elo = base_elo")
    conn.execute("DELETE FROM elo_history")
    conn.execute("UPDATE semesters_players SET points = 0")

    matches = conn.execute(
        """SELECT m.match_id, m.round_id, m.player1_id, m.player2_id,
                  m.winner_id, s.semester_id
           FROM matches m
           JOIN rounds r ON m.round_id = r.round_id
           JOIN sessions s ON r.session_id = s.session_id
           ORDER BY m.match_id ASC"""
    ).fetchall()

    players = conn.execute(
        "SELECT player_id, base_elo FROM players"
    )

    elo_map = {player_id: elo for player_id, elo in players}

    for match_id, round_id, p1_id, p2_id, winner_id, semester_id in matches:
        p1_before = elo_map[p1_id]

        if p2_id is None:
            conn.execute(
                "UPDATE matches SET player1_elo_before = ?, player1_elo_after = ? WHERE match_id = ?",
                (p1_before, p1_before, match_id)
            )
            continue

        p2_before = elo_map[p2_id]

        if winner_id == p1_id:
            chg1, chg2 = calc_elo_change(p1_before, p2_before)
        elif winner_id == p2_id:
            chg2, chg1 = calc_elo_change(p2_before, p1_before)
        else:
            chg1 = chg2 = 0

        new1 = p1_before + chg1
        new2 = p2_before + chg2

        conn.execute(
            """UPDATE matches
               SET player1_elo_before = ?, player2_elo_before = ?,
                   player1_elo_after = ?, player2_elo_after = ?
               WHERE match_id = ?""",
            (p1_before, p2_before, new1, new2, match_id)
        )

        conn.execute(
            """INSERT INTO elo_history
               (player_id, match_id, elo_before, elo_after, elo_change)
               VALUES (?, ?, ?, ?, ?)""",
            (p1_id, match_id, p1_before, new1, new1 - p1_before)
        )

        conn.execute(
            """INSERT INTO elo_history
               (player_id, match_id, elo_before, elo_after, elo_change)
               VALUES (?, ?, ?, ?, ?)""",
            (p2_id, match_id, p2_before, new2, new2 - p2_before)
        )

        if winner_id is not None and semester_id is not None:
            _award_semester_point(conn, semester_id, winner_id)

        elo_map[p1_id] = new1
        elo_map[p2_id] = new2


def recalculate_all_elo(conn):
    """Wipe Elo history and semester points, then recalculate everything."""
    with transaction(conn):
        _recalculate_all_elo(conn)


def edit_match_winner(conn, match_id, new_winner_id):
    """Edit a match winner and recalculate the entire system."""
    with transaction(conn):
        conn.execute(
            "UPDATE matches SET winner_id = ? WHERE match_id = ?",
            (new_winner_id, match_id)
        )
        _recalculate_all_elo(conn)


def delete_match(conn, match_id):
    """Delete a match and recalculate the entire system."""
    with transaction(conn):
        conn.execute(
            "DELETE FROM matches WHERE match_id = ?",
            (match_id,)
        )
        _recalculate_all_elo(conn)


def get_match_id(conn, p1_id, p2_id, round_id):
    """Return the match_id for two players in a round."""
    row = conn.execute(
        "SELECT match_id FROM matches WHERE player1_id = ? AND player2_id = ? AND round_id = ?",
        (p1_id, p2_id, round_id)
    ).fetchone()
    return row[0] if row else None


# ---------------------------------------------------------------
# Standings / reporting
# ---------------------------------------------------------------

def get_semester_standings(conn, semester_id):
    """Return semester standings ordered by points, wins and Elo."""
    return _rows_as_dicts(
        conn,
        """SELECT * FROM v_semester_standings
           WHERE semester_id = ?
           ORDER BY points DESC, wins DESC, current_elo DESC""",
        (semester_id,)
    )


def get_player_elo_timeline(conn, player_id):
    """Return Elo history records for a player."""
    return _rows_as_dicts(
        conn,
        "SELECT * FROM v_player_elo_timeline WHERE player_id = ? ORDER BY recorded_at",
        (player_id,)
    )


if __name__ == "__main__":
    init_db()