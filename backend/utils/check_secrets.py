from dotenv import load_dotenv
import os


def get_secret(key: str) -> str:
    # 1. First, try environment or .env
    load_dotenv()
    value = os.getenv(key)
    if value:
        return value

    # 2. If not found, try streamlit.secrets (for Streamlit apps)
    try:
        import streamlit as st
        value = st.secrets.get(key)
        if value:
            return value
    except Exception:
        pass  # Streamlit is not installed or not running

    # 3. If neither found, fail loudly
    raise RuntimeError(f"❌ Missing secret: {key}")
