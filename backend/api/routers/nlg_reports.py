"""
NLG Reports Router  
Natural Language Generation for financial reports
Uses Ollama with Qwen model when USE_LOCAL_LLM=true, otherwise falls back to OpenAI
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import uuid
import os
import httpx

import database
import models
from auth import get_current_user

router = APIRouter(prefix="/nlg-reports", tags=["nlg-reports"])

# Configuration
USE_LOCAL_LLM = os.getenv("USE_LOCAL_LLM", "false").lower() == "true"
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


@router.post("/{company_id}/generate", response_model=dict)
async def generate_narrative_report(
    company_id: uuid.UUID,
    report_type: str,  # monthly, quarterly, board, mda
    report_period: str,  # YYYY-MM or YYYY-QN
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Generate NLG financial narrative report"""
    # Get financial data for period
    financial_data = await get_financial_data_for_period(db, company_id, report_period)
    
    # Get variance analysis
    variances = await calculate_variances(db, company_id, report_period)
    
    # Generate narrative using GPT-4
    narrative = await generate_narrative_with_gpt4(
        report_type=report_type,
        financial_data=financial_data,
        variances=variances
    )
    
    # Extract key insights
    key_insights = extract_key_insights(financial_data, variances)
    
    # Save report
    report = models.NarrativeReport(
        company_id=company_id,
        report_type=report_type,
        report_period=report_period,
        narrative_content=narrative,
        key_insights=key_insights,
        variance_explanations=variances,
        financial_data=financial_data,
        generated_by_model="gpt-4o"
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    
    return {
        "report_id": str(report.id),
        "narrative": narrative,
        "key_insights": key_insights,
        "variances": variances,
        "generated_at": report.generated_at.isoformat()
    }


@router.get("/{company_id}/reports", response_model=List[dict])
def list_narrative_reports(
    company_id: uuid.UUID,
    report_type: Optional[str] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List generated narrative reports"""
    query = db.query(models.NarrativeReport).filter(
        models.NarrativeReport.company_id == company_id
    )
    
    if report_type:
        query = query.filter(models.NarrativeReport.report_type == report_type)
    
    reports = query.order_by(models.NarrativeReport.generated_at.desc()).limit(20).all()
    
    return [
        {
            "id": str(r.id),
            "report_type": r.report_type,
            "report_period": r.report_period,
            "narrative_preview": r.narrative_content[:500] + "...",
            "generated_at": r.generated_at.isoformat()
        }
        for r in reports
    ]


@router.get("/{report_id}/full", response_model=dict)
def get_full_narrative_report(
    report_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get full narrative report"""
    report = db.query(models.NarrativeReport).filter(
        models.NarrativeReport.id == report_id
    ).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return {
        "id": str(report.id),
        "report_type": report.report_type,
        "report_period": report.report_period,
        "narrative": report.narrative_content,
        "key_insights": report.key_insights,
        "variance_explanations": report.variance_explanations,
        "financial_data": report.financial_data,
        "generated_at": report.generated_at.isoformat()
    }


# Helper functions

async def get_financial_data_for_period(
    db: Session,
    company_id: uuid.UUID,
    period: str
) -> dict:
    """Get financial metrics for reporting period"""
    from analytics.metrics import calculate_monthly_metrics
    
    # Parse period
    if len(period) == 7:  # YYYY-MM
        period_date = datetime.strptime(period, "%Y-%m").date()
    else:  # YYYY-QN
        year, quarter = period.split("-Q")
        month = (int(quarter) - 1) * 3 + 1
        period_date = date(int(year), month, 1)
    
    metrics = calculate_monthly_metrics(db, company_id, period_date)
    
    return {
        "period": period,
        "cash_balance": float(metrics.get("ending_cash", 0)),
        "revenue": float(metrics.get("total_revenue", 0)),
        "expenses": float(metrics.get("total_expenses", 0)),
        "burn_rate": float(metrics.get("burn_rate", 0)),
        "runway_months": float(metrics.get("runway_months", 0)),
        "net_cash_flow": float(metrics.get("net_cash_flow", 0))
    }


async def calculate_variances(
    db: Session,
    company_id: uuid.UUID,
    period: str
) -> dict:
    """Calculate variances vs prior period and budget"""
    # Get current period data
    current = await get_financial_data_for_period(db, company_id, period)
    
    # Get prior period
    period_date = datetime.strptime(period, "%Y-%m").date() if len(period) == 7 else None
    if period_date:
        prior_period = (period_date - relativedelta(months=1)).strftime("%Y-%m")
        prior = await get_financial_data_for_period(db, company_id, prior_period)
        
        variances = {
            "cash_variance": {
                "amount": current["cash_balance"] - prior["cash_balance"],
                "percent": ((current["cash_balance"] / prior["cash_balance"]) - 1) * 100 if prior["cash_balance"] else 0
            },
            "revenue_variance": {
                "amount": current["revenue"] - prior["revenue"],
                "percent": ((current["revenue"] / prior["revenue"]) - 1) * 100 if prior["revenue"] else 0
            },
            "expense_variance": {
                "amount": current["expenses"] - prior["expenses"],
                "percent": ((current["expenses"] / prior["expenses"]) - 1) * 100 if prior["expenses"] else 0
            }
        }
    else:
        variances = {}
    
    return variances


async def generate_narrative_with_gpt4(
    report_type: str,
    financial_data: dict,
    variances: dict
) -> str:
    """Generate narrative using GPT-4"""
    prompt = f"""
You are a CFO preparing a {report_type} financial report. Based on the data below, write a concise, 
executive-friendly narrative summary (300-500 words).

Financial Data:
- Cash Balance: ${financial_data['cash_balance']:,.2f}
- Revenue: ${financial_data['revenue']:,.2f}
- Expenses: ${financial_data['expenses']:,.2f}
- Burn Rate: ${financial_data['burn_rate']:,.2f}/month
- Runway: {financial_data['runway_months']:.1f} months

Variances vs Prior Period:
{format_variances(variances)}

Write a narrative that:
1. Summarizes overall financial position
2. Explains key variances in plain English
3. Highlights risks and opportunities
4. Provides actionable insights

Use a professional yet accessible tone. Focus on what matters to executives and board members.
"""
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert CFO and financial analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        # Fallback narrative
        return generate_fallback_narrative(financial_data, variances)


def format_variances(variances: dict) -> str:
    """Format variances for prompt"""
    if not variances:
        return "No prior period data available"
    
    lines = []
    for key, value in variances.items():
        metric = key.replace("_variance", "").replace("_", " ").title()
        lines.append(f"- {metric}: ${value['amount']:,.2f} ({value['percent']:+.1f}%)")
    
    return "\n".join(lines)


def extract_key_insights(financial_data: dict, variances: dict) -> list:
    """Extract key insights from data"""
    insights = []
    
    # Runway alert
    if financial_data['runway_months'] < 6:
        insights.append({
            "type": "warning",
            "title": "Low Runway Alert",
            "description": f"Only {financial_data['runway_months']:.1f} months of runway remaining"
        })
    
    # Revenue growth
    if variances.get('revenue_variance', {}).get('percent', 0) > 10:
        insights.append({
            "type": "positive",
            "title": "Revenue Growth",
            "description": f"Revenue increased {variances['revenue_variance']['percent']:.1f}% from prior period"
        })
    
    # Expense increase
    if variances.get('expense_variance', {}).get('percent', 0) > 15:
        insights.append({
            "type": "attention",
            "title": "Expense Spike",
            "description": f"Expenses increased {variances['expense_variance']['percent']:.1f}% - investigation recommended"
        })
    
    return insights


def generate_fallback_narrative(financial_data: dict, variances: dict) -> str:
    """Generate simple narrative without LLM"""
    return f"""Financial Summary for {financial_data['period']}

The company ended the period with ${financial_data['cash_balance']:,.2f} in cash. 
Revenue for the period was ${financial_data['revenue']:,.2f}, while expenses totaled ${financial_data['expenses']:,.2f}.

The current monthly burn rate is ${financial_data['burn_rate']:,.2f}, resulting in a runway of {financial_data['runway_months']:.1f} months.

Key variances from the prior period should be reviewed for strategic planning purposes.
"""
