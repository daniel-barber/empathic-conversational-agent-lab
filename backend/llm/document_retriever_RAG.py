from pymilvus import (
    connections,
    FieldSchema, CollectionSchema,
    DataType, Collection, utility
)
import numpy as np
import ollama
import os
from typing import List, Optional

class DocumentRetriever:
    MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
    MILVUS_PORT = os.getenv("MILVUS_PORT", "19530")
    COLLECTION_NAME = "documents"
    EMB_DIM = 768
    EMBEDDING_MODEL = "hf.co/CompendiumLabs/bge-base-en-v1.5-gguf"

    def __init__(
        self,
        embedding_model: Optional[str] = None,
        collection_name: Optional[str] = None,
    ) -> None:
        # 1) Verbindung
        connections.connect(alias="default", host=self.MILVUS_HOST, port=self.MILVUS_PORT)

        # 2) Collection anlegen, falls nötig
        name = collection_name or self.COLLECTION_NAME
        if not utility.has_collection(name):
            fields = [
                FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.EMB_DIM),
                FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
            ]
            schema = CollectionSchema(fields, description="Dokumente mit Embeddings")
            Collection(name, schema)
        # 3) Collection-Objekt holen
        self.collection = Collection(name)

        # 4) Index erstellen, falls noch nicht da
        indexes = [idx.field_name for idx in self.collection.indexes]
        if "embedding" not in indexes:
            self.collection.create_index(
                field_name="embedding",
                index_params={
                    "index_type": "IVF_FLAT",
                    "metric_type": "COSINE",
                    "params": {"nlist": 128}
                }
            )
        # 5) Collection in den Speicher laden
        self.collection.load()

        # 6) Embedding-Modell setzen
        self.embedding_model = embedding_model or self.EMBEDDING_MODEL

    def add_documents(self, chunks: List[str]) -> None:
        embs = []
        for text in chunks:
            result = ollama.embed(model=self.embedding_model, input=text)
            emb = np.array(result["embeddings"][0], dtype=np.float32).tolist()
            embs.append(emb)
        self.collection.insert([embs, chunks])
        self.collection.flush()

    def retrieve(self, query: str, top_k: int = 3) -> List[str]:
        result = ollama.embed(model=self.embedding_model, input=query)
        q_emb = np.array(result["embeddings"][0], dtype=np.float32).tolist()
        # Ensure loaded
        self.collection.load()
        search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
        res = self.collection.search(
            data=[q_emb],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            output_fields=["text"],
        )
        return [hit.entity.get("text") for hits in res for hit in hits]
