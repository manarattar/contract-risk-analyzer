import json
import subprocess
import sys
from threading import BoundedSemaphore
from pathlib import Path

from fastapi import Depends, HTTPException, Query

from app.review.auth import Principal, owned, principal
from app.review.ingestion import object_path
from app.review.routes import router
from app.review.settings import settings
from app.review.store import transaction

_render_slots = BoundedSemaphore(2)


def render_page(payload):
    try:
        result = subprocess.run([sys.executable, "-B", "-m", "app.review.page_renderer"],
                                input=json.dumps(payload), capture_output=True, text=True, encoding='utf-8',
                                cwd=Path(__file__).resolve().parents[2],
                                timeout=15, check=True)
        return json.loads(result.stdout)
    except (subprocess.SubprocessError, OSError, ValueError):
        raise HTTPException(422, "This page could not be rendered. Use the extracted text or ask the operator to check the original.")


@router.get("/documents/{document_id}/pages/{number}")
def original_page(document_id: str, number: int, block_id: str | None = None,
                  start: int = Query(0, ge=0), end: int | None = Query(None, ge=1),
                  user: Principal = Depends(principal)):
    with transaction() as conn:
        doc = owned(conn, document_id, user)
    if doc["kind"] != "pdf":
        raise HTTPException(415, "Original-page view is available for PDF only.")
    if not settings().page_rendering_enabled and doc['mode'] != 'demo':
        raise HTTPException(503, "Original-page rendering is not enabled in this workspace.")
    source = json.loads(doc["source"]) if doc["source"] else None
    if not source:
        raise HTTPException(409, "Source extraction is not ready.")
    if not 1 <= number <= source["page_count"]:
        raise HTTPException(404, "Page not found.")
    blocks = [b for b in source["blocks"] if b["page"] == number]
    block = next((b for b in blocks if b["id"] == block_id), None)
    if block_id and not block:
        raise HTTPException(404, "Evidence is not on this page.")
    quote = ""
    if block:
        end = len(block["text"]) if end is None else end
        if not start < end <= len(block["text"]):
            raise HTTPException(422, "Invalid evidence span.")
        quote = block["text"][start:end]
    if not _render_slots.acquire(blocking=False):
        raise HTTPException(503, "Page renderer is busy. Please retry.")
    try:
        result = render_page({"path": str(object_path(document_id, "pdf")), "hash": doc["hash"],
                              "page": number, "block": block, "quote": quote, "page_blocks": blocks})
        # A deletion/cancellation during rendering must prevent a late response.
        with transaction() as conn:
            current = owned(conn, document_id, user)
            if current["epoch"] != doc["epoch"] or current["hash"] != doc["hash"]:
                raise HTTPException(409, "The document changed. Reload the review.")
        return result
    finally:
        _render_slots.release()
