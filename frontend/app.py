# app.py

import streamlit as st
from dotenv import load_dotenv
import pathlib, sys

# 1) load .env so get_secret() sees your token
load_dotenv()

# 2) add project root to PYTHONPATH so "backend" is discoverable
sys.path.append(str(pathlib.Path(__file__).parent))

# 3) now import from backend package
from backend.llm.replicate_client_chatbot import ReplicateClientChatbot
from backend.utils.check_secrets import get_secret

# 4) Streamlit UI setup
st.set_page_config(page_title="Empathic Chatbot", page_icon="🦙")
st.title("💬 Empathic Chatbot")

# 5) instantiate your chatbot
token = get_secret("REPLICATE_API_TOKEN")
chatbot = ReplicateClientChatbot(api_token=token)

# 6) chat history in session
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 7) render history
for turn in st.session_state.chat_history:
    with st.chat_message(turn["role"]):
        st.markdown(turn["content"])

# 8) new user input
if user_input := st.chat_input("What’s on your mind?"):
    # show user message
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.chat_history.append({"role": "user", "content": user_input})

    # generate one-sentence reply
    reply = chatbot.generate_response(
        user_input=user_input,
        history=st.session_state.chat_history[:-1]
    )

    # display and save assistant’s reply
    with st.chat_message("assistant"):
        st.markdown(reply)
    st.session_state.chat_history.append({"role": "assistant", "content": reply})
