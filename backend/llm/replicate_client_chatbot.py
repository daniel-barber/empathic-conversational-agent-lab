# backend/llm/replicate_client_chatbot.py

from typing import List, Optional, Dict, Tuple
import replicate
from langdetect import detect
from backend.llm.document_retriever_RAG import DocumentRetriever
from backend.database.db import create_tables, get_active_prompt

class ReplicateClientChatbot:
    """
    Chatbot that integrates Replicate's GPT-4.1 Mini model
    with Retrieval-Augmented Generation (RAG).
    """
    DEFAULT_MODEL = "openai/gpt-4.1-mini"
    DEFAULT_SYSTEM_PROMPT = (
        "You are a calm, empathic assistant. "
        "Use only the provided context; do not hallucinate. "
        "If you cannot answer from the context, say so honestly."
    )

    def __init__(
        self,
        api_token: str,
        model: Optional[str] = None,
        retriever: Optional[DocumentRetriever] = None,
        timeout: Tuple[float, float] = (5, 300)
    ):
        create_tables()
        self.client = replicate.Client(api_token=api_token, timeout=timeout)
        self.model = model or self.DEFAULT_MODEL
        self.retriever = retriever or DocumentRetriever()

    def generate_response(
        self,
        user_input: str,
        history: Optional[List[Dict[str, str]]] = None,
        system_prompt: Optional[str] = None,
        top_p: float = 1.0,
        temperature: float = 1.0
    ) -> str:
        # 1) Choose system prompt
        prompt_text = system_prompt or get_active_prompt() or self.DEFAULT_SYSTEM_PROMPT

        # 2) Retrieve and bullet‐list the RAG context
        raw_docs = self.retriever.retrieve(query=user_input, top_k=5)
        context_str = "\n".join(f"- {chunk}" for chunk in raw_docs)

        # 3) Detect the user’s language
        user_lang = detect(user_input)  # e.g. 'en', 'de'

        # 4) If the user is English, pre-translate German context into English
        if user_lang.startswith("en"):
            translation_payload = {
                "prompt": context_str,
                "system_prompt": (
                    "You are a translation assistant. "
                    "Translate these bullet points into clear English, "
                    "preserving meaning but dropping any German-specific formatting."
                ),
                "temperature": 0.0,
                "top_p": 1.0,
                "max_completion_tokens": 512,
            }
            translated = ""
            for chunk in replicate.run(
                self.model,
                input=translation_payload,
                stream=True
            ):
                translated += chunk
            context_str = translated.strip()

        # 5) Build the single-prompt string
        prompt = f"Context:\n{context_str}\n\n"
        if history:
            for turn in history:
                who = "User" if turn["role"] == "user" else "Assistant"
                prompt += f"{who}: {turn['content']}\n"
        prompt += f"User: {user_input}\nAssistant:"

        # 6) Package exactly as the gpt-4.1-mini schema expects
        payload = {
            "prompt": prompt,
            "system_prompt": prompt_text,
            "temperature": temperature,
            "top_p": top_p,
            "max_completion_tokens": 512,
        }
        print(">>> OUTGOING PAYLOAD:", payload)

        # 7) Stream the response
        response = ""
        for chunk in replicate.run(
            self.model,
            input=payload,
            stream=True
        ):
            response += chunk

        return response.strip()
