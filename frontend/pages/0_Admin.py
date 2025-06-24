import streamlit as st
from backend.database.db import (
    list_prompts, get_prompt_text, create_prompt, set_active_prompt
)

st.set_page_config("🛠️ Admin – Prompts")

st.title("🛠️ Prompt Manager")

# ---------- Sidebar : create / edit ----------
with st.sidebar:
    st.header("➕ New / Edit prompt")
    if "draft_name" not in st.session_state:
        st.session_state.draft_name = ""
        st.session_state.draft_text = ""

    st.session_state.draft_name = st.text_input("Version name", value=st.session_state.draft_name)
    st.session_state.draft_text = st.text_area("Prompt text", value=st.session_state.draft_text, height=220)
    activate_now = st.checkbox("Activate immediately", value=True)

    if st.button("💾 Save version", disabled=not st.session_state.draft_name.strip()):
        create_prompt(
            version_name=st.session_state.draft_name.strip(),
            prompt_text=st.session_state.draft_text.strip(),
            activate=activate_now,
        )
        st.success("Saved!")
        # clear draft
        st.session_state.draft_name, st.session_state.draft_text = "", ""
        st.rerun()

# ---------- Main area : existing versions ----------
st.subheader("Saved prompt versions")

rows = list_prompts()
if not rows:
    st.info("Nothing saved yet.")
else:
    for pid, name, ts, active in rows:
        with st.expander(f"{'⭐ ' if active else ''}{name}  —  {ts[:19]}"):
            st.code(get_prompt_text(pid), language="markdown")
            col1, col2 = st.columns(2)
            with col1:
                if not active and st.button("Set active", key=f"act{pid}"):
                    set_active_prompt(pid)
                    st.rerun()
            with col2:
                if st.button("Copy → editor", key=f"copy{pid}"):
                    st.session_state.draft_name = f"{name} (edit)"
                    st.session_state.draft_text = get_prompt_text(pid)
                    st.sidebar.warning("Copied — edit in sidebar, then Save.")
st.caption("⭐ = currently used by the chatbot")
