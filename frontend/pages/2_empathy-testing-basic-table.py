import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path
from backend.database.db import (
    get_connection,
    update_epitome_eval,
    DB_PATH
)
from backend.services.epitome_evaluation import call_epitome_model


# Check Database is there
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

# Display title
st.title("Empathy Testing")

# Empathy testing button
if st.button("Evaluate Missing EPITOME"):
    missing_df = df[df["epitome_eval"].isnull()]

    with st.spinner("Evaluating missing chats..."):
        for idx, row in missing_df.iterrows():
            user_input = row["user_input"]
            llm_response = row["llm_response"]
            chat_id = row["chat_id"]
            pair_number = row["pair_number"]

            try:
                evaluation = call_epitome_model(user_input, llm_response)
                update_epitome_eval(chat_id, pair_number, evaluation)
            except Exception as e:
                st.error(f"Failed on chat_id {chat_id}: {str(e)}")

    st.success("All missing evaluations completed!")

    # Refresh the table after evaluations
    df = load_chats_from_db()

st.dataframe(df)

