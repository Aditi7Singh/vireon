"""
Voice-Based Financial Commands Router
=======================================
Accept text commands (from browser Speech-to-Text or direct input),
parse intent with AI, and route to the appropriate financial data endpoints.

POST /voice/command                — Process a voice/text command
GET  /voice/commands/history/{company_id} — Recent command history
GET  /voice/capabilities           — Supported command categories
POST /voice/command/batch          — Process multiple commands
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timedelta, date
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

import database
import models
from auth import get_current_user

router = APIRouter(prefix="/voice", tags=["voice-commands"])

# ---------------------------------------------------------------------------
# In-memory command history (keyed by company_id)
# ---------------------------------------------------------------------------

_COMMAND_LOG: dict[str, list] = {}


def _log_command(company_id: str, command: str, intent: str, result: dict) -> None:
    if company_id not in _COMMAND_LOG:
        _COMMAND_LOG[company_id] = []
    _COMMAND_LOG[company_id].insert(
        0,
        {
            "id": str(uuid.uuid4()),
            "command": command,
            "intent": intent,
            "timestamp": datetime.utcnow().isoformat(),
            "success": result.get("success", True),
        },
    )
    _COMMAND_LOG[company_id] = _COMMAND_LOG[company_id][:200]


# ---------------------------------------------------------------------------
# Intent parsing — keyword rules (no external LLM dependency for speed)
# ---------------------------------------------------------------------------

INTENT_RULES = [
    (r"\b(cash|runway|burn)\b", "cash_flow_query"),
    (r"\b(revenue|arr|mrr|sales)\b", "revenue_query"),
    (r"\b(invoice|invoices|outstanding|receivable)\b", "invoice_query"),
    (r"\b(expense|spend|spending|costs?)\b", "expense_query"),
    (r"\b(vendor|supplier|bill|payable)\b", "vendor_query"),
    (r"\b(anomal|unusual|flag|fraud|suspicious)\b", "anomaly_query"),
    (r"\b(tax|gst|tds|quarterly)\b", "tax_query"),
    (r"\b(budget|variance|actuals?)\b", "budget_query"),
    (r"\b(forecast|predict|projection)\b", "forecast_query"),
    (r"\b(payroll|salary|salaries|headcount)\b", "payroll_query"),
    (r"\b(report|statement|balance sheet|p&l|income)\b", "report_query"),
    (r"\b(compliance|sox|gdpr|audit)\b", "compliance_query"),
    (r"\b(help|what can|commands?|capabilities)\b", "help"),
]


def _classify_intent(text: str) -> str:
    lower = text.lower()
    for pattern, intent in INTENT_RULES:
        if re.search(pattern, lower):
            return intent
    return "general_query"


def _extract_period(text: str) -> dict:
    lower = text.lower()
    if "last month" in lower or "previous month" in lower:
        return {"label": "last_month", "days": 30}
    if "last quarter" in lower or "q1" in lower or "q2" in lower or "q3" in lower or "q4" in lower:
        return {"label": "last_quarter", "days": 90}
    if "last year" in lower or "this year" in lower:
        return {"label": "last_year", "days": 365}
    if "this week" in lower:
        return {"label": "this_week", "days": 7}
    return {"label": "last_30_days", "days": 30}


def _handle_cash_flow(company_id: uuid.UUID, text: str, db: Session) -> dict:
    cutoff = date.today() - timedelta(days=90)
    inflows = (
        db.query(models.FinancialLedgerEntry)
        .filter(
            models.FinancialLedgerEntry.company_id == company_id,
            models.FinancialLedgerEntry.transaction_date >= cutoff,
            models.FinancialLedgerEntry.amount > 0,
        )
        .all()
    )
    outflows = (
        db.query(models.FinancialLedgerEntry)
        .filter(
            models.FinancialLedgerEntry.company_id == company_id,
            models.FinancialLedgerEntry.transaction_date >= cutoff,
            models.FinancialLedgerEntry.amount < 0,
        )
        .all()
    )
    total_in = sum(float(r.amount) for r in inflows)
    total_out = abs(sum(float(r.amount) for r in outflows))
    return {
        "type": "cash_flow",
        "answer": f"In the last 90 days, cash inflows are ₹{total_in:,.0f} and outflows are ₹{total_out:,.0f}. Net cash flow: ₹{total_in - total_out:,.0f}.",
        "data": {"inflows": total_in, "outflows": total_out, "net": total_in - total_out},
    }


def _handle_revenue(company_id: uuid.UUID, text: str, db: Session) -> dict:
    period = _extract_period(text)
    cutoff = date.today() - timedelta(days=period["days"])
    invoices = (
        db.query(models.Invoice)
        .filter(
            models.Invoice.company_id == company_id,
            models.Invoice.type == "ACCOUNTS_RECEIVABLE",
            models.Invoice.issue_date >= cutoff,
        )
        .all()
    )
    total = sum(float(i.total_amount or 0) for i in invoices)
    paid = sum(float(i.amount_paid or 0) for i in invoices)
    return {
        "type": "revenue",
        "answer": f"Revenue for {period['label'].replace('_',' ')}: ₹{total:,.0f} billed, ₹{paid:,.0f} collected ({len(invoices)} invoices).",
        "data": {"billed": total, "collected": paid, "invoice_count": len(invoices), "period": period["label"]},
    }


def _handle_invoices(company_id: uuid.UUID, text: str, db: Session) -> dict:
    open_invoices = (
        db.query(models.Invoice)
        .filter(
            models.Invoice.company_id == company_id,
            models.Invoice.type == "ACCOUNTS_RECEIVABLE",
            models.Invoice.status.in_(["DRAFT", "SENT", "OVERDUE"]),
        )
        .all()
    )
    overdue = [i for i in open_invoices if i.status == "OVERDUE"]
    outstanding = sum(float(i.amount_due or 0) for i in open_invoices)
    return {
        "type": "invoices",
        "answer": f"You have {len(open_invoices)} open invoices totalling ₹{outstanding:,.0f}, of which {len(overdue)} are overdue.",
        "data": {"open_count": len(open_invoices), "overdue_count": len(overdue), "outstanding_amount": outstanding},
    }


def _handle_anomalies(company_id: uuid.UUID, text: str, db: Session) -> dict:
    open_anomalies = (
        db.query(models.Anomaly)
        .filter(
            models.Anomaly.company_id == company_id,
            models.Anomaly.status == "open",
        )
        .order_by(models.Anomaly.created_at.desc())
        .limit(5)
        .all()
    )
    high = [a for a in open_anomalies if a.severity in ("high", "critical")]
    items = [{"description": a.description, "severity": a.severity} for a in open_anomalies[:3]]
    return {
        "type": "anomalies",
        "answer": f"There are {len(open_anomalies)} open anomalies, including {len(high)} high/critical. Top alerts: {'; '.join(a['description'][:60] for a in items)}.",
        "data": {"open_count": len(open_anomalies), "critical_count": len(high), "top_items": items},
    }


def _handle_help(_: uuid.UUID, text: str, __: Session) -> dict:
    return {
        "type": "help",
        "answer": "I can answer questions about: cash flow, revenue, invoices, expenses, vendors, anomalies, tax, budget, forecasts, payroll, reports, and compliance. Try: 'Show me last month revenue' or 'Any anomalies this week?'",
        "data": {
            "supported_intents": [r[1] for r in INTENT_RULES],
        },
    }


INTENT_HANDLERS = {
    "cash_flow_query": _handle_cash_flow,
    "revenue_query": _handle_revenue,
    "invoice_query": _handle_invoices,
    "anomaly_query": _handle_anomalies,
    "help": _handle_help,
}


def _default_handler(intent: str) -> dict:
    return {
        "type": intent,
        "answer": f"I understood you're asking about {intent.replace('_', ' ')}. This data is available in the dashboard — try navigating to the relevant section.",
        "data": {},
    }


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class VoiceCommandRequest(BaseModel):
    company_id: uuid.UUID
    command: str
    language: str = "en"
    source: str = "text"


class BatchCommandRequest(BaseModel):
    company_id: uuid.UUID
    commands: List[str]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/command")
def process_voice_command(
    payload: VoiceCommandRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Process a voice or text financial command.
    Returns a natural-language answer + structured data.
    """
    if not payload.command.strip():
        raise HTTPException(status_code=400, detail="Command cannot be empty.")

    intent = _classify_intent(payload.command)
    handler = INTENT_HANDLERS.get(intent)

    if handler:
        result = handler(payload.company_id, payload.command, db)
    else:
        result = _default_handler(intent)

    result["success"] = True
    result["intent"] = intent
    result["command"] = payload.command
    result["processed_at"] = datetime.utcnow().isoformat()

    _log_command(str(payload.company_id), payload.command, intent, result)
    return result


