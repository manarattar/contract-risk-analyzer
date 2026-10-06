from unittest.mock import patch
from pathlib import Path

from app.config import Settings
from app.services.storage import LocalStorage, sanitize_filename
from app.services import vector_store
from app.services.llm_client import get_llm_client
from app.database import make_engine


def test_defaults(monkeypatch):
    for key in ("DATABASE_URL", "STORAGE_BACKEND", "VECTOR_BACKEND", "LLM_PROVIDER"):
        monkeypatch.delenv(key, raising=False)
    settings = Settings(_env_file=None)
    assert (settings.database_url, settings.storage_backend, settings.vector_backend,
            settings.llm_provider) == ("sqlite:///./data/contracts.db", "local", "chroma", "openai")


def test_filename_and_local_storage(tmp_path):
    assert sanitize_filename(r"..\folder\unsafe name?.pdf") == "unsafe_name_.pdf"
    storage = LocalStorage(tmp_path)
    ref = storage.save(r"..\folder\contract.txt", b"hello")
    with storage.local_path(ref) as path:
        assert Path(path).read_bytes() == b"hello"


def test_database_urls():
    with patch("app.database.create_engine") as create:
        make_engine("sqlite:///sample.db")
        assert create.call_args.kwargs["connect_args"] == {"check_same_thread": False}
        make_engine("postgresql+psycopg://host/db")
        assert "connect_args" not in create.call_args.kwargs


def test_llm_factory():
    with patch("app.services.llm_client.get_settings", return_value=Settings(_env_file=None)), \
         patch("app.services.llm_client.OpenAI") as openai:
        get_llm_client()
        openai.assert_called_once()
    settings = Settings(_env_file=None, llm_provider="azure_openai", azure_openai_api_key="key")
    with patch("app.services.llm_client.get_settings", return_value=settings), \
         patch("app.services.llm_client.AzureOpenAI") as azure:
        get_llm_client()
        azure.assert_called_once()


def test_vector_factory():
    with patch("app.config.get_settings", return_value=Settings(_env_file=None)):
        assert isinstance(vector_store.get_vector_store(), vector_store.ChromaStore)
    settings = Settings(_env_file=None, vector_backend="azure_search")
    with patch("app.config.get_settings", return_value=settings), \
         patch.object(vector_store, "AzureSearchStore") as azure:
        vector_store.get_vector_store()
        azure.assert_called_once()


def test_local_storage_delete(tmp_path):
    storage = LocalStorage(tmp_path)
    ref = storage.save("contract.txt", b"hello")
    storage.delete(ref)
    assert not (tmp_path / ref).exists()
