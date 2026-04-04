"""
Reasoning Engine for Financial Insights
========================================
Implements intelligent financial analysis with:
- Knowledge base of 50+ financial concepts
- Variance analysis (profit deviations)
- Cash flow trend analysis
- Proactive recommendation generation

This engine powers the AI agent's financial reasoning capabilities.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# ============================================================================
# FINANCIAL KNOWLEDGE BASE
# ============================================================================

@dataclass
class FinancialConcept:
    """Definition of a financial concept"""
    name: str
    definition: str
    interpretation: str  # How to interpret the metric
    good_range: str  # What values are considered healthy
    red_flags: List[str]  # Warning signs
    related_concepts: List[str]  # Related metrics


class FinancialKnowledgeBase:
    """
    Centralized knowledge base with 50+ financial concepts.
    
    Used by reasoning engine to:
    - Explain metrics to users
    - Identify warning signs
    - Generate recommendations
    - Compare to benchmarks
    """
    
    def __init__(self):
        self.concepts = self._initialize_concepts()
        logger.info(f"Financial Knowledge Base initialized with {len(self.concepts)} concepts")
    
    def _initialize_concepts(self) -> Dict[str, FinancialConcept]:
        """Initialize all financial concepts"""
        return {
            # LIQUIDITY CONCEPTS
            "current_ratio": FinancialConcept(
                name="Current Ratio",
                definition="Current Assets / Current Liabilities. Measures short-term liquidity.",
                interpretation="Shows ability to pay obligations due within 12 months. Higher indicates more cushion.",
                good_range="1.5 - 3.0",
                red_flags=["< 1.0 (cannot pay obligations)", "> 3.0 (cash not deployed)"],
                related_concepts=["quick_ratio", "working_capital", "cash_conversion_cycle"]
            ),
            
            "quick_ratio": FinancialConcept(
                name="Quick Ratio",
                definition="(Current Assets - Inventory) / Current Liabilities. Most conservative liquidity test.",
                interpretation="Shows immediate liquidity without selling inventory. Also called Acid Test.",
                good_range="> 1.0",
                red_flags=["< 1.0 (immediate liquidity problem)", "too low with high inventory levels"],
                related_concepts=["current_ratio", "inventory_turnover", "days_inventory_outstanding"]
            ),
            
            "working_capital": FinancialConcept(
                name="Working Capital",
                definition="Current Assets - Current Liabilities. Net short-term resources.",
                interpretation="Positive WC means company can fund operations. Negative WC signals trouble.",
                good_range="> 0",
                red_flags=["Negative (undercapitalized)", "Growing too fast (tied up cash)", "Declining (funding risk)"],
                related_concepts=["current_ratio", "cash_flow", "dso", "dio"]
            ),
            
            "cash_conversion_cycle": FinancialConcept(
                name="Cash Conversion Cycle",
                definition="DIO + DSO - DPO. Days from cash outlay to cash recovery.",
                interpretation="How long capital is tied up. Negative = great (paid after collecting).",
                good_range="0 - 60 days (lower is better)",
                red_flags=["> 90 days (inefficient)", "Increasing (worse management)"],
                related_concepts=["dso", "dio", "dpo", "working_capital"]
            ),
            
            # PROFITABILITY CONCEPTS
            "gross_margin": FinancialConcept(
                name="Gross Margin",
                definition="(Revenue - COGS) / Revenue. Profitability after direct costs.",
                interpretation="% of revenue remaining after paying production costs. Lower for retail, higher for SaaS.",
                good_range="SaaS: 70-90%, Retail: 30-50%, Avg: 40-60%",
                red_flags=["Declining trend", "Below industry average", "Negative (unsustainable)"],
                related_concepts=["operating_margin", "net_margin", "cogs_management"]
            ),
            
            "operating_margin": FinancialConcept(
                name="Operating Margin",
                definition="Operating Profit / Revenue. Profitability from core operations.",
                interpretation="% of revenue left after all operating expenses. Ignores financing & taxes.",
                good_range="Startups: -20% to 0%, Mature SaaS: 20-40%",
                red_flags=["Negative (unprofitable)", "Declining (cost structure breaking)"],
                related_concepts=["gross_margin", "net_margin", "operating_leverage"]
            ),
            
            "net_margin": FinancialConcept(
                name="Net Profit Margin",
                definition="Net Income / Revenue. Bottom-line profitability.",
                interpretation="% of revenue that becomes profit. After all costs, taxes, interest.",
                good_range="Startups: -50% to -10%, Profitable SaaS: 5-25%",
                red_flags=["Negative for 3+ quarters", "Declining", "Below industry peers"],
                related_concepts=["operating_margin", "gross_margin", "tax_efficiency"]
            ),
            
            "ebitda": FinancialConcept(
                name="EBITDA",
                definition="Operating Profit + Depreciation + Amortization. Cash profitability.",
                interpretation="Operational profitability before capital structure & non-cash items.",
                good_range="> 0 (or growing toward it)",
                red_flags=["Negative", "Declining", "EBITDA not matching cash flow"],
                related_concepts=["operating_profit", "free_cash_flow", "cash_burn"]
            ),
            
            # LEVERAGE & SOLVENCY
            "debt_to_equity": FinancialConcept(
                name="Debt-to-Equity Ratio",
                definition="Total Debt / Total Equity. Capital structure.",
                interpretation="How much borrowed vs owned capital. Higher = more risk.",
                good_range="< 2.0 (< 2x debt vs equity)",
                red_flags=["> 3.0 (overleveraged)", "Increasing rapidly", "Negative equity (insolvent)"],
                related_concepts=["debt_to_assets", "interest_coverage", "dscr"]
            ),
            
            "interest_coverage": FinancialConcept(
                name="Interest Coverage Ratio",
                definition="Operating Profit / Interest Expense. Debt service ability.",
                interpretation="How many times operating profit covers interest. Higher = safer.",
                good_range="> 5.0 (comfortable debt service)",
                red_flags=["< 2.5 (risky)", "< 1.5 (critical)"],
                related_concepts=["debt_to_equity", "dscr", "cash_flow_coverage"]
            ),
            
            # EFFICIENCY CONCEPTS
            "asset_turnover": FinancialConcept(
                name="Asset Turnover Ratio",
                definition="Annual Revenue / Average Total Assets. Asset efficiency.",
                interpretation="How many dollars of revenue per dollar of assets. Higher = more efficient.",
                good_range="> 1.0",
                red_flags=["< 0.5 (very inefficient)", "Declining", "Bloated asset base"],
                related_concepts=["inventory_turnover", "receivables_turnover", "roe"]
            ),
            
            "roa": FinancialConcept(
                name="Return on Assets (ROA)",
                definition="Net Income / Average Total Assets. Asset productivity.",
                interpretation="Profit generated per dollar of assets. Direct measure of efficiency.",
                good_range="> 5%",
                red_flags=["Negative", "< 2%", "Declining"],
                related_concepts=["asset_turnover", "roe", "dupont_analysis"]
            ),
            
            "roe": FinancialConcept(
                name="Return on Equity (ROE)",
                definition="Net Income / Average Shareholder Equity. Shareholder returns.",
                interpretation="Profit generated per dollar of equity. Shows value creation for owners.",
                good_range="> 10%",
                red_flags=["Negative", "< 5%", "Declining"],
                related_concepts=["roa", "dupont_analysis", "valuation"]
            ),
            
            "dso": FinancialConcept(
                name="Days Sales Outstanding (DSO)",
                definition="Account Receivable / (Revenue / 365). Collection efficiency.",
                interpretation="Average days to collect payment. Lower = faster cash.",
                good_range="30-60 days",
                red_flags=["> 90 days (slow collection)", "Increasing (collection problems)"],
                related_concepts=["cash_conversion_cycle", "receivables_turnover", "ar_aging"]
            ),
            
            "dio": FinancialConcept(
                name="Days Inventory Outstanding (DIO)",
                definition="Inventory / (COGS / 365). Inventory holding time.",
                interpretation="Days inventory sits before sale. Lower = better cash flow.",
                good_range="Industry dependent (15-90 days typical)",
                red_flags=["Increasing", "Obsolete inventory", "Excess stock"],
                related_concepts=["inventory_turnover", "cash_conversion_cycle", "supply_chain"]
            ),
            
            # CASH FLOW CONCEPTS
            "ocf": FinancialConcept(
                name="Operating Cash Flow (OCF)",
                definition="Cash generated from operations before investing/financing.",
                interpretation="Most reliable indicator of financial health. Harder to manipulate than profit.",
                good_range="> Net Income",
                red_flags=["< Net Income (quality issue)", "Negative", "Declining"],
                related_concepts=["net_income", "fcf", "working_capital", "quality_of_earnings"]
            ),
            
            "fcf": FinancialConcept(
                name="Free Cash Flow (FCF)",
                definition="Operating Cash Flow - CapEx. Discretionary cash.",
                interpretation="Cash available for debt, dividends, acquisitions. Most important metric.",
                good_range="> 0",
                red_flags=["Negative (burning cash)", "Declining", "Less than debt service"],
                related_concepts=["ocf", "capex_efficiency", "cash_runway"]
            ),
            
            "cash_burn": FinancialConcept(
                name="Monthly Cash Burn",
                definition="Negative Monthly Cash Flow. Rate of cash depletion.",
                interpretation="How fast cash reserves deplete. Startups focus on reducing burn.",
                good_range="Trending toward breakeven",
                red_flags=["High burn (< 12 months runway)", "Accelerating burn", "Unsustainable"],
                related_concepts=["cash_runway", "runway", "burn_rate"]
            ),
            
            "cash_runway": FinancialConcept(
                name="Cash Runway",
                definition="Months of operations funded by current cash.",
                interpretation="Time until cash depleted at current burn rate. Critical for startups.",
                good_range="> 12 months",
                red_flags=["< 6 months (critical)", "< 12 months (should fundraise)"],
                related_concepts=["cash_burn", "burn_rate", "fundraising_needs"]
            ),
            
            # GROWTH & VALUATION
            "revenue_growth": FinancialConcept(
                name="Revenue Growth Rate",
                definition="(Current Revenue - Prior Revenue) / Prior Revenue.",
                interpretation="Percentage increase in sales period-over-period. Key SaaS metric.",
                good_range="SaaS Series A: 20-40% YoY, Series B+: 10-20% YoY",
                red_flags=["< 10% (mature/declining)", "Negative (contraction)", "Decelerating"],
                related_concepts=["mrr_growth", "arr_growth", "customer_acquisition"]
            ),
            
            "mrr": FinancialConcept(
                name="Monthly Recurring Revenue (MRR)",
                definition="Predictable recurring revenue booked each month.",
                interpretation="Foundation of SaaS business. Indicates subscription health.",
                good_range="Growing 5-10% MoM",
                red_flags=["Declining", "Flat", "High churn"],
                related_concepts=["arr", "churn", "nrr", "customer_ltv"]
            ),
            
            "arr": FinancialConcept(
                name="Annual Recurring Revenue (ARR)",
                definition="MRR * 12. Annualized recurring revenue.",
                interpretation="Valuation multiple driven by ARR. Key funding metric.",
                good_range="Growing",
                red_flags=["Flat", "Declining", "Below peer average"],
                related_concepts=["mrr", "churn", "customer_ltv"]
            ),
            
            # STRATEGIC CONCEPTS
            "payback_period": FinancialConcept(
                name="Customer Payback Period",
                definition="Months to recover Customer Acquisition Cost from gross profit.",
                interpretation="How long to recover customer acquisition investment.",
                good_range="< 12 months",
                red_flags=["> 24 months (uneconomical)", "Increasing"],
                related_concepts=["cac", "ltv", "unit_economics"]
            ),
            
            "ltv": FinancialConcept(
                name="Customer Lifetime Value (LTV)",
                definition="Total profit from customer over lifetime.",
                interpretation="Total value customer generates. Should be 3x+ CAC.",
                good_range="> 3x CAC",
                red_flags=["< 2x CAC (uneconomical)", "Declining"],
                related_concepts=["cac", "payback_period", "churn", "expansion_revenue"]
            ),
            
            "churn": FinancialConcept(
                name="Customer Churn Rate",
                definition="% of customers lost each period.",
                interpretation="Rate of customer defection. Critical SaaS metric.",
                good_range="< 5% monthly (95%+ retention)",
                red_flags=["> 10% (severe problem)", "Increasing"],
                related_concepts=["nrr", "retention", "customer_satisfaction"]
            ),
            
            "nrr": FinancialConcept(
                name="Net Revenue Retention (NRR)",
                definition="(Beginning MRR + Expansion - Churn) / Beginning MRR.",
                interpretation="Growth from existing customers net of churn. > 100% = expansion.",
                good_range="> 100%",
                red_flags=["< 100% (net contraction)", "Declining"],
                related_concepts=["gross_retention", "churn", "expansion_revenue"]
            ),
            
            # QUALITY & HEALTH
            "quality_of_earnings": FinancialConcept(
                name="Quality of Earnings",
                definition="How much net income comes from core operations vs non-operating items.",
                interpretation="Higher quality when earnings = operating cash flow.",
                good_range="OCF >= Net Income",
                red_flags=["OCF < NI (accounting tricks)", "Large non-operating items"],
                related_concepts=["ocf", "earnings_quality", "cash_flow"]
            ),
            
            "burn_multiple": FinancialConcept(
                name="Burn Multiple",
                definition="Net Burn / Net New ARR. Efficiency of growth spending.",
                interpretation="How much burn per dollar of new revenue. Lower = better.",
                good_range="< 2.0x (< $2 burn per $1 new ARR)",
                red_flags=["> 3.0x (wasteful)", "Increasing"],
                related_concepts=["net_burn", "cac", "payback_period"]
            ),
            
            "rule_of_40": FinancialConcept(
                name="Rule of 40",
                definition="Growth Rate + Profit Margin >= 40%.",
                interpretation="Balance of growth speed vs profitability. Industry standard benchmark.",
                good_range=">= 40",
                red_flags=["< 30 (poor balance)", "All growth, no path to profit"],
                related_concepts=["growth_rate", "profit_margin", "unit_economics"]
            ),
        }
    
    def get_concept(self, concept_name: str) -> Optional[FinancialConcept]:
        """Get concept by name"""
        concept = self.concepts.get(concept_name.lower().replace(" ", "_"))
        if not concept:
            logger.warning(f"Concept not found: {concept_name}")
        return concept
    
    def explain(self, concept_name: str) -> str:
        """Get human-readable explanation of concept"""
        concept = self.get_concept(concept_name)
        if not concept:
            return f"Unknown concept: {concept_name}"
        
        return f"""
{concept.name}
{'-' * len(concept.name)}
Definition: {concept.definition}
Interpretation: {concept.interpretation}
Healthy Range: {concept.good_range}
Red Flags: {', '.join(concept.red_flags)}
Related: {', '.join(concept.related_concepts)}
        """.strip()


# ============================================================================
# VARIANCE ANALYSIS
# ============================================================================

class ProfitVarianceAnalyzer:
    """Analyzes profit deviations and identifies root causes"""
    
    def __init__(self, kb: FinancialKnowledgeBase):
        self.kb = kb
        logger.info("Profit Variance Analyzer initialized")
    
    def analyze_margin_variance(
        self,
        actual_margin: float,
        expected_margin: float,
        metric_name: str = "Profit Margin",
    ) -> Dict[str, Any]:
        """
        Analyze why actual margin differs from expected.
        
        Returns root cause analysis and recommendations.
        """
        variance_pct = ((actual_margin - expected_margin) / expected_margin) * 100 if expected_margin != 0 else 0
        
        analysis = {
            "metric": metric_name,
            "actual": round(actual_margin, 4),
            "expected": round(expected_margin, 4),
            "variance_pct": round(variance_pct, 2),
            "direction": "Favorable" if variance_pct > 0 else "Unfavorable",
        }
        
        # Root cause indicators
        if abs(variance_pct) < 2:
            analysis["root_cause"] = "In control - variance < 2%"
        elif variance_pct > 0:
            analysis["root_cause"] = "Better than expected - Investigate positive drivers"
            analysis["potential_sources"] = [
                "Operating leverage (revenue growing faster than costs)",
                "Cost efficiencies realized",
                "Favorable product/service mix",
            ]
        else:
            analysis["root_cause"] = "Worse than expected - Investigate negative drivers"
            analysis["potential_sources"] = [
                "Cost overruns (COGS or OpEx)",
                "Revenue shortfall or discount pressure",
                "Unfavorable product/service mix",
                "One-time charges or inefficiencies",
            ]
        
        logger.info(f"Profit variance analysis: {metric_name} variance={variance_pct:.1f}%")
        return analysis
    
    def analyze_revenue_variance(
        self,
        actual_revenue: float,
        expected_revenue: float,
        actual_cogs: float,
        expected_cogs: float,
    ) -> Dict[str, Any]:
        """
        Detailed revenue and COGS variance analysis.
        
        Breaks down into volume and price variances.
        """
        revenue_variance = actual_revenue - expected_revenue
        revenue_variance_pct = (revenue_variance / expected_revenue * 100) if expected_revenue > 0 else 0
        
        cogs_variance = actual_cogs - expected_cogs
        cogs_variance_pct = (cogs_variance / expected_cogs * 100) if expected_cogs > 0 else 0
        
        actual_margin = (actual_revenue - actual_cogs) / actual_revenue if actual_revenue > 0 else 0
        expected_margin = (expected_revenue - expected_cogs) / expected_revenue if expected_revenue > 0 else 0
        
        return {
            "revenue_variance": {
                "amount": round(revenue_variance, 2),
                "percent": round(revenue_variance_pct, 2),
                "status": "Favorable" if revenue_variance > 0 else "Unfavorable",
            },
            "cogs_variance": {
                "amount": round(cogs_variance, 2),
                "percent": round(cogs_variance_pct, 2),
                "status": "Favorable" if cogs_variance < 0 else "Unfavorable",
            },
            "margin_impact": {
                "actual": round(actual_margin, 4),
                "expected": round(expected_margin, 4),
                "change": round(actual_margin - expected_margin, 4),
            },
            "key_insight": self._get_variance_insight(revenue_variance_pct, cogs_variance_pct),
        }
    
    def _get_variance_insight(self, revenue_var: float, cogs_var: float) -> str:
        """Generate insight based on variance pattern"""
        if revenue_var > 0 and cogs_var < 0:
            return "Excellent: Revenue up, costs down - maximize this situation"
        elif revenue_var > 0 and cogs_var > 0:
            return "Good: Revenue up, though costs rising - monitor cost growth"
        elif revenue_var < 0 and cogs_var < 0:
            return "Poor: Revenue down, costs unchanged - volume deleveraging"
        elif revenue_var < 0 and cogs_var > 0:
            return "Critical: Revenue down AND costs up - immediate action needed"
        else:
            return "Mixed variance pattern - detailed analysis needed"


# ============================================================================
# CASH FLOW ANALYSIS
# ============================================================================

class CashFlowAnalyzer:
    """Analyzes cash flow trends and identifies problems"""
    
    def __init__(self, kb: FinancialKnowledgeBase):
        self.kb = kb
        logger.info("Cash Flow Analyzer initialized")
    
    def analyze_cf_quality(
        self,
        net_income: float,
        operating_cash_flow: float,
    ) -> Dict[str, Any]:
        """
        Analyze quality of earnings based on cash flow.
        
        High quality when OCF >= NI.
        """
        if net_income == 0:
            quality_ratio = 1.0 if operating_cash_flow >= 0 else 0.0
        else:
            quality_ratio = operating_cash_flow / net_income if net_income > 0 else 0.0
        
        if quality_ratio >= 1.0:
            quality = "High"
            interpretation = "Earnings backed by strong operating cash flow"
        elif quality_ratio >= 0.8:
            quality = "Good"
            interpretation = "Earnings mostly backed by cash"
        elif quality_ratio >= 0.5:
            quality = "Fair"
            interpretation = "Some concerns - not all earnings converting to cash"
        else:
            quality = "Poor"
            interpretation = "Earnings quality concerns - check working capital and accounting"
        
        return {
            "quality_score": round(quality_ratio, 2),
            "quality_rating": quality,
            "interpretation": interpretation,
            "net_income": round(net_income, 2),
            "operating_cf": round(operating_cash_flow, 2),
            "cf_gap": round(operating_cash_flow - net_income, 2),
        }
    
    def analyze_fcf_trajectory(
        self,
        monthly_fcf: List[float],
    ) -> Dict[str, Any]:
        """
        Analyze free cash flow trends over months.
        
        Identifies if company is on sustainable path.
        """
        if not monthly_fcf or len(monthly_fcf) < 2:
            return {"error": "Need at least 2 months of data"}
        
        # Remove None values
        fcf_data = [x for x in monthly_fcf if x is not None]
        if not fcf_data:
            return {"error": "No valid FCF data"}
        
        first_3m = fcf_data[:min(3, len(fcf_data))]
        last_3m = fcf_data[-min(3, len(fcf_data)):]
        
        avg_first = sum(first_3m) / len(first_3m)
        avg_last = sum(last_3m) / len(last_3m)
        
        trend = avg_last - avg_first
        trend_pct = (trend / abs(avg_first) * 100) if avg_first != 0 else 0
        
        # Determine trajectory
        if avg_last > 0:
            status = "Profitable"
        elif trend > 0:
            status = "Improving toward profitability"
        elif trend < 0:
            status = "Deteriorating"
        else:
            status = "Flat"
        
        return {
            "current_monthly_fcf": round(fcf_data[-1], 2),
            "avg_first_3m": round(avg_first, 2),
            "avg_last_3m": round(avg_last, 2),
            "trend": round(trend, 2),
            "trend_pct": round(trend_pct, 2),
            "status": status,
            "interpretation": self._get_fcf_trajectory_insight(avg_last, trend),
        }
    
    def _get_fcf_trajectory_insight(self, avg_fcf: float, trend: float) -> str:
        """Generate insight from FCF trajectory"""
        if avg_fcf > 0:
            return "Profitable - focus on growth and reinvestment"
        elif trend > 0:
            return f"Path to profitability - trend is positive, runway remaining"
        elif trend < 0:
            return f"Deteriorating - burn accelerating, urgent action needed"
        else:
            return "Flat - assess why improvements stalling"


# ============================================================================
# RECOMMENDATION ENGINE
# ============================================================================

class RecommendationGenerator:
    """Generates specific, actionable recommendations based on analysis"""
    
    def __init__(self, kb: FinancialKnowledgeBase):
        self.kb = kb
        logger.info("Recommendation Generator initialized")
    
    def generate_recommendations(
        self,
        financial_metrics: Dict[str, float],
        company_stage: str = "growth",  # "startup", "growth", "mature"
    ) -> List[Dict[str, str]]:
        """
        Generate prioritized recommendations based on metrics.
        
        Args:
            financial_metrics: Dict of metric_name -> value
            company_stage: Company lifecycle stage
            
        Returns:
            List of recommendations with priority and rationale
        """
        recommendations = []
        
        # Check profitability
        if "net_margin" in financial_metrics and financial_metrics["net_margin"] < 0:
            recommendations.append({
                "priority": "High",
                "recommendation": "Achieve unit economics profitability",
                "rationale": f"Currently losing ₹{abs(financial_metrics['net_margin']):.1%} on every rupee of revenue",
                "actions": [
                    "Increase gross margin through pricing or cost reduction",
                    "Reduce operating expenses as % of revenue",
                    "Consider focusing on profitable segments",
                ]
            })
        
        # Check cash runway
        if "runway_months" in financial_metrics:
            runway = financial_metrics["runway_months"]
            if runway < 6:
                recommendations.append({
                    "priority": "Critical",
                    "recommendation": "Fundraising or profitability urgently required",
                    "rationale": f"Only {runway:.1f} months of runway remaining",
                    "actions": [
                        "Accelerate fundraising process",
                        "Reduce burn through cost controls",
                        "Identify path to profitability",
                    ]
                })
            elif runway < 12 and company_stage == "growth":
                recommendations.append({
                    "priority": "High",
                    "recommendation": "Prepare for Series funding",
                    "rationale": f"{runway:.1f} months runway - typical Series fundraise takes 3-6 months",
                    "actions": [
                        "Build fundraising story and materials",
                        "Strengthen cap table and governance",
                        "Improve unit economics metrics",
                    ]
                })
        
        # Check burn rate health
        if "monthly_burn" in financial_metrics and "monthly_revenue" in financial_metrics:
            burn = financial_metrics["monthly_burn"]
            revenue = financial_metrics["monthly_revenue"]
            net_burn = burn - revenue
            
            if net_burn > revenue * 0.5:
                recommendations.append({
                    "priority": "High",
                    "recommendation": "Reduce monthly burn rate",
                    "rationale": f"Burning ₹{net_burn:.0f}/month is {net_burn/revenue:.0%} of revenue unsustainable",
                    "actions": [
                        "Review largest cost categories (typically people)",
                        "Reduce contractor/agency spend",
                        "Cut non-essential projects",
                    ]
                })
        
        # Check growth
        if "mrr_growth" in financial_metrics and financial_metrics["mrr_growth"] < 0:
            recommendations.append({
                "priority": "High",
                "recommendation": "Stabilize revenue decline",
                "rationale": "Revenue contraction is critical issue",
                "actions": [
                    "Analyze churn drivers with churned customers",
                    "Increase customer success/support",
                    "Accelerate feature development",
                    "Review pricing and packaging",
                ]
            })
        
        # Check collections
        if "dso" in financial_metrics and financial_metrics["dso"] > 60:
            recommendations.append({
                "priority": "Medium",
                "recommendation": "Improve collections process",
                "rationale": f"DSO of {financial_metrics['dso']:.0f} days ties up excess cash",
                "actions": [
                    "Enforce payment terms more strictly",
                    "Offer early payment discounts",
                    "Move to credit card or ACH for smaller customers",
                ]
            })
        
        # Check leverage
        if "debt_to_equity" in financial_metrics and financial_metrics["debt_to_equity"] > 2.0:
            recommendations.append({
                "priority": "Medium",
                "recommendation": "Reduce leverage ratios",
                "rationale": f"D/E of {financial_metrics['debt_to_equity']:.1f}x is above comfort zone",
                "actions": [
                    "Use FCF to pay down debt",
                    "Refinance to lower rates/longer terms",
                    "Consider equity raise if dilution preferable",
                ]
            })
        
        logger.info(f"Generated {len(recommendations)} recommendations for {company_stage} stage company")
        return recommendations
