from typing import List

_client = None


def _get_client():
    import chromadb
    from chromadb.config import Settings
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path="./chroma", settings=Settings(anonymized_telemetry=False))
    return _client


def _collection_name(doc_id: str) -> str:
    # ChromaDB collection names must be 3-63 chars, alphanumeric + hyphens
    return f"doc-{doc_id.replace('_', '-')[:55]}"


def _chroma_store_chunks(doc_id: str, chunks: List[dict]) -> None:
    client = _get_client()
    from chromadb.utils import embedding_functions
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


def _chroma_search(doc_id: str, query: str, n: int = 4) -> List[str]:
    client = _get_client()
    from chromadb.utils import embedding_functions
    ef = embedding_functions.DefaultEmbeddingFunction()
    name = _collection_name(doc_id)
    try:
        collection = client.get_collection(name, embedding_function=ef)
        results = collection.query(query_texts=[query], n_results=min(n, collection.count()))
        return results["documents"][0] if results["documents"] else []
    except Exception:
        return []


class ChromaStore:
    store_chunks = staticmethod(_chroma_store_chunks)
    search = staticmethod(_chroma_search)


class AzureSearchStore:
    def __init__(self):
        from azure.core.credentials import AzureKeyCredential
        from azure.identity import DefaultAzureCredential, get_bearer_token_provider
        from azure.search.documents import SearchClient
        from app.config import get_settings
        from openai import AzureOpenAI
        settings = get_settings()
        search_credential = (AzureKeyCredential(settings.azure_search_key)
                             if settings.azure_search_key else DefaultAzureCredential())
        self.client = SearchClient(settings.azure_search_endpoint, settings.azure_search_index,
                                   credential=search_credential)
        options = {"azure_endpoint": settings.azure_openai_endpoint,
                   "api_version": settings.azure_openai_api_version}
        if settings.azure_openai_api_key:
            options["api_key"] = settings.azure_openai_api_key
        else:
            options["azure_ad_token_provider"] = get_bearer_token_provider(
                DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default")
        self.embeddings = AzureOpenAI(**options).embeddings
        self.deployment = settings.azure_openai_embedding_deployment

    def _embed(self, texts):
        return [item.embedding for item in self.embeddings.create(
            model=self.deployment, input=texts).data]

    def store_chunks(self, doc_id, chunks):
        escaped = doc_id.replace("'", "''")
        existing = self.client.search(
            search_text="*", filter=f"doc_id eq '{escaped}'", select=["id"])
        ids = [{"id": item["id"]} for item in existing]
        if ids:
            self.client.delete_documents(documents=ids)
        if not chunks:
            return
        texts = [chunk["text"] for chunk in chunks]
        vectors = self._embed(texts)
        self.client.upload_documents([{"id": f"{doc_id}-{chunk['index']}",
                                       "doc_id": doc_id, "text": chunk["text"],
                                       "content_vector": vector}
                                      for chunk, vector in zip(chunks, vectors)])

    def search(self, doc_id, query, n=4):
        from azure.search.documents.models import VectorizedQuery
        vector = self._embed([query])[0]
        escaped = doc_id.replace("'", "''")
        results = self.client.search(
            search_text=None,
            vector_queries=[VectorizedQuery(vector=vector, k_nearest_neighbors=n,
                                            fields="content_vector")],
            filter=f"doc_id eq '{escaped}'", top=n)
        return [item["text"] for item in results]


def get_vector_store():
    from app.config import get_settings
    return AzureSearchStore() if get_settings().vector_backend == "azure_search" else ChromaStore()


def store_chunks(doc_id: str, chunks: List[dict]) -> None:
    get_vector_store().store_chunks(doc_id, chunks)


def search(doc_id: str, query: str, n: int = 4) -> List[str]:
    return get_vector_store().search(doc_id, query, n)
