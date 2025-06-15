from pymilvus import (
    connections,
    FieldSchema, CollectionSchema,
    DataType, Collection, utility
)
import numpy as np
import os
import json
from typing import List, Optional, Dict, Any
import PyPDF2
from pathlib import Path
from sentence_transformers import SentenceTransformer


class DocumentRetriever:
    MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
    MILVUS_PORT = os.getenv("MILVUS_PORT", "19530")
    COLLECTION_NAME = "documents"
    EMB_DIM = 384
    EMBEDDING_MODEL = "intfloat/e5-small-v2"

    def __init__(
            self,
            embedding_model: Optional[str] = None,
            collection_name: Optional[str] = None,
    ) -> None:
        # 1) SentenceTransformer
        self.model = SentenceTransformer(embedding_model or self.EMBEDDING_MODEL)

        # 2) Connect to Milvus
        connections.connect(alias="default", host=self.MILVUS_HOST, port=self.MILVUS_PORT)

        # 3) Create collection if needed
        name = collection_name or self.COLLECTION_NAME
        if not utility.has_collection(name):
            fields = [
                FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.EMB_DIM),
                FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
                FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=1000),
                FieldSchema(name="metadata", dtype=DataType.VARCHAR, max_length=10000),
            ]
            schema = CollectionSchema(fields, description="Dokumente mit Embeddings")
            Collection(name, schema)

        self.collection = Collection(name)

        # 4) Create Index, if not already there
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

        self.collection.load()

    def read_pdf(self, file_path: str) -> List[str]:
        chunks = []
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                chunk_size = 1000
                overlap = 200
                for i in range(0, len(text), chunk_size - overlap):
                    chunk = text[i:i + chunk_size].strip()
                    if chunk:
                        chunks.append(chunk)
        except Exception as e:
            print(f"Fehler beim Lesen der PDF-Datei {file_path}: {e}")
        return chunks

    def read_json(self, file_path: str) -> List[str]:
        chunks = []
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)

                def extract_text_from_json(obj, path=""):
                    if isinstance(obj, dict):
                        for key, value in obj.items():
                            new_path = f"{path}.{key}" if path else key
                            extract_text_from_json(value, new_path)
                    elif isinstance(obj, list):
                        for i, item in enumerate(obj):
                            new_path = f"{path}[{i}]"
                            extract_text_from_json(item, new_path)
                    else:
                        if isinstance(obj, (str, int, float, bool)) and str(obj).strip():
                            chunk_text = f"{path}: {obj}"
                            if len(chunk_text) > 10:
                                chunks.append(chunk_text)

                extract_text_from_json(data)

                json_str = json.dumps(data, ensure_ascii=False, indent=2)
                if len(json_str) < 2000:
                    chunks.append(f"Vollständige JSON-Struktur:\n{json_str}")
        except Exception as e:
            print(f"Fehler beim Lesen der JSON-Datei {file_path}: {e}")
        return chunks

    def add_file(self, file_path: str) -> None:
        file_path = Path(file_path)
        if not file_path.exists():
            print(f"Datei nicht gefunden: {file_path}")
            return
        file_extension = file_path.suffix.lower()
        filename = file_path.name
        chunks = []
        if file_extension == '.pdf':
            chunks = self.read_pdf(str(file_path))
        elif file_extension == '.json':
            chunks = self.read_json(str(file_path))
        else:
            print(f"Nicht unterstütztes Dateiformat: {file_extension}")
            return
        if not chunks:
            print(f"Keine Inhalte in Datei gefunden: {filename}")
            return
        self.add_documents_with_metadata(chunks, filename, {"file_type": file_extension})
        print(f"Datei {filename} erfolgreich hinzugefügt ({len(chunks)} Chunks)")

    def add_documents_with_metadata(self, chunks: List[str], source: str = "", metadata: Dict[str, Any] = None) -> None:
        if not chunks:
            return
        embs = self.model.encode(chunks, convert_to_numpy=True).tolist()
        metadata_json = json.dumps(metadata or {}, ensure_ascii=False)
        data = [
            {
                "text": chunk,
                "embedding": emb,
                "source": source,
                "metadata": metadata_json
            }
            for chunk, emb in zip(chunks, embs)
        ]

        self.collection.insert(data)
        self.collection.flush()

    def add_documents(self, chunks: List[str]) -> None:
        self.add_documents_with_metadata(chunks)

    def retrieve(self, query: str, top_k: int = 3) -> List[str]:
        q_emb = self.model.encode([query], convert_to_numpy=True).tolist()
        self.collection.load()
        search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
        results = self.collection.search(
            data=q_emb,
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            output_fields=["text", "source", "metadata"],
        )
        texts = []
        for hits in results:
            for hit in hits:
                texts.append(hit.entity.get("text"))
        return texts

    def retrieve_with_metadata(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        q_emb = self.model.encode([query], convert_to_numpy=True).tolist()
        self.collection.load()
        search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
        results = self.collection.search(
            data=q_emb,
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            output_fields=["text", "source", "metadata"],
        )
        documents = []
        for hits in results:
            for hit in hits:
                doc = {
                    "text": hit.entity.get("text"),
                    "source": hit.entity.get("source"),
                    "score": hit.score,
                    "metadata": json.loads(hit.entity.get("metadata", "{}"))
                }
                documents.append(doc)
        return documents
