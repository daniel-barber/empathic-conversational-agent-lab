import replicate
import ollama
import numpy as np

# backend/retriever.py
class DocumentRetriever:
    """
    Simple in-memory retriever using ollama embeddings and cosine similarity,
    following the "Code a simple RAG from scratch" tutorial.
    """
    EMBEDDING_MODEL = 'hf.co/CompendiumLabs/bge-base-en-v1.5-gguf'

    def __init__(self, embedding_model: str = None):
        """
        :param embedding_model: ollama embedding model identifier
        """
        self.embedding_model = embedding_model or self.EMBEDDING_MODEL
        # List of tuples: (chunk_text: str, embedding: np.ndarray)
        self.vector_db: list[tuple[str, np.ndarray]] = []

    def add_documents(self, docs: list[str]) -> None:
        """
        Embeds and adds a list of documents (chunks) to the in-memory vector database.
        """
        for chunk in docs:
            # Generate embedding for the chunk
            emb = ollama.embed(model=self.embedding_model, input=chunk)['embeddings'][0]
            emb_array = np.array(emb, dtype=float)
            self.vector_db.append((chunk, emb_array))

    def retrieve(self, query: str, top_k: int = 3) -> list[str]:
        """
        Retrieves the top_k most similar document chunks for the given query.
        """
        # Embed the query
        q_emb = np.array(ollama.embed(model=self.embedding_model, input=query)['embeddings'][0], dtype=float)
        # Compute cosine similarities
        sims = []
        q_norm = np.linalg.norm(q_emb)
        for chunk, emb in self.vector_db:
            sim = np.dot(q_emb, emb) / (q_norm * np.linalg.norm(emb)) if q_norm and np.linalg.norm(emb) else 0
            sims.append((chunk, sim))
        # Sort by descending similarity and return top_k chunks
        sims.sort(key=lambda x: x[1], reverse=True)
        return [chunk for chunk, _ in sims[:top_k]]


# backend/replicate_client_chatbot.py
class ReplicateClientChatbot:
    """
    Encapsulates interactions with the Replicate LLaMA-3 model,
    streaming exactly one clean sentence per user query,
    enhanced with Retrieval-Augmented Generation (RAG).
    """

    DEFAULT_MODEL = "meta/meta-llama-3-8b-instruct"
    DEFAULT_SYSTEM_PROMPT = (
        "You are an empathetic, helpful, and friendly AI assistant."
        " Use the provided context to answer the user's question in exactly one sentence and then stop."
        " Do NOT ask follow-up questions or include any “User:” lines."
        " Wait for the next user input."
    )

    def __init__(
        self,
        api_token: str,
        model: str = None,
        retriever: DocumentRetriever | None = None,
        timeout: tuple[float, float] = (5, 300),
    ):
        """
        :param api_token: your REPLICATE_API_TOKEN
        :param model: replicate model name (defaults to LLaMA-3 8B instruct)
        :param retriever: optional custom document retriever instance
        :param timeout: (connect_timeout, read_timeout)
        """
        self.client = replicate.Client(api_token=api_token, timeout=timeout)
        self.model = model or self.DEFAULT_MODEL
        self.retriever = retriever or DocumentRetriever()

    def generate_response(
        self,
        user_input: str,
        history: list[dict] = None,
        system_prompt: str = None,
        top_p: float = 0.9,
        temperature: float = 0.7,
        presence_penalty: float = 1.15,
        max_tokens: int = 100,
        stop_sequences: list[str] = None,
        context_k: int = 3,
    ) -> str:
        """
        1) Retrieves top-K relevant docs for the new user input.
        2) Builds a prompt from system instruction + context + history + new user_input,
        3) Streams back (cutting at stop markers).
        """
        # 1) choose or override the system prompt
        sp = system_prompt or self.DEFAULT_SYSTEM_PROMPT

        # 2) retrieve relevant documents
        docs = self.retriever.retrieve(query=user_input, top_k=context_k)
        # format context block per tutorial
        context = '\n'.join([f"- {doc}" for doc in docs])

        # 3) assemble the full prompt with context
        full_prompt = f"{sp}\n\nUse only the following pieces of context to answer the question. Don’t make up information:\n{context}\n\n"
        if history:
            for turn in history:
                speaker = "User" if turn["role"] == "user" else "Assistant"
                full_prompt += f"{speaker}: {turn['content']}\n"
        full_prompt += f"User: {user_input}\nAssistant:"

        # 4) prepare replicate input
        stops = stop_sequences or ["\nUser:", "\nAssistant:"]
        payload = {
            "prompt": full_prompt,
            "prompt_template": "{prompt}",
            "top_p": top_p,
            "temperature": temperature,
            "presence_penalty": presence_penalty,
            "max_tokens": max_tokens,
            "stop": stops,
        }

        # 5) stream & cut at first marker
        response = ""
        for chunk in self.client.stream(self.model, input=payload):
            text = str(chunk)
            response += text
            for marker in stops:
                idx = response.find(marker)
                if idx != -1:
                    return response[:idx].strip()
        return response.strip()
