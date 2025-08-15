import json

import streamlit as st
import pandas as pd
import sqlite3
from backend.database.db import (
    update_epitome_eval,
    DB_PATH
)
from backend.services.epitome_evaluation import call_epitome_model

st.set_page_config("🛠️ Empathy Testing Prettier")

# Admin Page Logic
if "is_admin" not in st.session_state:
    pwd = st.sidebar.text_input(
        "🔐 Admin password",
        type="password",
        key="admin_pwd_input"
    )
    if pwd == st.secrets["ADMIN_PASS"]:
        st.session_state.is_admin = True
        del st.session_state["admin_pwd_input"]
        st.rerun()

if not st.session_state.get("is_admin", False):
    st.sidebar.error("Enter admin password to view this page.")
    st.stop()


# Check Database is there

def load_chats_from_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    df = pd.read_sql_query("SELECT * FROM chat_pairs", conn)
    conn.close()
    return df

# Load database
df = load_chats_from_db()

# Display title
st.title("Empathy Testing Prettier")

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

st.header("Chat Evaluations")

# Group by chat_id first
grouped = df.groupby('chat_id')

for chat_id, group in grouped:
    with st.container(border=True):
        st.markdown(f"## Chat ID: `{chat_id}`")

        group = group.sort_values("pair_number")

        for idx, row in group.iterrows():
            st.markdown(f"### ➡️ Pair {row['pair_number']}")

            st.markdown("**🧑 Seeker's Message:**")
            st.markdown(f"> {row['user_input']}")

            st.markdown("**🤖 LLM Response:**")
            st.markdown(f"> {row['llm_response']}")

            st.markdown("**📈 EPITOME Evaluation:**")

            if row["epitome_eval"]:
                try:
                    epitome = json.loads(row["epitome_eval"])

                    eval_data = {
                        "Category": ["Emotional Reactions", "Interpretations", "Explorations"],
                        "Score (0–2)": [
                            epitome["emotional_reactions"]["score"],
                            epitome["interpretations"]["score"],
                            epitome["explorations"]["score"]
                        ],
                        "Rationale": [
                            epitome["emotional_reactions"]["rationale"],
                            epitome["interpretations"]["rationale"],
                            epitome["explorations"]["rationale"]
                        ]
                    }
                    eval_df = pd.DataFrame(eval_data)
                    st.table(eval_df)

                except Exception as e:
                    st.error(f"Error parsing EPITOME evaluation: {str(e)}")
            else:
                st.warning("No EPITOME Evaluation available yet.")

            if row["user_feedback"]:
                st.markdown("**📝 User Feedback:**")
                st.info(f"{row['user_feedback']}")
            st.markdown("---")
