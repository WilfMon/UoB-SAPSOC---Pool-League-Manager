-- =========================================================
-- Pool League Manager — SQLite Schema
-- =========================================================
-- Usage:
--   sqlite3 league.db < schema.sql
--
-- Hierarchy:
--   semesters -> sessions (weekly nights) -> rounds -> matches
-- =========================================================

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------
-- PLAYERS
-- ---------------------------------------------------------
CREATE TABLE players (
    player_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name    TEXT NOT NULL,
    last_name     TEXT NOT NULL,
    is_member     INTEGER NOT NULL DEFAULT 0 CHECK (is_member IN (0, 1)),
    joined_date   TEXT NOT NULL DEFAULT (date('now')),
    base_elo      INTEGER NOT NULL DEFAULT 1000,     -- permanent starting point, set once
    current_elo   INTEGER NOT NULL DEFAULT 1000,     -- live rating, derived/recalculable
    is_active     INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    notes         TEXT
);

-- ---------------------------------------------------------
-- semesters (semesters)
-- ---------------------------------------------------------
CREATE TABLE semesters (
    semester_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name              TEXT NOT NULL,                     -- e.g. "Autumn 2026"
    start_date        TEXT NOT NULL,
    end_date          TEXT,
    status            TEXT NOT NULL DEFAULT 'upcoming'
                          CHECK (status IN ('upcoming', 'active', 'completed')),
    winner_player_id  INTEGER REFERENCES players(player_id)
);

-- Records each player's Elo at the moment a semester starts, so you can
-- measure "movement this semester" separately from lifetime Elo, and their
-- semester points — points are scoped to (semester_id, player_id), so a
-- new semester naturally starts everyone back at zero without any extra
-- reset logic. Points are earned by beating another player (see
-- trg_award_semester_point below).
CREATE TABLE semesters_players (
    semester_id     INTEGER NOT NULL REFERENCES semesters(semester_id) ON DELETE CASCADE,
    player_id     INTEGER NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    starting_elo  INTEGER NOT NULL,
    points        INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (semester_id, player_id)
);

-- ---------------------------------------------------------
-- SESSIONS (weekly league nights)
-- ---------------------------------------------------------
CREATE TABLE sessions (
    session_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    semester_id     INTEGER NOT NULL REFERENCES semesters(semester_id) ON DELETE CASCADE,
    session_date  TEXT NOT NULL,
    status        TEXT NOT NULL DEFAULT 'scheduled'
                      CHECK (status IN ('scheduled', 'in_progress', 'completed', 'cancelled')),
    UNIQUE (semester_id, session_date)
);

-- Which players actually attended a given session — this is your pool
-- of players to randomly pair up each round, and it's how you spot byes.
CREATE TABLE session_attendance (
    session_id  INTEGER NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    player_id   INTEGER NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    PRIMARY KEY (session_id, player_id)
);

-- ---------------------------------------------------------
-- ROUNDS (typically 5-8 per session)
-- ---------------------------------------------------------
CREATE TABLE rounds (
    round_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id    INTEGER NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    round_number  INTEGER NOT NULL,
    UNIQUE (session_id, round_number)
);

-- ---------------------------------------------------------
-- MATCHES (one pairing, one round)
-- player2_id NULL = bye for player1
-- ---------------------------------------------------------
CREATE TABLE matches (
    match_id             INTEGER PRIMARY KEY AUTOINCREMENT,
    round_id             INTEGER NOT NULL REFERENCES rounds(round_id) ON DELETE CASCADE,
    player1_id           INTEGER NOT NULL REFERENCES players(player_id),
    player2_id           INTEGER REFERENCES players(player_id),      -- NULL = bye
    winner_id            INTEGER REFERENCES players(player_id),
    player1_elo_before   INTEGER NOT NULL,
    player2_elo_before   INTEGER,
    player1_elo_after    INTEGER,
    player2_elo_after    INTEGER,
    played_at            TEXT DEFAULT (datetime('now')),
    CHECK (player2_id IS NULL OR player1_id != player2_id),
    CHECK (winner_id IS NULL OR winner_id IN (player1_id, player2_id))
);

