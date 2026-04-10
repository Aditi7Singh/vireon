"""
LangGraph Auditor Agent
=======================
Autonomous bank reconciliation agent.

Workflow:
  1. fetch_gl_entries    — pull GL payment entries from the database / ERPNext
  2. fetch_bank_statement— accept uploaded bank-statement data (CSV/JSON rows)
  3. reconcile           — deterministic matching: exact amount + date ± 2 days
  4. flag_discrepancies  — return unmatched items with severity scores
  5. generate_report     — LLM summarises findings in plain English

The agent never does arithmetic inside the LLM; it only interprets the output
from the deterministic reconcile() function.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Annotated, Any, Dict, List, Literal, Optional, TypedDict

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import tool
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

from config.settings import get_llm

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Agent State
# ---------------------------------------------------------------------------


class AuditorState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    gl_entries: List[Dict]
    bank_statement: List[Dict]
    reconciliation_result: Dict
    session_id: str
    company_id: Optional[str]


# ---------------------------------------------------------------------------
# Deterministic Reconciliation Engine (no LLM math!)
# ---------------------------------------------------------------------------


def _reconcile_entries(
    gl_entries: List[Dict],
    bank_statement: List[Dict],
    date_tolerance_days: int = 2,
    amount_tolerance_pct: float = 0.01,
) -> Dict:
    """
    Match GL entries against bank statement rows deterministically.

    Matching logic:
      1. Exact amount match + date within ±tolerance days  → "matched"
      2. Amount within 1 % + date within ±tolerance        → "likely_match"
      3. No match found                                     → "unmatched"

    Returns a dict with matched, unmatched_gl, unmatched_bank, discrepancies.
    """
    matched: List[Dict] = []
    unmatched_gl: List[Dict] = []
    unmatched_bank: List[Dict] = []
    discrepancies: List[Dict] = []

    used_bank_idx: set = set()

    for gl in gl_entries:
        gl_amount = float(gl.get("amount", 0))
        try:
            gl_date = datetime.strptime(str(gl.get("date", "")), "%Y-%m-%d").date()
        except ValueError:
            gl_date = date.today()

        best_match_idx = None
        best_match_type = None
        best_delta = float("inf")

        for bi, bk in enumerate(bank_statement):
            if bi in used_bank_idx:
                continue

            bk_amount = float(bk.get("amount", 0))
            try:
                bk_date = datetime.strptime(str(bk.get("date", "")), "%Y-%m-%d").date()
            except ValueError:
                bk_date = date.today()

            date_diff = abs((gl_date - bk_date).days)
            if date_diff > date_tolerance_days:
                continue

            amount_diff = abs(gl_amount - bk_amount)
            pct_diff = amount_diff / (abs(gl_amount) + 1e-8)

            if amount_diff < 0.01 and date_diff < best_delta:
                best_match_idx = bi
                best_match_type = "exact"
                best_delta = date_diff
            elif pct_diff <= amount_tolerance_pct and date_diff < best_delta:
                best_match_idx = bi
                best_match_type = "likely"
                best_delta = date_diff

        if best_match_idx is not None:
            bk = bank_statement[best_match_idx]
            used_bank_idx.add(best_match_idx)
            matched.append(
                {
                    "gl": gl,
                    "bank": bk,
                    "match_type": best_match_type,
                    "amount_delta": round(
                        float(gl.get("amount", 0)) - float(bk.get("amount", 0)), 2
                    ),
                    "date_delta_days": abs(
                        (gl_date - (
                            datetime.strptime(str(bk.get("date", "")), "%Y-%m-%d").date()
                            if bk.get("date") else date.today()
                        )).days
                    ),
                }
            )
        else:
            unmatched_gl.append(gl)
            severity = (
                "critical"
                if abs(gl_amount) > 10_000
                else "warning" if abs(gl_amount) > 1_000
                else "info"
            )
            discrepancies.append(
                {
                    "type": "gl_not_in_bank",
                    "severity": severity,
                    "entry": gl,
                    "amount": gl_amount,
                    "description": (
                        f"GL entry ${gl_amount:,.2f} on {gl_date} "
                        f"({gl.get('description', 'no description')}) "
                        f"has no matching bank transaction."
                    ),
                }
            )

    # Bank entries with no GL match
    for bi, bk in enumerate(bank_statement):
        if bi not in used_bank_idx:
            bk_amount = float(bk.get("amount", 0))
            unmatched_bank.append(bk)
            severity = (
                "critical"
                if abs(bk_amount) > 10_000
                else "warning" if abs(bk_amount) > 1_000
                else "info"
            )
            discrepancies.append(
                {
                    "type": "bank_not_in_gl",
                    "severity": severity,
                    "entry": bk,
                    "amount": bk_amount,
                    "description": (
                        f"Bank transaction ${bk_amount:,.2f} on {bk.get('date', '?')} "
                        f"({bk.get('description', 'no description')}) "
                        f"has no corresponding GL entry."
                    ),
                }
            )

    total_gl = sum(float(e.get("amount", 0)) for e in gl_entries)
    total_bank = sum(float(e.get("amount", 0)) for e in bank_statement)

    return {
        "matched": matched,
        "unmatched_gl": unmatched_gl,
        "unmatched_bank": unmatched_bank,
        "discrepancies": discrepancies,
        "summary": {
            "total_gl_entries": len(gl_entries),
            "total_bank_entries": len(bank_statement),
            "matched_count": len(matched),
            "unmatched_gl_count": len(unmatched_gl),
            "unmatched_bank_count": len(unmatched_bank),
            "discrepancy_count": len(discrepancies),
            "critical_discrepancies": sum(
                1 for d in discrepancies if d["severity"] == "critical"
            ),
            "total_gl_amount": round(total_gl, 2),
            "total_bank_amount": round(total_bank, 2),
            "variance": round(total_gl - total_bank, 2),
        },
    }


# ---------------------------------------------------------------------------
# LangGraph Tools
# ---------------------------------------------------------------------------


@tool
def fetch_gl_entries(company_id: str, period_start: str, period_end: str) -> str:
    """
    Fetch GL payment entries for a company within a date range.
    Returns JSON list of GL entries with keys: id, date, amount, description, account.
    """
    # In production, query models.FinancialLedgerEntry from the database.
    # Here we return realistic demo data.
    demo_entries = [
        {"id": "GL001", "date": period_start, "amount": 12500.00, "description": "AWS Invoice Nov", "account": "Cloud Infrastructure"},
        {"id": "GL002", "date": period_start, "amount": 4800.00, "description": "Payroll ACH batch", "account": "Payroll"},
        {"id": "GL003", "date": period_end, "amount": 320.00, "description": "Office supplies", "account": "OpEx"},
        {"id": "GL004", "date": period_end, "amount": 99000.00, "description": "Enterprise customer payment", "account": "Revenue"},
        {"id": "GL005", "date": period_start, "amount": 1200.00, "description": "Software subscription", "account": "SaaS Tools"},
    ]
    return json.dumps(demo_entries)


@tool
def fetch_bank_statement(company_id: str, period_start: str, period_end: str) -> str:
    """
    Fetch simulated bank statement rows for the period.
    Returns JSON list with keys: date, amount, description, reference.
    """
    # Simulate a bank statement with one discrepancy (GL004 amount differs)
    demo_bank = [
        {"date": period_start, "amount": 12500.00, "description": "AWS SVCS", "reference": "ACH-001"},
        {"date": period_start, "amount": 4800.00, "description": "PAYROLL BATCH", "reference": "ACH-002"},
        {"date": period_end, "amount": 320.00, "description": "OFFICE DEPOT", "reference": "POS-123"},
        {"date": period_end, "amount": 97000.00, "description": "ACME CORP PAYMENT", "reference": "WIRE-789"},  # $2,000 short
        # GL005 (software subscription) is missing from the bank — discrepancy!
        {"date": period_start, "amount": 5500.00, "description": "UNKNOWN CHARGE", "reference": "POS-999"},    # extra bank entry
    ]
    return json.dumps(demo_bank)


@tool
def run_reconciliation(gl_json: str, bank_json: str) -> str:
    """
    Run deterministic reconciliation between GL entries and bank statement.
    Returns a JSON reconciliation report with matches, discrepancies, and summary.
    """
    try:
        gl_entries = json.loads(gl_json)
        bank_entries = json.loads(bank_json)
    except json.JSONDecodeError as e:
        return json.dumps({"error": f"JSON parse error: {e}"})

    result = _reconcile_entries(gl_entries, bank_entries)
    return json.dumps(result, default=str)


AUDITOR_TOOLS = [fetch_gl_entries, fetch_bank_statement, run_reconciliation]


# ---------------------------------------------------------------------------
# System Prompt
# ---------------------------------------------------------------------------


_AUDITOR_SYSTEM_PROMPT = """
You are Vireon's Autonomous Auditor Agent.

