import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "database.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    print(f"Connecting to database at {DB_PATH}")

    return conn

def create_tables():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_pairs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT NOT NULL,
            pair_number INTEGER NOT NULL,
            user_input TEXT NOT NULL,
            llm_response TEXT NOT NULL,
            epitome_eval TEXT,
            user_feedback TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        conn.commit()


def insert_chat_pair(chat_id, pair_number, user_input, llm_response, epitome_eval=None, user_feedback=None):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO chat_pairs (chat_id, pair_number, user_input, llm_response, epitome_eval, user_feedback)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            chat_id,
            pair_number,
            user_input,
            llm_response,
            str(epitome_eval) if epitome_eval else None,
            user_feedback
        ))
        conn.commit()


def update_user_feedback(chat_id: str, pair_number: int, user_feedback: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE chat_pairs
            SET user_feedback = ?
            WHERE chat_id = ? AND pair_number = ?
        """, (user_feedback, chat_id, pair_number))
        conn.commit()


def update_epitome_eval(chat_id: str, pair_number: int, epitome_eval_json: dict):
    with get_connection() as conn:
        cursor = conn.cursor()
        print(f"Updating chat_id={chat_id}, pair_number={pair_number}...")
        cursor.execute("""
            UPDATE chat_pairs
            SET epitome_eval = ?
            WHERE chat_id = ? AND pair_number = ?
        """, (json.dumps(epitome_eval_json), chat_id, pair_number))
        conn.commit()
        print(f"Rows affected: {cursor.rowcount}")
