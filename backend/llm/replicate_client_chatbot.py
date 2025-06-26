# backend/llm/replicate_client_chatbot.py

from typing import List, Optional, Dict, Tuple
import replicate
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
        # Initialize Replicate client
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
        # 1) System prompt
        prompt_text = system_prompt or get_active_prompt() or self.DEFAULT_SYSTEM_PROMPT

        # 2) RAG retrieval
        raw_docs = self.retriever.retrieve(query=user_input, top_k=5)
        context_str = "\n".join(f"- {chunk}" for chunk in raw_docs)

        # 3) Build a plain prompt string (chat style)
        prompt = f"Context:\n{context_str}\n\n"

        if history:
            for turn in history:
                role = "User" if turn["role"] == "user" else "Assistant"
                prompt += f"{role}: {turn['content']}\n"

        prompt += f"User: {user_input}\nAssistant:"

        # 4) Payload according to Replicate's API spec
        payload = {
            "prompt": prompt,
            "system_prompt": prompt_text,
            "temperature": temperature,
            "top_p": top_p,
            "max_completion_tokens": 512,
        }

        print(">>> OUTGOING PAYLOAD:", payload)

        # 5) Streaming response
        response = ""
        try:
            for chunk in self.client.run(
                    self.model,
                    input=payload,
                    stream=True
            ):
                response += chunk
        except Exception as e:
            print("❌ Error from Replicate.run:", e)
            raise

        return response.strip()