Your job is to perform a bank reconciliation for the given period.

Follow this exact workflow:
1. Call fetch_gl_entries to retrieve the GL payment data.
2. Call fetch_bank_statement to retrieve bank statement data.
3. Call run_reconciliation with the GL and bank JSON you received.
4. Summarise the reconciliation result clearly:
   - How many entries matched?
   - What discrepancies were found (critical first)?
   - What is the total variance (GL total minus bank total)?
   - What actions does the finance team need to take?

IMPORTANT:
- Do NOT perform any arithmetic in your own reasoning. Trust the numbers from run_reconciliation.
- Be precise about amounts and dates.
- Format the report in clear sections with bullet points.
"""


# ---------------------------------------------------------------------------
# Agent Nodes
# ---------------------------------------------------------------------------


def auditor_agent_node(state: AuditorState) -> AuditorState:
    llm = get_llm(thinking=False)
    llm_with_tools = llm.bind_tools(AUDITOR_TOOLS)
    system_msg = SystemMessage(content=_AUDITOR_SYSTEM_PROMPT)
    response = llm_with_tools.invoke([system_msg] + state["messages"])
    return {"messages": [response]}


def auditor_tools_node(state: AuditorState) -> AuditorState:
    from langgraph.prebuilt import ToolNode
    executor = ToolNode(AUDITOR_TOOLS)
    result = executor.invoke(state)
    msgs = result if isinstance(result, list) else result.get("messages", [])
    return {"messages": msgs}


def should_continue_auditor(
    state: AuditorState,
) -> Literal["auditor_tools", "end"]:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "auditor_tools"
    return "end"


# ---------------------------------------------------------------------------
# Graph Builder
# ---------------------------------------------------------------------------


def build_auditor_graph():
    graph = StateGraph(AuditorState)
    graph.add_node("auditor_agent", auditor_agent_node)
    graph.add_node("auditor_tools", auditor_tools_node)
    graph.set_entry_point("auditor_agent")
    graph.add_conditional_edges(
        "auditor_agent",
        should_continue_auditor,
        {"auditor_tools": "auditor_tools", "end": END},
    )
    graph.add_edge("auditor_tools", "auditor_agent")
    return graph.compile()


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def run_bank_reconciliation(
    company_id: str,
    period_start: str,
    period_end: str,
    session_id: Optional[str] = None,
) -> str:
    """
    Run the full autonomous bank reconciliation for a company and period.

    Args:
        company_id:   company UUID string
        period_start: ISO date string "YYYY-MM-DD"
        period_end:   ISO date string "YYYY-MM-DD"
        session_id:   optional session identifier

    Returns:
        Narrative reconciliation report as a string.
    """
    if not session_id:
        session_id = f"audit-{uuid.uuid4().hex[:8]}"

    graph = build_auditor_graph()

    initial_message = HumanMessage(
        content=(
            f"Please perform a bank reconciliation for company {company_id} "
            f"for the period {period_start} to {period_end}. "
            f"Fetch the GL entries, fetch the bank statement, run the reconciliation, "
            f"and give me a detailed discrepancy report."
        )
    )

    initial_state: AuditorState = {
        "messages": [initial_message],
        "gl_entries": [],
        "bank_statement": [],
        "reconciliation_result": {},
        "session_id": session_id,
        "company_id": company_id,
    }

    try:
        result = graph.invoke(initial_state)
        msgs = result.get("messages", []) if isinstance(result, dict) else result
        for msg in reversed(msgs):
            if isinstance(msg, AIMessage) and msg.content:
                return msg.content
        return "Reconciliation complete but no summary was generated."
    except Exception as exc:
        logger.error("Auditor agent error: %s", exc, exc_info=True)
        return f"Reconciliation failed: {exc}"
