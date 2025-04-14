from dotenv import load_dotenv
import os
import streamlit as st


def get_secret(key: str) -> str:
    value = st.secrets.get(key)

    if value:
        st.info("🔐 Loaded from Streamlit secrets.")
    else:
        load_dotenv()
        value = os.getenv(key)
        if value:
            st.info("🧪 Loaded from .env file.")
        else:
            st.error(f"❌ Missing secret: {key}")
            st.stop()

    return value
