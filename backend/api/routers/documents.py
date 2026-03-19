from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
import schemas
import database
import auth
import models
from datetime import datetime

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/upload", response_model=schemas.Document)
def upload_document(
    company_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    """Upload a document for OCR processing (Stub)."""
    # In production, this would upload to S3 and trigger a Lambda
    db_doc = models.Document(
        company_id=company_id,
        filename=file.filename,
        file_type=file.content_type,
        status="pending"
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)
    return db_doc

@router.get("/{document_id}", response_model=schemas.Document)
def get_document(
    document_id: UUID,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    """Get document status and OCR results."""
    doc = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc
