# backend/llm/document_retriever_RAG.py
from typing import List, Optional, Tuple

import numpy as np
import ollama


class DocumentRetriever:
    """
    In-memory retriever for embedding and retrieving text chunks
    using Ollama embeddings and cosine similarity.
    """

    EMBEDDING_MODEL: str = "hf.co/CompendiumLabs/bge-base-en-v1.5-gguf"

    def __init__(
        self,
        embedding_model: Optional[str] = None
    ) -> None:
        """
        :param embedding_model: Identifier for the Ollama embedding model
        """
        self.embedding_model: str = embedding_model or self.EMBEDDING_MODEL
        self.vector_db: List[Tuple[str, np.ndarray]] = []

    def add_documents(self, chunks: List[str]) -> None:
        """
        Embed and store a list of text chunks in memory.
        """
        for text in chunks:
            # Generate embedding for each chunk and store it
            result = ollama.embed(model=self.embedding_model, input=text)
            emb_array = np.array(result["embeddings"][0], dtype=float)
            self.vector_db.append((text, emb_array))

    def retrieve(self, query: str, top_k: int = 3) -> List[str]:
        """
        Return the top_k most similar text chunks to the query.

        1. Embed the query.
        2. Compute cosine similarity against stored embeddings.
        3. Sort and return the highest-scoring chunks.
        """
        query_emb = np.array(
            ollama.embed(model=self.embedding_model, input=query)["embeddings"][0],
            dtype=float
        )
        query_norm = np.linalg.norm(query_emb)

        scores: List[Tuple[str, float]] = []
        for text, emb in self.vector_db:
            denom = query_norm * np.linalg.norm(emb)
            score = float(np.dot(query_emb, emb) / denom) if denom else 0.0
            scores.append((text, score))

        scores.sort(key=lambda pair: pair[1], reverse=True)
        return [text for text, _ in scores[:top_k]]