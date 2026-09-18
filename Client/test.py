from database.db import get_connection, get_player_matches_played, get_player_absence_streak ,recalculate_all_elo, complete_semester, remove_semester

conn = get_connection()

#print(get_player_matches_played(conn, 1))

#print(get_player_absence_streak(conn, 70))

remove_semester(conn, 5)