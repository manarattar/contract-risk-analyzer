import uuid
from pathlib import Path
from app.services.storage import get_storage, sanitize_filename

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
from app.telemetry import span

router = APIRouter()

ALLOWED_TYPES = {"pdf", "docx", "txt"}
MAX_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
UPLOAD_DIR = Path("./data/uploads")


def _extension(filename: str) -> str:
    return Path(filename).suffix.lstrip(".").lower()


def _run_analysis(doc_id: str, file_path: str, file_type: str, db: Session):
    """Background task: parse → split → analyze → store."""
    try:
        with span("pipeline.upload", document_id=doc_id, file_type=file_type):
            _process_analysis(doc_id, file_path, file_type, db)
    except Exception as e:
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if doc:
            doc.status = "failed"
            doc.error_message = str(e)
            db.commit()
        raise


def _process_analysis(doc_id: str, file_path: str, file_type: str, db: Session):
    with span("pipeline.parse", document_id=doc_id, file_type=file_type):
        with get_storage().local_path(file_path) as path:
            text = extract_text(path, file_type)
    with span("pipeline.split", document_id=doc_id) as split_span:
        clauses = split_into_clauses(text)
        split_span.set_attribute("clause_count", len(clauses))

    settings = get_settings()
    with span("pipeline.analyse", document_id=doc_id, clause_count=len(clauses)) as analysis_span:
        if settings.use_mock:
            analysis = get_mock_analysis()
        else:
            analysis = analyze_contract(clauses, full_text=text)
        analysis_span.set_attribute("overall_score", analysis.overall_risk_score)
        analysis_span.set_attribute("risk_level", analysis.overall_risk_level.value)

    with span("pipeline.embed_index", document_id=doc_id, clause_count=len(clauses),
              vector_backend=settings.vector_backend):
        vector_store.store_chunks(doc_id, clauses)

    analysis_row = Analysis(document_id=doc_id, analysis_json=analysis.model_dump_json())
    db.add(analysis_row)

    doc = db.query(Document).filter(Document.id == doc_id).first()
    if doc:
        doc.status = "complete"
    db.commit()


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

    doc_id = str(uuid.uuid4())
    safe_name = f"{doc_id}_{sanitize_filename(file.filename)}"
    file_path = get_storage().save(safe_name, content)

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
