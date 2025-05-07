# app.py – Empathic Chatbot mit Streamlit
import streamlit as st
from dotenv import load_dotenv
import pathlib, sys, uuid

# 1) Setup Umgebung & Pfade
load_dotenv()
PROJECT_ROOT = pathlib.Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

# 2) Imports
from backend.llm.replicate_client_chatbot import ReplicateClientChatbot
from backend.utils.check_secrets import get_secret
from backend.database.db import create_tables, insert_chat_pair, get_recent_pairs

# 3) Datenbank vorbereiten
create_tables()

# 4) Seite konfigurieren
st.set_page_config(page_title="Empathic Chatbot", page_icon="🦙", layout="wide")
st.title("💬 Empathic Chatbot")

# 5) Session State initialisieren
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
    st.session_state.chat_id = str(uuid.uuid4())
    st.session_state.pair_number = 1

# 6) Sidebar – Verlauf aus DB anzeigen
with st.sidebar:
    st.header("Settings")
    st.write("Manage your chat session.")
    rows = get_recent_pairs(st.session_state.chat_id, limit=5)
    for r in reversed(rows):
        st.markdown(f"**#{r['pair_number']}** You: {r['user_input']} → Bot: {r['llm_response']}")
    if st.button("Clear Chat History"):
        st.session_state.clear()

# 7) Chatbot initialisieren
token = get_secret("REPLICATE_API_TOKEN")
chatbot = ReplicateClientChatbot(api_token=token)

# 8) Chatverlauf anzeigen
for turn in st.session_state.chat_history:
    avatar = "🧑‍💻" if turn["role"] == "user" else "🤖"
    with st.chat_message(turn["role"], avatar=avatar):
        st.markdown(turn["content"])

# 9) Neue Eingabe verarbeiten
if user_input := st.chat_input("Type your message..."):
    # 1. Nutzeranzeige
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(user_input)
    st.session_state.chat_history.append({"role": "user", "content": user_input})

    # 2. Bot-Antwort
    with st.chat_message("assistant", avatar="🤖"), st.spinner("Thinking… 🦙"):
        reply = chatbot.generate_response(
            user_input=user_input,
            history=st.session_state.chat_history[-6:]  # max 3 Paare
        )
        reply = reply.strip() if reply else "[Keine Antwort erhalten]"
        st.markdown(reply)

    # 3. Verlauf & Datenbank aktualisieren
    st.session_state.chat_history.append({"role": "assistant", "content": reply})

    try:
        insert_chat_pair(
            chat_id=st.session_state.chat_id,
            pair_number=st.session_state.pair_number,
            user_input=user_input,
            llm_response=reply
        )
        st.session_state.pair_number += 1
    except Exception as e:
        st.error(f"❌ Fehler beim Speichern in die DB: {e}")

    # 4. Seite neu laden → Verlauf sichtbar
    st.rerun()
