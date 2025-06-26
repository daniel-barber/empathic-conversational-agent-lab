# scripts/preload_documents.py

import json, os, pathlib
from backend.llm.document_retriever_RAG import DocumentRetriever

DATA_DIR = pathlib.Path(__file__).parent.parent / "data"
DOCS_DIR = pathlib.Path(__file__).parent.parent / "docs"
MANIFEST_PATH = DATA_DIR / "doc_manifest.json"

def load_manifest():
    if MANIFEST_PATH.exists():
        return set(json.loads(MANIFEST_PATH.read_text()))
    return set()

def save_manifest(filenames):
    DATA_DIR.mkdir(exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(sorted(list(filenames)), ensure_ascii=False, indent=2))

def main():
    retriever = DocumentRetriever()
    seen = load_manifest()
    current = {f.name for f in DOCS_DIR.glob("*") if f.suffix.lower() in ('.pdf','.json')}
    to_add = current - seen

    for fname in to_add:
        path = DOCS_DIR / fname
        print(f"Indexing new file: {fname}")
        retriever.add_file(str(path))
    if to_add:
        print(f"Added {len(to_add)} files.")
    else:
        print("No new files to index.")
    save_manifest(current)
    print(f"Manifest updated with {len(current)} files.")

if __name__ == "__main__":
    main()
