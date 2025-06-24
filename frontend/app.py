# app.py – Empathic Chatbot with Streamlit

import streamlit as st
from dotenv import load_dotenv
import pathlib, sys, uuid
from PyPDF2 import PdfReader


# 1) Set page config must come first
st.set_page_config(page_title="Empathic Chatbot", page_icon="🦙", layout="wide")

# 2) Setup environment & paths
load_dotenv()
PROJECT_ROOT = pathlib.Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

# 3) Additional imports
from backend.llm.replicate_client_chatbot import ReplicateClientChatbot
from backend.utils.check_secrets import get_secret
from backend.database.db import create_tables, insert_chat_pair, get_recent_pairs, update_user_feedback, \
    get_feedback_statistics, get_active_prompt_id
from backend.llm.document_retriever_RAG import DocumentRetriever

# 4) Read PDF & split into chunks
PDF_PATH = "docs/chiaseeds.pdf"
reader = PdfReader(PDF_PATH)
full_text = ""
for page in reader.pages:
    text = page.extract_text() or ""
    full_text += text + "\n\n"
chunks = [c.strip() for c in full_text.split("\n\n") if c.strip()]

# 5) Initialize retriever
retriever = DocumentRetriever()

# 6) Only add new chunks to Milvus
#    First count how many vectors are already in there:
existing_count = retriever.collection.num_entities
if existing_count < len(chunks):
    # only add the "missing" chunks
    new_chunks = chunks[existing_count:]
    retriever.add_documents(new_chunks)
    st.info(f"{len(new_chunks)} new document chunks added.")
else:
    st.info("All documents are already loaded.")

# 7) Prepare database
create_tables()

# 8) Streamlit UI
st.title("💬 Empathic Chatbot")

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
    st.session_state.chat_id = str(uuid.uuid4())
    st.session_state.pair_number = 1
    st.session_state.feedback_given = set()  # Set for already rated messages

# Initialize chatbot
token = get_secret("REPLICATE_API_TOKEN")
chatbot = ReplicateClientChatbot(api_token=token, retriever=retriever)

# Display chat history
for i, turn in enumerate(st.session_state.chat_history):
    avatar = "🧑‍💻" if turn["role"] == "user" else "🤖"
    with st.chat_message(turn["role"], avatar=avatar):
        st.markdown(turn["content"])

        # Show feedback section only for bot responses
        if turn["role"] == "assistant":
            # Disable the widget once this reply has already been rated
            disabled = i in st.session_state.feedback_given

            st.caption("How empathic was this response?")

            raw_score = st.feedback(
                options="faces",  # or "faces", "thumbs"
                key=f"fb_{st.session_state.chat_id}_{i}",
                disabled=disabled,
            )

            # When the user clicks, Streamlit re-runs and raw_score gets a value.
            if raw_score is not None and not disabled:
                stars = raw_score + 1  # st.feedback returns 0-4 → map to 1-5
                update_user_feedback(
                    chat_id=st.session_state.chat_id,
                    pair_number=(i // 2) + 1,
                    user_feedback=stars,
                )
                st.session_state.feedback_given.add(i)
                st.toast(f"⭐ Thanks for the {stars}-star rating!")

# New input
if user_input := st.chat_input("Type your message..."):
    # Display user input
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(user_input)
    st.session_state.chat_history.append({"role": "user", "content": user_input})

    # Get bot response
    with st.chat_message("assistant", avatar="🤖"), st.spinner("Thinking… 🦙"):
        reply = chatbot.generate_response(
            user_input=user_input,
            history=st.session_state.chat_history[-6:]
        ) or "[No response received]"
        reply = reply.strip()
        st.markdown(reply)

    # Update history & save to DB
    st.session_state.chat_history.append({"role": "assistant", "content": reply})
    try:
        insert_chat_pair(
            chat_id=st.session_state.chat_id,
            pair_number=st.session_state.pair_number,
            user_input=user_input,
            llm_response=reply,
            prompt_id=get_active_prompt_id(),
        )
        st.session_state.pair_number += 1
    except Exception as e:
        st.error(f"❌ Error saving to DB: {e}")

    st.rerun()

# Optional: Feedback statistics in sidebar
with st.sidebar:
    st.header("📊 Feedback Overview")

    # Session feedback
    if st.session_state.feedback_given:
        st.metric("Ratings given this session", len(st.session_state.feedback_given))
    else:
        st.info("No ratings given yet this session")

    # Overall feedback statistics (optional)
    try:
        with st.expander("📈 Overall Statistics"):
            stats = get_feedback_statistics()
            if stats['total_feedback'] > 0:
                st.metric("Total Ratings", stats['total_feedback'])
                st.metric("Average Rating", f"⭐ {stats['avg_rating']}/5")

                # Show rating distribution
                st.write("**Rating Distribution:**")
                for rating in range(1, 6):
                    count = stats['rating_counts'][rating]
                    if count > 0:
                        st.write(f"{'⭐' * rating} ({rating}): {count}")
            else:
                st.info("No ratings in database yet")
    except Exception as e:
        st.error(f"Error loading statistics: {e}")

    if st.button("🔄 Reset chat"):
        st.session_state.chat_history = []
        st.session_state.feedback_given = set()
        st.session_state.chat_id = str(uuid.uuid4())
        st.session_state.pair_number = 1
        st.rerun()