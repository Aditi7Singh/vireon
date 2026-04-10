"""
Automatic Accrual Detection Service
=====================================
Identifies unbooked accruals using revenue recognition rules and GL patterns.

Detects two categories:
  1. EXPENSE ACCRUALS — expenses incurred but not yet posted
     - Recurring vendor charges that abruptly stopped
     - Services consumed in a period with no matching invoice
     - Payroll-related estimates at period-end

  2. REVENUE ACCRUALS (Deferred Revenue)
     - Advance payments not yet earned (deferred revenue)
     - Milestones reached but not yet invoiced
     - Subscription revenue that should be recognized ratably

Output: structured list of suggested journal entries with confidence scores.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


class AccrualSuggestion:
    def __init__(
        self,
        accrual_type: str,           # "expense" | "revenue" | "deferred_revenue"
        account: str,
        vendor_or_customer: str,
        suggested_amount: float,
        confidence: float,           # 0.0 – 1.0
        reason: str,
        period: str,                 # "YYYY-MM"
        debit_account: str,
        credit_account: str,
        priority: str,               # "high" | "medium" | "low"
    ):
        self.accrual_type = accrual_type
        self.account = account
        self.vendor_or_customer = vendor_or_customer
        self.suggested_amount = round(suggested_amount, 2)
        self.confidence = round(confidence, 3)
        self.reason = reason
        self.period = period
        self.debit_account = debit_account
        self.credit_account = credit_account
        self.priority = priority

    def to_dict(self) -> Dict:
        return {
            "accrual_type": self.accrual_type,
            "account": self.account,
            "vendor_or_customer": self.vendor_or_customer,
            "suggested_amount": self.suggested_amount,
            "confidence": self.confidence,
            "reason": self.reason,
            "period": self.period,
            "debit_account": self.debit_account,
            "credit_account": self.credit_account,
            "priority": self.priority,
        }


# ---------------------------------------------------------------------------
# Expense Accrual Detection
# ---------------------------------------------------------------------------


def detect_missing_expense_accruals(
    gl_entries: List[Dict],
    current_period: Optional[str] = None,
    min_months_history: int = 3,
    absence_threshold_pct: float = 0.80,
) -> List[AccrualSuggestion]:
    """
    Detect recurring expenses that are absent in the current period.

    Logic:
    - Group GL entries by vendor + account
    - For each group, calculate average monthly amount over history
    - If the current period has no entry (or < 20% of average), suggest accrual

    Args:
        gl_entries:  Raw GL entries [{date, amount, vendor, account, category}]
        current_period:  "YYYY-MM" (defaults to last full month)
        min_months_history:  Minimum months needed to establish a pattern
        absence_threshold_pct:  If current amount < this % of average → flag

    Returns:
        List of AccrualSuggestion objects
    """
    if not gl_entries:
        return []

    if not current_period:
        today = date.today()
        current_period = (today.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")

    df = pd.DataFrame(gl_entries)
    if "date" not in df.columns or "amount" not in df.columns:
        return []

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    df["period"] = df["date"].dt.strftime("%Y-%m")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
    df["vendor"] = df.get("vendor", pd.Series(dtype=str)).fillna("Unknown").astype(str)
    df["account"] = df.get("account", pd.Series(dtype=str)).fillna("General").astype(str)

    suggestions: List[AccrualSuggestion] = []

    for (vendor, account), grp in df.groupby(["vendor", "account"]):
        # Only expense accounts (positive amounts → outflows)
        if grp["amount"].mean() <= 0:
            continue

        monthly = grp.groupby("period")["amount"].sum().reset_index()
        history = monthly[monthly["period"] < current_period]

        if len(history) < min_months_history:
            continue

        avg_monthly = float(history["amount"].mean())
        if avg_monthly < 100:  # ignore tiny amounts
            continue

        current_rows = monthly[monthly["period"] == current_period]
        current_amount = float(current_rows["amount"].sum()) if len(current_rows) > 0 else 0.0

        if current_amount < avg_monthly * (1 - absence_threshold_pct):
            missing = avg_monthly - current_amount
            confidence = 0.9 if current_amount == 0 else 0.65
            priority = "high" if avg_monthly > 10_000 else "medium" if avg_monthly > 2_000 else "low"

            suggestions.append(AccrualSuggestion(
                accrual_type="expense",
                account=str(account),
                vendor_or_customer=str(vendor),
                suggested_amount=missing,
                confidence=confidence,
                reason=(
                    f"Recurring vendor '{vendor}' averages ${avg_monthly:,.0f}/month in '{account}' "
                    f"over {len(history)} months, but only ${current_amount:,.0f} posted in {current_period}. "
                    f"Missing: ${missing:,.0f}."
                ),
                period=str(current_period),
                debit_account=str(account),
                credit_account="Accrued Liabilities",
                priority=priority,
            ))

    return suggestions


# ---------------------------------------------------------------------------
# Revenue Recognition Accruals
# ---------------------------------------------------------------------------


def detect_deferred_revenue_recognition(
    invoices: List[Dict],
    current_period: Optional[str] = None,
) -> List[AccrualSuggestion]:
    """
    Detect advance payments (deferred revenue) that should be earned/recognized.

    Logic:
    - Find invoices paid in advance (payment_date < service_start_date, or
      invoices with future service periods)
    - Calculate the portion of each that should be recognized in current_period
    - Suggest: DR Deferred Revenue / CR Revenue

    Args:
        invoices:  [{id, amount, payment_date, service_start, service_end, status, customer}]
        current_period:  "YYYY-MM"
    """
    if not invoices:
        return []

    if not current_period:
        current_period = date.today().strftime("%Y-%m")

    cp_date = datetime.strptime(current_period + "-01", "%Y-%m-%d").date()
    cp_end = (cp_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    suggestions: List[AccrualSuggestion] = []

    for inv in invoices:
        try:
            amount = float(inv.get("amount", 0))
            if amount <= 0:
                continue

            service_start = inv.get("service_start")
            service_end = inv.get("service_end")
            if not service_start or not service_end:
                continue

            sstart = datetime.strptime(str(service_start), "%Y-%m-%d").date()
            send = datetime.strptime(str(service_end), "%Y-%m-%d").date()
            total_days = max((send - sstart).days, 1)

            # Portion earned in current period
            overlap_start = max(sstart, cp_date)
            overlap_end = min(send, cp_end)
            if overlap_start > overlap_end:
                continue

            earned_days = (overlap_end - overlap_start).days + 1
            earned_amount = (earned_days / total_days) * amount

            if earned_amount < 50:
                continue

            customer = str(inv.get("customer", inv.get("contact_id", "Unknown")))
            suggestions.append(AccrualSuggestion(
                accrual_type="deferred_revenue",
                account="Deferred Revenue",
                vendor_or_customer=customer,
                suggested_amount=earned_amount,
                confidence=0.92,
                reason=(
                    f"Invoice #{inv.get('id', '?')} from {customer}: ${amount:,.0f} "
                    f"covers {sstart} to {send} ({total_days} days). "
                    f"${earned_amount:,.0f} ({earned_days} days) should be recognized in {current_period}."
                ),
                period=str(current_period),
                debit_account="Deferred Revenue",
                credit_account="Revenue",
                priority="high" if earned_amount > 5_000 else "medium",
            ))

        except (ValueError, KeyError):
            continue

    return suggestions


# ---------------------------------------------------------------------------
# Payroll Accruals
# ---------------------------------------------------------------------------


def detect_payroll_accruals(
    payroll_entries: List[Dict],
    current_period: Optional[str] = None,
) -> List[AccrualSuggestion]:
    """
    Detect period-end payroll accruals (salary earned but not yet paid).

    Logic:
    - Find pay periods that span month-end
    - Calculate the pro-rated amount attributable to the current period
    """
    if not payroll_entries:
        return []

    if not current_period:
        current_period = date.today().strftime("%Y-%m")

    suggestions: List[AccrualSuggestion] = []
    total_accrual = 0.0

    cp_year, cp_month = map(int, current_period.split("-"))
    period_end = date(cp_year, cp_month, 1)
    if cp_month == 12:
        next_month = date(cp_year + 1, 1, 1)
    else:
        next_month = date(cp_year, cp_month + 1, 1)
    period_end = next_month - timedelta(days=1)

    for entry in payroll_entries:
        try:
            pay_date_str = str(entry.get("pay_date", ""))
            if not pay_date_str:
                continue
            pay_date = datetime.strptime(pay_date_str, "%Y-%m-%d").date()

            # If pay date is in the first week of NEXT month, accrual needed
            if next_month <= pay_date <= next_month + timedelta(days=7):
                gross = float(entry.get("gross_pay", 0))
                dept = str(entry.get("department", "All Departments"))
                # Pro-rate: assume semi-monthly or biweekly
                accrual = gross * 0.5  # rough 50% estimate for mid-month pay
                total_accrual += accrual

        except ValueError:
            continue

    if total_accrual > 0:
        suggestions.append(AccrualSuggestion(
            accrual_type="expense",
            account="Salaries & Wages",
            vendor_or_customer="Employees",
            suggested_amount=total_accrual,
            confidence=0.85,
            reason=(
                f"Estimated payroll accrual for {current_period}: ${total_accrual:,.0f} "
                f"(wages earned through period-end not yet processed)."
            ),
            period=str(current_period),
            debit_account="Salaries & Wages Expense",
            credit_account="Accrued Payroll",
            priority="high",
        ))

    return suggestions


# ---------------------------------------------------------------------------
# Full Scan
# ---------------------------------------------------------------------------


def run_accrual_detection(
    gl_entries: List[Dict],
    invoices: List[Dict],
    payroll_entries: List[Dict],
    current_period: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run the complete accrual detection scan.

    Returns a structured report with suggested journal entries.
    """
    expense_accruals = detect_missing_expense_accruals(gl_entries, current_period)
    deferred_revenue = detect_deferred_revenue_recognition(invoices, current_period)
    payroll_accruals = detect_payroll_accruals(payroll_entries, current_period)

    all_suggestions = expense_accruals + deferred_revenue + payroll_accruals
    all_suggestions.sort(key=lambda s: (-s.suggested_amount, s.confidence), reverse=False)
    all_suggestions.sort(key=lambda s: s.suggested_amount, reverse=True)

    total_suggested = sum(s.suggested_amount for s in all_suggestions)
    high_priority = [s for s in all_suggestions if s.priority == "high"]

    return {
        "period": current_period or date.today().strftime("%Y-%m"),
        "total_suggestions": len(all_suggestions),
        "total_suggested_amount": round(total_suggested, 2),
        "high_priority_count": len(high_priority),
        "breakdown": {
            "expense_accruals": len(expense_accruals),
            "deferred_revenue": len(deferred_revenue),
            "payroll_accruals": len(payroll_accruals),
        },
        "suggestions": [s.to_dict() for s in all_suggestions],
        "summary": (
            f"Found {len(all_suggestions)} unbooked accruals totalling ${total_suggested:,.0f} "
            f"for {current_period}. {len(high_priority)} require immediate attention."
        ),
    }
