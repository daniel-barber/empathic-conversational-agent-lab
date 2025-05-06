import streamlit as st
import replicate
import os
import pathlib
import sys

# Ensure project root is in path
sys.path.append(str(pathlib.Path(__file__).parent.parent))

# Set page config
st.set_page_config(page_title="LLaMA 3 Chatbot", page_icon="🦙")
st.title("💬 LLaMA 3 Conversational Agent")

# Use secret manager
from backend.utils.check_secrets import get_secret

# Load API token
replicate_token = get_secret("REPLICATE_API_TOKEN")
replicate_client = replicate.Client(api_token=replicate_token)

# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Input form
with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_area("You:", height=100)
    submitted = st.form_submit_button("Send")

if submitted and user_input:
    # Add user message to chat history
    st.session_state.chat_history.append({"role": "user", "content": user_input})

    # Create full prompt from chat history
    prompt = ""
    for message in st.session_state.chat_history:
        role = message["role"]
        content = message["content"]
        if role == "user":
            prompt += f"User: {content}\n"
        else:
            prompt += f"Assistant: {content}\n"
    prompt += "Assistant:"

    # Streaming output
    with st.chat_message("assistant"):
        streamed_response = st.empty()
        full_response = ""
        try:
            st.info("Sending prompt to Replicate API...")  # Show user something is happening

            stream = replicate.stream(
                "meta/meta-llama-3-8b",
                input={
                    "prompt": prompt,
                    "top_k": 0,
                    "top_p": 0.9,
                    "temperature": 0.7,
                    "max_tokens": 300,
                    "presence_penalty": 1.15,
                    "prompt_template": "{prompt}",
                    "stop": "\nUser:"
                },
            )

            for chunk in stream:
                st.write(f"Chunk received: {chunk}")  # TEMPORARY DEBUG LINE
                full_response += str(chunk)
                streamed_response.markdown(full_response)

            st.success("Response complete.")  # Inform user

        except Exception as e:
            st.error(f"❌ Error while streaming from Replicate: {e}")
            full_response = f"❌ Error: {e}"
            streamed_response.markdown(full_response)

    # Save assistant reply
    st.session_state.chat_history.append({"role": "assistant", "content": full_response})

# Display chat history
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
