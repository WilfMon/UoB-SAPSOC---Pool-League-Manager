from db import get_connection, delete_round, delete_session, update_player_active, list_players_in_session

"""
conn = get_connection()

for i in range(0, 100): 
    delete_round(conn, i)
    
delete_session(conn, 2)
"""
conn = get_connection()

players = list_players_in_session(conn, 35)

for p in players:
    print(f"{p["first_name"]} {p["last_name"]}")

update_player_active(conn, 10)