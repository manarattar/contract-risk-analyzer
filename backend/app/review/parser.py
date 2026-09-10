"""Source-preserving bounded parser, invoked in a separate process by the worker.

A process boundary/time limit is NOT an OS sandbox. Arbitrary upload is disabled
until an operator approves actual parser isolation. No OCR or external fetching.
"""
import json
import re
import sys
import zipfile
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree as ET

PARSER_VERSION = "source-blocks-1"
NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


class ParseError(ValueError):
    pass


def parse(path, kind, max_pages=50, max_chars=150000):
    blocks, warnings, page_count, chars = [], [], None, 0

    def add(text, location, page=None, bbox=None):
        nonlocal chars
        if not text.strip():
            return
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        if any(ord(c) < 32 and c not in "\n\t" for c in text):
            raise ParseError("invalid_text_encoding")
        chars += len(text)
        if chars > max_chars:
            raise ParseError("extracted_text_limit")
        # Bounded spans without dropping short/preamble text or long sentences.
        for start in range(0, len(text), 5000):
            segment = text[start:start + 5000]
            blocks.append({"id": f"b{len(blocks) + 1}", "text": segment,
                           "location": location, "page": page, "bbox": bbox,
                           "source_offset": start})
        if len(blocks) > 1000:
            raise ParseError("block_limit")

    if kind == "txt":
        try:
            text = Path(path).read_text(encoding="utf-8-sig", errors="strict")
        except UnicodeError as exc:
            raise ParseError("invalid_text_encoding") from exc
        offset = 0
        for part in re.split(r"(\n\s*\n)", text):
            add(part, f"Text offset {offset}")
            offset += len(part)
    elif kind == "pdf":
        import pymupdf as fitz
        with fitz.open(path) as doc:
            if doc.needs_pass:
                raise ParseError("password_protected")
            page_count = len(doc)
            if page_count > max_pages:
                raise ParseError("page_limit")
            for number, page in enumerate(doc, 1):
                found = page.get_text("blocks", sort=True)
                if sum(len(b[4].strip()) for b in found if b[6] == 0) < 20:
                    warnings.append(f"Page {number} has insufficient readable text; OCR/manual verification required.")
                for item in found:
                    if item[6] == 0:
                        add(item[4], f"Page {number}", number, list(item[:4]))
            warnings.append("PDF reading order and completeness require human verification; OCR is not available.")
    elif kind == "docx":
        with zipfile.ZipFile(path) as archive:
            entries = archive.infolist()
            if len(entries) > 2000 or sum(i.file_size for i in entries) > 100 * 1024 * 1024:
                raise ParseError("archive_limit")
            names = [i.filename for i in entries]
            if len(names) != len(set(names)):
                raise ParseError("duplicate_archive_entry")
            for item in entries:
                name = item.filename
                parts = PurePosixPath(name).parts
                if ".." in parts or name.startswith(("/", "\\")) or "\\" in name or ":" in name:
                    raise ParseError("unsafe_archive_path")
                if item.file_size > 20 * 1024 * 1024 or item.file_size > max(item.compress_size, 1) * 100:
                    raise ParseError("archive_expansion_limit")
                if any(x in name.lower() for x in ("vbaproject", "embeddings/", ".zip", "activex")):
                    raise ParseError("embedded_content_not_supported")
            if "[Content_Types].xml" not in names or "word/document.xml" not in names:
                raise ParseError("invalid_docx")
            def xml(name):
                data = archive.read(name)
                if b"<!DOCTYPE" in data.upper() or b"<!ENTITY" in data.upper():
                    raise ParseError("xml_entities_not_supported")
                return ET.fromstring(data)
            for name in names:
                if name.endswith(".rels"):
                    for rel in xml(name):
                        if rel.attrib.get("TargetMode") == "External":
                            # Conservative pilot policy, including external hyperlinks.
                            raise ParseError("external_relationship_not_supported")
            source_files = ["word/document.xml"] + sorted(n for n in names if re.fullmatch(r"word/(header\d+|footer\d+|footnotes|endnotes)\.xml", n))
            for name in source_files:
                root = xml(name)
                if root.find(f".//{NS}del") is not None or root.find(f".//{NS}ins") is not None:
                    warnings.append("Tracked changes are present; verify the intended document version.")
                for index, p in enumerate(root.iter(f"{NS}p"), 1):
                    # Iteration includes paragraphs inside table cells in document order.
                    text = "".join(node.text or "" if node.tag in {f"{NS}t", f"{NS}delText"} else "\t" if node.tag == f"{NS}tab" else "\n" if node.tag == f"{NS}br" else "" for node in p.iter())
                    add(text, f"{name.removeprefix('word/')} / paragraph {index}")
            warnings.append("DOCX logical order includes table-cell paragraphs and notes; original pagination and complex table relationships are not verified.")
    else:
        raise ParseError("unsupported_format")
    if not blocks:
        raise ParseError("no_readable_text")
    partial = any("insufficient" in w or "Tracked" in w for w in warnings)
    return {"parser_version": PARSER_VERSION, "blocks": blocks, "page_count": page_count,
            "coverage": "partial" if partial else "readable", "warnings": warnings,
            "completeness": "Requires human confirmation"}


if __name__ == "__main__":
    try:
        import os
        if os.environ.get('REVIEW_SANDBOX_REQUIRED') == '1':
            from app.review.sandbox import restrict
            restrict(sys.argv[1])
        # Linux worker resource bounds supplement the no-network container.
        if sys.platform != "win32":
            import resource
            resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
            resource.setrlimit(resource.RLIMIT_CPU, (45, 45))
        print(json.dumps(parse(sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]))))
    except Exception as exc:
        # No filenames or parser stack traces are returned to the application.
        print(json.dumps({"error": str(exc) if isinstance(exc, ParseError) else "malformed_document"}))
        sys.exit(1)
