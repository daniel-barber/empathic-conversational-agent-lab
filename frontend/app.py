# app.py – Empathic Chatbot mit Streamlit

import streamlit as st
from dotenv import load_dotenv
import pathlib, sys, uuid
from PyPDF2 import PdfReader

# 1) Set page config muss als erstes kommen
st.set_page_config(page_title="Empathic Chatbot", page_icon="🦙", layout="wide")

# 2) Setup Umgebung & Pfade
load_dotenv()
PROJECT_ROOT = pathlib.Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

# 3) Weitere Imports
from backend.llm.replicate_client_chatbot import ReplicateClientChatbot
from backend.utils.check_secrets import get_secret
from backend.database.db import create_tables, insert_chat_pair, get_recent_pairs
from backend.llm.document_retriever_RAG import DocumentRetriever

# 4) PDF einlesen & in Chunks splitten
PDF_PATH = "docs/chiaseeds.pdf"
reader = PdfReader(PDF_PATH)
full_text = ""
for page in reader.pages:
    text = page.extract_text() or ""
    full_text += text + "\n\n"
chunks = [c.strip() for c in full_text.split("\n\n") if c.strip()]

# 5) Retriever instanziieren
retriever = DocumentRetriever()

# 6) Nur neue Chunks in Milvus einfügen
#    Wir zählen erst, wie viele Vektoren schon drin sind:
existing_count = retriever.collection.num_entities
if existing_count < len(chunks):
    # nur die „fehlenden“ Chunks hinzufügen
    new_chunks = chunks[existing_count:]
    retriever.add_documents(new_chunks)
    st.info(f"{len(new_chunks)} neue Dokument-Chunks hinzugefügt.")
else:
    st.info("Alle Dokumente sind bereits geladen.")

# 7) Datenbank vorbereiten
create_tables()

# 8) Streamlit UI
st.title("💬 Empathic Chatbot")


# Session State initialisieren
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
    st.session_state.chat_id = str(uuid.uuid4())
    st.session_state.pair_number = 1

# Chatbot initialisieren
token = get_secret("REPLICATE_API_TOKEN")
chatbot = ReplicateClientChatbot(api_token=token, retriever=retriever)

# Chatverlauf anzeigen
for turn in st.session_state.chat_history:
    avatar = "🧑‍💻" if turn["role"] == "user" else "🤖"
    with st.chat_message(turn["role"], avatar=avatar):
        st.markdown(turn["content"])

# Neue Eingabe
if user_input := st.chat_input("Type your message..."):
    # Nutzereingabe anzeigen
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(user_input)
    st.session_state.chat_history.append({"role": "user", "content": user_input})

    # Bot-Antwort holen
    with st.chat_message("assistant", avatar="🤖"), st.spinner("Thinking… 🦙"):
        reply = chatbot.generate_response(
            user_input=user_input,
            history=st.session_state.chat_history[-6:]
        ) or "[Keine Antwort erhalten]"
        reply = reply.strip()
        st.markdown(reply)

    # Verlauf updaten & in DB speichern
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

    st.rerun()
