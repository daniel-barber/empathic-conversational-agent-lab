import sys
import pathlib

# Make sure the parent folder (project root) is on the import path
sys.path.append(str(pathlib.Path(__file__).parent.parent))

import streamlit as st
st.set_page_config(page_title="Empathic Agent Lab", page_icon="🧠")

from backend.utils.check_secrets import get_secret

replicate_token = get_secret("REPLICATE_API_TOKEN")

st.title("🤖 Empathic Conversational Agent")
st.success("Secret loaded successfully!")
st.write("🔐 Your token starts with:", replicate_token[:4] + "..." if replicate_token else "Not found")
