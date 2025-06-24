# backend/llm/replicate_client_chatbot.py
from typing import Dict, List, Optional, Tuple

import replicate
from backend.llm.document_retriever_RAG import DocumentRetriever
from backend.database.db import create_tables, get_active_prompt


def __init__(self, api_token: str, model: Optional[str] = None,
             retriever: Optional[DocumentRetriever] = None,
             timeout: Tuple[float, float] = (5, 300)) -> None:
    create_tables()
    self.client = replicate.Client(api_token=api_token, timeout=timeout)
    ...


class ReplicateClientChatbot:
    """
    Chatbot that integrates Replicate's LLaMA-3 model
    with Retrieval-Augmented Generation (RAG).
    """
    print(f"[DEBUG] Loading ReplicateClientChatbot from {__file__}")

    DEFAULT_MODEL: str = "meta/meta-llama-3-8b-instruct"
    DEFAULT_SYSTEM_PROMPT: str = (
        "You are a calm, empathetic, and friendly assistant."
        "You respond thoughtfully, communicate with kindness, and strive to make the user feel understood and supported."
        "Use the provided context to answer questions clearly and accurately, without quoting it verbatim."
        "Incorporate information retrieved via RAG to enhance your answers, but do not rely on it exclusively."
        "Never hallucinate or fabricate information, and do not perform any form of validation or calculation."
        "Provide only the final answer—do not include explanations, scores, system notes, or commentary of any kind."
        "Your output must consist solely of the answer text no RAG SCORE, NO RAG(Risk Assessment Grid) and no Notes be precises!!."
        "If a question cannot be answered based on the available information, acknowledge this honestly and refrain from speculation."
        "be strict"
    )

    def __init__(
        self,
        api_token: str,
        model: Optional[str] = None,
        retriever: Optional[DocumentRetriever] = None,
        timeout: Tuple[float, float] = (5, 300)
    ) -> None:
        """
        :param api_token: Replicate API token
        :param model: Optional override for the LLaMA-3 model
        :param retriever: DocumentRetriever instance for RAG
        :param timeout: Client timeouts (connect, read)
        """
        self.client = replicate.Client(api_token=api_token, timeout=timeout)
        self.model: str = model or self.DEFAULT_MODEL
        self.retriever: DocumentRetriever = retriever or DocumentRetriever()

    def generate_response(
        self,
        user_input: str,
        history: Optional[List[Dict[str, str]]] = None,
        system_prompt: Optional[str] = None,
        top_p: float = 0.9,
        temperature: float = 0.7,
        presence_penalty: float = 1.15,
        max_tokens: int = 100,
        stop_sequences: Optional[List[str]] = None,
        context_k: int = 30
    ) -> str:
        """
        1. Retrieve top-k relevant chunks for the new user input.
        2. Build a prompt combining system instructions, retrieved context,
           conversation history, and the user query.
        3. Stream and truncate the model response at the first stop marker.
        """
        active_prompt = get_active_prompt() or self.DEFAULT_SYSTEM_PROMPT
        prompt_text = system_prompt or active_prompt

        # Fetch context from the retriever
        docs = self.retriever.retrieve(query=user_input, top_k=context_k)
        context_block = "\n".join(f"- {doc}" for doc in docs)

        # Assemble the full prompt
        full_prompt = (
            f"{prompt_text}\n\n"
            f"Use only the following context. Do not invent details:\n{context_block}\n\n"
        )
        if history:
            for turn in history:
                role = "User" if turn.get("role") == "user" else "Assistant"
                full_prompt += f"{role}: {turn.get('content')}\n"
        full_prompt += f"User: {user_input}\nAssistant:"

        # Prepare and send payload
        stops = stop_sequences or ["\nUser:", "\nAssistant:"]
        payload = {
            "prompt": full_prompt,
            "prompt_template": "{prompt}",
            "top_p": top_p,
            "temperature": temperature,
            "presence_penalty": presence_penalty,
            "max_tokens": max_tokens,
            "stop": stops
        }

        # Stream response and cut at marker
        response = ""
        for chunk in self.client.stream(self.model, input=payload):
            response += str(chunk)
            for marker in stops:
                idx = response.find(marker)
                if idx != -1:
                    return response[:idx].strip()
        return response.strip()
