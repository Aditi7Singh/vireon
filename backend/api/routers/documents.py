from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
import base64
import os
from pydantic import BaseModel
from typing import Optional
import schemas
import database
import auth
import models
from services.document_extraction import extract_document_content, classify_document
from tasks.document_tasks import process_document_ocr

router = APIRouter(prefix="/documents", tags=["documents"])


class DocumentWorkflowAction(BaseModel):
    action: str
    note: Optional[str] = None

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
    
    # Save to storage (Mock cloud storage)
    from services.storage_service import storage
    storage_path = storage.save_file(raw, file.filename)

    extracted_text = None
    extracted_data = None
    structured_data = None
    status = "pending" if async_mode else "processed"
    if not async_mode:
        extracted_text, extracted_data, structured_data, status = extract_document_content(raw, file.filename, file.content_type)

    db_doc = models.Document(
        company_id=company_id,
        file_name=file.filename,
        file_type=file.content_type,
        status=status,
        ocr_text=extracted_text,
        extracted_data=extracted_data,
        structured_data=structured_data,
        # In a real app, we'd add a 'storage_path' column to Document model. 
        # For this prototype, we'll store it in extracted_data metadata if needed.
    )
    if not db_doc.extracted_data:
        db_doc.extracted_data = {}
    db_doc.extracted_data["storage_path"] = storage_path
    
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


@router.post("/{document_id}/classify", response_model=schemas.DocumentWriteResponse)
def classify_uploaded_document(
    document_id: UUID,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user),
):
    doc = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    classification = classify_document(doc.ocr_text, doc.file_name, doc.file_type)
    if not doc.extracted_data:
        doc.extracted_data = {}
    doc.extracted_data["classification"] = classification
    db.commit()
    return {
        "success": True,
        "message": f"Classified as {classification.get('document_type', 'unclassified')}",
        "document_id": str(document_id),
    }


@router.post("/{document_id}/workflow", response_model=schemas.DocumentWriteResponse)
def document_workflow_action(
    document_id: UUID,
    payload: DocumentWorkflowAction,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user),
):
    """Execute document workflow actions: approve, reject, post_ledger."""
    doc = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    action = (payload.action or "").strip().lower()
    if action not in {"approve", "reject", "post_ledger"}:
        raise HTTPException(status_code=400, detail="Unsupported action. Use approve|reject|post_ledger")

    if not doc.structured_data:
        doc.structured_data = {}
    workflow = doc.structured_data.get("workflow", {})
    workflow.update(
        {
            "last_action": action,
            "note": payload.note,
            "acted_by": getattr(current_user, "username", "system"),
        }
    )
    doc.structured_data["workflow"] = workflow

    if action == "approve":
        doc.status = "completed"
    elif action == "reject":
        doc.status = "failed"
    elif action == "post_ledger":
        doc.status = "completed"

    db.commit()
    return {
        "success": True,
        "message": f"Workflow action '{action}' applied",
        "document_id": str(document_id),
    }
