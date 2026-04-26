from __future__ import annotations

from datetime import datetime, date
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

import models


class CloseService:
    """Month-end close orchestration service."""

    def __init__(self, db: Session):
        self.db = db

    def _get_or_create_close_period(self, company_id: UUID, period: str) -> models.ClosePeriod:
        close_period = (
            self.db.query(models.ClosePeriod)
            .filter(
                models.ClosePeriod.company_id == company_id,
                models.ClosePeriod.period == period,
            )
            .first()
        )
        if close_period:
            return close_period

        close_period = models.ClosePeriod(
            company_id=company_id,
            period=period,
            status="in_progress",
            readiness_score=0.0,
        )
        self.db.add(close_period)
        self.db.flush()
        return close_period

    def validate_close_readiness(self, company_id: UUID, period: str) -> dict[str, Any]:
        close_period = self._get_or_create_close_period(company_id, period)

        checks = {
            "monthly_metrics_available": self.db.query(models.MonthlyMetric)
            .filter(models.MonthlyMetric.company_id == company_id)
            .count()
            > 0,
            "ledger_entries_present": self.db.query(models.FinancialLedgerEntry)
            .filter(models.FinancialLedgerEntry.company_id == company_id)
            .count()
            > 0,
            "unreconciled_bank_transactions": self.db.query(models.BankingTransaction)
            .join(models.BankFeed, models.BankFeed.id == models.BankingTransaction.feed_id)
            .filter(models.BankFeed.company_id == company_id)
            .count(),
            "open_ar_invoices": self.db.query(models.Invoice)
            .filter(
                models.Invoice.company_id == company_id,
                models.Invoice.type == "ACCOUNTS_RECEIVABLE",
                models.Invoice.amount_due > 0,
            )
            .count(),
            "open_ap_invoices": self.db.query(models.Invoice)
            .filter(
                models.Invoice.company_id == company_id,
                models.Invoice.type == "ACCOUNTS_PAYABLE",
                models.Invoice.amount_due > 0,
            )
            .count(),
        }

        pass_flags = [
            checks["monthly_metrics_available"],
            checks["ledger_entries_present"],
            checks["open_ar_invoices"] == 0,
            checks["open_ap_invoices"] == 0,
        ]
        score = round((sum(1 for v in pass_flags if v) / len(pass_flags)) * 100, 2)

        close_period.readiness_score = score
        close_period.status = "validated" if score >= 75 else "in_progress"

        checklist_rows = [
            ("metrics", "Monthly metrics loaded", checks["monthly_metrics_available"]),
            ("ledger", "Ledger activity present", checks["ledger_entries_present"]),
            ("ar", "No open AR invoices", checks["open_ar_invoices"] == 0),
            ("ap", "No open AP invoices", checks["open_ap_invoices"] == 0),
        ]
        for item_key, item_name, passed in checklist_rows:
            item = (
                self.db.query(models.CloseChecklist)
                .filter(
                    models.CloseChecklist.close_period_id == close_period.id,
                    models.CloseChecklist.item_key == item_key,
                )
                .first()
            )
            if not item:
                item = models.CloseChecklist(
                    close_period_id=close_period.id,
                    item_key=item_key,
                    item_name=item_name,
                )
                self.db.add(item)
            item.status = "complete" if passed else "blocked"
            item.details = {"check_result": bool(passed)}

        self.db.add(
            models.CloseAudit(
                close_period_id=close_period.id,
                action="validate_close_readiness",
                actor_id="system",
                audit_data={"checks": checks, "score": score},
            )
        )
        self.db.commit()

        return {
            "company_id": str(company_id),
            "period": period,
            "status": close_period.status,
            "readiness_score": score,
            "checks": checks,
        }

    def calculate_accruals(self, company_id: UUID, period: str) -> dict[str, Any]:
        close_period = self._get_or_create_close_period(company_id, period)

        unpaid_ap = (
            self.db.query(func.coalesce(func.sum(models.Invoice.amount_due), 0))
            .filter(
                models.Invoice.company_id == company_id,
                models.Invoice.type == "ACCOUNTS_PAYABLE",
                models.Invoice.amount_due > 0,
            )
            .scalar()
        )
        payroll_estimate = (
            self.db.query(func.coalesce(func.sum(models.Employee.salary), 0))
            .filter(models.Employee.company_id == company_id, models.Employee.status == "active")
            .scalar()
        )

        ap_accrual = Decimal(str(unpaid_ap or 0))
        payroll_accrual = Decimal(str(payroll_estimate or 0)) / Decimal("12")
        total = ap_accrual + payroll_accrual

        self.db.add(
            models.CloseAudit(
                close_period_id=close_period.id,
                action="calculate_accruals",
                actor_id="system",
                audit_data={
                    "ap_accrual": float(ap_accrual),
                    "payroll_accrual": float(payroll_accrual),
                    "total": float(total),
                },
            )
        )
        self.db.commit()

        return {
            "company_id": str(company_id),
            "period": period,
            "accruals": {
                "accounts_payable": float(ap_accrual),
                "payroll": float(payroll_accrual),
                "total": float(total),
            },
        }

    def run_intercompany_elimination(self, company_ids: list[UUID], period: str) -> dict[str, Any]:
        rows = (
            self.db.query(models.IntercompanyTransaction)
            .filter(
                models.IntercompanyTransaction.period == period,
                models.IntercompanyTransaction.from_company_id.in_(company_ids),
                models.IntercompanyTransaction.to_company_id.in_(company_ids),
                models.IntercompanyTransaction.status.in_(["open", "matched"]),
            )
            .all()
        )

        eliminated = Decimal("0")
        for row in rows:
            eliminated += Decimal(str(row.amount or 0))
            row.status = "eliminated"

        self.db.commit()
        return {
            "period": period,
            "company_ids": [str(cid) for cid in company_ids],
            "transactions_processed": len(rows),
            "eliminated_amount": float(eliminated),
        }

    def lock_period(self, company_id: UUID, period: str, user_id: UUID) -> dict[str, Any]:
        close_period = self._get_or_create_close_period(company_id, period)
        close_period.status = "locked"
        close_period.locked_at = datetime.utcnow()
        close_period.locked_by = str(user_id)

        self.db.add(
            models.CloseAudit(
                close_period_id=close_period.id,
                action="lock_period",
                actor_id=str(user_id),
                audit_data={"period": period},
            )
        )
        self.db.commit()

        return {
            "company_id": str(company_id),
            "period": period,
            "status": close_period.status,
            "locked_at": close_period.locked_at.isoformat() if close_period.locked_at else None,
            "locked_by": close_period.locked_by,
        }

    def get_close_status(self, company_id: UUID) -> dict[str, Any]:
        periods = (
            self.db.query(models.ClosePeriod)
            .filter(models.ClosePeriod.company_id == company_id)
            .order_by(models.ClosePeriod.created_at.desc())
            .limit(6)
            .all()
        )

        timeline = []
        for period in periods:
            checklist = (
                self.db.query(models.CloseChecklist)
                .filter(models.CloseChecklist.close_period_id == period.id)
                .all()
            )
            complete = sum(1 for c in checklist if c.status == "complete")
            timeline.append(
                {
                    "period": period.period,
                    "status": period.status,
                    "readiness_score": period.readiness_score,
                    "checklist_completed": complete,
                    "checklist_total": len(checklist),
                    "locked_at": period.locked_at.isoformat() if period.locked_at else None,
                }
            )

        return {
            "company_id": str(company_id),
            "as_of": date.today().isoformat(),
            "periods": timeline,
            "open_periods": sum(1 for p in periods if p.status != "locked"),
        }
