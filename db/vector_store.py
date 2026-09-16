"""ChromaDB vector store for document memory."""

from typing import Any

from config.settings import CHROMA_DIR

COLLECTION_NAME = "document_memory"


def _get_collection():
    """Return the document-memory collection, creating it if needed."""
    import chromadb

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection(name=COLLECTION_NAME)


def store_document(doc_id: str, text: str, metadata: dict[str, Any] | None = None) -> None:
    """Store document text in ChromaDB for later retrieval."""
    if not text.strip():
        return
    try:
        collection = _get_collection()
        meta = metadata or {}
        # Chroma metadata values must be scalars
        clean_meta = {k: (v if isinstance(v, (str, int, float, bool)) else str(v)) for k, v in meta.items()}
        collection.upsert(
            ids=[doc_id],
            documents=[text[:8000]],
            metadatas=[clean_meta] if clean_meta else None,
        )
    except Exception:
        pass


def query_documents(query: str, n_results: int = 5) -> list[dict[str, Any]]:
    """Query document memory by text similarity."""
    try:
        collection = _get_collection()
        result = collection.query(query_texts=[query], n_results=n_results)
        hits: list[dict[str, Any]] = []
        ids = (result.get("ids") or [[]])[0]
        docs = (result.get("documents") or [[]])[0]
        metas = (result.get("metadatas") or [[]])[0]
        for i, doc_id in enumerate(ids):
            hits.append({
                "id": doc_id,
                "text": docs[i] if i < len(docs) else "",
                "metadata": metas[i] if i < len(metas) else {},
            })
        return hits
    except Exception:
        return []
