import streamlit as st
from dotenv import load_dotenv
import replicate
import pathlib
import sys

load_dotenv()
sys.path.append(str(pathlib.Path(__file__).parent.parent))

# Streamlit UI setup
st.set_page_config(page_title="Empathic chatbot", page_icon="🦙")
st.title("💬 Empathic chatbot")

from backend.utils.check_secrets import get_secret
replicate_token = get_secret("REPLICATE_API_TOKEN")
client = replicate.Client(api_token=replicate_token, timeout=(5, 120))

# Initialize history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Show past messages
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Get new user input
if user_input := st.chat_input("What’s on your mind?"):
    # Display user
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.chat_history.append({"role": "user", "content": user_input})

    # Build prompt
    system_prompt = (
        "You are an empathetic, helpful, and friendly AI assistant. "
        "Listen carefully and respond with warmth."
    )
    model_prompt = system_prompt + "\n\n"
    for m in st.session_state.chat_history:
        speaker = "User" if m["role"] == "user" else "Assistant"
        model_prompt += f"{speaker}: {m['content']}\n"
    model_prompt += "Assistant:"

    # Prepare input dict like your example
    replicate_input = {
        "prompt": model_prompt,
        "top_p": 0.9,
        "temperature": 0.7,
        "presence_penalty": 1.15,
        "max_tokens": 300,
        "stop": ["\nUser:", "\nAssistant:"],
    }

    # Stream the response
    with st.chat_message("assistant"):
        placeholder = st.empty()
        response_text = ""
        try:
            for chunk in client.stream("meta/meta-llama-3-8b", input=replicate_input):
                # chunk already contains the next piece of text
                response_text += str(chunk)
                placeholder.markdown(response_text)
        except Exception as e:
            placeholder.markdown(f"❌ Error: {e}")

    # Save assistant reply
    st.session_state.chat_history.append({"role": "assistant", "content": response_text})
