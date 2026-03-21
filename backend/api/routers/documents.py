from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
import base64
import os
import schemas
import database
import auth
import models
from services.document_extraction import extract_document_content
from tasks.document_tasks import process_document_ocr

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/upload", response_model=schemas.Document)
def upload_document(
    company_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    """Upload a document and run basic local text extraction.

    This is a production-safe baseline (no external OCR dependency required).
    """
    raw = file.file.read()
    async_mode = os.getenv("OCR_ASYNC", "false").lower() == "true"

    extracted_text = None
    extracted_data = None
    status = "pending" if async_mode else "processed"
    if not async_mode:
        extracted_text, extracted_data, status = extract_document_content(raw, file.filename, file.content_type)

    db_doc = models.Document(
        company_id=company_id,
        file_name=file.filename,
        file_type=file.content_type,
        status=status,
        ocr_text=extracted_text,
        extracted_data=extracted_data,
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)

    if async_mode:
        process_document_ocr.delay(
            str(db_doc.id),
            base64.b64encode(raw).decode("utf-8"),
            file.filename or "uploaded_file",
            file.content_type or "application/octet-stream",
        )

    return db_doc


@router.post("/{document_id}/reprocess", response_model=schemas.DocumentWriteResponse)
def reprocess_document(
    document_id: UUID,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user),
):
    doc = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    doc.status = "pending"
    db.commit()
    return {"success": True, "message": "Document marked for reprocessing", "document_id": str(document_id)}

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
