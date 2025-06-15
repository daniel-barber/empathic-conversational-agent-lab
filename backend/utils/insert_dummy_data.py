import sys
from pathlib import Path

# Add the root folder (the one containing 'backend') to sys.path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from backend.database.db import insert_chat_pair, create_tables

def insert_dummy_data():
    dummy_data = [
        {
            "chat_id": "chat_001",
            "pair_number": 1,
            "user_input": "I feel very alone lately. Nobody seems to understand me.",
            "llm_response": "I'm sorry you're feeling isolated. I'm here if you want to talk.",
            "epitome_eval": None,  # No EPITOME eval yet
            "user_feedback": "Good response, made me feel better."
        },
        {
            "chat_id": "chat_002",
            "pair_number": 1,
            "user_input": "I've been stressed about my exams and can't sleep.",
            "llm_response": "Exams can be so stressful. Are you getting enough breaks?",
            "epitome_eval": {
                "emotional_reaction": "strong",
                "interpretation": "weak",
                "exploration": "strong"
            },  # Already evaluated
            "user_feedback": None
        },
        {
            "chat_id": "chat_003",
            "pair_number": 1,
            "user_input": "I think I'm failing at everything I try.",
            "llm_response": "That sounds really hard. I'm proud of you for reaching out.",
            "epitome_eval": None,
            "user_feedback": None
        }
    ]

    for entry in dummy_data:
        insert_chat_pair(
            chat_id=entry["chat_id"],
            pair_number=entry["pair_number"],
            user_input=entry["user_input"],
            llm_response=entry["llm_response"],
            epitome_eval=entry["epitome_eval"],
            user_feedback=entry["user_feedback"]
        )

if __name__ == "__main__":
    create_tables()
    insert_dummy_data()
