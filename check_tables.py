import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "backend" / "database" / "database.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("Tables in database:", tables)

conn.close()
