import hashlib
import re
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.review.settings import settings


def object_path(document_id: str, kind: str):
    if not re.fullmatch(r"[a-f0-9]{32}", document_id) or kind not in {"pdf", "docx", "txt"}:
        raise ValueError("Invalid storage identifier")
    root = (settings().data_dir.resolve() / "uploads").resolve()
    path = (root / f"{document_id}.{kind}").resolve()
    if path.parent != root:
        raise ValueError("Storage path escaped root")
    return path


def display_name(name):
    name = (name or "document").replace("\\", "/").split("/")[-1]
    name = re.sub(r"[\x00-\x1f\x7f<>:\"|?*]", "_", name).strip(" .")
    return name[:180] or "document"


async def receive(file: UploadFile):
    name = display_name(file.filename)
    kind = Path(name).suffix.lower().lstrip(".")
    if kind not in {"pdf", "docx", "txt"}:
        raise HTTPException(415, "Choose a PDF, DOCX or UTF-8 TXT file.")
    identifier = uuid.uuid4().hex
    path = object_path(identifier, kind)
    digest, size, prefix = hashlib.sha256(), 0, b""
    try:
        with path.open("xb") as target:
            while chunk := await file.read(65536):
                size += len(chunk)
                if size > settings().max_bytes:
                    raise HTTPException(413, "The file exceeds the 10 MiB limit.")
                prefix = (prefix + chunk)[:8]
                digest.update(chunk)
                target.write(chunk)
        if size == 0:
            raise HTTPException(422, "The file is empty.")
        if kind == "pdf" and not prefix.startswith(b"%PDF-"):
            raise HTTPException(415, "File signature does not match PDF.")
        if kind == "docx" and not prefix.startswith(b"PK\x03\x04"):
            raise HTTPException(415, "File signature does not match DOCX.")
        return identifier, kind, name, digest.hexdigest()
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    finally:
        await file.close()
