import sqlite3
from pathlib import Path

def get_connection(dest="league.db"):
    DB_PATH = Path(__file__).resolve().parent.parent / "data" / dest

    return sqlite3.connect(DB_PATH)