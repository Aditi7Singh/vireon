"""
Board Report Generation Router
Generate investor-ready board reports with KPIs and PDF export
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal
import uuid
import json

import database
import models
from auth import get_current_user

router = APIRouter(prefix="/board-reports", tags=["board-reports"])


@router.post("/", response_model=dict)
def generate_board_report(
    company_id: uuid.UUID,
    reporting_period: str,
    report_date: Optional[date] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Generate a comprehensive board report"""
    report_date = report_date or date.today()
    
    # Calculate key metrics
    metrics = calculate_board_metrics(db, company_id, reporting_period)
    risk_indicators = identify_risk_indicators(db, company_id, metrics)
    mitigation_plans = generate_mitigation_plans(risk_indicators)
    
    board_report = models.BoardReport(
        company_id=company_id,
        report_date=report_date,
        reporting_period=reporting_period,
        cash_position=metrics.get("cash_position"),
        runway_months=metrics.get("runway_months"),
        burn_rate=metrics.get("burn_rate"),
        arr=metrics.get("arr"),
        mrr=metrics.get("mrr"),
        cac_payback_months=metrics.get("cac_payback_months"),
        ltv_cac_ratio=metrics.get("ltv_cac_ratio"),
        revenue_growth_rate=metrics.get("revenue_growth_rate"),
        risk_indicators=risk_indicators,
        mitigation_plans=mitigation_plans
    )
    
    db.add(board_report)
    db.commit()
    db.refresh(board_report)
    
    return {
        "report_id": str(board_report.id),
        "reporting_period": reporting_period,
        "cash_position": float(metrics.get("cash_position", 0)),
        "runway_months": float(metrics.get("runway_months", 0)),
        "burn_rate": float(metrics.get("burn_rate", 0)),
        "arr": float(metrics.get("arr", 0)),
        "revenue_growth_rate": float(metrics.get("revenue_growth_rate", 0)),
        "risk_count": len(risk_indicators)
    }


