from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

import models


class ConsolidationService:
    def __init__(self, db: Session):
        self.db = db

    def add_subsidiary(self, parent_id: UUID, subsidiary_id: UUID) -> dict[str, Any]:
        existing = (
            self.db.query(models.EntityHierarchy)
            .filter(
                models.EntityHierarchy.parent_company_id == parent_id,
                models.EntityHierarchy.subsidiary_company_id == subsidiary_id,
            )
            .first()
        )
        if existing:
            return {"success": True, "message": "Relationship already exists", "id": str(existing.id)}

        row = models.EntityHierarchy(parent_company_id=parent_id, subsidiary_company_id=subsidiary_id, ownership_pct=Decimal("100"))
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return {"success": True, "id": str(row.id)}

    def match_intercompany_transactions(self, company_ids: list[UUID], period: str) -> dict[str, Any]:
        txns = (
            self.db.query(models.IntercompanyTransaction)
            .filter(
                models.IntercompanyTransaction.from_company_id.in_(company_ids),
                models.IntercompanyTransaction.to_company_id.in_(company_ids),
                models.IntercompanyTransaction.period == period,
            )
            .all()
        )

        matched = 0
        unmatched = 0
        for txn in txns:
            counterpart = (
                self.db.query(models.IntercompanyTransaction)
                .filter(
                    models.IntercompanyTransaction.from_company_id == txn.to_company_id,
                    models.IntercompanyTransaction.to_company_id == txn.from_company_id,
                    models.IntercompanyTransaction.period == period,
                    models.IntercompanyTransaction.amount == txn.amount,
                )
                .first()
            )
            if counterpart:
                txn.status = "matched"
                counterpart.status = "matched"
                matched += 1
            else:
                unmatched += 1

        self.db.commit()
        return {
            "period": period,
            "company_ids": [str(cid) for cid in company_ids],
            "matched": matched,
            "unmatched": unmatched,
        }

    def translate_to_base_currency(self, amounts: dict[str, float], target_currency: str) -> dict[str, Any]:
        if target_currency.upper() == "INR":
            rates = {"INR": 1.0, "USD": 83.0, "EUR": 90.0, "GBP": 106.0}
        else:
            rates = {target_currency.upper(): 1.0, "INR": 1.0}

        translated: dict[str, float] = {}
        total = 0.0
        for key, value in amounts.items():
            if ":" in key:
                _, currency = key.split(":", 1)
            else:
                currency = target_currency
            rate = rates.get(currency.upper(), 1.0)
            converted = float(value) * rate
            translated[key] = round(converted, 2)
            total += converted

        return {
            "target_currency": target_currency.upper(),
            "translated_amounts": translated,
            "total": round(total, 2),
            "rates_used": rates,
        }

    def _latest_metric_map(self, company_ids: list[UUID]) -> dict[str, models.MonthlyMetric]:
        out: dict[str, models.MonthlyMetric] = {}
        for cid in company_ids:
            metric = (
                self.db.query(models.MonthlyMetric)
                .filter(models.MonthlyMetric.company_id == cid)
                .order_by(models.MonthlyMetric.metric_month.desc())
                .first()
            )
            if metric:
                out[str(cid)] = metric
        return out

    def generate_consolidated_balance_sheet(self, company_ids: list[UUID], period: str) -> dict[str, Any]:
        metric_map = self._latest_metric_map(company_ids)
        assets = 0.0
        liabilities = 0.0
        equity = 0.0
        for metric in metric_map.values():
            cash = float(metric.ending_cash or 0)
            assets += cash
            liabilities += max(0.0, float(metric.total_expenses or 0) * 0.25)
            equity += max(0.0, assets - liabilities)

        payload = {
            "period": period,
            "assets": round(assets, 2),
            "liabilities": round(liabilities, 2),
            "equity": round(max(0.0, assets - liabilities), 2),
            "company_count": len(metric_map),
        }
        return payload

    def generate_consolidated_pnl(self, company_ids: list[UUID], period: str) -> dict[str, Any]:
        metric_map = self._latest_metric_map(company_ids)
        revenue = sum(float(m.total_revenue or 0) for m in metric_map.values())
        expenses = sum(float(m.total_expenses or 0) for m in metric_map.values())
        net_income = revenue - expenses

        payload = {
            "period": period,
            "revenue": round(revenue, 2),
            "expenses": round(expenses, 2),
            "net_income": round(net_income, 2),
            "company_count": len(metric_map),
        }
        return payload

    def snapshot_consolidation(self, company_ids: list[UUID], period: str, target_currency: str = "INR") -> dict[str, Any]:
        bs = self.generate_consolidated_balance_sheet(company_ids, period)
        pnl = self.generate_consolidated_pnl(company_ids, period)

        snap = models.ConsolidationSnapshot(
            period=period,
            company_ids=[str(cid) for cid in company_ids],
            target_currency=target_currency,
            balance_sheet=bs,
            pnl=pnl,
            minority_interest=Decimal("0"),
        )
        self.db.add(snap)
        self.db.commit()
        self.db.refresh(snap)

        return {
            "snapshot_id": str(snap.id),
            "period": period,
            "target_currency": target_currency,
            "balance_sheet": bs,
            "pnl": pnl,
        }
