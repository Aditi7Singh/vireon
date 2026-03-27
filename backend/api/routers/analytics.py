from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from fastapi.responses import StreamingResponse
import io
from typing import Optional, List, Dict
from datetime import date, datetime, timedelta
from pydantic import BaseModel
from sqlalchemy import func

import models
import schemas
import database
import auth
from analytics import metrics, scenarios
from pdf_utils import generate_runway_report_pdf, generate_budget_variance_report_pdf
from services.planning import calculate_forecast, get_budget_variance
from services import burn_service

router = APIRouter(prefix="", tags=["analytics", "scenarios"])


class ComparativePeriodRequest(BaseModel):
    current_month: Optional[str] = None
    previous_month: Optional[str] = None


def _parse_month(month_text: str) -> date:
    return datetime.strptime(month_text, "%Y-%m").date().replace(day=1)


def _safe_metric(metric: Optional[models.MonthlyMetric]) -> Dict[str, float]:
    if not metric:
        return {"revenue": 0.0, "expenses": 0.0, "cash": 0.0, "net_burn": 0.0}
    revenue = float(metric.total_revenue or 0)
    expenses = float(metric.total_expenses or 0)
    return {
        "revenue": revenue,
        "expenses": expenses,
        "cash": float(metric.ending_cash or 0),
        "net_burn": float(expenses - revenue),
    }


def _default_company_id(db: Session) -> UUID:
    company_row = db.query(models.Company.id).order_by(models.Company.created_at.asc()).first()
    if not company_row:
        raise HTTPException(status_code=404, detail="No company found")
    return company_row[0]


def _format_runway_zero_date(runway_months: float) -> str:
    if runway_months <= 0:
        return "N/A"
    days = int(runway_months * 30.44)
    return (datetime.utcnow().date() + timedelta(days=days)).isoformat()


def _runway_confidence(db: Session, company_id: UUID) -> str:
    metric_count = db.query(models.MonthlyMetric).filter(models.MonthlyMetric.company_id == company_id).count()
    if metric_count >= 12:
        return "High"
    if metric_count >= 6:
        return "Medium"
    return "Low"


def _compute_revenue_dynamics(db: Session, company_id: UUID) -> dict:
    rows = (
        db.query(models.MonthlyMetric)
        .filter(models.MonthlyMetric.company_id == company_id)
        .order_by(models.MonthlyMetric.metric_month.desc())
        .limit(2)
        .all()
    )

    if not rows:
        return {"mrr": 0.0, "arr": 0.0, "growth_pct": 0.0, "churn_rate": 0.0, "nrr": 0.0}

    current_revenue = float(rows[0].total_revenue or 0)
    previous_revenue = float(rows[1].total_revenue or 0) if len(rows) > 1 else current_revenue

    growth_pct = 0.0
    if previous_revenue > 0:
        growth_pct = ((current_revenue - previous_revenue) / previous_revenue) * 100

    # Proxy metrics when subscription telemetry is unavailable.
    churn_rate = 0.0
    nrr = 100.0 if previous_revenue > 0 else 0.0
    if previous_revenue > 0:
        nrr = (current_revenue / previous_revenue) * 100
        if current_revenue < previous_revenue:
            churn_rate = ((previous_revenue - current_revenue) / previous_revenue) * 100

    return {
        "mrr": current_revenue,
        "arr": current_revenue * 12,
        "growth_pct": round(growth_pct, 2),
        "churn_rate": round(churn_rate, 2),
        "nrr": round(nrr, 2),
    }

