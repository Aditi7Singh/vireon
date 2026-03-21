from __future__ import annotations

import base64
from uuid import UUID

import models
from anomaly.celery_app import app as celery
from database import SessionLocal
from services.document_extraction import extract_document_content


@celery.task
def process_document_ocr(document_id: str, file_b64: str, filename: str, content_type: str):
    db = SessionLocal()
    try:
        doc = db.query(models.Document).filter(models.Document.id == UUID(document_id)).first()
        if not doc:
            return {"success": False, "message": "Document not found"}

        raw = base64.b64decode(file_b64.encode("utf-8"))
        ocr_text, extracted_data, status = extract_document_content(raw, filename, content_type)

        doc.ocr_text = ocr_text
        doc.extracted_data = extracted_data
        doc.status = status
        db.commit()
        return {"success": True, "document_id": document_id, "status": status}
    finally:
        db.close()
