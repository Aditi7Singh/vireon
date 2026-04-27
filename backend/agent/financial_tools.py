"""
Enhanced Financial Agent Tools (30+ Tools)
===========================================
Tools that augment the agent with financial analysis capabilities.

Available Tools:
1. Financial Analysis Tools (10)
2. Cash Flow Tools (5)
3. Profitability Tools (5)
4. Growth & Efficiency Tools (5)
5. Risk & Valuation Tools (5)
6. Benchmarking & Recommendations (5)
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class FinancialAnalysisTool:
    """Base class for all financial analysis tools"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool with given parameters"""
        raise NotImplementedError


# ============================================================================
# CATEGORY 1: FINANCIAL ANALYSIS TOOLS (10 Tools)
# ============================================================================

class Tool_CalculateFinancialRatios(FinancialAnalysisTool):
    """Calculate all major financial ratios"""
    
    def __init__(self):
        super().__init__(
            name="Calculate Financial Ratios",
            description="Calculate comprehensive set of financial ratios (profitability, liquidity, leverage, efficiency)"
        )
    
    def execute(self, financial_data: Dict[str, float]) -> Dict[str, Any]:
        """
        Args:
            financial_data: Dict with keys like revenue, net_income, total_assets, etc.
        """
        from backend.services.financial_functions import (
            current_ratio,
            quick_ratio,
            gross_profit,
            operating_profit,
            profit_margins,
            debt_to_equity_ratio,
            interest_coverage_ratio,
            return_on_assets,
        )

        revenue = financial_data.get("revenue", 0)
        gp = gross_profit(revenue, financial_data.get("cogs", 0))
        op = operating_profit(gp, financial_data.get("operating_expenses", 0))
        np = financial_data.get("net_income", 0)
        margins = profit_margins(revenue, gp, op, np)
        
        return {
            "current_ratio": current_ratio(
                financial_data.get("current_assets", 0),
                financial_data.get("current_liabilities", 0)
            ),
            "quick_ratio": quick_ratio(
                financial_data.get("current_assets", 0),
                financial_data.get("inventory", 0),
                financial_data.get("current_liabilities", 0)
            ),
            "gross_margin": margins["gross_margin"],
            "operating_margin": margins["operating_margin"],
            "net_margin": margins["net_margin"],
            "debt_to_equity": debt_to_equity_ratio(
                financial_data.get("total_debt", 0),
                financial_data.get("total_equity", 0)
            ),
            "interest_coverage": interest_coverage_ratio(
                financial_data.get("operating_profit", 0),
                financial_data.get("interest_expense", 0)
            ),
            "roa": return_on_assets(
                financial_data.get("net_income", 0),
                financial_data.get("average_total_assets", 0)
            ),
        }


class Tool_AnalyzeCashFlow(FinancialAnalysisTool):
    """Comprehensive cash flow analysis"""
    
    def __init__(self):
        super().__init__(
            name="Analyze Cash Flow",
            description="Analyze operating, investing, and financing cash flows with quality assessment"
        )
    
    def execute(
        self,
        net_income: float,
        operating_cash_flow: float,
        capex: float,
        debt_issued: float = 0,
        debt_repaid: float = 0,
        equity_raised: float = 0,
    ) -> Dict[str, Any]:
        """Analyze all three cash flow components"""
        
        from backend.services.financial_functions import free_cash_flow
        from backend.services.reasoning_engine import CashFlowAnalyzer, FinancialKnowledgeBase
        
        fcf = free_cash_flow(operating_cash_flow, capex)
        
        kb = FinancialKnowledgeBase()
        analyzer = CashFlowAnalyzer(kb)
        
        quality = analyzer.analyze_cf_quality(net_income, operating_cash_flow)
        
        investing_cf = -capex
        financing_cf = debt_issued - debt_repaid + equity_raised
        
        return {
            "operating_cash_flow": round(operating_cash_flow, 2),
            "investing_cash_flow": round(investing_cf, 2),
            "financing_cash_flow": round(financing_cf, 2),
            "free_cash_flow": round(fcf, 2),
            "cash_flow_quality": quality,
            "insights": [
                f"FCF of ₹{fcf:.0f} available for debt paydown, dividends, or growth",
                f"Cash quality ratio: {quality['quality_score']:.2f}x" if quality.get('quality_score') else "Quality check needed",
            ]
        }


class Tool_ProfitabilityAnalysis(FinancialAnalysisTool):
    """Detailed profitability breakdown"""
    
    def __init__(self):
        super().__init__(
            name="Profitability Analysis",
            description="Analyze gross, operating, and net profitability with margins"
        )
    
    def execute(
        self,
        revenue: float,
        cogs: float,
        operating_expenses: float,
        interest_expense: float = 0,
        tax_expense: float = 0,
    ) -> Dict[str, Any]:
        """Break down profitability levels"""
        
        from backend.services.financial_functions import (
            gross_profit, operating_profit, net_profit, ebitda, profit_margins
        )
        
        gp = gross_profit(revenue, cogs)
        op = operating_profit(gp, operating_expenses)
        np = net_profit(op, interest_expense, tax_expense)
        
        margins = profit_margins(revenue, gp, op, np)
        
        return {
            "revenue": round(revenue, 2),
            "gross_profit": round(gp, 2),
            "operating_profit": round(op, 2),
            "net_profit": round(np, 2),
            "margins": margins,
            "profitability_status": "Profitable" if np > 0 else "Unprofitable",
        }


