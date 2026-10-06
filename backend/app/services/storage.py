import re
import tempfile
from contextlib import contextmanager
from pathlib import Path
from app.config import get_settings


def sanitize_filename(name: str) -> str:
    name = (name or "file").replace("\\", "/").split("/")[-1]
    return re.sub(r"[^A-Za-z0-9._-]", "_", name).strip("._") or "file"


class LocalStorage:
    def __init__(self, root="./data/uploads"):
        self.root = Path(root)

    def save(self, name: str, content: bytes) -> str:
        self.root.mkdir(parents=True, exist_ok=True)
        ref = sanitize_filename(name)
        (self.root / ref).write_bytes(content)
        return ref

    def delete(self, ref: str) -> None:
        (self.root / sanitize_filename(ref)).unlink()

    @contextmanager
    def local_path(self, ref: str):
        yield str(self.root / sanitize_filename(ref))


class AzureBlobStorage:
    def __init__(self, settings=None):
        settings = settings or get_settings()
        from azure.identity import DefaultAzureCredential
        from azure.storage.blob import BlobServiceClient
        credential = settings.azure_storage_key or DefaultAzureCredential()
        client = BlobServiceClient(account_url=settings.azure_storage_account_url, credential=credential)
        self.container = client.get_container_client(settings.azure_storage_container)

    def save(self, name: str, content: bytes) -> str:
        ref = sanitize_filename(name)
        self.container.upload_blob(ref, content, overwrite=True)
        return ref

    def delete(self, ref: str) -> None:
        self.container.delete_blob(ref)

    @contextmanager
    def local_path(self, ref: str):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / sanitize_filename(ref)
            path.write_bytes(self.container.download_blob(ref).readall())
            yield str(path)


def get_storage():
    return AzureBlobStorage() if get_settings().storage_backend == "azure_blob" else LocalStorage()
