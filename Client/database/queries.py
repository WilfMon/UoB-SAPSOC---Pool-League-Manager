from database.db import get_connection

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
    conn.commit()
    conn.close()
    
def get_player(name):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM players WHERE name = ?", (name,))
    rows = cursor.fetchall()
    
    return rows

def get_all():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM players")
    rows = cursor.fetchall()
    
    return rows

def get_all_players():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM players")
    rows = cursor.fetchall()

    names = [row[0] for row in rows]
    return names