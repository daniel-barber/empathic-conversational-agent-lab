import streamlit as st
import json
import re
import pandas as pd
import sqlite3

from backend.database.db import DB_PATH

st.set_page_config(page_title="Prompt-Level Empathy Dashboard")


def load_chats_from_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    df = pd.read_sql_query("""
        SELECT
          cp.*,
          pv.version_name,
          pv.prompt_text AS system_prompt
        FROM chat_pairs cp
        LEFT JOIN prompt_versions pv
          ON cp.prompt_id = pv.id
        """, conn)
    conn.close()
    return df


def parse_epitome(json_str):
    if pd.isna(json_str):
        return pd.Series([None, None, None])
    try:
        j = json.loads(json_str)
        return pd.Series([
            j["emotional_reactions"]["score"],
            j["interpretations"]["score"],
            j["explorations"]["score"],
        ])
    except Exception:
        return pd.Series([None, None, None])


def parse_feedback(fb_text):
    if not isinstance(fb_text, str):
        return None
    m = re.search(r"Rating:\s*([1-5])\/5", fb_text)
    return int(m.group(1)) if m else None


# ——— Load & enrich data ———
df = load_chats_from_db()

# EPITOME scores
df[["emotional_reactions", "interpretations", "explorations"]] = (
    df["epitome_eval"].apply(parse_epitome)
)
df["epitome_total_score"] = (
    df["emotional_reactions"]
  + df["interpretations"]
  + df["explorations"]
)

# User feedback score
df["feedback_score"] = df["user_feedback"].apply(parse_feedback)


# ——— Prompt-Level Summary ———
agg = (
    df
      .groupby("version_name")
      .agg(
         **{
           "Prompt Name": ("version_name", "first"),
           "Chats":       ("chat_id",      "count"),
           "Avg ER":      ("emotional_reactions", "mean"),
           "Avg IP":      ("interpretations",     "mean"),
           "Avg EX":      ("explorations",        "mean"),
           "Avg Feedback":("feedback_score",      "mean"),
         }
      )
      .sort_values("Chats", ascending=False)
      .reset_index(drop=True)
)

st.header("Prompt-Level Empathy Summary")
st.dataframe(
    agg.style.format({
      "Avg ER":      "{:.2f}",
      "Avg IP":      "{:.2f}",
      "Avg EX":      "{:.2f}",
      "Avg Feedback":"{:.1f}/5",
    })
)


# ——— Full Prompt Text Reference ———
st.header("Full Prompt Texts")
for prompt_name in agg["Prompt Name"]:
    with st.expander(prompt_name):
        text = df.loc[df.version_name == prompt_name, "system_prompt"].unique()
        st.code(text[0] if len(text) else "—")

