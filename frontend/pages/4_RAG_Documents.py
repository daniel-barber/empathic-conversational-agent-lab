import streamlit as st
import pathlib, json
from pymilvus import utility, connections
from backend.llm.document_retriever_RAG import DocumentRetriever

st.set_page_config("🛠️ RAG Documents")

# Admin Page Logic
if "is_admin" not in st.session_state:
    pwd = st.sidebar.text_input(
        "🔐 Admin password",
        type="password",
        key="admin_pwd_input"
    )
    if pwd == st.secrets["ADMIN_PASS"]:
        st.session_state.is_admin = True
        del st.session_state["admin_pwd_input"]
        st.rerun()

if not st.session_state.get("is_admin", False):
    st.sidebar.error("Enter admin password to view this page.")
    st.stop()

# — config
st.set_page_config(page_title="RAG Documents", page_icon="📚")
DATA_DIR = pathlib.Path("data")
DOCS_DIR = pathlib.Path("docs")
MANIFEST_PATH = DATA_DIR / "doc_manifest.json"

# — manifest helpers
def load_manifest():
    if MANIFEST_PATH.exists():
        try:
            return set(json.loads(MANIFEST_PATH.read_text()))
        except json.JSONDecodeError:
            st.error("Fehler: Manifest-Datei konnte nicht geparst werden.")
    return set()

def save_manifest(filenames):
    DATA_DIR.mkdir(exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(sorted(list(filenames)), ensure_ascii=False, indent=2))

# — init
retriever = DocumentRetriever()
existing = load_manifest()

if not MANIFEST_PATH.exists():
    save_manifest(existing)

st.title("📚 RAG – Indexed Documents")

# — REINDEX BUTTON —
st.subheader("🔄 Reindex All Documents")
if st.button("Reindex all"):
    # 1) drop the Milvus collection
    connections.connect(alias="default",
                        host=DocumentRetriever.MILVUS_HOST,
                        port=DocumentRetriever.MILVUS_PORT)
    if utility.has_collection(DocumentRetriever.COLLECTION_NAME):
        utility.drop_collection(DocumentRetriever.COLLECTION_NAME)

    # 2) recreate retriever (it will recreate the collection)
    retriever = DocumentRetriever()

    # 3) re-add every file from your manifest
    DOCS_DIR = pathlib.Path("docs")
    for fname in sorted(existing):
        path = DOCS_DIR / fname
        if path.exists():
            with st.spinner(f"Indexiere {fname} neu…"):
                retriever.add_file(str(path))
        else:
            st.warning(f"Datei nicht gefunden: {fname}")
    st.success("✅ Alle Dokumente wurden neu indiziert.")
    st.rerun()


# — UPLOAD NEW FILES
# … keep your imports and initialization above …

# Use a counter in session_state to generate a fresh key for the uploader
if "upload_ctr" not in st.session_state:
    st.session_state.upload_ctr = 0

# Build a dynamic key
UPLOAD_KEY = f"rag_upload_files_{st.session_state.upload_ctr}"

st.subheader("📥 Dokument hochladen")
uploaded = st.file_uploader(
    "PDFs oder JSONs hier ablegen (einzeln oder mehrfach)",
    type=["pdf", "json"],
    accept_multiple_files=True,
    key=UPLOAD_KEY,
)


# Track whether we indexed anything new this run
any_added = False

if uploaded:
    for up in uploaded:
        st.write(f"📥 Processing upload: {up.name}")
        if up.name in existing:
            st.warning(f"⏭️ {up.name} ist bereits indiziert.")
            continue

        # 1) Save to disk
        try:
            DOCS_DIR.mkdir(parents=True, exist_ok=True)
            with st.spinner(f"Speichere {up.name} …"):
                with open(DOCS_DIR / up.name, "wb") as f:
                    f.write(up.getbuffer())
            st.success(f"✅ {up.name} gespeichert.")
        except Exception as e:
            st.error(f"❌ Fehler beim Speichern von {up.name}: {e}")
            continue

        # 2) Index into Milvus
        try:
            with st.spinner(f"Indexiere {up.name} …"):
                retriever.add_file(str(DOCS_DIR / up.name))
            st.success(f"✅ {up.name} erfolgreich indiziert.")
            existing.add(up.name)
            save_manifest(existing)
            any_added = True
        except Exception as e:
            st.error(f"❌ Fehler beim Indizieren von {up.name}: {e}")

    # Only rerun if we actually indexed something new
    if any_added:
        st.session_state.upload_ctr += 1
        st.rerun()
    else:
        st.info("⚠️ Keine neuen Dokumente indiziert. Liste bleibt unverändert.")



# — SHOW & DELETE
st.subheader("🗂️ Indizierte Dokumente")
if not existing:
    st.info("Noch keine Dokumente indiziert.")
else:
    for fname in sorted(existing):
        col1, col2 = st.columns([0.8, 0.2])
        col1.write(f"**{fname}**")
        if col2.button("🗑️ Delete", key=f"del_{fname}"):
            # 1) delete file on disk
            fp = DOCS_DIR / fname
            if fp.exists(): fp.unlink()

            # 2) delete vectors from Milvus
            expr = f"source == '{fname}'"
            retriever.collection.delete(expr)
            retriever.collection.flush()

            # 3) update manifest
            existing.remove(fname)
            save_manifest(existing)

            st.success(f"🗑️ {fname} gelöscht.")
            st.rerun()