@router.get("/metrics/financials/{company_id}")
def get_financial_summary(
    company_id: UUID, 
    db: Session = Depends(database.get_db)
):
    """
    Get core financial metrics using the Math Engine.
    """
    latest_metric = db.query(models.MonthlyMetric).filter(
        models.MonthlyMetric.company_id == company_id
    ).order_by(models.MonthlyMetric.metric_month.desc()).first()

    if not latest_metric:
        raise HTTPException(status_code=404, detail="No financial metrics found for this company")

    cash_balance = float(latest_metric.ending_cash)
    revenue = float(latest_metric.total_revenue)
    gross_burn = float(latest_metric.total_expenses)
    
    # Use Math Engine for calculations
    net_burn = metrics.calculate_net_burn(revenue, gross_burn)
    runway = metrics.calculate_runway(cash_balance, net_burn)
    arr = metrics.calculate_arr(revenue) 
    
    return {
        "company_id": str(company_id),
        "total_cash": cash_balance,
        "monthly_revenue": revenue,
        "monthly_gross_burn": gross_burn,
        "monthly_net_burn": net_burn,
        "runway_months": runway,
        "arr": arr,
        "as_of": latest_metric.metric_month.isoformat()
    }

@router.get("/metrics/history/{company_id}")
def get_metrics_history(
    company_id: UUID, 
    months: int = 12,
    db: Session = Depends(database.get_db)
):
    """Get historical financial metrics for charts."""
    metrics_list = db.query(models.MonthlyMetric).filter(
        models.MonthlyMetric.company_id == company_id
    ).order_by(models.MonthlyMetric.metric_month.desc()).limit(months).all()
    
    # Reverse to get chronological order [oldest -> newest]
    metrics_list.reverse()
    
    return [
        {
            "month": m.metric_month.strftime("%Y-%m"),
            "revenue": float(m.total_revenue),
            "expenses": float(m.total_expenses),
            "net_burn": float(m.total_expenses - m.total_revenue),
            "cash": float(m.ending_cash)
        }
        for m in metrics_list
    ]


