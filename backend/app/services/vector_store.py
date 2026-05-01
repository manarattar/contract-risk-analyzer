from typing import List
import chromadb
from chromadb.utils import embedding_functions

_client: chromadb.PersistentClient = None


def _get_client() -> chromadb.PersistentClient:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path="./chroma")
    return _client


def _collection_name(doc_id: str) -> str:
    # ChromaDB collection names must be 3-63 chars, alphanumeric + hyphens
    return f"doc-{doc_id.replace('_', '-')[:55]}"


def store_chunks(doc_id: str, chunks: List[dict]) -> None:
    client = _get_client()
    ef = embedding_functions.DefaultEmbeddingFunction()
    name = _collection_name(doc_id)

    # Delete existing collection if present (re-upload scenario)
    try:
        client.delete_collection(name)
    except Exception:
        pass

    collection = client.create_collection(name, embedding_function=ef)
    texts = [c["text"] for c in chunks]
    ids = [f"{doc_id}-{c['index']}" for c in chunks]
    collection.add(documents=texts, ids=ids)


def search(doc_id: str, query: str, n: int = 4) -> List[str]:
    client = _get_client()
    ef = embedding_functions.DefaultEmbeddingFunction()
    name = _collection_name(doc_id)
    try:
        collection = client.get_collection(name, embedding_function=ef)
        results = collection.query(query_texts=[query], n_results=min(n, collection.count()))
        return results["documents"][0] if results["documents"] else []
    except Exception:
        return []