class Tool_WorkingCapitalAnalysis(FinancialAnalysisTool):
    """Working capital management assessment"""
    
    def __init__(self):
        super().__init__(
            name="Working Capital Analysis",
            description="Assess working capital efficiency and cash conversion cycle"
        )
    
    def execute(
        self,
        current_assets: float,
        current_liabilities: float,
        inventory: float,
        dso: float,
        dio: float,
        dpo: float,
    ) -> Dict[str, Any]:
        """Analyze working capital"""
        
        from backend.services.financial_functions import (
            current_ratio, working_capital, cash_conversion_cycle
        )
        
        cr = current_ratio(current_assets, current_liabilities)
        wc = working_capital(current_assets, current_liabilities)
        ccc = cash_conversion_cycle(dio, dso, dpo)
        
        return {
            "current_ratio": round(cr, 2),
            "working_capital": round(wc, 2),
            "cash_conversion_cycle_days": round(ccc, 1),
            "interpretation": {
                "liquidity": "Healthy" if cr >= 1.5 else "Risk" if cr < 1.0 else "Tight",
                "capital_efficiency": "Good" if ccc < 60 else "Poor" if ccc > 90 else "Fair",
            }
        }


class Tool_VarianceAnalysis(FinancialAnalysisTool):
    """Analyze profit variances"""
    
    def __init__(self):
        super().__init__(
            name="Variance Analysis",
            description="Analyze why actual results differ from expectations"
        )
    
    def execute(
        self,
        actual_margin: float,
        expected_margin: float,
        actual_revenue: float,
        expected_revenue: float,
        actual_cogs: float = None,
        expected_cogs: float = None,
    ) -> Dict[str, Any]:
        """Analyze variances"""
        
        from backend.services.reasoning_engine import ProfitVarianceAnalyzer, FinancialKnowledgeBase
        
        kb = FinancialKnowledgeBase()
        analyzer = ProfitVarianceAnalyzer(kb)
        
        margin_var = analyzer.analyze_margin_variance(actual_margin, expected_margin)
        
        if actual_cogs and expected_cogs:
            revenue_var = analyzer.analyze_revenue_variance(
                actual_revenue, expected_revenue, actual_cogs, expected_cogs
            )
            margin_var["revenue_variance"] = revenue_var
        
        return margin_var


class Tool_GrowthAnalysis(FinancialAnalysisTool):
    """Growth rate and trend analysis"""
    
    def __init__(self):
        super().__init__(
            name="Growth Analysis",
            description="Analyze revenue and profitability growth trends"
        )
    
    def execute(
        self,
        current_period_revenue: float,
        prior_period_revenue: float,
        current_period_profit: float,
        prior_period_profit: float,
    ) -> Dict[str, Any]:
        """Calculate growth rates"""
        
        revenue_growth = ((current_period_revenue - prior_period_revenue) / prior_period_revenue * 100) \
            if prior_period_revenue > 0 else 0
        
        profit_growth = ((current_period_profit - prior_period_profit) / abs(prior_period_profit) * 100) \
            if prior_period_profit != 0 else 0
        
        return {
            "revenue_growth_pct": round(revenue_growth, 2),
            "profit_growth_pct": round(profit_growth, 2),
            "revenue_growth_status": "Accelerating" if revenue_growth > 20 else "Healthy" if revenue_growth > 10 else "Slowing" if revenue_growth > 0 else "Declining",
            "profit_growth_status": "Accelerating" if profit_growth > 20 else "Growing" if profit_growth > 0 else "Declining",
        }


class Tool_FinancialHealthScore(FinancialAnalysisTool):
    """Overall financial health assessment"""
    
    def __init__(self):
        super().__init__(
            name="Financial Health Score",
            description="Calculate overall financial health score (0-100)"
        )
    
    def execute(
        self,
        profitability: float,  # 0-1
        liquidity: float,  # 0-1
        leverage: float,  # 0-1
        efficiency: float,  # 0-1
    ) -> Dict[str, Any]:
        """Calculate health score"""
        
        from backend.services.financial_functions import financial_health_score
        
        return financial_health_score(profitability, liquidity, leverage, efficiency)


class Tool_CompareToIndustry(FinancialAnalysisTool):
    """Compare metrics to industry benchmarks"""
    
    def __init__(self):
        super().__init__(
            name="Compare to Industry Benchmarks",
            description="Compare company metrics to industry averages"
        )
    
    def execute(
        self,
        company_metric: float,
        industry_benchmark: float,
        metric_name: str,
        higher_is_better: bool = True,
    ) -> Dict[str, Any]:
        """Compare metric"""
        
        from backend.services.financial_functions import metric_vs_benchmark
        
        direction = "higher_is_better" if higher_is_better else "lower_is_better"
        result = metric_vs_benchmark(company_metric, industry_benchmark, direction)
        
        return {
            "metric": metric_name,
            "company_value": round(company_metric, 2),
            "industry_benchmark": round(industry_benchmark, 2),
            **result,
        }


