from __future__ import annotations

import io
import json
from typing import Tuple


def extract_document_content(raw: bytes, filename: str | None, content_type: str | None) -> Tuple[str | None, dict | None, str]:
    """Returns (ocr_text, extracted_data, status)."""
    extracted_text = None
    extracted_data = None
    status = "processed"

    ctype = (content_type or "").lower()
    name = (filename or "").lower()

    try:
        if "text" in ctype or name.endswith((".txt", ".md", ".csv")):
            extracted_text = raw.decode("utf-8", errors="ignore")
        elif "json" in ctype or name.endswith(".json"):
            decoded = raw.decode("utf-8", errors="ignore")
            extracted_data = json.loads(decoded)
            extracted_text = json.dumps(extracted_data)
        elif "pdf" in ctype or name.endswith(".pdf"):
            try:
                from pypdf import PdfReader
                reader = PdfReader(io.BytesIO(raw))
                pages = [p.extract_text() or "" for p in reader.pages]
                extracted_text = "\n".join(pages).strip() or None
            except Exception:
                status = "pending"
        else:
            status = "pending"
    except Exception:
        status = "failed"

    return extracted_text, extracted_data, status