@router.post("/scenarios/simulate-hiring", response_model=schemas.ScenarioResponse)
def simulate_hiring_scenario(
    request: schemas.HiringScenarioRequest,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    """
    Simulate impact of hiring on runway.
    """
    latest_metric = db.query(models.MonthlyMetric).filter(
        models.MonthlyMetric.company_id == request.company_id
    ).order_by(models.MonthlyMetric.metric_month.desc()).first()

    if not latest_metric:
        raise HTTPException(status_code=404, detail="No financial data found")

    result = scenarios.simulate_hiring(
        current_cash=float(latest_metric.ending_cash),
        current_revenue=float(latest_metric.total_revenue),
        current_gross_burn=float(latest_metric.total_expenses),
        new_salary_annual=request.avg_salary,
        count=request.num_employees
    )
    
    return {
        "scenario": result["scenario"],
        "impact_metrics": {
            "additional_monthly_burn": result["additional_monthly_burn"],
            "new_net_burn": result["new_net_burn"]
        },
        "new_runway": result["new_runway"]
    }


@router.post("/scenarios/simulate-revenue", response_model=schemas.ScenarioResponse)
def simulate_revenue_scenario(
    request: schemas.RevenueScenarioRequest,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    """
    Simulate impact of revenue growth/contraction on runway.
    """
    latest_metric = db.query(models.MonthlyMetric).filter(
        models.MonthlyMetric.company_id == request.company_id
    ).order_by(models.MonthlyMetric.metric_month.desc()).first()

    if not latest_metric:
        raise HTTPException(status_code=404, detail="No financial data found")

    result = scenarios.simulate_revenue_change(
        current_cash=float(latest_metric.ending_cash),
        current_revenue=float(latest_metric.total_revenue),
        current_gross_burn=float(latest_metric.total_expenses),
        percentage_change=request.percentage_change
    )
    
    return {
        "scenario": result["scenario"],
        "impact_metrics": {
            "new_monthly_revenue": result.get("new_monthly_revenue", 0.0),
            "new_net_burn": result.get("new_net_burn", 0.0)
        },
        "new_runway": result.get("new_runway", 0.0)
    }
@router.get("/scorecard/{company_id}")
def get_scorecard(
    company_id: UUID,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    latest_metric = db.query(models.MonthlyMetric).filter(
        models.MonthlyMetric.company_id == company_id
    ).order_by(models.MonthlyMetric.metric_month.desc()).first()

    if not latest_metric:
        return {
            "total_cash": 0,
            "monthly_revenue": 0,
            "monthly_gross_burn": 0,
            "monthly_net_burn": 0,
            "runway_months": 0,
            "arr": 0,
            "as_of": ""
        }

    cash_balance = float(latest_metric.ending_cash)
    revenue = float(latest_metric.total_revenue)
    gross_burn = float(latest_metric.total_expenses)
    net_burn = metrics.calculate_net_burn(revenue, gross_burn)
    runway = metrics.calculate_runway(cash_balance, net_burn)
    arr = metrics.calculate_arr(revenue)
    
    return {
        "company_id": str(company_id),
        "total_cash": cash_balance,
        "monthly_revenue": revenue,
        "monthly_gross_burn": gross_burn,
        "monthly_net_burn": net_burn,
        "runway_months": runway if isinstance(runway, (int, float)) else 999,
        "arr": arr,
        "as_of": latest_metric.metric_month.isoformat()
    }


@router.get("/scorecard")
def get_scorecard_default(
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    return get_scorecard(_default_company_id(db), db, current_user)

@router.get("/burn-rate/{company_id}")
def get_burn_rate(
    company_id: UUID,
    period: int = 30,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    # Simple mock/placeholder logic for category breakdown
    expenses = (
        db.query(models.Expense.category, models.Expense.total_amount)
        .filter(models.Expense.company_id == company_id)
        .all()
    )
    breakdown = {}
    total = 0
    for exp in expenses:
        cat = exp.category or "Other"
        amount = float(exp.total_amount or 0)
        breakdown[cat] = breakdown.get(cat, 0) + amount
        total += amount
    
    return {
        "monthly_burn": total / 3 if total > 0 else 0, # Avg over 3 months if simulated
        "breakdown_by_category": breakdown,
        "trend": -4.2
    }


@router.get("/burn-rate")
def get_burn_rate_default(
    period: int = 30,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    return get_burn_rate(_default_company_id(db), period, db, current_user)

@router.get("/runway/{company_id}")
def get_runway(
    company_id: UUID,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    latest_metric = db.query(models.MonthlyMetric).filter(models.MonthlyMetric.company_id == company_id).order_by(models.MonthlyMetric.metric_month.desc()).first()
    if not latest_metric:
        return {"runway_months": 0, "zero_date": "N/A", "confidence_interval": "Low"}
    
    runway = metrics.calculate_runway(
        float(latest_metric.ending_cash),
        metrics.calculate_net_burn(float(latest_metric.total_revenue), float(latest_metric.total_expenses)),
    )
    runway_value = float(runway if isinstance(runway, (int, float)) else 999)
    
    return {
        "runway_months": runway_value,
        "zero_date": _format_runway_zero_date(runway_value),
        "confidence_interval": _runway_confidence(db, company_id),
    }


@router.get("/runway")
def get_runway_default(
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    return get_runway(_default_company_id(db), db, current_user)

@router.get("/revenue/{company_id}")
def get_revenue(
    company_id: UUID,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    return _compute_revenue_dynamics(db, company_id)


@router.get("/revenue")
def get_revenue_default(
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    return get_revenue(_default_company_id(db), db, current_user)

@router.get("/expenses/{company_id}")
def get_expenses(
    company_id: UUID,
    months: int = 3,
    department: str = None,
    product_tag: str = None,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    month = date.today().strftime("%Y-%m")

    # Primary source: ledger-based burn service for normalized categories.
    burn_breakdown = burn_service.get_expense_breakdown(company_id, db, month)
    headcount = burn_service.get_headcount_costs(company_id, db)

    tech = burn_breakdown.get("tech_costs", {})
    non_tech = burn_breakdown.get("non_tech_costs", {})
    payroll = burn_breakdown.get("payroll", {})
    hiring_total = sum(float(h.get("monthly_cost", 0)) for h in headcount.get("pending_hires", []))

    breakdown = {
        "payroll": float(payroll.get("total", 0)),
        "aws": float(tech.get("aws_total", 0)),
        "saas": float(tech.get("saas_total", 0)) + float(tech.get("licenses_total", 0)),
        "marketing": float(non_tech.get("marketing", 0)),
        "office": float(non_tech.get("office_bengaluru", 0)) + float(non_tech.get("office_gangavathi", 0)),
        "hiring": float(hiring_total),
        "misc": float(non_tech.get("misc", 0)),
    }

    # Fallback: if ledger-backed categories are empty, use Expense table totals.
    if all(v == 0 for v in breakdown.values()):
        query = db.query(models.Expense).filter(models.Expense.company_id == company_id)
        expenses = query.all()
        for exp in expenses:
            cat = (exp.category or "other").strip().lower().replace(" ", "_")
            amount = float(exp.total_amount or 0)
            if "cloud" in cat or "infra" in cat or "aws" in cat:
                breakdown["aws"] += amount
            elif "payroll" in cat or "salary" in cat:
                breakdown["payroll"] += amount
            elif "office" in cat:
                breakdown["office"] += amount
            elif "marketing" in cat:
                breakdown["marketing"] += amount
            elif "hiring" in cat:
                breakdown["hiring"] += amount
            elif "saas" in cat or "license" in cat:
                breakdown["saas"] += amount
            else:
                breakdown["misc"] += amount

    return {
        "breakdown": breakdown,
        "trend": [],
        "movers": []
    }


@router.get("/expenses")
def get_expenses_default(
    months: int = 3,
    department: Optional[str] = None,
    product_tag: Optional[str] = None,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    return get_expenses(
        company_id=_default_company_id(db),
        months=months,
        department=department,
        product_tag=product_tag,
        db=db,
        current_user=current_user,
    )

@router.get("/cash-balance/{company_id}")
def get_cash_balance(
    company_id: UUID,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    latest_metric = db.query(models.MonthlyMetric).filter(models.MonthlyMetric.company_id == company_id).order_by(models.MonthlyMetric.metric_month.desc()).first()
    if not latest_metric:
        return {"cash": 0, "ar": 0, "ap": 0, "net_cash": 0}

    # Use deterministic AR/AP sums from open invoices to avoid hard-coded values.
    ar_open = float(
        sum(
            float(x[0] or 0)
            for x in db.query(models.Invoice.amount_due)
            .filter(
                models.Invoice.company_id == company_id,
                models.Invoice.type == "ACCOUNTS_RECEIVABLE",
                models.Invoice.amount_due > 0,
            )
            .all()
        )
    )
    ap_open = float(
        sum(
            float(x[0] or 0)
            for x in db.query(models.Invoice.amount_due)
            .filter(
                models.Invoice.company_id == company_id,
                models.Invoice.type == "ACCOUNTS_PAYABLE",
                models.Invoice.amount_due > 0,
            )
            .all()
        )
    )
    cash = float(latest_metric.ending_cash)
    
    return {
        "cash": cash,
        "ar": ar_open,
        "ap": ap_open,
        "net_cash": cash + ar_open - ap_open,
    }


@router.get("/collections/aging/{company_id}")
def get_collections_aging(
    company_id: UUID,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user),
):
    """QuickBooks-style AR/AP aging summary with overdue worklist."""
    as_of = date.today()

    ar_buckets = metrics.calculate_ar_aging(db, company_id, as_of)

    ap_buckets = {"0_30": 0.0, "31_60": 0.0, "61_90": 0.0, "90_plus": 0.0}
    ap_open = (
        db.query(models.Invoice)
        .filter(
            models.Invoice.company_id == company_id,
            models.Invoice.type == "ACCOUNTS_PAYABLE",
            models.Invoice.amount_due > 0,
            models.Invoice.issue_date <= as_of,
        )
        .all()
    )
    for inv in ap_open:
        age_days = (as_of - inv.issue_date).days
        amount = float(inv.amount_due or 0)
        if age_days <= 30:
            ap_buckets["0_30"] += amount
        elif age_days <= 60:
            ap_buckets["31_60"] += amount
        elif age_days <= 90:
            ap_buckets["61_90"] += amount
        else:
            ap_buckets["90_plus"] += amount

    overdue_ar = (
        db.query(models.Invoice)
        .filter(
            models.Invoice.company_id == company_id,
            models.Invoice.type == "ACCOUNTS_RECEIVABLE",
            models.Invoice.amount_due > 0,
            models.Invoice.due_date < as_of,
        )
        .order_by(models.Invoice.due_date.asc())
        .limit(20)
        .all()
    )

    return {
        "as_of": as_of.isoformat(),
        "ar": {
            "buckets": ar_buckets,
            "total_open": round(sum(ar_buckets.values()), 2),
        },
        "ap": {
            "buckets": ap_buckets,
            "total_open": round(sum(ap_buckets.values()), 2),
        },
        "overdue_receivables": [
            {
                "invoice_id": str(inv.id),
                "invoice_number": inv.invoice_number,
                "due_date": inv.due_date.isoformat() if inv.due_date else None,
                "days_overdue": (as_of - inv.due_date).days if inv.due_date else None,
                "amount_due": float(inv.amount_due or 0),
            }
            for inv in overdue_ar
        ],
    }


@router.get("/cash-balance")
def get_cash_balance_default(
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    return get_cash_balance(_default_company_id(db), db, current_user)


@router.get("/reports/runway/pdf")
def export_runway_report_pdf(
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    """Export cash runway analysis as PDF report."""
    company = db.query(models.Company).first()
    if not company:
        raise HTTPException(status_code=404, detail="No company found")
    
    # Get current metrics
    latest_metric = db.query(models.MonthlyMetric).filter(
        models.MonthlyMetric.company_id == company.id
    ).order_by(models.MonthlyMetric.metric_month.desc()).first()
    
    if not latest_metric:
        raise HTTPException(status_code=404, detail="No financial metrics found")
    
    metrics_data = {
        "ending_cash": float(latest_metric.ending_cash),
        "burn_rate": float(latest_metric.burn_rate),
        "runway_months": float(latest_metric.runway_months),
        "total_revenue": float(latest_metric.total_revenue),
        "total_expenses": float(latest_metric.total_expenses),
    }
    
    # Get forecasts
    forecasts = calculate_forecast(db, str(company.id), months_ahead=12)
    
    # Generate PDF
    pdf_content = generate_runway_report_pdf(metrics_data, forecasts)
    
    return StreamingResponse(
        io.BytesIO(pdf_content),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=runway_report.pdf"}
    )


@router.get("/reports/budget/{budget_id}/pdf")
def export_budget_variance_report_pdf(
    budget_id: UUID,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    """Export budget vs actual analysis as PDF report."""
    budget_data = get_budget_variance(db, budget_id)
    
    if not budget_data:
        raise HTTPException(status_code=404, detail="Budget not found")
    
    # Generate PDF
    pdf_content = generate_budget_variance_report_pdf(budget_data)
    
    return StreamingResponse(
        io.BytesIO(pdf_content),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=budget_{budget_id}_report.pdf"}
    )


@router.get("/compliance/reminders/{company_id}")
def get_compliance_reminders(
    company_id: UUID,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    """Get upcoming tax compliance deadlines."""
    return metrics.get_tax_compliance_reminders(db, company_id)


@router.get("/metrics/vc/{company_id}")
def get_vc_metrics_dashboard(
    company_id: UUID,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    """Get high-level VC/Investor metrics."""
    return metrics.get_vc_metrics(db, company_id)


@router.get("/metrics/comparative/{company_id}")
def get_comparative_period_analysis(
    company_id: UUID,
    current_month: Optional[str] = None,
    previous_month: Optional[str] = None,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user),
):
    """Comparative period analysis for revenue, expenses, cash, and burn."""
    current_date: Optional[date] = None
    previous_date: Optional[date] = None

    if current_month:
        try:
            current_date = _parse_month(current_month)
        except ValueError:
            raise HTTPException(status_code=400, detail="current_month must be YYYY-MM")

    if previous_month:
        try:
            previous_date = _parse_month(previous_month)
        except ValueError:
            raise HTTPException(status_code=400, detail="previous_month must be YYYY-MM")

    if current_date is None:
        latest = (
            db.query(models.MonthlyMetric)
            .filter(models.MonthlyMetric.company_id == company_id)
            .order_by(models.MonthlyMetric.metric_month.desc())
            .first()
        )
        if not latest:
            return {
                "company_id": str(company_id),
                "current_month": None,
                "previous_month": None,
                "metrics": {},
            }
        current_date = latest.metric_month.replace(day=1)

    if previous_date is None:
        previous_date = (current_date - timedelta(days=1)).replace(day=1)

    current_metric = (
        db.query(models.MonthlyMetric)
        .filter(models.MonthlyMetric.company_id == company_id, models.MonthlyMetric.metric_month == current_date)
        .first()
    )
    previous_metric = (
        db.query(models.MonthlyMetric)
        .filter(models.MonthlyMetric.company_id == company_id, models.MonthlyMetric.metric_month == previous_date)
        .first()
    )

    current_vals = _safe_metric(current_metric)
    previous_vals = _safe_metric(previous_metric)

    metrics_out = {}
    for key in ["revenue", "expenses", "cash", "net_burn"]:
        cur = current_vals[key]
        prev = previous_vals[key]
        delta = cur - prev
        pct = (delta / prev) * 100 if prev != 0 else 0.0
        metrics_out[key] = {
            "current": round(cur, 2),
            "previous": round(prev, 2),
            "delta": round(delta, 2),
            "delta_pct": round(pct, 2),
        }

    return {
        "company_id": str(company_id),
        "current_month": current_date.isoformat(),
        "previous_month": previous_date.isoformat(),
        "metrics": metrics_out,
    }


@router.get("/vendors/performance/{company_id}")
def get_vendor_performance_scoring(
    company_id: UUID,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user),
):
    """Score vendor reliability and payment quality from AP behavior."""
    vendor_contacts = (
        db.query(models.Contact)
        .filter(models.Contact.company_id == company_id, models.Contact.type == "VENDOR")
        .all()
    )

    scores = []
    for vendor in vendor_contacts:
        invoices = (
            db.query(models.Invoice)
            .filter(
                models.Invoice.company_id == company_id,
                models.Invoice.contact_id == vendor.id,
                models.Invoice.type == "ACCOUNTS_PAYABLE",
            )
            .all()
        )
        if not invoices:
            continue

        total = len(invoices)
        paid = 0
        overdue = 0
        late_paid = 0
        total_spend = 0.0
        today = date.today()
        for inv in invoices:
            total_spend += float(inv.total_amount or 0)
            status = (inv.status or "").upper()
            if status == "PAID":
                paid += 1
                if inv.payment_date and inv.due_date and inv.payment_date > inv.due_date:
                    late_paid += 1
            if float(inv.amount_due or 0) > 0 and inv.due_date and inv.due_date < today:
                overdue += 1

        late_ratio = late_paid / total if total else 0.0
        overdue_ratio = overdue / total if total else 0.0
        paid_ratio = paid / total if total else 0.0

        score = 100.0
        score -= late_ratio * 35
        score -= overdue_ratio * 35
        score += paid_ratio * 10
        score = max(0.0, min(100.0, score))

        tier = "A" if score >= 85 else "B" if score >= 70 else "C" if score >= 50 else "D"
        scores.append(
            {
                "vendor_id": str(vendor.id),
                "vendor_name": vendor.name,
                "score": round(score, 2),
                "tier": tier,
                "invoice_count": total,
                "total_spend": round(total_spend, 2),
                "overdue_count": overdue,
                "late_paid_count": late_paid,
            }
        )

    scores.sort(key=lambda x: x["score"], reverse=True)
    return {"company_id": str(company_id), "count": len(scores), "vendors": scores}


@router.get("/cash-flow/forecast/{company_id}")
def get_cash_flow_forecast(
    company_id: UUID,
    months: int = 6,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user),
):
    """Cash-flow forecast built from forecast table with fallback to planning service."""
    if months <= 0:
        raise HTTPException(status_code=400, detail="months must be positive")

    rows = (
        db.query(models.Forecast)
        .filter(models.Forecast.company_id == company_id)
        .order_by(models.Forecast.forecast_date.asc())
        .limit(months)
        .all()
    )

    if not rows:
        generated = calculate_forecast(db, company_id, months_ahead=months)
        return {
            "company_id": str(company_id),
            "source": "planning_service_fallback",
            "months": months,
            "forecast": [
                {
                    "month": x["forecast_date"].isoformat(),
                    "projected_revenue": float(x["mrr_predicted"]),
                    "projected_cash": float(x["cash_predicted"]),
                }
                for x in generated
            ],
        }

    latest_metric = (
        db.query(models.MonthlyMetric)
        .filter(models.MonthlyMetric.company_id == company_id)
        .order_by(models.MonthlyMetric.metric_month.desc())
        .first()
    )
    baseline_net_burn = float((latest_metric.total_expenses or 0) - (latest_metric.total_revenue or 0)) if latest_metric else 0.0

    out = []
    for r in rows:
        projected_revenue = float(r.mrr_predicted or 0)
        projected_cash = float(r.cash_predicted or 0)
        projected_net_burn = max(0.0, baseline_net_burn - (projected_revenue * 0.05))
        out.append(
            {
                "month": r.forecast_date.isoformat(),
                "projected_revenue": round(projected_revenue, 2),
                "projected_net_burn": round(projected_net_burn, 2),
                "projected_cash": round(projected_cash, 2),
            }
        )

    return {
        "company_id": str(company_id),
        "source": "forecast_table",
        "months": months,
        "forecast": out,
    }


@router.get("/working-capital/optimize/{company_id}")
def get_working_capital_optimization(
    company_id: UUID,
    lookback_days: int = 90,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user),
):
    """Working capital KPIs and optimization suggestions."""
    today = date.today()
    start = today - timedelta(days=max(lookback_days, 1))

    open_ar = float(
        sum(
            float(x[0] or 0)
            for x in db.query(models.Invoice.amount_due)
            .filter(
                models.Invoice.company_id == company_id,
                models.Invoice.type == "ACCOUNTS_RECEIVABLE",
                models.Invoice.amount_due > 0,
            )
            .all()
        )
    )
    open_ap = float(
        sum(
            float(x[0] or 0)
            for x in db.query(models.Invoice.amount_due)
            .filter(
                models.Invoice.company_id == company_id,
                models.Invoice.type == "ACCOUNTS_PAYABLE",
                models.Invoice.amount_due > 0,
            )
            .all()
        )
    )

    ar_sales = float(
        sum(
            float(x[0] or 0)
            for x in db.query(models.Invoice.total_amount)
            .filter(
                models.Invoice.company_id == company_id,
                models.Invoice.type == "ACCOUNTS_RECEIVABLE",
                models.Invoice.issue_date >= start,
                models.Invoice.issue_date <= today,
            )
            .all()
        )
    )
    ap_purchases = float(
        sum(
            float(x[0] or 0)
            for x in db.query(models.Invoice.total_amount)
            .filter(
                models.Invoice.company_id == company_id,
                models.Invoice.type == "ACCOUNTS_PAYABLE",
                models.Invoice.issue_date >= start,
                models.Invoice.issue_date <= today,
            )
            .all()
        )
    )

    daily_sales = ar_sales / lookback_days if lookback_days > 0 else 0.0
    daily_purchases = ap_purchases / lookback_days if lookback_days > 0 else 0.0
    dso = open_ar / daily_sales if daily_sales > 0 else 0.0
    dpo = open_ap / daily_purchases if daily_purchases > 0 else 0.0
    ccc = dso - dpo

    recommendations: List[str] = []
    if dso > 45:
        recommendations.append("Reduce DSO: tighten credit terms and automate dunning for >30 day invoices.")
    if dpo < 25:
        recommendations.append("Increase DPO: renegotiate payment terms with strategic vendors.")
    if ccc > 30:
        recommendations.append("Cash conversion cycle is high; prioritize collections and AP term optimization.")
    if not recommendations:
        recommendations.append("Working capital posture is healthy; maintain collection cadence and vendor term discipline.")

    return {
        "company_id": str(company_id),
        "lookback_days": lookback_days,
        "open_ar": round(open_ar, 2),
        "open_ap": round(open_ap, 2),
        "dso_days": round(dso, 2),
        "dpo_days": round(dpo, 2),
        "cash_conversion_cycle_days": round(ccc, 2),
        "recommendations": recommendations,
    }


@router.get("/credit/risk/{company_id}")
def get_credit_risk_scoring(
    company_id: UUID,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user),
):
    """Credit analysis and risk scoring from liquidity, runway, and volatility signals."""
    latest = (
        db.query(models.MonthlyMetric)
        .filter(models.MonthlyMetric.company_id == company_id)
        .order_by(models.MonthlyMetric.metric_month.desc())
        .first()
    )
    if not latest:
        return {
            "company_id": str(company_id),
            "score": 0,
            "rating": "D",
            "signals": {"reason": "No monthly metrics available"},
        }

    revenue_series = [
        float(x.total_revenue or 0)
        for x in db.query(models.MonthlyMetric)
        .filter(models.MonthlyMetric.company_id == company_id)
        .order_by(models.MonthlyMetric.metric_month.desc())
        .limit(6)
        .all()
    ]
    mean_revenue = sum(revenue_series) / len(revenue_series) if revenue_series else 0.0
    revenue_volatility = 0.0
    if len(revenue_series) >= 2 and mean_revenue > 0:
        variance = sum((x - mean_revenue) ** 2 for x in revenue_series) / len(revenue_series)
        revenue_volatility = (variance ** 0.5) / mean_revenue

    cash = float(latest.ending_cash or 0)
    monthly_expenses = float(latest.total_expenses or 0)
    runway_months = float(latest.runway_months or 0)

    open_ap = float(
        sum(
            float(x[0] or 0)
            for x in db.query(models.Invoice.amount_due)
            .filter(
                models.Invoice.company_id == company_id,
                models.Invoice.type == "ACCOUNTS_PAYABLE",
                models.Invoice.amount_due > 0,
            )
            .all()
        )
    )
    current_ratio_proxy = (cash / open_ap) if open_ap > 0 else 2.0

    score = 100.0
    if runway_months < 6:
        score -= 25
    elif runway_months < 9:
        score -= 10

    if current_ratio_proxy < 1:
        score -= 25
    elif current_ratio_proxy < 1.5:
        score -= 10

    if revenue_volatility > 0.35:
        score -= 20
    elif revenue_volatility > 0.2:
        score -= 10

    if monthly_expenses > 0 and cash < monthly_expenses:
        score -= 10

    score = max(0.0, min(100.0, score))
    rating = "A" if score >= 85 else "B" if score >= 70 else "C" if score >= 55 else "D"

    return {
        "company_id": str(company_id),
        "score": round(score, 2),
        "rating": rating,
        "signals": {
            "runway_months": round(runway_months, 2),
            "cash": round(cash, 2),
            "open_ap": round(open_ap, 2),
            "current_ratio_proxy": round(current_ratio_proxy, 2),
            "revenue_volatility": round(revenue_volatility, 4),
        },
    }