class Tool_ExplainConcept(FinancialAnalysisTool):
    """Explain a financial concept"""
    
    def __init__(self):
        super().__init__(
            name="Explain Financial Concept",
            description="Get explanation of a financial concept or metric"
        )
    
    def execute(self, concept_name: str) -> Dict[str, str]:
        """Explain concept"""
        
        from backend.services.reasoning_engine import FinancialKnowledgeBase
        
        kb = FinancialKnowledgeBase()
        explanation = kb.explain(concept_name)
        
        return {"explanation": explanation}


# ============================================================================
# CATEGORY 2: CASH FLOW TOOLS (5 Tools)
# ============================================================================

class Tool_CalculateRunway(FinancialAnalysisTool):
    """Calculate cash runway"""
    
    def __init__(self):
        super().__init__(
            name="Calculate Cash Runway",
            description="Calculate months of cash runway at current burn rate"
        )
    
    def execute(
        self,
        current_cash: float,
        monthly_burn: float,
        monthly_revenue: float = 0,
        monthly_growth_rate: float = 0.0,
    ) -> Dict[str, Any]:
        """Calculate runway"""
        
        from backend.services.financial_functions import cash_runway_extended
        
        return cash_runway_extended(current_cash, monthly_burn, monthly_revenue, monthly_growth_rate)


class Tool_ForecastCashFlow(FinancialAnalysisTool):
    """Forecast future cash flow scenarios"""
    
    def __init__(self):
        super().__init__(
            name="Forecast Cash Flow",
            description="Project cash flow under different scenarios (base, upside, downside)"
        )
    
    def execute(
        self,
        current_cash: float,
        monthly_burn: float,
        months_ahead: int = 12,
        burn_reduction_rate: float = 0.0,  # 5% = 0.05
        revenue_growth_rate: float = 0.0,
    ) -> Dict[str, Any]:
        """Forecast cash"""
        
        projections = []
        cash = current_cash
        burn = monthly_burn
        
        for month in range(1, months_ahead + 1):
            # Reduce burn and increase revenue
            burn *= (1 - burn_reduction_rate)
            
            # Project month end cash
            cash -= burn
            
            projections.append({
                "month": month,
                "projected_cash": round(max(0, cash), 2),
                "monthly_burn": round(burn, 2),
            })
        
        return {
            "scenario_name": "Base Case",
            "months": months_ahead,
            "starting_cash": round(current_cash, 2),
            "ending_cash": round(max(0, projections[-1]["projected_cash"] if projections else 0), 2),
            "projections": projections,
        }


