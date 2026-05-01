import uuid
import os
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.database import get_db, Document, Analysis
from app.schemas import UploadResponse, StatusResponse
from app.config import get_settings
from app.services.document_parser import extract_text
from app.services.clause_splitter import split_into_clauses
from app.services import vector_store
from app.services.mock_analyzer import get_mock_analysis
from app.services.risk_analyzer import analyze_contract

router = APIRouter()

ALLOWED_TYPES = {"pdf", "docx", "txt"}
MAX_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
UPLOAD_DIR = Path("./data/uploads")


def _extension(filename: str) -> str:
    return Path(filename).suffix.lstrip(".").lower()


def _run_analysis(doc_id: str, file_path: str, file_type: str, db: Session):
    """Background task: parse → split → analyze → store."""
    try:
        text = extract_text(file_path, file_type)
        clauses = split_into_clauses(text)

        settings = get_settings()
        if settings.use_mock:
            analysis = get_mock_analysis()
        else:
            analysis = analyze_contract(clauses, full_text=text)

        # Store chunks in vector DB
        vector_store.store_chunks(doc_id, clauses)

        # Persist analysis to SQLite
        import json
        analysis_row = Analysis(
            document_id=doc_id,
            analysis_json=analysis.model_dump_json(),
        )
        db.add(analysis_row)

        doc = db.query(Document).filter(Document.id == doc_id).first()
        if doc:
            doc.status = "complete"
        db.commit()

    except Exception as e:
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if doc:
            doc.status = "failed"
            doc.error_message = str(e)
            db.commit()
        raise


@router.post("/upload", response_model=UploadResponse)
async def upload_contract(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    ext = _extension(file.filename or "")
    if ext not in ALLOWED_TYPES:
        raise HTTPException(400, f"Unsupported file type '.{ext}'. Allowed: PDF, DOCX, TXT.")

    content = await file.read()
    if len(content) > MAX_SIZE_BYTES:
        raise HTTPException(400, "File exceeds 10 MB limit.")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    doc_id = str(uuid.uuid4())
    safe_name = f"{doc_id}_{file.filename}"
    file_path = str(UPLOAD_DIR / safe_name)

    with open(file_path, "wb") as f:
        f.write(content)

    doc = Document(id=doc_id, filename=file.filename, file_type=ext, status="processing")
    db.add(doc)
    db.commit()

    # Run analysis in background; pass a new db session
    new_db = next(get_db())
    background_tasks.add_task(_run_analysis, doc_id, file_path, ext, new_db)

    return UploadResponse(document_id=doc_id, status="processing", filename=file.filename)


@router.get("/status/{document_id}", response_model=StatusResponse)
def get_status(document_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(404, "Document not found.")
    return StatusResponse(
        document_id=doc.id,
        status=doc.status,
        error_message=doc.error_message,
    )