-- ---------------------------------------------------------
-- ELO HISTORY (append-only log — one row per player per match)
-- ---------------------------------------------------------
CREATE TABLE elo_history (
    elo_history_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id       INTEGER NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    match_id        INTEGER REFERENCES matches(match_id) ON DELETE CASCADE,
    elo_before      INTEGER NOT NULL,
    elo_after       INTEGER NOT NULL,
    elo_change      INTEGER NOT NULL,
    recorded_at     TEXT DEFAULT (datetime('now'))
);

-- ---------------------------------------------------------
-- INDEXES
-- ---------------------------------------------------------
CREATE INDEX idx_matches_round     ON matches(round_id);
CREATE INDEX idx_matches_player1   ON matches(player1_id);
CREATE INDEX idx_matches_player2   ON matches(player2_id);
CREATE INDEX idx_elo_history_player ON elo_history(player_id);
CREATE INDEX idx_rounds_session    ON rounds(session_id);
CREATE INDEX idx_sessions_semester   ON sessions(semester_id);
CREATE INDEX idx_attendance_player ON session_attendance(player_id);

-- ---------------------------------------------------------
-- TRIGGER: keep players.current_elo in sync automatically.
-- Your Python app calculates the new Elo and inserts one row
-- into elo_history — this trigger does the rest.
-- ---------------------------------------------------------
CREATE TRIGGER trg_sync_player_elo
AFTER INSERT ON elo_history
BEGIN
    UPDATE players
    SET current_elo = NEW.elo_after
    WHERE player_id = NEW.player_id;
END;

-- ---------------------------------------------------------
-- VIEW: live semester standings, computed on the fly so it can
-- never drift out of sync with the underlying match data.
-- points comes straight from semesters_players, since that's the
-- authoritative running total maintained by db.py.
-- ---------------------------------------------------------
CREATE VIEW v_semester_standings AS
SELECT
    sp.semester_id,
    sp.player_id,
    p.first_name || ' ' || p.last_name AS player_name,
    sp.starting_elo,
    p.current_elo AS current_elo,
    sp.points AS points,
    COUNT(CASE WHEN m.winner_id = sp.player_id THEN 1 END) AS wins,
    COUNT(CASE
            WHEN m.winner_id IS NOT NULL
             AND m.winner_id != sp.player_id
             AND (m.player1_id = sp.player_id OR m.player2_id = sp.player_id)
            THEN 1
          END) AS losses,
    COUNT(CASE
            WHEN m.player2_id IS NULL AND m.player1_id = sp.player_id
            THEN 1
          END) AS byes,
    COUNT(CASE
            WHEN (m.player1_id = sp.player_id OR m.player2_id = sp.player_id)
             AND m.player2_id IS NOT NULL
            THEN 1
          END) AS matches_played
FROM semesters_players sp
JOIN players p ON p.player_id = sp.player_id
LEFT JOIN sessions s ON s.semester_id = sp.semester_id
LEFT JOIN rounds   r ON r.session_id = s.session_id
LEFT JOIN matches  m ON m.round_id = r.round_id
                     AND (m.player1_id = sp.player_id OR m.player2_id = sp.player_id)
GROUP BY sp.semester_id, sp.player_id;

-- ---------------------------------------------------------
-- VIEW: a player's full Elo timeline, handy for a graph in the GUI
-- ---------------------------------------------------------
CREATE VIEW v_player_elo_timeline AS
SELECT
    eh.player_id,
    p.first_name || ' ' || p.last_name AS player_name,
    eh.elo_before,
    eh.elo_after,
    eh.elo_change,
    eh.recorded_at,
    eh.match_id
FROM elo_history eh
JOIN players p ON p.player_id = eh.player_id
ORDER BY eh.recorded_at;