import uuid
import os
import concurrent.futures
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.database import get_db, Comparison
from app.schemas import CompareStatusResponse, ContractComparison
from app.config import get_settings
from app.services.document_parser import extract_text
from app.services.clause_splitter import split_into_clauses
from app.services.risk_analyzer import analyze_contract
from app.services.mock_analyzer import get_mock_analysis
from app.services.comparison_service import compare_contracts

router = APIRouter()

ALLOWED_TYPES = {"pdf", "docx", "txt"}
MAX_SIZE_BYTES = 10 * 1024 * 1024
UPLOAD_DIR = Path("./data/uploads")


def _extension(filename: str) -> str:
    return Path(filename).suffix.lstrip(".").lower()


def _analyze_one(file_path: str, file_type: str):
    settings = get_settings()
    text = extract_text(file_path, file_type)
    clauses = split_into_clauses(text)
    if settings.use_mock:
        return get_mock_analysis()
    return analyze_contract(clauses, full_text=text)


def _run_comparison(
    comparison_id: str,
    path_a: str, ext_a: str,
    path_b: str, ext_b: str,
    name_a: str, name_b: str,
    db: Session,
):
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            fut_a = pool.submit(_analyze_one, path_a, ext_a)
            fut_b = pool.submit(_analyze_one, path_b, ext_b)
            analysis_a = fut_a.result()
            analysis_b = fut_b.result()

        result = compare_contracts(comparison_id, analysis_a, analysis_b, name_a, name_b)

        row = db.query(Comparison).filter(Comparison.id == comparison_id).first()
        if row:
            row.status = "complete"
            row.result_json = result.model_dump_json()
            db.commit()

    except Exception as e:
        row = db.query(Comparison).filter(Comparison.id == comparison_id).first()
        if row:
            row.status = "failed"
            row.error_message = str(e)
            db.commit()
        raise
    finally:
        for p in [path_a, path_b]:
            try:
                os.remove(p)
            except Exception:
                pass


@router.post("/compare", response_model=CompareStatusResponse)
async def start_compare(
    background_tasks: BackgroundTasks,
    file_a: UploadFile = File(...),
    file_b: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    for f in [file_a, file_b]:
        ext = _extension(f.filename or "")
        if ext not in ALLOWED_TYPES:
            raise HTTPException(400, f"Unsupported type '.{ext}'. Allowed: PDF, DOCX, TXT.")

    content_a = await file_a.read()
    content_b = await file_b.read()

    for content in [content_a, content_b]:
        if len(content) > MAX_SIZE_BYTES:
            raise HTTPException(400, "File exceeds 10 MB limit.")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    comparison_id = str(uuid.uuid4())

    ext_a = _extension(file_a.filename or "file_a.txt")
    ext_b = _extension(file_b.filename or "file_b.txt")
    path_a = str(UPLOAD_DIR / f"{comparison_id}_a_{file_a.filename}")
    path_b = str(UPLOAD_DIR / f"{comparison_id}_b_{file_b.filename}")

    with open(path_a, "wb") as f:
        f.write(content_a)
    with open(path_b, "wb") as f:
        f.write(content_b)

    row = Comparison(
        id=comparison_id,
        name_a=file_a.filename,
        name_b=file_b.filename,
        status="processing",
    )
    db.add(row)
    db.commit()

    new_db = next(get_db())
    background_tasks.add_task(
        _run_comparison,
        comparison_id, path_a, ext_a, path_b, ext_b,
        file_a.filename, file_b.filename, new_db,
    )

    return CompareStatusResponse(comparison_id=comparison_id, status="processing")


@router.get("/compare/status/{comparison_id}", response_model=CompareStatusResponse)
def get_compare_status(comparison_id: str, db: Session = Depends(get_db)):
    row = db.query(Comparison).filter(Comparison.id == comparison_id).first()
    if not row:
        raise HTTPException(404, "Comparison not found.")
    return CompareStatusResponse(
        comparison_id=row.id,
        status=row.status,
        error_message=row.error_message,
    )


@router.get("/compare/result/{comparison_id}", response_model=ContractComparison)
def get_compare_result(comparison_id: str, db: Session = Depends(get_db)):
    row = db.query(Comparison).filter(Comparison.id == comparison_id).first()
    if not row:
        raise HTTPException(404, "Comparison not found.")
    if row.status != "complete":
        raise HTTPException(400, f"Comparison is still {row.status}.")
    return ContractComparison.model_validate_json(row.result_json)
