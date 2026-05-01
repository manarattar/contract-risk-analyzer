from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db, Analysis, Document
from app.schemas import ContractAnalysis
from app.services.report_generator import generate_report

router = APIRouter()


@router.get("/report/{document_id}")
def download_report(document_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(404, "Document not found.")

    row = db.query(Analysis).filter(Analysis.document_id == document_id).first()
    if not row:
        raise HTTPException(404, "Analysis not found.")

    analysis = ContractAnalysis.model_validate_json(row.analysis_json)
    pdf_buffer = generate_report(analysis, doc.filename)

    safe_name = doc.filename.rsplit(".", 1)[0].replace(" ", "_")
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}_risk_report.pdf"'},
    )
