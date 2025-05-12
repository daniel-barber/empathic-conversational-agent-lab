# backend/llm/replicate_client_chatbot.py
from typing import Dict, List, Optional, Tuple

import replicate
from backend.llm.document_retriever_RAG import DocumentRetriever


class ReplicateClientChatbot:
    """
    Chatbot that integrates Replicate's LLaMA-3 model
    with Retrieval-Augmented Generation (RAG).
    """
    print(f"[DEBUG] Loading ReplicateClientChatbot from {__file__}")

    DEFAULT_MODEL: str = "meta/meta-llama-3-8b-instruct"
    DEFAULT_SYSTEM_PROMPT: str = (
        "You are an empathetic, helpful, and friendly AI assistant."
        " Use the provided context to answer the user's question concisely and accurately without quoting it verbatim."
        " Do NOT hallucinate or invent information."
        "use the RAG to give more detailed and correct answers to the questions"
        " Provide your answer in a couple of sentence and then stop. Do not write a whole paragraph"
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
        prompt_text = system_prompt or self.DEFAULT_SYSTEM_PROMPT

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
