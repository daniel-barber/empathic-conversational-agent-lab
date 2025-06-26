# reindex_all.py
import json
import pathlib
from backend.llm.document_retriever_RAG import DocumentRetriever

# 1) Initialize retriever (this will recreate the 'documents' collection)
retriever = DocumentRetriever()

# 2) Load your manifest of filenames
DATA_DIR = pathlib.Path("data")
MANIFEST_PATH = DATA_DIR / "doc_manifest.json"
existing = set(json.loads(MANIFEST_PATH.read_text()))

# 3) For each manifest file, re-add it into Milvus
DOCS_DIR = pathlib.Path("docs")
for fname in existing:
    path = DOCS_DIR / fname
    if path.exists():
        print(f"Indexing {fname}…")
        retriever.add_file(str(path))
    else:
        print(f"⚠️ File missing on disk: {fname}")
print("✅ Reindexing complete.")
