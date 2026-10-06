from unittest.mock import Mock

from app.services.vector_store import AzureSearchStore


def test_store_chunks_replaces_only_matching_document():
    store = AzureSearchStore.__new__(AzureSearchStore)
    store.client = Mock()
    store.client.search.return_value = [{"id": "old-1"}, {"id": "old-2"}]
    store._embed = Mock(return_value=[[0.1] * 1536])

    store.store_chunks("doc'one", [{"index": 0, "text": "replacement"}])

    store.client.search.assert_called_once_with(
        search_text="*", filter="doc_id eq 'doc''one'", select=["id"])
    store.client.delete_documents.assert_called_once_with(
        documents=[{"id": "old-1"}, {"id": "old-2"}])
    store.client.upload_documents.assert_called_once_with([{
        "id": "doc'one-0", "doc_id": "doc'one", "text": "replacement",
        "content_vector": [0.1] * 1536,
    }])
