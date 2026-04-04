"""
Financial Analysis API Routes
==============================
FastAPI endpoints for financial analysis and recommendations.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

try:
    from services.financial_functions import (
        # Cash Flow Functions
        operating_cash_flow,
        investing_cash_flow,
        financing_cash_flow,
        free_cash_flow,
        cash_conversion_cycle,
        cash_runway_extended,
        # Profitability Functions
        gross_profit,
        operating_profit,
        net_profit,
        ebitda,
        profit_margins,
        # Working Capital Functions
        current_ratio,
        quick_ratio,
        working_capital,
        working_capital_to_revenue,
        # Leverage Functions
        debt_to_equity_ratio,
        debt_to_assets_ratio,
        interest_coverage_ratio,
        debt_service_coverage_ratio,
        # Efficiency Functions
        asset_turnover_ratio,
        inventory_turnover_ratio,
        receivables_turnover_ratio,
        return_on_assets,
        # Valuation Functions
        price_to_earnings_ratio,
        price_to_sales_ratio,
        enterprise_value_to_ebitda,
        # Benchmarking
        metric_vs_benchmark,
        financial_health_score,
    )

    from services.reasoning_engine import (
        FinancialKnowledgeBase,
        ProfitVarianceAnalyzer,
        CashFlowAnalyzer,
        RecommendationGenerator,
    )
except ImportError:
    from backend.services.financial_functions import (
        # Cash Flow Functions
        operating_cash_flow,
        investing_cash_flow,
        financing_cash_flow,
        free_cash_flow,
        cash_conversion_cycle,
        cash_runway_extended,
        # Profitability Functions
        gross_profit,
        operating_profit,
        net_profit,
        ebitda,
        profit_margins,
        # Working Capital Functions
        current_ratio,
        quick_ratio,
        working_capital,
        working_capital_to_revenue,
        # Leverage Functions
        debt_to_equity_ratio,
        debt_to_assets_ratio,
        interest_coverage_ratio,
        debt_service_coverage_ratio,
        # Efficiency Functions
        asset_turnover_ratio,
        inventory_turnover_ratio,
        receivables_turnover_ratio,
        return_on_assets,
        # Valuation Functions
        price_to_earnings_ratio,
        price_to_sales_ratio,
        enterprise_value_to_ebitda,
        # Benchmarking
        metric_vs_benchmark,
        financial_health_score,
    )

    from backend.services.reasoning_engine import (
        FinancialKnowledgeBase,
        ProfitVarianceAnalyzer,
        CashFlowAnalyzer,
        RecommendationGenerator,
    )

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/financial",
    tags=["financial"],
    responses={404: {"description": "Not found"}},
)

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class CashFlowInput(BaseModel):
    """Cash flow analysis input"""
    operating_cash_flow: float = Field(..., gt=0, description="Operating cash flow (₹)")
    investing_cash_flow: float = Field(..., description="Investing cash flow (₹)")
    financing_cash_flow: float = Field(..., description="Financing cash flow (₹)")
    capex: float = Field(0, ge=0, description="Capital expenditure (₹)")
    net_income: float = Field(..., description="Net income (₹)")


class ProfitabilityInput(BaseModel):
    """Profitability analysis input"""
    revenue: float = Field(..., gt=0, description="Total revenue (₹)")
    cogs: float = Field(..., ge=0, description="Cost of goods sold (₹)")
    operating_expenses: float = Field(..., ge=0, description="Operating expenses (₹)")
    interest_expense: float = Field(0, ge=0, description="Interest expense (₹)")
    tax_expense: float = Field(0, ge=0, description="Tax expense (₹)")


class LiquidityInput(BaseModel):
    """Liquidity analysis input"""
    current_assets: float = Field(..., gt=0, description="Current assets (₹)")
    current_liabilities: float = Field(..., gt=0, description="Current liabilities (₹)")
    inventory: float = Field(0, ge=0, description="Inventory (₹)")


class LeverageInput(BaseModel):
    """Leverage analysis input"""
    total_debt: float = Field(..., ge=0, description="Total debt (₹)")
    total_equity: float = Field(..., gt=0, description="Total equity (₹)")
    operating_profit: float = Field(..., description="Operating profit/EBIT (₹)")
    interest_expense: float = Field(..., ge=0, description="Interest expense (₹)")


class ComprehensiveAnalysisInput(BaseModel):
    """Comprehensive financial analysis input"""
    company_id: str = Field(..., description="Company identifier")
    company_stage: str = Field("growth", description="Company stage: startup, growth, or mature")
    
    # Income Statement
    revenue: float = Field(..., gt=0, description="Annual revenue (₹)")
    cogs: float = Field(..., ge=0, description="Cost of goods sold (₹)")
    operating_expenses: float = Field(..., ge=0, description="Operating expenses (₹)")
    interest_expense: float = Field(0, ge=0, description="Interest expense (₹)")
    tax_expense: float = Field(0, ge=0, description="Tax expense (₹)")
    
    # Balance Sheet
    current_assets: float = Field(..., gt=0, description="Current assets (₹)")
    inventory: float = Field(0, ge=0, description="Inventory (₹)")
    total_assets: float = Field(..., gt=0, description="Total assets (₹)")
    current_liabilities: float = Field(..., gt=0, description="Current liabilities (₹)")
    total_debt: float = Field(0, ge=0, description="Total debt (₹)")
    total_equity: float = Field(..., gt=0, description="Total equity (₹)")
    
    # Cash Flow
    operating_cash_flow: float = Field(..., description="Operating cash flow (₹)")
    capex: float = Field(0, ge=0, description="Capital expenditure (₹)")
    
    # Additional Metrics
    cash_balance: float = Field(..., ge=0, description="Cash on hand (₹)")
    monthly_burn: float = Field(0, ge=0, description="Monthly cash burn (₹)")
    market_cap: Optional[float] = Field(None, ge=0, description="Market capitalization (₹)")
    
    # Working Capital Details
    dso: float = Field(45, ge=0, description="Days sales outstanding")
    dio: float = Field(30, ge=0, description="Days inventory outstanding")
    dpo: float = Field(45, ge=0, description="Days payable outstanding")


class RecommendationInput(BaseModel):
    """Request recommendations input"""
    company_id: str = Field(..., description="Company identifier")
    company_stage: str = Field("growth", description="Company stage")
    financial_metrics: Dict[str, float] = Field(..., description="Financial metrics")


# ============================================================================
# CASH FLOW ENDPOINTS
# ============================================================================

@router.post("/analyze/cash-flow", tags=["cash-flow"])
async def analyze_cash_flow(input_data: CashFlowInput) -> Dict[str, Any]:
    """
    Analyze cash flow statement
    
    Returns: Operating, investing, financing cash flows and free cash flow
    """
    try:
        fcf = free_cash_flow(input_data.operating_cash_flow, input_data.capex)
        
        kb = FinancialKnowledgeBase()
        analyzer = CashFlowAnalyzer(kb)
        
        cf_quality = analyzer.analyze_cf_quality(
            input_data.net_income,
            input_data.operating_cash_flow
        )
        
        return {
            "status": "success",
            "analysis_date": datetime.now().isoformat(),
            "cash_flows": {
                "operating_cash_flow": round(input_data.operating_cash_flow, 2),
                "investing_cash_flow": round(input_data.investing_cash_flow, 2),
                "financing_cash_flow": round(input_data.financing_cash_flow, 2),
                "net_change_in_cash": round(
                    input_data.operating_cash_flow +
                    input_data.investing_cash_flow +
                    input_data.financing_cash_flow,
                    2
                ),
                "free_cash_flow": round(fcf, 2),
            },
            "quality_assessment": cf_quality,
        }
    except Exception as e:
        logger.error(f"Error analyzing cash flow: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/calculate/runway", tags=["cash-flow"])
async def calculate_runway(
    cash_balance: float = Query(..., gt=0, description="Current cash (₹)"),
    monthly_burn: float = Query(..., ge=0, description="Monthly burn (₹)"),
    monthly_revenue: float = Query(0, ge=0, description="Monthly revenue (₹)"),
    growth_rate: float = Query(0, ge=0, description="Monthly growth rate"),
) -> Dict[str, Any]:
    """
    Calculate cash runway estimate
    
    Returns: Months of runway at current burn rate
    """
    try:
        result = cash_runway_extended(cash_balance, monthly_burn, monthly_revenue, growth_rate)
        
        return {
            "status": "success",
            "analysis_date": datetime.now().isoformat(),
            **result,
        }
    except Exception as e:
        logger.error(f"Error calculating runway: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/analyze/working-capital", tags=["cash-flow"])
async def analyze_working_capital(input_data: LiquidityInput) -> Dict[str, Any]:
    """Analyze working capital"""
    try:
        cr = current_ratio(input_data.current_assets, input_data.current_liabilities)
        qr = quick_ratio(input_data.current_assets, input_data.inventory, input_data.current_liabilities)
        wc = working_capital(input_data.current_assets, input_data.current_liabilities)
        
        return {
            "status": "success",
            "analysis_date": datetime.now().isoformat(),
            "liquidity_metrics": {
                "current_ratio": round(cr, 2),
                "quick_ratio": round(qr, 2),
                "working_capital": round(wc, 2),
                "current_assets": round(input_data.current_assets, 2),
                "current_liabilities": round(input_data.current_liabilities, 2),
            },
            "assessment": {
                "liquidity_status": "Healthy" if cr >= 1.5 else "Tight" if cr >= 1.0 else "Critical",
                "quick_assessment": "Good" if qr >= 1.0 else "At Risk",
            }
        }
    except Exception as e:
        logger.error(f"Error analyzing working capital: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# PROFITABILITY ENDPOINTS
# ============================================================================

@router.post("/analyze/profitability", tags=["profitability"])
async def analyze_profitability(input_data: ProfitabilityInput) -> Dict[str, Any]:
    """Analyze profitability metrics"""
    try:
        gp = gross_profit(input_data.revenue, input_data.cogs)
        op = operating_profit(gp, input_data.operating_expenses)
        np = op - input_data.interest_expense - input_data.tax_expense
        eb = ebitda(op, 0, 0)  # Assuming no D&A provided

        margins = {
            "gross_margin": round((gp / input_data.revenue) * 100, 2) if input_data.revenue > 0 else 0.0,
            "operating_margin": round((op / input_data.revenue) * 100, 2) if input_data.revenue > 0 else 0.0,
            "net_margin": round((np / input_data.revenue) * 100, 2) if input_data.revenue > 0 else 0.0,
        }
        
        return {
            "status": "success",
            "analysis_date": datetime.now().isoformat(),
            "profitability": {
                "revenue": round(input_data.revenue, 2),
                "gross_profit": round(gp, 2),
                "operating_profit": round(op, 2),
                "ebitda": round(eb, 2),
                "net_profit": round(np, 2),
                "net_profit_status": "Profitable" if np > 0 else "Unprofitable",
            },
            "margins": margins,
        }
    except Exception as e:
        logger.error(f"Error analyzing profitability: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# LEVERAGE ENDPOINTS
# ============================================================================

@router.post("/analyze/leverage", tags=["leverage"])
async def analyze_leverage(input_data: LeverageInput) -> Dict[str, Any]:
    """Analyze leverage and solvency"""
    try:
        de = debt_to_equity_ratio(input_data.total_debt, input_data.total_equity)
        da = debt_to_assets_ratio(input_data.total_debt, input_data.total_debt + input_data.total_equity)
        icr = interest_coverage_ratio(input_data.operating_profit, input_data.interest_expense)
        
        return {
            "status": "success",
            "analysis_date": datetime.now().isoformat(),
            "leverage_metrics": {
                "debt_to_equity": round(de, 2),
                "debt_to_assets": round(da, 2),
                "interest_coverage": round(icr, 2),
                "total_debt": round(input_data.total_debt, 2),
                "total_equity": round(input_data.total_equity, 2),
            },
            "leverage_assessment": {
                "debt_level": "Conservative" if de < 1.0 else "Moderate" if de < 2.0 else "High",
                "interest_coverage": "Healthy" if icr > 5.0 else "Adequate" if icr > 2.5 else "Stressed",
            }
        }
    except Exception as e:
        logger.error(f"Error analyzing leverage: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# COMPREHENSIVE ANALYSIS
# ============================================================================

@router.post("/analyze/comprehensive", tags=["comprehensive"])
async def comprehensive_analysis(input_data: ComprehensiveAnalysisInput) -> Dict[str, Any]:
    """
    Comprehensive financial analysis of a company
    
    Returns: All major metrics, ratios, assessments, and recommendations
    """
    try:
        logger.info(f"Starting comprehensive analysis for company {input_data.company_id}")
        
        # Calculate all metrics
        gp = gross_profit(input_data.revenue, input_data.cogs)
        op = operating_profit(gp, input_data.operating_expenses)
        np = net_profit(op, input_data.interest_expense, input_data.tax_expense)
        
        cr = current_ratio(input_data.current_assets, input_data.current_liabilities)
        wc = working_capital(input_data.current_assets, input_data.current_liabilities)
        ccc = cash_conversion_cycle(input_data.dio, input_data.dso, input_data.dpo)
        
        de = debt_to_equity_ratio(input_data.total_debt, input_data.total_equity)
        icr = interest_coverage_ratio(op, input_data.interest_expense)
        
        fcf = free_cash_flow(input_data.operating_cash_flow, input_data.capex)
        
        margins = profit_margins(input_data.revenue, gp, op, np)
        
        # Calculate health score
        profitability_score = min(1.0, np / input_data.revenue) if input_data.revenue > 0 else 0
        liquidity_score = min(1.0, cr / 2.0)
        leverage_score = max(0, min(1.0, 1.0 / de)) if de > 0 else 1.0
        efficiency_score = min(1.0, 1.0 / (ccc / 365)) if ccc > 0 else 0
        
        health = financial_health_score(profitability_score, liquidity_score, leverage_score, efficiency_score)
        
        # Generate recommendations
        kb = FinancialKnowledgeBase()
        rec_gen = RecommendationGenerator(kb)
        
        financial_metrics = {
            "revenue": input_data.revenue,
            "net_income": np,
            "gross_margin": margins.get("gross_margin", 0),
            "operating_margin": margins.get("operating_margin", 0),
            "net_margin": margins.get("net_margin", 0),
            "current_ratio": cr,
            "quick_ratio": 0,  # Simplified
            "debt_to_equity": de,
            "interest_coverage": icr,
            "cash_conversion_cycle": ccc,
            "cash_runway": input_data.cash_balance / input_data.monthly_burn if input_data.monthly_burn > 0 else float('inf'),
            "monthly_burn": input_data.monthly_burn,
            "free_cash_flow": fcf,
        }
        
        recommendations = rec_gen.generate_recommendations(financial_metrics, input_data.company_stage)
        
        logger.info(f"Comprehensive analysis completed for {input_data.company_id}")
        
        return {
            "status": "success",
            "analysis_date": datetime.now().isoformat(),
            "company_id": input_data.company_id,
            "company_stage": input_data.company_stage,
            
            # Income Statement
            "income_statement": {
                "revenue": round(input_data.revenue, 2),
                "cogs": round(input_data.cogs, 2),
                "gross_profit": round(gp, 2),
                "operating_expenses": round(input_data.operating_expenses, 2),
                "operating_profit": round(op, 2),
                "interest_expense": round(input_data.interest_expense, 2),
                "net_income": round(np, 2),
            },
            
            # Key Metrics
            "key_metrics": {
                "profitability": margins,
                "liquidity": {
                    "current_ratio": round(cr, 2),
                    "working_capital": round(wc, 2),
                },
                "leverage": {
                    "debt_to_equity": round(de, 2),
                    "interest_coverage": round(icr, 2),
                },
                "efficiency": {
                    "cash_conversion_cycle": round(ccc, 1),
                },
            },
            
            # Cash Flow
            "cash_flow": {
                "operating_cash_flow": round(input_data.operating_cash_flow, 2),
                "capex": round(input_data.capex, 2),
                "free_cash_flow": round(fcf, 2),
                "cash_balance": round(input_data.cash_balance, 2),
                "monthly_burn": round(input_data.monthly_burn, 2),
                "runway_months": round(input_data.cash_balance / input_data.monthly_burn, 1) if input_data.monthly_burn > 0 else "Profitable",
            },
            
            # Health Score
            "financial_health": health,
            
            # Recommendations
            "recommendations": recommendations,
            "recommendation_summary": {
                "total": len(recommendations),
                "critical": sum(1 for r in recommendations if r.get("priority") == "Critical"),
                "high": sum(1 for r in recommendations if r.get("priority") == "High"),
                "medium": sum(1 for r in recommendations if r.get("priority") == "Medium"),
            }
        }
    except Exception as e:
        logger.error(f"Error in comprehensive analysis: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# CONCEPT EXPLANATION
# ============================================================================

@router.get("/concepts/{concept_name}", tags=["knowledge"])
async def explain_concept(concept_name: str) -> Dict[str, Any]:
    """
    Get explanation of a financial concept
    
    Examples: current_ratio, gross_margin, debt_to_equity, cash_burn, etc.
    """
    try:
        kb = FinancialKnowledgeBase()
        concept = kb.get_concept(concept_name)
        
        if concept is None:
            raise HTTPException(status_code=404, detail=f"Concept '{concept_name}' not found")
        
        return {
            "status": "success",
            "concept_name": concept_name,
            "definition": concept.definition,
            "interpretation": concept.interpretation,
            "good_range": concept.good_range,
            "red_flags": concept.red_flags,
            "related_concepts": concept.related_concepts,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error explaining concept: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/concepts", tags=["knowledge"])
async def list_concepts() -> Dict[str, Any]:
    """List all available financial concepts"""
    try:
        kb = FinancialKnowledgeBase()
        concepts = [name for name in kb.concepts.keys()]
        
        return {
            "status": "success",
            "total_concepts": len(concepts),
            "concepts": sorted(concepts),
        }
    except Exception as e:
        logger.error(f"Error listing concepts: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# RECOMMENDATIONS
# ============================================================================

@router.post("/recommendations", tags=["recommendations"])
async def get_recommendations(input_data: RecommendationInput) -> Dict[str, Any]:
    """Generate financial recommendations"""
    try:
        kb = FinancialKnowledgeBase()
        rec_gen = RecommendationGenerator(kb)
        
        recommendations = rec_gen.generate_recommendations(
            input_data.financial_metrics,
            input_data.company_stage
        )
        
        return {
            "status": "success",
            "company_id": input_data.company_id,
            "company_stage": input_data.company_stage,
            "recommendation_count": len(recommendations),
            "recommendations": recommendations,
            "summary": {
                "critical": sum(1 for r in recommendations if r.get("priority") == "Critical"),
                "high": sum(1 for r in recommendations if r.get("priority") == "High"),
                "medium": sum(1 for r in recommendations if r.get("priority") == "Medium"),
            }
        }
    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get("/health", tags=["health"])
async def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "financial-analysis",
        "timestamp": datetime.now().isoformat(),
    }
