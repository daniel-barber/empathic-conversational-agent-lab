# backend/llm/document_retriever_RAG.py
from typing import List, Optional
import os
import numpy as np
from pymilvus import (
    connections,
    FieldSchema,
    CollectionSchema,
    DataType,
    Collection,
)
import ollama


class DocumentRetriever:
    """
    Retriever for embedding and retrieving text chunks
    using Ollama embeddings and Milvus vector storage and search.
    """

    # -------------------------
    # Module-level setup
    # -------------------------
    MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
    MILVUS_PORT = os.getenv("MILVUS_PORT", "19530")

    # Connect to Milvus
    connections.connect(alias="default", host=MILVUS_HOST, port=MILVUS_PORT)

    # Collection parameters
    COLLECTION_NAME = "documents"
    EMB_DIM = 1536  # dimension of the embedding vectors

    # Ensure the collection exists, create if not
    if Collection.exists(COLLECTION_NAME):
        collection = Collection(COLLECTION_NAME)
    else:
        fields = [
            FieldSchema(
                name="id", dtype=DataType.INT64, is_primary=True, auto_id=True
            ),
            FieldSchema(
                name="embedding", dtype=DataType.FLOAT_VECTOR, dim=EMB_DIM
            ),
            FieldSchema(
                name="text", dtype=DataType.VARCHAR, max_length=65535
            ),
        ]
        schema = CollectionSchema(
            fields, description="Store of document embeddings"
        )
        collection = Collection(name=COLLECTION_NAME, schema=schema)
        # Create an index for fast vector search
        collection.create_index(
            field_name="embedding",
            index_params={
                "index_type": "IVF_FLAT",
                "metric_type": "COSINE",
                "params": {"nlist": 128},
            },
        )

    # Load the collection into memory for search
    collection.load()

    # -------------------------
    # Instance-level setup
    # -------------------------
    EMBEDDING_MODEL: str = "hf.co/CompendiumLabs/bge-base-en-v1.5-gguf"

    def __init__(
        self,
        embedding_model: Optional[str] = None,
        collection_name: Optional[str] = None,
    ) -> None:
        """
        :param embedding_model: Ollama model identifier for embedding
        :param collection_name: Milvus collection name (default "documents")
        """
        self.embedding_model = embedding_model or self.EMBEDDING_MODEL
        if collection_name:
            self.collection = Collection(collection_name)
        else:
            self.collection = DocumentRetriever.collection

    # -------------------------
    # Document insertion
    # -------------------------

    def add_documents(self, chunks: List[str]) -> None:
        """
        Embed and insert a list of text chunks into Milvus.
        """
        embeddings = []
        for text in chunks:
            # Generate embedding via Ollama
            result = ollama.embed(model=self.embedding_model, input=text)
            vec = np.array(result["embeddings"][0], dtype=np.float32)
            embeddings.append(vec.tolist())

        # Insert embeddings and texts into Milvus
        self.collection.insert([embeddings, chunks])
        # Ensure data is flushed to storage
        self.collection.flush()

    # -------------------------
    # Retrieval / search
    # -------------------------

    def retrieve(self, query: str, top_k: int = 3) -> List[str]:
        """
        Return the top_k most similar text chunks to the query using Milvus search.
        """
        # Embed the query via Ollama
        result = ollama.embed(model=self.embedding_model, input=query)
        query_emb = np.array(result["embeddings"][0], dtype=np.float32).tolist()

        # Define search parameters
        search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
        # Ensure the collection is loaded
        self.collection.load()

        # Perform search
        search_results = self.collection.search(
            data=[query_emb],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            output_fields=["text"],
        )
        # Extract and return the text from results
        results = []
        for hits in search_results:
            for hit in hits:
                results.append(hit.entity.get("text"))
        return results
