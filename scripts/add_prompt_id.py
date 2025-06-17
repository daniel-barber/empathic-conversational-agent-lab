# scripts/add_prompt_id.py  (run from project root)
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))


from backend.database.db import get_connection   # re-uses your DB_PATH + logger

with get_connection() as conn:
    cur = conn.cursor()

    # --- Does the column already exist? -----------------
    cur.execute("PRAGMA table_info(chat_pairs)")
    columns = [c[1] for c in cur.fetchall()]

    if "prompt_id" in columns:
        print("ℹ️  'prompt_id' column is already present — nothing to do.")
    else:
        # --- Add the column ----------------------------
        cur.execute("ALTER TABLE chat_pairs ADD COLUMN prompt_id INTEGER;")
        conn.commit()
        print("✅  Added prompt_id column to chat_pairs")
