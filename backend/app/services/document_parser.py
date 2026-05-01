import re
from pathlib import Path


def parse_pdf(path: str) -> str:
    import fitz
    doc = fitz.open(path)
    pages = [page.get_text() for page in doc]
    doc.close()
    return "\n".join(pages)


def parse_docx(path: str) -> str:
    from docx import Document
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def parse_txt(path: str) -> str:
    return Path(path).read_text(encoding="utf-8", errors="replace")


def clean_text(text: str) -> str:
    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Remove null bytes and control characters except newlines/tabs
    text = re.sub(r"[^\S\n\t ]+", " ", text)
    # Collapse 3+ blank lines into 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_text(path: str, file_type: str) -> str:
    parsers = {
        "pdf": parse_pdf,
        "docx": parse_docx,
        "txt": parse_txt,
    }
    parser = parsers.get(file_type.lower())
    if not parser:
        raise ValueError(f"Unsupported file type: {file_type}")
    raw = parser(path)
    return clean_text(raw)
