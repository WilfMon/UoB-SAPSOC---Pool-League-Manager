from db import get_connection, delete_match, get_match_id


conn = get_connection()

print(get_match_id(conn, 4, 3, 2))