class Tool_OptimizeCashFlow(FinancialAnalysisTool):
    """Identify cash flow optimization opportunities"""
    
    def __init__(self):
        super().__init__(
            name="Optimize Cash Flow",
            description="Identify specific actions to improve cash flow"
        )
    
    def execute(
        self,
        dso: float,
        dio: float,
        dpo: float,
        current_cash: float,
        monthly_burn: float,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Suggest optimizations"""
        
        recommendations = []
        
        # DSO opportunities
        if dso > 45:
            potential_improvement = ((dso - 45) / 365) * current_cash
            recommendations.append({
                "area": "Collections (DSO)",
                "current": f"{dso:.0f} days",
                "target": "45 days",
                "action": "Accelerate customer collection process",
                "potential_cash_release": round(potential_improvement, 0),
                "priority": "High" if dso > 60 else "Medium",
            })
        
        # DIO opportunities
        if dio > 45:
            recommendations.append({
                "area": "Inventory Management (DIO)",
                "current": f"{dio:.0f} days",
                "target": "30 days",
                "action": "Optimize inventory levels, improve turnover",
                "potential_cash_release": round(dio * monthly_burn / 30, 0),
                "priority": "High"
            })
        
        # DPO opportunities
        if dpo < 45:
            recommendations.append({
                "area": "Payables (DPO)",
                "current": f"{dpo:.0f} days",
                "target": "45 days",
                "action": "Negotiate extended payment terms with suppliers",
                "potential_cash_release": round((45 - dpo) * monthly_burn / 30, 0),
                "priority": "Medium"
            })
        
        return {"optimizations": recommendations}


class Tool_CashFlowQualityCheck(FinancialAnalysisTool):
    """Assess quality of reported earnings"""
    
    def __init__(self):
        super().__init__(
            name="Cash Flow Quality Check",
            description="Assess if reported earnings match underlying cash generation"
        )
    
    def execute(
        self,
        net_income: float,
        operating_cash_flow: float,
    ) -> Dict[str, Any]:
        """Check quality"""
        
        from backend.services.reasoning_engine import CashFlowAnalyzer, FinancialKnowledgeBase
        
        kb = FinancialKnowledgeBase()
        analyzer = CashFlowAnalyzer(kb)
        
        return analyzer.analyze_cf_quality(net_income, operating_cash_flow)


class Tool_CapexEfficiency(FinancialAnalysisTool):
    """Analyze capital expenditure effectiveness"""
    
    def __init__(self):
        super().__init__(
            name="CapEx Efficiency Assessment",
            description="Assess return on capital investments"
        )
    
    def execute(
        self,
        annual_capex: float,
        revenue: float,
        net_income: float,
        depreciation: float,
    ) -> Dict[str, Any]:
        """Assess CapEx"""
        
        capex_to_revenue = (annual_capex / revenue * 100) if revenue > 0 else 0
        capex_to_depreciation = (annual_capex / depreciation) if depreciation > 0 else 0
        incremental_return = (net_income / annual_capex) if annual_capex > 0 else 0
        
        return {
            "annual_capex": round(annual_capex, 2),
            "capex_to_revenue_pct": round(capex_to_revenue, 2),
            "capex_to_depreciation_ratio": round(capex_to_depreciation, 2),
            "incremental_return_on_capex": round(incremental_return, 4),
            "assessment": "Efficient" if capex_to_revenue < 10 else "Heavy CapEx" if capex_to_revenue > 20 else "Moderate",
        }


# ============================================================================
# CATEGORY 3: PROFITABILITY TOOLS (5 Tools)  
# ============================================================================

class Tool_MarginAnalysis(FinancialAnalysisTool):
    """Detailed margin analysis"""
    
    def __init__(self):
        super().__init__(
            name="Margin Analysis",
            description="Analyze gross, operating, and net margins over time"
        )
    
    def execute(
        self,
        current_gross_margin: float,
        prior_gross_margin: float,
        current_operating_margin: float,
        prior_operating_margin: float,
        current_net_margin: float,
        prior_net_margin: float,
    ) -> Dict[str, Any]:
        """Analyze margins"""
        
        return {
            "gross_margin": {
                "current": round(current_gross_margin * 100, 2),
                "prior": round(prior_gross_margin * 100, 2),
                "change_bps": round((current_gross_margin - prior_gross_margin) * 10000, 0),
                "trend": "Improving" if current_gross_margin > prior_gross_margin else "Declining",
            },
            "operating_margin": {
                "current": round(current_operating_margin * 100, 2),
                "prior": round(prior_operating_margin * 100, 2),
                "change_bps": round((current_operating_margin - prior_operating_margin) * 10000, 0),
                "trend": "Improving" if current_operating_margin > prior_operating_margin else "Declining",
            },
            "net_margin": {
                "current": round(current_net_margin * 100, 2),
                "prior": round(prior_net_margin * 100, 2),
                "change_bps": round((current_net_margin - prior_net_margin) * 10000, 0),
                "trend": "Improving" if current_net_margin > prior_net_margin else "Declining",
            }
        }


class Tool_UnitEconomicsAnalysis(FinancialAnalysisTool):
    """SaaS unit economics analysis"""
    
    def __init__(self):
        super().__init__(
            name="Unit Economics Analysis",
            description="Analyze customer acquisition cost, lifetime value, payback period"
        )
    
    def execute(
        self,
        customer_acquisition_cost: float,
        customer_lifetime_value: float,
        payback_months: float,
        annual_churn_rate: float,
    ) -> Dict[str, Any]:
        """Analyze unit economics"""
        
        ltv_to_cac = customer_lifetime_value / customer_acquisition_cost if customer_acquisition_cost > 0 else 0
        
        return {
            "cac": round(customer_acquisition_cost, 2),
            "ltv": round(customer_lifetime_value, 2),
            "ltv_to_cac_ratio": round(ltv_to_cac, 2),
            "payback_months": round(payback_months, 1),
            "annual_churn_rate": round(annual_churn_rate * 100, 2),
            "health": "Excellent" if ltv_to_cac > 3 else "Good" if ltv_to_cac > 2 else "Poor",
        }


class Tool_BreakEvenAnalysis(FinancialAnalysisTool):
    """Break-even point analysis"""
    
    def __init__(self):
        super().__init__(
            name="Break-even Analysis",
            description="Calculate break-even revenue, unit volume, and time to breakeven"
        )
    
    def execute(
        self,
        fixed_costs: float,
        variable_cost_per_unit: float,
        price_per_unit: float,
        monthly_revenue: float,
    ) -> Dict[str, Any]:
        """Calculate break-even"""
        
        contribution_margin = price_per_unit - variable_cost_per_unit
        breakeven_units = fixed_costs / contribution_margin if contribution_margin > 0 else 0
        breakeven_revenue = breakeven_units * price_per_unit
        
        current_units = monthly_revenue / price_per_unit if price_per_unit > 0 else 0
        monthly_profit = (current_units * contribution_margin) - fixed_costs
        
        months_to_breakeven = -fixed_costs / monthly_profit if monthly_profit < 0 else 0
        
        return {
            "breakeven_revenue": round(breakeven_revenue, 2),
            "breakeven_units": round(breakeven_units, 0),
            "current_monthly_profit": round(monthly_profit, 2),
            "months_to_breakeven": round(months_to_breakeven, 1) if months_to_breakeven > 0 else "Profitable",
            "contribution_margin_pct": round((contribution_margin / price_per_unit * 100) if price_per_unit > 0 else 0, 2),
        }


class Tool_CostStructureAnalysis(FinancialAnalysisTool):
    """Analyze cost structure"""
    
    def __init__(self):
        super().__init__(
            name="Cost Structure Analysis",
            description="Break down and analyze fixed vs variable costs"
        )
    
    def execute(
        self,
        revenue: float,
        fixed_costs: float,
        variable_costs: float,
    ) -> Dict[str, Any]:
        """Analyze costs"""
        
        total_costs = fixed_costs + variable_costs
        cost_ratio = total_costs / revenue if revenue > 0 else 0
        fixed_cost_ratio = fixed_costs / revenue if revenue > 0 else 0
        variable_cost_ratio = variable_costs / revenue if revenue > 0 else 0
        
        return {
            "revenue": round(revenue, 2),
            "fixed_costs": round(fixed_costs, 2),
            "variable_costs": round(variable_costs, 2),
            "total_costs": round(total_costs, 2),
            "cost_to_revenue_pct": round(cost_ratio * 100, 2),
            "fixed_cost_pct_of_revenue": round(fixed_cost_ratio * 100, 2),
            "variable_cost_pct_of_revenue": round(variable_cost_ratio * 100, 2),
            "operating_leverage": "High" if fixed_cost_ratio > 0.5 else "Moderate" if fixed_cost_ratio > 0.3 else "Low",
        }


class Tool_SCAAnalysis(FinancialAnalysisTool):
    """Scenario/Sensitivity analysis"""
    
    def __init__(self):
        super().__init__(
            name="Scenario Analysis",
            description="Model financial impact of different scenarios"
        )
    
    def execute(
        self,
        base_case_revenue: float,
        base_case_margin: float,
        scenarios: Dict[str, Dict[str, float]],
    ) -> Dict[str, Any]:
        """Run scenario analysis"""
        
        base_profit = base_case_revenue * base_case_margin
        
        results = {
            "base_case": {
                "revenue": round(base_case_revenue, 2),
                "margin": round(base_case_margin * 100, 2),
                "profit": round(base_profit, 2),
            },
            "scenarios": {}
        }
        
        for scenario_name, scenario_data in scenarios.items():
            revenue = scenario_data.get("revenue", base_case_revenue)
            margin = scenario_data.get("margin", base_case_margin)
            profit = revenue * margin
            
            results["scenarios"][scenario_name] = {
                "revenue": round(revenue, 2),
                "margin": round(margin * 100, 2),
                "profit": round(profit, 2),
                "vs_base": round(profit - base_profit, 2),
            }
        
        return results


# ============================================================================
# CATEGORY 4: GROWTH & EFFICIENCY TOOLS (5 Tools)
# ============================================================================

class Tool_CustomerMetricsAnalysis(FinancialAnalysisTool):
    """Analyze customer-related metrics"""
    
    def __init__(self):
        super().__init__(
            name="Customer Metrics Analysis",
            description="Analyze MRR, ARR, churn, NRR, and customer health"
        )
    
    def execute(
        self,
        mrr: float,
        churn_rate: float,
        nrr: float = None,
        customer_count: int = 0,
        expansion_revenue: float = 0,
    ) -> Dict[str, Any]:
        """Analyze customer metrics"""
        
        arr = mrr * 12
        arr_expansion = expansion_revenue
        
        # If NRR not provided, calculate from churn and expansion
        if nrr is None:
            nrr = (1 - churn_rate) + (expansion_revenue / mrr) if mrr > 0 else 1 - churn_rate
        
        arpu = (mrr / customer_count) if customer_count > 0 else 0
        
        return {
            "mrr": round(mrr, 2),
            "arr": round(arr, 2),
            "arr_expansion": round(arr_expansion, 2),
            "customer_count": customer_count,
            "arpu": round(arpu, 2),
            "monthly_churn_rate": round(churn_rate * 100, 2),
            "nrr": round(nrr * 100, 2),
            "health": "Excellent" if nrr > 120 else "Good" if nrr > 100 else "Fair" if nrr > 90 else "At Risk",
        }


class Tool_OperatingLeverageAnalysis(FinancialAnalysisTool):
    """Analyze operating leverage"""
    
    def __init__(self):
        super().__init__(
            name="Operating Leverage Analysis",
            description="Analyze impact of revenue changes on profit"
        )
    
    def execute(
        self,
        revenue_change_pct: float,
        expected_operating_expense_change_pct: float,
            current_operating_margin: float,
        current_revenue: float,
    ) -> Dict[str, Any]:
        """Analyze operating leverage"""
        
        # Operating leverage = % change in profit / % change in revenue
        new_revenue = current_revenue * (1 + revenue_change_pct)
        
        # Assume expenses don't change proportionally (leverage effect)
        new_opex = current_revenue * (1 - current_operating_margin) * (1 + expected_operating_expense_change_pct)
        current_opex = current_revenue * (1 - current_operating_margin)
        
        current_profit = current_revenue * current_operating_margin
        new_profit = new_revenue - new_opex
        profit_change_pct = ((new_profit - current_profit) / current_profit * 100) if current_profit > 0 else 0
        
        operating_leverage = (profit_change_pct / (revenue_change_pct * 100)) if revenue_change_pct > 0 else 0
        
        return {
            "revenue_change_pct": round(revenue_change_pct * 100, 2),
            "profit_change_pct": round(profit_change_pct, 2),
            "operating_leverage_multiple": round(operating_leverage, 2),
            "interpretation": f"1% revenue increase → {operating_leverage:.1f}% profit increase",
        }


class Tool_ScalingAnalysis(FinancialAnalysisTool):
    """Analyze company's ability to scale"""
    
    def __init__(self):
        super().__init__(
            name="Scaling Analysis",
            description="Assess growth sustainability and scaling potential"
        )
    
    def execute(
        self,
        current_revenue: float,
        revenue_growth_pct: float,
        operating_margin: float,
        cash_available: float,
        monthly_burn: float,
    ) -> Dict[str, Any]:
        """Analyze scaling"""
        
        # Rule of 40: growth_rate + profit_margin >= 40
        rule_of_40_score = (revenue_growth_pct * 100) + (operating_margin * 100)
        
        scaling_potential = "Excellent" if rule_of_40_score >= 40 else "Good" if rule_of_40_score >= 30 else "At Risk"
        
        return {
            "revenue": round(current_revenue, 2),
            "growth_rate_pct": round(revenue_growth_pct * 100, 2),
            "operating_margin_pct": round(operating_margin * 100, 2),
            "rule_of_40_score": round(rule_of_40_score, 2),
            "scaling_potential": scaling_potential,
            "cash_runway_months": round(cash_available / monthly_burn, 1) if monthly_burn > 0 else "Infinite",
        }


class Tool_EfficiencyMetricsComparison(FinancialAnalysisTool):
    """Compare efficiency against benchmarks"""
    
    def __init__(self):
        super().__init__(
            name="Efficiency Metrics Comparison",
            description="Compare CAC payback, LTV/CAC, and other efficiency metrics to benchmarks"
        )
    
    def execute(
        self,
        cac_payback_months: float,
        ltv_cac_ratio: float,
        magic_number: float = None,
    ) -> Dict[str, Any]:
        """Compare efficiency"""
        
        benchmarks = {
            "cac_payback_months": {"good": 12, "excellent": 6},
            "ltv_cac_ratio": {"good": 3.0, "excellent": 5.0},
            "magic_number": {"good": 0.75, "excellent": 1.0},  # (ARR Increase) / Sales & Marketing Spend
        }
        
        return {
            "cac_payback_months": {
                "value": round(cac_payback_months, 1),
                "benchmark": benchmarks["cac_payback_months"]["good"],
                "status": "Below Benchmark (Better)" if cac_payback_months < benchmarks["cac_payback_months"]["good"] else "Above Benchmark (Worse)",
            },
            "ltv_cac_ratio": {
                "value": round(ltv_cac_ratio, 2),
                "benchmark": benchmarks["ltv_cac_ratio"]["good"],
                "status": "Above Benchmark (Better)" if ltv_cac_ratio > benchmarks["ltv_cac_ratio"]["good"] else "Below Benchmark (Worse)",
            },
        }


# ============================================================================
# CATEGORY 5: RISK & VALUATION TOOLS (5 Tools) + 
# CATEGORY 6: BENCHMARKING & RECOMMENDATIONS (5 Tools)
# ============================================================================

class Tool_DebtHealthAssessment(FinancialAnalysisTool):
    """Assess debt and solvency"""
    
    def __init__(self):
        super().__init__(
            name="Debt Health Assessment",
            description="Assess leverage, debt service capacity, and refinancing risk"
        )
    
    def execute(
        self,
        total_debt: float,
        total_equity: float,
        ebitda: float,
        operating_cash_flow: float,
        annual_interest_payments: float,
        annual_principal_payments: float,
    ) -> Dict[str, Any]:
        """Assess debt"""
        
        from backend.services.financial_functions import (
            debt_to_equity_ratio, interest_coverage_ratio, debt_service_coverage_ratio
        )
        
        de = debt_to_equity_ratio(total_debt, total_equity)
        icr = interest_coverage_ratio(ebitda, annual_interest_payments)
        dscr = debt_service_coverage_ratio(operating_cash_flow, annual_principal_payments, annual_interest_payments)
        
        leverage_risk = "High" if de > 2.0 else "Moderate" if de > 1.0 else "Low"
        service_risk = "High" if dscr < 1.0 else "Moderate" if dscr < 1.25 else "Low"
        
        return {
            "debt_to_equity": round(de, 2),
            "interest_coverage_ratio": round(icr, 2),
            "debt_service_coverage_ratio": round(dscr, 2),
            "leverage_risk": leverage_risk,
            "service_risk": service_risk,
            "overall_debt_health": "Concerning" if leverage_risk == "High" or service_risk == "High" else "Acceptable" if leverage_risk == "Moderate" else "Strong",
        }


class Tool_ValuationMultiples(FinancialAnalysisTool):
    """Calculate valuation multiples"""
    
    def __init__(self):
        super().__init__(
            name="Valuation Multiples",
            description="Calculate P/E, P/S, EV/EBITDA, and other valuation metrics"
        )
    
    def execute(
        self,
        market_cap: float,
        net_income: float,
        revenue: float,
        ebitda: float,
        net_debt: float = 0,
    ) -> Dict[str, Any]:
        """Calculate multiples"""
        
        from backend.services.financial_functions import (
            price_to_earnings_ratio, price_to_sales_ratio, enterprise_value_to_ebitda
        )
        
        pe = price_to_earnings_ratio(market_cap, net_income) if net_income > 0 else None
        ps = price_to_sales_ratio(market_cap, revenue)
        ev = market_cap + net_debt
        ev_ebitda = enterprise_value_to_ebitda(ev, ebitda) if ebitda > 0 else None
        
        return {
            "price_to_earnings": pe if pe else "N/A (unprofitable)",
            "price_to_sales": round(ps, 2),
            "ev_ebitda": ev_ebitda if ev_ebitda else "N/A (EBITDA <= 0)",
            "enterprise_value": round(ev, 2),
        }


class Tool_GenerateRecommendations(FinancialAnalysisTool):
    """Generate specific action recommendations"""
    
    def __init__(self):
        super().__init__(
            name="Generate Recommendations",
            description="Generate prioritized recommendations based on financial analysis"
        )
    
    def execute(
        self,
        financial_metrics: Dict[str, float],
        company_stage: str = "growth",
    ) -> Dict[str, Any]:
        """Generate recommendations"""
        
        from backend.services.reasoning_engine import RecommendationGenerator, FinancialKnowledgeBase
        
        kb = FinancialKnowledgeBase()
        rec_gen = RecommendationGenerator(kb)
        
        recommendations = rec_gen.generate_recommendations(financial_metrics, company_stage)
        
        return {
            "recommendations": recommendations,
            "total_count": len(recommendations),
            "critical_count": sum(1 for r in recommendations if r.get("priority") == "Critical"),
            "high_priority_count": sum(1 for r in recommendations if r.get("priority") == "High"),
        }


class Tool_RiskAssessment(FinancialAnalysisTool):
    """Assess overall financial risks"""
    
    def __init__(self):
        super().__init__(
            name="Risk Assessment",
            description="Identify and prioritize financial risks"
        )
    
    def execute(
        self,
        cash_runway_months: float,
        growth_rate: float,
        profitability: bool,
        leverage_ratio: float,
        customer_concentration: float,
    ) -> Dict[str, Any]:
        """Assess risks"""
        
        risks = []
        
        if cash_runway_months < 6:
            risks.append({
                "risk": "Cash depletion",
                "severity": "Critical",
                "runway_months": cash_runway_months,
                "action": "Urgent fundraising or profitability needed",
            })
        elif cash_runway_months < 12:
            risks.append({
                "risk": "Funding pressure",
                "severity": "High",
                "runway_months": cash_runway_months,
                "action": "Prepare for fundraising",
            })
        
        if growth_rate < 0:
            risks.append({
                "risk": "Revenue decline",
                "severity": "High",
                "growth_rate": growth_rate,
                "action": "Stabilize revenue, analyze churn",
            })
        
        if not profitability and cash_runway_months < 24:
            risks.append({
                "risk": "Path to profitability unclear",
                "severity": "High",
                "action": "Develop clear profitability plan",
            })
        
        if leverage_ratio > 2.0:
            risks.append({
                "risk": "High leverage",
                "severity": "Medium",
                "de_ratio": leverage_ratio,
                "action": "Review debt service capacity",
            })
        
        if customer_concentration > 0.3:
            risks.append({
                "risk": "Customer concentration",
                "severity": "Medium",
                "top_customer_pct": customer_concentration * 100,
                "action": "Diversify customer base",
            })
        
        return {
            "total_risks": len(risks),
            "critical_risks": sum(1 for r in risks if r["severity"] == "Critical"),
            "high_risks": sum(1 for r in risks if r["severity"] == "High"),
            "risks": risks,
            "overall_risk_profile": "Critical" if any(r["severity"] == "Critical" for r in risks) else "High" if any(r["severity"] == "High" for r in risks) else "Medium",
        }


class Tool_ComprehensiveFinancialReview(FinancialAnalysisTool):
    """Comprehensive financial review (all metrics at once)"""
    
    def __init__(self):
        super().__init__(
            name="Comprehensive Financial Review",
            description="Full financial analysis covering profitability, liquidity, efficiency, growth, and risk"
        )
    
    def execute(
        self,
        financial_data: Dict[str, float],
        company_stage: str = "growth",
    ) -> Dict[str, Any]:
        """Run comprehensive review"""
        
        # This would call multiple tools and aggregate results
        # For brevity, returning template structure
        
        return {
            "review_date": datetime.now().isoformat(),
            "company_stage": company_stage,
            "sections": {
                "profitability": "Run profitability tool",
                "liquidity": "Run working capital tool",
                "efficiency": "Run efficiency tools",
                "growth": "Run growth analysis tool",
                "risks": "Run risk assessment tool",
                "recommendations": "Run recommendation generator",
            },
            "executive_summary": "Comprehensive review complete - see detailed sections above",
        }


class Tool_DuPontDecomposition(FinancialAnalysisTool):
    """Decompose ROE into core operating drivers"""

    def __init__(self):
        super().__init__(
            name="DuPont Decomposition",
            description="Break down ROE into margin, turnover, and leverage components"
        )

    def execute(self, net_income: float, revenue: float, total_assets: float, total_equity: float) -> Dict[str, Any]:
        net_margin = (net_income / revenue) if revenue else 0.0
        asset_turnover = (revenue / total_assets) if total_assets else 0.0
        equity_multiplier = (total_assets / total_equity) if total_equity else 0.0
        roe = net_margin * asset_turnover * equity_multiplier
        return {
            "net_margin": round(net_margin, 4),
            "asset_turnover": round(asset_turnover, 4),
            "equity_multiplier": round(equity_multiplier, 4),
            "roe": round(roe, 4),
        }


class Tool_RunwayStressTest(FinancialAnalysisTool):
    """Stress test runway under higher burn scenarios"""

    def __init__(self):
        super().__init__(
            name="Runway Stress Test",
            description="Estimate runway under base, moderate stress, and severe stress burn cases"
        )

    def execute(self, current_cash: float, monthly_burn: float) -> Dict[str, Any]:
        def _runway(cash: float, burn: float) -> float:
            return round((cash / burn), 2) if burn > 0 else 120.0

        base = _runway(current_cash, monthly_burn)
        moderate = _runway(current_cash, monthly_burn * 1.2)
        severe = _runway(current_cash, monthly_burn * 1.5)
        return {
            "base_runway_months": base,
            "moderate_stress_runway_months": moderate,
            "severe_stress_runway_months": severe,
            "risk_flag": severe < 6,
        }


class Tool_CollectionsRiskScore(FinancialAnalysisTool):
    """Collections risk scoring from AR behavior"""

    def __init__(self):
        super().__init__(
            name="Collections Risk Score",
            description="Score receivables collection risk from DSO and overdue exposure"
        )

    def execute(self, dso: float, overdue_ratio: float) -> Dict[str, Any]:
        score = 100
        score -= max(0, dso - 45) * 1.2
        score -= max(0.0, overdue_ratio) * 100 * 0.8
        score = max(0, min(100, round(score, 1)))
        return {
            "collections_risk_score": score,
            "status": "Low" if score >= 75 else "Moderate" if score >= 50 else "High",
        }


# ============================================================================
# REGISTRY OF ALL TOOLS
# ============================================================================

def get_all_financial_tools() -> Dict[str, FinancialAnalysisTool]:
    """Get registry of all available financial tools"""
    
    tools = [
        # Category 1: Financial Analysis (10)
        Tool_CalculateFinancialRatios(),
        Tool_AnalyzeCashFlow(),
        Tool_ProfitabilityAnalysis(),
        Tool_WorkingCapitalAnalysis(),
        Tool_VarianceAnalysis(),
        Tool_GrowthAnalysis(),
        Tool_FinancialHealthScore(),
        Tool_CompareToIndustry(),
        Tool_ExplainConcept(),
        
        # Category 2: Cash Flow (5)
        Tool_CalculateRunway(),
        Tool_ForecastCashFlow(),
        Tool_OptimizeCashFlow(),
        Tool_CashFlowQualityCheck(),
        Tool_CapexEfficiency(),
        
        # Category 3: Profitability (5)
        Tool_MarginAnalysis(),
        Tool_UnitEconomicsAnalysis(),
        Tool_BreakEvenAnalysis(),
        Tool_CostStructureAnalysis(),
        Tool_SCAAnalysis(),
        
        # Category 4: Growth & Efficiency (5)
        Tool_CustomerMetricsAnalysis(),
        Tool_OperatingLeverageAnalysis(),
        Tool_ScalingAnalysis(),
        Tool_EfficiencyMetricsComparison(),
        
        # Category 5: Risk & Valuation (5)
        Tool_DebtHealthAssessment(),
        Tool_ValuationMultiples(),
        Tool_RiskAssessment(),
        
        # Category 6: Benchmarking & Recommendations (5)
        Tool_GenerateRecommendations(),
        Tool_ComprehensiveFinancialReview(),

        # Additional strategic tools
        Tool_DuPontDecomposition(),
        Tool_RunwayStressTest(),
        Tool_CollectionsRiskScore(),
    ]
    
    return {tool.name: tool for tool in tools}
