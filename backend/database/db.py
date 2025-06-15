import json
import sqlite3
from pathlib import Path
import re

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
def get_recent_pairs(chat_id: str, limit: int = 5):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT pair_number, user_input, llm_response
            FROM chat_pairs
            WHERE chat_id = ?
            ORDER BY id DESC
            LIMIT ?
        """, (chat_id, limit))
        return cursor.fetchall()


def update_user_feedback(chat_id: str, pair_number: int, user_feedback: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE chat_pairs
            SET user_feedback = ?
            WHERE chat_id = ? AND pair_number = ?
        """, (user_feedback, chat_id, pair_number))
        conn.commit()


def get_feedback_statistics():
    """Get feedback statistics from the user_feedback field"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_feedback 
            FROM chat_pairs 
            WHERE user_feedback IS NOT NULL 
            AND user_feedback LIKE 'Rating:%'
        """)

        feedback_rows = cursor.fetchall()

        if not feedback_rows:
            return {
                'total_feedback': 0,
                'avg_rating': 0,
                'rating_counts': {}
            }

        ratings = []
        rating_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

        # Extract ratings from feedback text
        for row in feedback_rows:
            feedback_text = row['user_feedback']
            # Extract rating using regex: "Rating: X/5"
            match = re.search(r'Rating: (\d)/5', feedback_text)
            if match:
                rating = int(match.group(1))
                if 1 <= rating <= 5:
                    ratings.append(rating)
                    rating_counts[rating] += 1

        avg_rating = sum(ratings) / len(ratings) if ratings else 0

        return {
            'total_feedback': len(ratings),
            'avg_rating': round(avg_rating, 2),
            'rating_counts': rating_counts
        }


def get_all_feedback():
    """Get all feedback entries with their associated chat pairs"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT chat_id, pair_number, user_input, llm_response, 
                   user_feedback, timestamp
            FROM chat_pairs 
            WHERE user_feedback IS NOT NULL
            ORDER BY timestamp DESC
        """)
        return cursor.fetchall()


def get_chat_feedback_summary(chat_id: str):
    """Get feedback summary for a specific chat session"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT pair_number, user_feedback
            FROM chat_pairs 
            WHERE chat_id = ? AND user_feedback IS NOT NULL
            ORDER BY pair_number
        """, (chat_id,))
        return cursor.fetchall()


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
