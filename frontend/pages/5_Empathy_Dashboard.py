import streamlit as st
import json
import re
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt

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
         Prompt_Name   = ("version_name",    "first"),
         Chats         = ("chat_id",         "count"),
         Avg_ER        = ("emotional_reactions", "mean"),
         Avg_IP        = ("interpretations",     "mean"),
         Avg_EX        = ("explorations",        "mean"),
         Avg_Feedback  = ("feedback_score",      "mean"),
      )
      .reset_index(drop=True)
)

# 1) Compute overall EPITOME avg and delta
agg["Avg_EP"]          = agg[["Avg_ER","Avg_IP","Avg_EX"]].mean(axis=1)
agg["Delta_FB_minus_EP"] = agg["Avg_Feedback"] - agg["Avg_EP"]

# 2) Reorder columns
cols = [
    "Prompt_Name",
    "Chats",
    "Avg_ER", "Avg_IP", "Avg_EX",
    "Avg_EP",
    "Avg_Feedback",
    "Delta_FB_minus_EP"
]
agg = agg[cols]

# 3) Render table with styling
st.header("Prompt-Level Empathy Summary")
st.dataframe(
    agg.style
       .format({
         "Avg_ER":"{:.2f}",
         "Avg_IP":"{:.2f}",
         "Avg_EX":"{:.2f}",
         "Avg_EP":"{:.2f}",
         "Avg_Feedback":"{:.1f}/5",
         "Delta_FB_minus_EP":"{:+.2f}"
       })
)

# 5) Full Prompt Text Reference
st.header("Full Prompt Texts")
for prompt_name in agg["Prompt_Name"]:
    with st.expander(prompt_name):
        text = df.loc[df.version_name == prompt_name, "system_prompt"].unique()
        st.code(text[0] if len(text) else "—")
