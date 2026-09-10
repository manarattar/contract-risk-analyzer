"""Bounded PDF rasterization. Run in a subprocess; not a replacement for OS isolation."""
import base64
import hashlib
import json
from pathlib import Path
import sys


def render(payload):
    import pymupdf as fitz
    path = Path(payload["path"])
    if path.stat().st_size > 10 * 1024 * 1024:
        raise ValueError("size")
    if hashlib.sha256(path.read_bytes()).hexdigest() != payload["hash"]:
        raise ValueError("source_changed")
    with fitz.open(path) as document:
        if document.needs_pass or not 1 <= len(document) <= 50:
            raise ValueError("unsupported_pdf")
        page = document[payload["page"] - 1]
        bounds = page.rect
        if bounds.width <= 0 or bounds.height <= 0:
            raise ValueError("invalid_page")
        scale = min(2, 1400 / max(bounds.width, bounds.height))
        pixmap = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False, annots=True)
        image = pixmap.tobytes("png")
        if len(image) > 8 * 1024 * 1024:
            raise ValueError("image_limit")
        rectangles, match = [], "none"
        block = payload.get("block")
        if block:
            clip = fitz.Rect(block["bbox"])
            quote = payload.get("quote", "")
            # Never pretend an ambiguous occurrence is an exact location.
            text = " ".join(page.get_textbox(clip).split())
            normalized = " ".join(quote.split())
            hits = page.search_for(quote, clip=clip) if normalized and text.count(normalized) == 1 else []
            rectangles, match = (hits, "quote") if hits else ([clip], "block")
        normalized_rects = []
        for rect in rectangles:
            rect = (rect * page.rotation_matrix) & bounds
            if not rect.is_empty:
                normalized_rects.append([(rect.x0-bounds.x0)/bounds.width, (rect.y0-bounds.y0)/bounds.height,
                                         rect.width/bounds.width, rect.height/bounds.height])
        return {"page": payload["page"], "page_count": len(document), "width": pixmap.width,
                "height": pixmap.height, "image": "data:image/png;base64," + base64.b64encode(image).decode(),
                "rectangles": normalized_rects, "match": match,
                "blocks": payload.get("page_blocks", [])}


if __name__ == "__main__":
    try:
        if sys.platform != "win32":
            import resource
            resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
            resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
        payload = json.load(sys.stdin)
        import os
        if os.environ.get('REVIEW_SANDBOX_REQUIRED') == '1':
            from app.review.sandbox import restrict
            restrict(payload['path'])
        print(json.dumps(render(payload)))
    except Exception:
        print(json.dumps({"error": "page_unavailable"}))
        sys.exit(1)
