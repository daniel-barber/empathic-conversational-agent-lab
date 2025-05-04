# app.py – Classy UI for Empathic Chatbot
import streamlit as st
from dotenv import load_dotenv
import pathlib, sys

# 1) Load environment and make backend importable
load_dotenv()
sys.path.append(str(pathlib.Path(__file__).parent))

# 2) Imports
from backend.llm.replicate_client_chatbot import ReplicateClientChatbot
from backend.utils.check_secrets import get_secret

# 3) Streamlit page configuration
st.set_page_config(
    page_title="Empathic Chatbot",
    page_icon="🦙",
    layout="wide",
    initial_sidebar_state="collapsed"
)
st.title("💬 Empathic Chatbot")

# 4) Sidebar controls
with st.sidebar:
    st.header("Settings")
    st.write("Manage your chat session.")
    if st.button("Clear Chat History"):
        st.session_state.clear()

# 5) Instantiate the chatbot
token = get_secret("REPLICATE_API_TOKEN")
chatbot = ReplicateClientChatbot(api_token=token)

# 6) Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 7) Display chat history with built-in chat components
for turn in st.session_state.chat_history:
    avatar = "🧑‍💻" if turn["role"] == "user" else "🤖"
    with st.chat_message(turn["role"], avatar=avatar):
        st.markdown(turn["content"])

# 8) Handle new user input at the bottom
if user_input := st.chat_input("Type your message..."):
    # Show user message
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(user_input)
    st.session_state.chat_history.append({"role": "user", "content": user_input})

    # Generate and display assistant's reply
    with st.chat_message("assistant", avatar="🤖"), st.spinner("Thinking… 🦙"):
        reply = chatbot.generate_response(
            user_input=user_input,
            history=st.session_state.chat_history[:-1]
        )
        st.markdown(reply)
    st.session_state.chat_history.append({"role": "assistant", "content": reply})