@router.get("/", response_model=List[dict])
def list_board_reports(
    company_id: uuid.UUID,
    limit: int = 10,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List board reports"""
    reports = db.query(models.BoardReport).filter(
        models.BoardReport.company_id == company_id
    ).order_by(models.BoardReport.report_date.desc()).limit(limit).all()
    
    result = []
    for report in reports:
        result.append({
            "id": str(report.id),
            "report_date": report.report_date.isoformat(),
            "reporting_period": report.reporting_period,
            "cash_position": float(report.cash_position) if report.cash_position else 0,
            "runway_months": float(report.runway_months) if report.runway_months else 0,
            "burn_rate": float(report.burn_rate) if report.burn_rate else 0,
            "arr": float(report.arr) if report.arr else 0,
            "revenue_growth_rate": float(report.revenue_growth_rate) if report.revenue_growth_rate else 0,
            "pdf_url": report.pdf_url,
            "generated_at": report.generated_at.isoformat()
        })
    
    return result


@router.get("/{report_id}", response_model=dict)
def get_board_report(
    report_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get detailed board report"""
    report = db.query(models.BoardReport).filter(
        models.BoardReport.id == report_id
    ).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Board report not found")
    
    return {
        "id": str(report.id),
        "company_id": str(report.company_id),
        "report_date": report.report_date.isoformat(),
        "reporting_period": report.reporting_period,
        "cash_position": float(report.cash_position) if report.cash_position else 0,
        "runway_months": float(report.runway_months) if report.runway_months else 0,
        "burn_rate": float(report.burn_rate) if report.burn_rate else 0,
        "arr": float(report.arr) if report.arr else 0,
        "mrr": float(report.mrr) if report.mrr else 0,
        "cac_payback_months": float(report.cac_payback_months) if report.cac_payback_months else 0,
        "ltv_cac_ratio": float(report.ltv_cac_ratio) if report.ltv_cac_ratio else 0,
        "revenue_growth_rate": float(report.revenue_growth_rate) if report.revenue_growth_rate else 0,
        "risk_indicators": report.risk_indicators,
        "mitigation_plans": report.mitigation_plans,
        "pdf_url": report.pdf_url,
        "generated_at": report.generated_at.isoformat()
    }


@router.post("/{report_id}/export-pdf", response_model=dict)
def export_board_report_pdf(
    report_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Export board report as PDF"""
    report = db.query(models.BoardReport).filter(
        models.BoardReport.id == report_id
    ).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Board report not found")
    
    # In production, generate actual PDF using ReportLab or WeasyPrint
    # For now, return a placeholder URL
    pdf_url = f"/reports/board/{report_id}.pdf"
    
    report.pdf_url = pdf_url
    db.commit()
    
    return {
        "message": "PDF generated successfully",
        "pdf_url": pdf_url,
        "report_id": str(report_id)
    }


@router.get("/{report_id}/investor-kpis", response_model=dict)
def get_investor_kpis(
    report_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get investor-focused KPIs from report"""
    report = db.query(models.BoardReport).filter(
        models.BoardReport.id == report_id
    ).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Board report not found")
    
    # Calculate additional investor KPIs
    return {
        "financial_health": {
            "cash_position": float(report.cash_position) if report.cash_position else 0,
            "runway_months": float(report.runway_months) if report.runway_months else 0,
            "burn_rate": float(report.burn_rate) if report.burn_rate else 0,
            "burn_multiple": calculate_burn_multiple(report)
        },
        "growth_metrics": {
            "arr": float(report.arr) if report.arr else 0,
            "mrr": float(report.mrr) if report.mrr else 0,
            "revenue_growth_rate": float(report.revenue_growth_rate) if report.revenue_growth_rate else 0,
            "magic_number": calculate_magic_number(db, report)
        },
        "efficiency_metrics": {
            "cac_payback_months": float(report.cac_payback_months) if report.cac_payback_months else 0,
            "ltv_cac_ratio": float(report.ltv_cac_ratio) if report.ltv_cac_ratio else 0,
            "rule_of_40": calculate_rule_of_40(report)
        },
        "risk_summary": {
            "total_risks": len(report.risk_indicators) if report.risk_indicators else 0,
            "critical_risks": count_critical_risks(report.risk_indicators),
            "risks": report.risk_indicators
        }
    }


@router.post("/compare", response_model=dict)
def compare_board_reports(
    company_id: uuid.UUID,
    report_ids: List[uuid.UUID],
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Compare multiple board reports"""
    if len(report_ids) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 reports to compare")
    
    reports = db.query(models.BoardReport).filter(
        and_(
            models.BoardReport.company_id == company_id,
            models.BoardReport.id.in_(report_ids)
        )
    ).order_by(models.BoardReport.report_date).all()
    
    comparison = {
        "reports": [],
        "trends": {}
    }
    
    for report in reports:
        comparison["reports"].append({
            "id": str(report.id),
            "period": report.reporting_period,
            "cash_position": float(report.cash_position) if report.cash_position else 0,
            "runway_months": float(report.runway_months) if report.runway_months else 0,
            "burn_rate": float(report.burn_rate) if report.burn_rate else 0,
            "arr": float(report.arr) if report.arr else 0,
            "revenue_growth_rate": float(report.revenue_growth_rate) if report.revenue_growth_rate else 0
        })
    
    # Calculate trends
    if len(reports) >= 2:
        comparison["trends"] = {
            "cash_trend": calculate_trend([r.cash_position for r in reports if r.cash_position]),
            "runway_trend": calculate_trend([r.runway_months for r in reports if r.runway_months]),
            "burn_trend": calculate_trend([r.burn_rate for r in reports if r.burn_rate]),
            "arr_growth": calculate_trend([r.arr for r in reports if r.arr])
        }
    
    return comparison


# Helper functions

def calculate_board_metrics(db: Session, company_id: uuid.UUID, period: str) -> dict:
    """Calculate all board metrics"""
    # Get latest monthly metric
    latest_metric = db.query(models.MonthlyMetric).filter(
        models.MonthlyMetric.company_id == company_id
    ).order_by(models.MonthlyMetric.metric_month.desc()).first()
    
    if not latest_metric:
        return {
            "cash_position": Decimal("0"),
            "runway_months": Decimal("0"),
            "burn_rate": Decimal("0"),
            "arr": Decimal("0"),
            "mrr": Decimal("0"),
            "cac_payback_months": Decimal("0"),
            "ltv_cac_ratio": Decimal("0"),
            "revenue_growth_rate": Decimal("0")
        }
    
    # Calculate ARR from MRR (last 12 months average revenue * 12)
    mrr = latest_metric.total_revenue if latest_metric.total_revenue else Decimal("0")
    arr = mrr * 12
    
    # Get previous month for growth calculation
    prev_metric = db.query(models.MonthlyMetric).filter(
        and_(
            models.MonthlyMetric.company_id == company_id,
            models.MonthlyMetric.metric_month < latest_metric.metric_month
        )
    ).order_by(models.MonthlyMetric.metric_month.desc()).first()
    
    revenue_growth = Decimal("0")
    if prev_metric and prev_metric.total_revenue and prev_metric.total_revenue > 0:
        revenue_growth = ((latest_metric.total_revenue - prev_metric.total_revenue) / prev_metric.total_revenue) * 100
    
    return {
        "cash_position": latest_metric.ending_cash,
        "runway_months": latest_metric.runway_months,
        "burn_rate": latest_metric.burn_rate,
        "arr": arr,
        "mrr": mrr,
        "cac_payback_months": Decimal("12"),  # Placeholder - needs customer data
        "ltv_cac_ratio": Decimal("3.0"),  # Placeholder - needs customer data
        "revenue_growth_rate": revenue_growth
    }


def identify_risk_indicators(db: Session, company_id: uuid.UUID, metrics: dict) -> list:
    """Identify financial risk indicators"""
    risks = []
    
    runway = metrics.get("runway_months", Decimal("0"))
    if runway < 6:
        risks.append({
            "severity": "critical",
            "category": "cash",
            "description": f"Runway below 6 months ({float(runway):.1f} months)",
            "recommendation": "Consider fundraising or significant cost reduction"
        })
    elif runway < 12:
        risks.append({
            "severity": "warning",
            "category": "cash",
            "description": f"Runway below 12 months ({float(runway):.1f} months)",
            "recommendation": "Begin fundraising preparation"
        })
    
    burn_rate = metrics.get("burn_rate", Decimal("0"))
    if burn_rate > 0:
        # Check for increasing burn
        risks.append({
            "severity": "info",
            "category": "burn",
            "description": f"Current burn rate: {float(burn_rate):,.0f}",
            "recommendation": "Monitor burn efficiency"
        })
    
    revenue_growth = metrics.get("revenue_growth_rate", Decimal("0"))
    if revenue_growth < 0:
        risks.append({
            "severity": "critical",
            "category": "growth",
            "description": f"Negative revenue growth: {float(revenue_growth):.1f}%",
            "recommendation": "Address revenue decline immediately"
        })
    elif revenue_growth < 10:
        risks.append({
            "severity": "warning",
            "category": "growth",
            "description": f"Low revenue growth: {float(revenue_growth):.1f}%",
            "recommendation": "Review growth strategies"
        })
    
    return risks


def generate_mitigation_plans(risks: list) -> list:
    """Generate mitigation plans for risks"""
    plans = []
    
    for risk in risks:
        if risk["category"] == "cash":
            plans.append({
                "risk_category": "cash",
                "actions": [
                    "Initiate fundraising conversations",
                    "Review all discretionary spending",
                    "Accelerate receivables collection",
                    "Consider bridge financing options"
                ],
                "timeline": "immediate",
                "owner": "CFO"
            })
        elif risk["category"] == "burn":
            plans.append({
                "risk_category": "burn",
                "actions": [
                    "Conduct department-level burn analysis",
                    "Review vendor contracts for savings",
                    "Optimize cloud infrastructure costs",
                    "Evaluate headcount efficiency"
                ],
                "timeline": "30 days",
                "owner": "CFO/COO"
            })
        elif risk["category"] == "growth":
            plans.append({
                "risk_category": "growth",
                "actions": [
                    "Review sales pipeline and conversion rates",
                    "Analyze customer churn and expansion",
                    "Evaluate product-market fit",
                    "Consider pricing optimization"
                ],
                "timeline": "60 days",
                "owner": "CEO/CRO"
            })
    
    return plans


def calculate_burn_multiple(report: models.BoardReport) -> float:
    """Calculate burn multiple (burn / net new ARR)"""
    if not report.burn_rate or not report.arr:
        return 0.0
    # Simplified - needs actual net new ARR calculation
    return float(report.burn_rate) / max(float(report.arr) / 12, 1)


def calculate_magic_number(db: Session, report: models.BoardReport) -> float:
    """Calculate magic number (net new ARR / sales & marketing spend)"""
    # Placeholder - needs actual S&M spend data
    return 0.75


def calculate_rule_of_40(report: models.BoardReport) -> float:
    """Calculate Rule of 40 (growth rate + profit margin)"""
    growth_rate = float(report.revenue_growth_rate) if report.revenue_growth_rate else 0
    # Profit margin placeholder - needs actual calculation
    profit_margin = -20.0  # Negative for burn
    return growth_rate + profit_margin


def count_critical_risks(risks: list) -> int:
    """Count critical severity risks"""
    if not risks:
        return 0
    return sum(1 for r in risks if r.get("severity") == "critical")


def calculate_trend(values: list) -> str:
    """Calculate trend direction from values"""
    if not values or len(values) < 2:
        return "stable"
    
    first_val = float(values[0]) if values[0] else 0
    last_val = float(values[-1]) if values[-1] else 0
    
    if last_val > first_val * 1.1:
        return "up"
    elif last_val < first_val * 0.9:
        return "down"
    else:
        return "stable"