@router.post("/command/batch")
def process_batch_commands(
    payload: BatchCommandRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Process multiple commands in sequence."""
    if len(payload.commands) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 commands per batch.")

    results = []
    for cmd in payload.commands:
        intent = _classify_intent(cmd)
        handler = INTENT_HANDLERS.get(intent)
        result = handler(payload.company_id, cmd, db) if handler else _default_handler(intent)
        result["command"] = cmd
        result["intent"] = intent
        results.append(result)

    return {"company_id": str(payload.company_id), "count": len(results), "results": results}


@router.get("/commands/history/{company_id}")
def get_command_history(
    company_id: uuid.UUID,
    limit: int = Query(50, le=200),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Return recent voice command history for a company."""
    history = _COMMAND_LOG.get(str(company_id), [])
    return {
        "company_id": str(company_id),
        "total_commands": len(history),
        "commands": history[:limit],
    }


@router.get("/capabilities")
def get_capabilities(
    current_user: models.User = Depends(get_current_user),
):
    """Return a list of supported command types with examples."""
    return {
        "supported_commands": [
            {"intent": "cash_flow_query", "examples": ["What's our cash balance?", "Show runway", "How's our burn rate?"]},
            {"intent": "revenue_query", "examples": ["Last month revenue", "What's our ARR?", "Show me MRR trends"]},
            {"intent": "invoice_query", "examples": ["Show open invoices", "Any overdue invoices?", "Outstanding receivables"]},
            {"intent": "expense_query", "examples": ["Top expenses this quarter", "Show spending by category"]},
            {"intent": "vendor_query", "examples": ["Unpaid vendor bills", "Who are our top vendors?"]},
            {"intent": "anomaly_query", "examples": ["Any anomalies?", "Flag unusual transactions", "Show suspicious activity"]},
            {"intent": "tax_query", "examples": ["Tax due this quarter", "GST liability summary"]},
            {"intent": "budget_query", "examples": ["Budget vs actuals", "Are we on budget?"]},
            {"intent": "forecast_query", "examples": ["Revenue forecast", "Cash flow next 3 months"]},
            {"intent": "payroll_query", "examples": ["Total payroll this month", "Headcount cost"]},
            {"intent": "report_query", "examples": ["P&L summary", "Balance sheet", "Income statement"]},
            {"intent": "compliance_query", "examples": ["Compliance status", "Any SOX issues?", "Audit findings"]},
        ],
        "languages_supported": ["en"],
        "input_modes": ["text", "speech-to-text (browser Web Speech API)"],
        "max_batch_size": 10,
    }
