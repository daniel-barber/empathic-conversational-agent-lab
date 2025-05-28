from pymilvus import (
    connections,
    FieldSchema, CollectionSchema,
    DataType, Collection, utility
)
import numpy as np
import ollama
import os
import json
from typing import List, Optional, Dict, Any
import PyPDF2
from pathlib import Path


class DocumentRetriever:
    MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
    MILVUS_PORT = os.getenv("MILVUS_PORT", "19530")
    COLLECTION_NAME = "documents"
    EMB_DIM = 768
    EMBEDDING_MODEL = "nomic-embed-text"

    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    def __init__(
            self,
            embedding_model: Optional[str] = None,
            collection_name: Optional[str] = None,
    ) -> None:
        # 1) Ollama Client with correct URL
        self.ollama_client = ollama.Client(host=self.OLLAMA_BASE_URL)

        # 2) Connect to Milvus
        connections.connect(alias="default", host=self.MILVUS_HOST, port=self.MILVUS_PORT)

        # 3) Create collection if needed
        name = collection_name or self.COLLECTION_NAME
        if not utility.has_collection(name):
            fields = [
                FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.EMB_DIM),
                FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
                FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=1000),  # Dateiname/Quelle
                FieldSchema(name="metadata", dtype=DataType.VARCHAR, max_length=10000),  # JSON-Metadaten
            ]
            schema = CollectionSchema(fields, description="Dokumente mit Embeddings")
            Collection(name, schema)

        # 4) Collection-Objekt holen
        self.collection = Collection(name)

        # 5) Index erstellen, falls noch nicht da
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

        # 6) Collection in den Speicher laden
        self.collection.load()

        # 7) Embedding model
        self.embedding_model = embedding_model or self.EMBEDDING_MODEL

    def read_pdf(self, file_path: str) -> List[str]:
        """PDF-Datei lesen und in Chunks aufteilen"""
        chunks = []
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"

                # Text in Chunks von ~1000 Zeichen aufteilen
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
        """JSON-Datei lesen und strukturiert in Chunks umwandeln"""
        chunks = []
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)

                # Rekursive Funktion zum Durchlaufen der JSON-Struktur
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
                        # Textuelle Werte als Chunks speichern
                        if isinstance(obj, (str, int, float, bool)) and str(obj).strip():
                            chunk_text = f"{path}: {obj}"
                            if len(chunk_text) > 10:  # Nur sinnvolle Chunks
                                chunks.append(chunk_text)

                extract_text_from_json(data)

                # Zusätzlich: Gesamte JSON-Struktur als einen Chunk (falls klein genug)
                json_str = json.dumps(data, ensure_ascii=False, indent=2)
                if len(json_str) < 2000:  # Nur wenn JSON nicht zu groß
                    chunks.append(f"Vollständige JSON-Struktur:\n{json_str}")

        except Exception as e:
            print(f"Fehler beim Lesen der JSON-Datei {file_path}: {e}")

        return chunks

    def add_file(self, file_path: str) -> None:
        """Datei hinzufügen (automatische Erkennung von PDF/JSON)"""
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

        # Embeddings erstellen und hinzufügen
        self.add_documents_with_metadata(chunks, filename, {"file_type": file_extension})
        print(f"Datei {filename} erfolgreich hinzugefügt ({len(chunks)} Chunks)")

    def add_documents_with_metadata(self, chunks: List[str], source: str = "", metadata: Dict[str, Any] = None) -> None:
        """Dokumente mit Metadaten hinzufügen"""
        if not chunks:
            return

        embs = []
        sources = []
        metadata_list = []

        metadata_json = json.dumps(metadata or {}, ensure_ascii=False)

        for text in chunks:
            # Embedding erstellen
            result = self.ollama_client.embed(model=self.embedding_model, input=text)
            emb = np.array(result["embeddings"][0], dtype=np.float32).tolist()
            embs.append(emb)
            sources.append(source)
            metadata_list.append(metadata_json)

        # In Milvus einfügen
        self.collection.insert([embs, chunks, sources, metadata_list])
        self.collection.flush()

    def add_documents(self, chunks: List[str]) -> None:
        """Rückwärtskompatibilität: Dokumente ohne Metadaten hinzufügen"""
        self.add_documents_with_metadata(chunks)

    def retrieve(self, query: str, top_k: int = 3) -> List[str]:
        """Dokumente basierend auf Query abrufen"""
        # Query-Embedding erstellen
        result = self.ollama_client.embed(model=self.embedding_model, input=query)
        q_emb = np.array(result["embeddings"][0], dtype=np.float32).tolist()

        # Ensure loaded
        self.collection.load()
        search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
        results = self.collection.search(
            data=[q_emb],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            output_fields=["text", "source", "metadata"],
        )

        # Ergebnisse extrahieren
        texts = []
        for hits in results:
            for hit in hits:
                texts.append(hit.entity.get("text"))
        return texts

    def retrieve_with_metadata(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Dokumente mit Metadaten basierend auf Query abrufen"""
        # Query-Embedding erstellen
        result = self.ollama_client.embed(model=self.embedding_model, input=query)
        q_emb = np.array(result["embeddings"][0], dtype=np.float32).tolist()

        # Ensure loaded
        self.collection.load()
        search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
        results = self.collection.search(
            data=[q_emb],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            output_fields=["text", "source", "metadata"],
        )

        # Ergebnisse mit Metadaten extrahieren
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