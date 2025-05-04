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
client = replicate.Client(api_token=replicate_token)

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
        "Answer the user's question and then stop. "
        "Do NOT ask follow-up questions or include any “User:” lines. "
        "Wait for the next user input."
    )

    # 2) Prompt zusammenbauen
    model_prompt = system_prompt + "\n\n"
    for m in st.session_state.chat_history:
        speaker = "User" if m["role"] == "user" else "Assistant"
        model_prompt += f"{speaker}: {m['content']}\n"
    model_prompt += "Assistant:"

    # 3) Input-Dict MIT prompt_template
    replicate_input = {
        "prompt": model_prompt,
        "prompt_template": "{prompt}",  # ← ganz wichtig!
        "top_p": 0.9,
        "temperature": 0.7,  # etwas höher für Variabilität
        "presence_penalty": 1.15,
        "max_tokens": 100,  # genug für einen Satz
        "stop": ["\nUser:", "\nAssistant:"],
    }

    # 4) Streaming mit Marker-Check & Abbruch
    with st.chat_message("assistant"):
        placeholder = st.empty()
        response_text = ""
        markers = ["\nUser:", "\nAssistant:"]
        try:
            for chunk in client.stream("meta/meta-llama-3-8b", input=replicate_input):
                chunk = str(chunk)
                response_text += chunk

                # Wenn ein Stop-Marker erscheint, schreibe nur den Teil davor
                cut = None
                for m in markers:
                    idx = response_text.find(m)
                    if idx != -1:
                        cut = response_text[:idx].strip()
                        break

                # Anzeige updaten
                placeholder.markdown(cut or response_text)

                # Abbrechen, wenn wir geschnitten haben
                if cut is not None:
                    response_text = cut
                    break

        except Exception as e:
            placeholder.markdown(f"❌ Error: {e}")

    # 5) Nur den einen Satz speichern
    st.session_state.chat_history.append({"role": "assistant", "content": response_text})