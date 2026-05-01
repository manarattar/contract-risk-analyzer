import re
from typing import List, Dict


# Patterns that signal the start of a new clause/section
_HEADER_PATTERNS = [
    re.compile(r"^(Article|Section|Clause)\s+\d+[\.\:]", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^\d+[\.\)]\s+[A-Z]", re.MULTILINE),
    re.compile(r"^[A-Z][A-Z\s]{4,50}$", re.MULTILINE),  # ALL CAPS SHORT HEADERS
]

MAX_CHUNK_CHARS = 1500
MIN_CHUNK_CHARS = 80


def _split_long_chunk(text: str) -> List[str]:
    """Split oversized chunks at sentence boundaries."""
    if len(text) <= MAX_CHUNK_CHARS:
        return [text]
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks, current = [], ""
    for sent in sentences:
        if len(current) + len(sent) > MAX_CHUNK_CHARS and current:
            chunks.append(current.strip())
            current = sent
        else:
            current = (current + " " + sent).strip()
    if current:
        chunks.append(current)
    return chunks or [text[:MAX_CHUNK_CHARS]]


def _strategy_headers(text: str) -> List[str]:
    """Split on recognizable section headers."""
    positions = set()
    for pattern in _HEADER_PATTERNS:
        for m in pattern.finditer(text):
            positions.add(m.start())
    if len(positions) < 2:
        return []
    positions = sorted(positions)
    chunks = []
    for i, pos in enumerate(positions):
        end = positions[i + 1] if i + 1 < len(positions) else len(text)
        chunk = text[pos:end].strip()
        if len(chunk) >= MIN_CHUNK_CHARS:
            chunks.append(chunk)
    return chunks


def _strategy_paragraphs(text: str) -> List[str]:
    """Fallback: split on double newlines, merge tiny paragraphs."""
    paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
    chunks, buffer = [], ""
    for para in paragraphs:
        buffer = (buffer + "\n\n" + para).strip()
        if len(buffer) >= MIN_CHUNK_CHARS:
            chunks.append(buffer)
            buffer = ""
    if buffer:
        chunks.append(buffer)
    return chunks


def split_into_clauses(text: str) -> List[Dict]:
    chunks = _strategy_headers(text)
    if len(chunks) < 3:
        chunks = _strategy_paragraphs(text)

    # Split any oversized chunks
    final: List[str] = []
    for chunk in chunks:
        final.extend(_split_long_chunk(chunk))

    return [{"index": i, "text": chunk} for i, chunk in enumerate(final)]
