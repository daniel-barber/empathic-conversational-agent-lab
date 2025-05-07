import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "database.db"

print(f"DB_PATH being used: {DB_PATH}")
print(f"Exists? {DB_PATH.exists()}")

def load_chats_from_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    df = pd.read_sql_query("SELECT * FROM chat_pairs", conn)
    conn.close()
    return df

# Load database
df = load_chats_from_db()

# Display
st.title("Empathy Testing")
st.dataframe(df)
