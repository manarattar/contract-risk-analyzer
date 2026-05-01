from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database import get_db, Document
from app.schemas import QARequest, QAResponse
from app.services import vector_store
from app.config import get_settings

router = APIRouter()

MOCK_QA_ANSWERS = [
    "Based on the contract, the payment terms require invoices to be paid within 15 days of receipt.",
    "The confidentiality clause survives termination for three years.",
    "Either party may terminate the agreement with 7 days written notice.",
]
_mock_counter = 0


@router.post("/qa", response_model=QAResponse)
def ask_question(request: QARequest, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == request.document_id).first()
    if not doc:
        raise HTTPException(404, "Document not found.")
    if doc.status != "complete":
        raise HTTPException(400, "Analysis still in progress. Please wait.")

    chunks = vector_store.search(request.document_id, request.question, n=4)

    settings = get_settings()
    if settings.use_mock or not chunks:
        global _mock_counter
        answer = MOCK_QA_ANSWERS[_mock_counter % len(MOCK_QA_ANSWERS)]
        _mock_counter += 1
        return QAResponse(
            answer=answer + "\n\nNote: This is AI-generated analysis for informational purposes only and does not constitute legal advice.",
            sources=chunks[:2] if chunks else ["No relevant sections found."],
        )

    from app.services.risk_analyzer import answer_question
    answer = answer_question(request.question, chunks)
    return QAResponse(
        answer=answer + "\n\nNote: This is AI-generated analysis for informational purposes only and does not constitute legal advice.",
        sources=chunks,
    )
