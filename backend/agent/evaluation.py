"""
Agent Response Evaluation
=========================
Lightweight heuristic evaluator to catch answer-quality regressions in CI.
"""

from datetime import datetime
from dataclasses import dataclass
import logging
from typing import Iterable, Optional
import re


logger = logging.getLogger(__name__)


DEFAULT_FORBIDDEN_PHRASES = {
    "i think",
    "maybe",
    "not sure",
    "i guess",
    "probably",
}


@dataclass
class EvaluationResult:
    score: float
    passed: bool
    checks: dict[str, bool]
    feedback: list[str]


def _contains_number(text: str) -> bool:
    return bool(re.search(r"\d", text))


def evaluate_agent_response(
    user_query: str,
    response: str,
    *,
    required_keywords: Optional[Iterable[str]] = None,
    forbidden_phrases: Optional[Iterable[str]] = None,
    min_numeric_tokens: int = 0,
    min_score: float = 0.75,
) -> EvaluationResult:
    """
    Evaluate an agent response with deterministic heuristics.

    The goal is not perfect grading; it is early detection of obvious quality
    regressions in structure, confidence, and numeric grounding.
    """
    response_clean = (response or "").strip()
    query_clean = (user_query or "").strip()

    checks: dict[str, bool] = {}
    feedback: list[str] = []

    checks["non_empty"] = len(response_clean) > 0
    if not checks["non_empty"]:
        feedback.append("Response is empty")

    checks["minimum_length"] = len(response_clean) >= 40
    if not checks["minimum_length"]:
        feedback.append("Response is too short to be useful")

    numeric_token_count = len(re.findall(r"\d+(?:\.\d+)?", response_clean))
    checks["numeric_grounding"] = numeric_token_count >= min_numeric_tokens
    if not checks["numeric_grounding"]:
        feedback.append(
            f"Response has insufficient numeric grounding ({numeric_token_count} < {min_numeric_tokens})"
        )

    required = [k.lower() for k in (required_keywords or [])]
    if required:
        missing = [k for k in required if k not in response_clean.lower()]
        checks["required_keywords"] = len(missing) == 0
        if missing:
            feedback.append(f"Missing required keywords: {', '.join(missing)}")
    else:
        checks["required_keywords"] = True

    forbidden = [p.lower() for p in (forbidden_phrases or DEFAULT_FORBIDDEN_PHRASES)]
    found_forbidden = [p for p in forbidden if p in response_clean.lower()]
    checks["forbidden_phrases"] = len(found_forbidden) == 0
    if found_forbidden:
        feedback.append(f"Contains weak-confidence phrasing: {', '.join(found_forbidden)}")

    query_mentions_money = any(w in query_clean.lower() for w in ["cash", "burn", "runway", "revenue", "expense"])
    if query_mentions_money:
        checks["has_number_for_finance_query"] = _contains_number(response_clean)
        if not checks["has_number_for_finance_query"]:
            feedback.append("Finance-oriented query response should include at least one number")
    else:
        checks["has_number_for_finance_query"] = True

    weighted = [
        ("non_empty", 0.2),
        ("minimum_length", 0.15),
        ("numeric_grounding", 0.2),
        ("required_keywords", 0.2),
        ("forbidden_phrases", 0.15),
        ("has_number_for_finance_query", 0.1),
    ]
    score = sum(weight for key, weight in weighted if checks.get(key, False))
    score = round(score, 3)

    hard_fail = (not checks["non_empty"]) or (not checks["forbidden_phrases"]) or (
        not checks["has_number_for_finance_query"]
    )

    return EvaluationResult(
        score=score,
        passed=(score >= min_score) and (not hard_fail),
        checks=checks,
        feedback=feedback,
    )


def log_agent_trace(
    *,
    session_id: str,
    chain_id: str,
    query: str,
    tools_used: Iterable[str],
    response: str,
    company_id: Optional[str] = None,
) -> None:
    """Emit a structured trace line for agent debugging and auditability."""
    logger.info(
        "agent_trace",
        extra={
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": session_id,
            "chain_id": chain_id,
            "company_id": company_id,
            "query": query,
            "tools_used": list(tools_used),
            "response_preview": (response or "")[:240],
        },
    )


def log_tool_call(
    *,
    session_id: str,
    chain_id: str,
    tool_name: str,
    status: str,
    data_timestamp: Optional[str] = None,
) -> None:
    """Emit a structured log line for a tool call."""
    logger.info(
        "tool_call",
        extra={
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": session_id,
            "chain_id": chain_id,
            "tool_name": tool_name,
            "status": status,
            "data_timestamp": data_timestamp,
        },
    )
