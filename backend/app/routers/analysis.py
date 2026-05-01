import json
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database import get_db, Analysis
from app.schemas import ContractAnalysis

router = APIRouter()


@router.get("/analysis/{document_id}", response_model=ContractAnalysis)
def get_analysis(document_id: str, db: Session = Depends(get_db)):
    row = db.query(Analysis).filter(Analysis.document_id == document_id).first()
    if not row:
        raise HTTPException(404, "Analysis not found. Document may still be processing.")
    return ContractAnalysis.model_validate_json(row.analysis_json)
