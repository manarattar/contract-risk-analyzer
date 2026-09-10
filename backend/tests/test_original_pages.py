import hashlib
import json

import pymupdf as fitz
import pytest

from .test_review_v2 import client, auth, sample  # noqa: F401 — shared synthetic fixture
from app.review.ingestion import object_path
from app.review.parser import parse
from app.review.page_renderer import render
from app.review.settings import settings
from app.review.store import transaction


def pdf_review(client, monkeypatch, rotation=0):
    monkeypatch.setenv("REVIEW_PAGE_RENDERING_ENABLED", "true")
    monkeypatch.setenv("REVIEW_PARSER_ISOLATION_APPROVED", "true")
    settings.cache_clear()
    identifier = sample(client)
    path = object_path(identifier, "pdf")
    with fitz.open() as pdf:
        page = pdf.new_page(width=600, height=800)
        page.insert_text((60, 90), "Synthetic payment is due within thirty days.")
        page.set_rotation(rotation)
        pdf.new_page(width=600, height=800)  # Image-only/blank page must remain visible.
        pdf.save(path)
    source = parse(path, "pdf")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    with transaction() as conn:
        conn.execute("UPDATE documents SET kind='pdf',hash=?,source=?,status='partial',mode='manual' WHERE id=?",
                     (digest, json.dumps(source), identifier))
    return identifier, path, source, digest


@pytest.mark.parametrize("rotation", [0, 90, 180, 270])
def test_quote_coordinates_and_bounded_raster(client, monkeypatch, rotation):
    identifier, path, source, digest = pdf_review(client, monkeypatch, rotation)
    result = render({"path": str(path), "hash": digest, "page": 1,
                     "block": source["blocks"][0], "quote": "within thirty days"})
    assert result["image"].startswith("data:image/png;base64,")
    assert max(result["width"], result["height"]) <= 1401
    assert result["match"] == "quote"
    assert result["rectangles"]
    for x, y, width, height in result["rectangles"]:
        assert 0 <= x < x + width <= 1.001 and 0 <= y < y + height <= 1.001
    fallback = render({"path": str(path), "hash": digest, "page": 1,
                       "block": source["blocks"][0], "quote": "not present"})
    assert fallback["match"] == "block"


def test_page_endpoint_access_bounds_and_deletion(client, monkeypatch):
    identifier, _, source, _ = pdf_review(client, monkeypatch)
    url = f"/api/v2/documents/{identifier}/pages/1"
    assert client.get(url).status_code == 401
    assert client.get(url, headers=auth("bob")).status_code == 404
    assert client.get(url+"?block_id=foreign", headers=auth()).status_code == 404
    assert client.get(url+"?block_id=b1&start=999&end=1000", headers=auth()).status_code == 422
    assert client.get(url.replace('/pages/1','/pages/3'), headers=auth()).status_code == 404
    response = client.get(url+"?block_id=b1", headers=auth())
    assert response.status_code == 200, response.text
    assert response.headers['cache-control'] == 'no-store'
    assert response.json()['blocks'][0]['text'] == source['blocks'][0]['text']
    response = client.get(url.replace('/pages/1','/pages/2'), headers=auth())
    assert response.status_code == 200 and response.json()['blocks'] == []
    assert client.delete(f"/api/v2/documents/{identifier}", headers=auth()).status_code == 202
    assert client.get(url, headers=auth()).status_code == 404


def test_late_render_cannot_return_deleted_source(client, monkeypatch):
    from app.review import pages
    from app.review.jobs import tombstone
    identifier, _, _, _ = pdf_review(client, monkeypatch)
    def deleted_during_render(payload):
        with transaction() as conn:
            row = dict(conn.execute('SELECT * FROM documents WHERE id=?',(identifier,)).fetchone())
            tombstone(conn, row)
        return {"image": "synthetic"}
    monkeypatch.setattr(pages, 'render_page', deleted_during_render)
    assert client.get(f'/api/v2/documents/{identifier}/pages/1',headers=auth()).status_code == 404


def test_renderer_checks_integrity_and_gate(client, monkeypatch):
    identifier, path, _, digest = pdf_review(client, monkeypatch)
    path.write_bytes(b'%PDF- changed synthetic file')
    with pytest.raises(ValueError, match='source_changed'):
        render({"path": str(path), "hash": digest, "page": 1})
    monkeypatch.setenv('REVIEW_PAGE_RENDERING_ENABLED','false'); settings.cache_clear()
    assert client.get(f'/api/v2/documents/{identifier}/pages/1',headers=auth()).status_code == 503
