# 0_Intro.py — Empathic AI for Cancer Patients - IP5

import streamlit as st

st.set_page_config(
    page_title="Empathic AI for Cancer Patients - IP5",
    page_icon="🩷",
    layout="wide",
    initial_sidebar_state="collapsed"

)

st.title("🩷 Empathic AI for Cancer Patients - IP5")

st.markdown("""
Welcome to the testing interface for our **IP5 project** on empathic AI for cancer patients, developed by Computer Science students in the [iCompetence](https://www.fhnw.ch/de/studium/informatik/icompetence) program at **FHNW**.

This work is carried out in the context of the **[IMPortant Horizon Europe initiative](https://important-project.com)**, which aims to make clinical trials more inclusive and supportive, especially for people affected by **breast cancer**. 

The chatbot is intended to support people who are processing a breast cancer diagnosis by offering **empathic and informative responses**, using a Retrieval-Augmented Generation (RAG) system based on publicly available information from [Krebsliga Schweiz](https://www.krebsliga.ch).

ℹ️ The chatbot is for **research and testing** purposes only and is **not affiliated with or endorsed by Krebsliga**.

---

### 💬 What can I ask?

If you have personal experience with breast cancer, feel free to ask about topics that are important to you.  
Otherwise, try to put yourself in the shoes of someone who has just received a diagnosis.  

You can ask about treatment options, clinical trials, emotions, daily life, or how to talk about your diagnosis. 
For example:

- *“What are side effects of chemotherapy?”*  
- *“I feel overwhelmed, what should I do?”*  
- *“How do I tell my family and friends I have breast cancer?”*  
- *“Can I continue working during treatment?”*  
- *“Is joining a clinical trial safe?”*

The chatbot will do its best to respond **empathetically and informatively**.

---

### 📋 Your role as a tester

After each chatbot reply, you’ll be asked to rate how **empathic** the response felt to you on a **1–5 smiley scale** —  
specifically whether it showed **warmth, understanding, and care**.

Your feedback will help us evaluate and improve the **emotional intelligence** of future AI systems in healthcare settings.

---

### 🔐 Privacy and Consent

By using this chatbot, you agree that your inputs may be **stored and analyzed anonymously** for research purposes within the scope of this student project.  

👉 **Please do not enter any personal or sensitive information**, such as real names, contact details, or anything you wouldn’t want to be stored or analyzed.

---

### 📫 Contact

If you have questions or feedback about this project, feel free to reach out to us:

**Daniel Barber** – daniel.barber@students.fhnw.ch  
**Tamira Leber** – tamira.leber@students.fhnw.ch

**Advisors:**  
Prof. Dr. **Samuel Fricker** – samuel.fricker@fhnw.ch  
**Maryam Yeganeh** – maryam.yeganeh@fhnw.ch

---
""")

st.markdown("""## 🚀 Ready to begin?
Click the button below to start chatting and help us improve empathic AI in healthcare.
""")


st.markdown(
    """
    <a href="Chat" target="_self">
        <button style="
            background-color: #f63366;
            color: white;
            padding: 0.75em 1.5em;
            border: none;
            border-radius: 6px;
            font-size: 16px;
            cursor: pointer;">
            Start the Chat
        </button>
    </a>
    """,
    unsafe_allow_html=True
)
