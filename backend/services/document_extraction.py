from __future__ import annotations

import io
import json
from typing import Tuple
import os


import re


def _extract_with_textract(raw: bytes) -> str | None:
    """Optional OCR provider path using AWS Textract.

    Enabled when OCR_PROVIDER=textract and boto3 credentials are configured.
    """
    try:
        import boto3

        client = boto3.client("textract", region_name=os.getenv("AWS_REGION", "us-east-1"))
        response = client.detect_document_text(Document={"Bytes": raw})
        lines = []
        for block in response.get("Blocks", []):
            if block.get("BlockType") == "LINE" and block.get("Text"):
                lines.append(block["Text"])
        return "\n".join(lines).strip() or None
    except Exception:
        return None

def _map_fields_regex(text: str) -> dict:
    """Simulate structured field mapping using heuristics and regex."""
    data = {
        "merchant_name": None,
        "date": None,
        "total_amount": 0.0,
        "tax_amount": 0.0,
        "currency": "INR",
        "confidence": 0.0
    }
    
    # 1. Merchant Heuristic (usually first line or near it)
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if lines:
        data["merchant_name"] = lines[0][:50]
        data["confidence"] += 0.2
        
    # 2. Date Heuristic
    date_match = re.search(r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", text)
    if date_match:
        data["date"] = date_match.group(1)
        data["confidence"] += 0.3
        
    # 3. Amount Heuristic (finding the largest currency-looking number)
    amounts = re.findall(r"(?:INR|Rs\.?|\$|Total|Due)[:\s]*([\d,]+\.?\d*)", text, re.I)
    if amounts:
        numeric_amounts = []
        for a in amounts:
            try:
                numeric_amounts.append(float(a.replace(",", "")))
            except ValueError:
                continue
        if numeric_amounts:
            data["total_amount"] = max(numeric_amounts)
            data["confidence"] += 0.4

    return data


def classify_document(text: str | None, filename: str | None, content_type: str | None) -> dict:
    """Classify uploaded document into accounting workflow buckets."""
    name = (filename or "").lower()
    ctype = (content_type or "").lower()
    raw = (text or "").lower()

    if "invoice" in raw or "bill to" in raw or "tax invoice" in raw or "invoice" in name:
        return {"document_type": "invoice", "workflow": "ap_ar_review", "confidence": 0.85}
    if "receipt" in raw or "card payment" in raw or "receipt" in name:
        return {"document_type": "receipt", "workflow": "expense_review", "confidence": 0.8}
    if "statement" in raw or "account summary" in raw or "bank" in name:
        return {"document_type": "bank_statement", "workflow": "bank_reconciliation", "confidence": 0.75}
    if "payroll" in raw or "salary" in raw:
        return {"document_type": "payroll", "workflow": "payroll_review", "confidence": 0.7}
    if "pdf" in ctype:
        return {"document_type": "unclassified_pdf", "workflow": "manual_review", "confidence": 0.5}
    return {"document_type": "unclassified", "workflow": "manual_review", "confidence": 0.4}


def extract_structured_fields(text: str) -> dict | None:
    """Use AI to extract high-fidelity structured data from OCR text."""
    from config.settings import get_llm
    from langchain_core.messages import SystemMessage, HumanMessage
    
    llm = get_llm(thinking=False)
    
    prompt = """
    Extract structured financial data from the following OCR text of a receipt or invoice.
    Return ONLY a JSON object with these keys:
    - merchant_name: string
    - date: string (YYYY-MM-DD or best effort)
    - total_amount: number
    - tax_amount: number
    - currency: string (3-letter code)
    - category: string (one of: Software, Travel, Food, Marketing, Office, Payroll, Other)
    
    If a value is missing, use null.
    
    OCR TEXT:
    {text}
    """
    
    for _ in range(2):
        try:
            messages = [
                SystemMessage(content="You are a financial data extraction expert. Return only valid JSON."),
                HumanMessage(content=prompt.format(text=text))
            ]
            response = llm.invoke(messages)

            # Parse JSON from response
            content = response.content
            if isinstance(content, list):
                content = "\n".join(str(x) for x in content)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            return json.loads(content.strip())
        except Exception as e:
            print(f"[EXTRACT] AI extraction failed: {e}")
    return None

def extract_document_content(raw: bytes, filename: str | None, content_type: str | None) -> Tuple[str | None, dict | None, dict | None, str]:
    """Returns (ocr_text, extracted_data_raw, structured_data_ai, status)."""
    extracted_text = None
    extracted_data = None
    structured_data = None
    status = "processed"

    ctype = (content_type or "").lower()
    name = (filename or "").lower()
    ocr_provider = os.getenv("OCR_PROVIDER", "local").lower()

    try:
        if "text" in ctype or name.endswith((".txt", ".md", ".csv")):
            extracted_text = raw.decode("utf-8", errors="ignore")
        elif "json" in ctype or name.endswith(".json"):
            decoded = raw.decode("utf-8", errors="ignore")
            extracted_text = decoded
            try:
                extracted_data = json.loads(decoded)
            except: pass
        elif "pdf" in ctype or name.endswith(".pdf"):
            try:
                from pypdf import PdfReader
                reader = PdfReader(io.BytesIO(raw))
                pages = [p.extract_text() or "" for p in reader.pages]
                extracted_text = "\n".join(pages).strip() or None
            except Exception:
                status = "pending"

            # If embedded text extraction is empty and textract is enabled, attempt OCR provider.
            if not extracted_text and ocr_provider == "textract":
                extracted_text = _extract_with_textract(raw)
                status = "processed" if extracted_text else "pending"
        else:
            status = "pending"
            
        # Post-process for structured data if text was found
        if extracted_text:
            if not extracted_data:
                extracted_data = _map_fields_regex(extracted_text)

            extracted_data = extracted_data or {}
            extracted_data["classification"] = classify_document(extracted_text, filename, content_type)

            # AI Refinement
            structured_data = extract_structured_fields(extracted_text)

    except Exception:
        status = "failed"

    return extracted_text, extracted_data, structured_data, status
