from db import get_connection, delete_round


conn = get_connection()

for i in range(0, 100): 
    delete_round(conn, i)
    