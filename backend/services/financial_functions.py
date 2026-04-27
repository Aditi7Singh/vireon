"""
Financial Functions Module
===========================
Industry-standard financial calculation formulas for startup financial analysis.

Organized into 7 categories:
1. Cash Flow Statement (6 functions)
2. Working Capital Analysis (4 functions)
3. Profitability Analysis (5 functions)
4. Leverage & Solvency Analysis (4 functions)
5. Efficiency & Activity Analysis (4 functions)
6. Valuation Models (3 functions)
7. Benchmarking (2 functions)

All functions include:
- Comprehensive input validation
- Logging for debugging
- Edge case handling
- Industry-standard formulas
- Type hints and docstrings
"""

import logging
import math
from typing import Dict, List, Tuple, Optional, Union
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# ============================================================================
# CATEGORY 1: CASH FLOW STATEMENT (6 Functions)
# ============================================================================

def operating_cash_flow(
    net_income: float,
    depreciation: float,
    amortization: float,
    change_in_ar: float,
    change_in_ap: float,
    change_in_inventory: float,
) -> float:
    """
    Calculate Operating Cash Flow (OCF) using Indirect Method.
    
    OCF = Net Income
        + Depreciation & Amortization
        - Increase in AR (working capital use)
        + Increase in AP (working capital source)
        - Increase in Inventory (working capital use)
    
    Args:
        net_income: Net income from P&L
        depreciation: Non-cash expense
        amortization: Non-cash expense
        change_in_ar: Increase in Accounts Receivable (negative = use of cash)
        change_in_ap: Increase in Accounts Payable (positive = source of cash)
        change_in_inventory: Increase in Inventory (negative = use of cash)
        
    Returns:
        Operating cash flow amount
    """
    if any(x is None for x in [net_income, depreciation, amortization, change_in_ar, change_in_ap, change_in_inventory]):
        logger.warning(f"operating_cash_flow: None values detected")
        return 0.0
    
    # Add back non-cash charges
    ocf = net_income + depreciation + amortization
    
    # Adjust for working capital changes
    # Increase in AR uses cash (negative)
    ocf -= change_in_ar
    
    # Increase in AP sources cash (positive)
    ocf += change_in_ap
    
    # Increase in inventory uses cash (negative)
    ocf -= change_in_inventory
    
    logger.info(f"operating_cash_flow: NI={net_income}, D&A={depreciation+amortization}, OCF={ocf}")
    return round(ocf, 2)


def investing_cash_flow(
    capex: float,
    acquisition_spend: float,
    investment_proceeds: float,
) -> float:
    """
    Calculate Investing Cash Flow.
    
    ICF = -CapEx - Acquisitions + Investment Proceeds
    
    Args:
        capex: Capital expenditures (outflow, positive value)
        acquisition_spend: M&A spend (outflow, positive value)
        investment_proceeds: Sale of assets/investments (inflow, positive value)
        
    Returns:
        Investing cash flow (negative = net outflow)
    """
    if any(x is None for x in [capex, acquisition_spend, investment_proceeds]):
        logger.warning("investing_cash_flow: None values detected")
        return 0.0
    
    # Cap negative values
    capex = max(0, capex)
    acquisition_spend = max(0, acquisition_spend)
    investment_proceeds = max(0, investment_proceeds)
    
    icf = -capex - acquisition_spend + investment_proceeds
    
    logger.info(f"investing_cash_flow: CapEx={capex}, M&A={acquisition_spend}, Proceeds={investment_proceeds}, ICF={icf}")
    return round(icf, 2)


def financing_cash_flow(
    debt_issued: float,
    debt_repaid: float,
    equity_raised: float,
    dividends_paid: float,
) -> float:
    """
    Calculate Financing Cash Flow.
    
    FCF = Debt Issued - Debt Repaid + Equity Raised - Dividends
    
    Args:
        debt_issued: New debt proceeds (inflow)
        debt_repaid: Debt principal payments (outflow)
        equity_raised: New equity raised (inflow)
        dividends_paid: Dividends distributed (outflow)
        
    Returns:
        Financing cash flow
    """
    if any(x is None for x in [debt_issued, debt_repaid, equity_raised, dividends_paid]):
        logger.warning("financing_cash_flow: None values detected")
        return 0.0
    
    # Cap values
    debt_issued = max(0, debt_issued)
    debt_repaid = max(0, debt_repaid)
    equity_raised = max(0, equity_raised)
    dividends_paid = max(0, dividends_paid)
    
    fcf = debt_issued - debt_repaid + equity_raised - dividends_paid
    
    logger.info(f"financing_cash_flow: Debt+={debt_issued}, Debt-={debt_repaid}, Equity={equity_raised}, Div={dividends_paid}, FCF={fcf}")
    return round(fcf, 2)


def free_cash_flow(
    operating_cash_flow: float,
    capex: float,
) -> float:
    """
    Calculate Free Cash Flow (most important cash metric).
    
    FCF = Operating Cash Flow - CapEx
    
    Positive FCF means company generates more cash than needed to fund growth.
    
    Args:
        operating_cash_flow: Operating cash flow
        capex: Capital expenditures
        
    Returns:
        Free cash flow available for debt repayment, dividends, acquisition, etc.
    """
    if operating_cash_flow is None or capex is None:
        logger.warning("free_cash_flow: None values detected")
        return 0.0
    
    capex = max(0, capex)
    fcf = operating_cash_flow - capex
    
    logger.info(f"free_cash_flow: OCF={operating_cash_flow}, CapEx={capex}, FCF={fcf}")
    return round(fcf, 2)


def cash_conversion_cycle(
    days_inventory_outstanding: float,
    days_sales_outstanding: float,
    days_payable_outstanding: float,
) -> float:
    """
    Calculate Cash Conversion Cycle (CCC).
    
    CCC = DIO + DSO - DPO
    
    How long capital is tied up in operations:
    - Positive CCC: Company pays suppliers before collecting from customers
    - Negative CCC: Company collects before paying (great for cash flow)
    
    Args:
        days_inventory_outstanding: Days to sell inventory (0-90 typical)
        days_sales_outstanding: Days to collect from customers (0-60 typical)
        days_payable_outstanding: Days taken to pay suppliers (0-90 typical)
        
    Returns:
        Cash conversion cycle in days
    """
    if any(x is None for x in [days_inventory_outstanding, days_sales_outstanding, days_payable_outstanding]):
        logger.warning("cash_conversion_cycle: None values detected")
        return 0.0
    
    # All should be >= 0
    dio = max(0, days_inventory_outstanding)
    dso = max(0, days_sales_outstanding)
    dpo = max(0, days_payable_outstanding)
    
    ccc = dio + dso - dpo
    
    logger.info(f"cash_conversion_cycle: DIO={dio}, DSO={dso}, DPO={dpo}, CCC={ccc}")
    return round(ccc, 2)


def cash_runway_extended(
    current_cash: float,
    monthly_burn: float,
    monthly_revenue: float = 0.0,
    monthly_growth_rate: float = 0.0,
) -> Dict[str, Union[float, str]]:
    """
    Calculate extended runway with growth assumptions.
    
    Accounts for:
    - Monthly burn rate
    - Monthly revenue (reduces burn)
    - Revenue growth rate (can turn burn negative = profits)
    
    Args:
        current_cash: Cash available in bank
        monthly_burn: Monthly operating expenses
        monthly_revenue: Monthly revenue (reduces burn)
        monthly_growth_rate: Revenue growth rate per month (0.05 = 5% MoM)
        
    Returns:
        Dict with:
        - runway_months: Months until cash depleted
        - profitability_month: Month when profitable (if ever)
        - peak_cash: Highest cash balance before decline
        - peak_cash_month: Month of peak cash
    """
    if any(x is None for x in [current_cash, monthly_burn, monthly_revenue]):
        logger.warning("cash_runway_extended: None values detected")
        return {
            "runway_months": 0,
            "months_of_runway": 0,
            "critical_status": True,
            "profitability_month": None,
            "peak_cash": current_cash,
            "peak_cash_month": 0,
        }
    
    current_cash = max(0, current_cash)
    monthly_burn = max(0, monthly_burn)
    monthly_revenue = max(0, monthly_revenue)
    monthly_growth_rate = max(0, min(0.1, monthly_growth_rate))  # Cap at 10% MoM
    
    net_burn = monthly_burn - monthly_revenue
    peak_cash = current_cash
    peak_cash_month = 0
    profitability_month = None
    runway_months = 0
    
    # Simulate month by month
    cash = current_cash
    revenue = monthly_revenue
    for month in range(1, 121):  # Simulate up to 10 years
        # Revenue grows
        revenue *= (1 + monthly_growth_rate)
        
        # Calculate net burn for this month
        monthly_net = monthly_burn - revenue
        
        # Update cash
        cash -= monthly_net
        
        # Check if net burn turned negative (profitable)
        if profitability_month is None and monthly_net < 0:
            profitability_month = month
        
        # Track peak cash
        if cash > peak_cash:
            peak_cash = cash
            peak_cash_month = month
        
        # Check if depleted
        if cash <= 0:
            runway_months = month
            break
    else:
        runway_months = 120  # Ran out of months in simulation
    
    result = {
        "runway_months": runway_months,
        "months_of_runway": runway_months,
        "critical_status": runway_months < 6,
        "profitability_month": profitability_month,
        "peak_cash": round(peak_cash, 2),
        "peak_cash_month": peak_cash_month,
    }
    
    logger.info(f"cash_runway_extended: runway={runway_months}m, profitable={profitability_month}, peak=${peak_cash}")
    return result


# ============================================================================
# CATEGORY 2: WORKING CAPITAL ANALYSIS (4 Functions)
# ============================================================================

def current_ratio(
    current_assets: float,
    current_liabilities: float,
) -> float:
    """
    Calculate Current Ratio (short-term liquidity metric).
    
    Current Ratio = Current Assets / Current Liabilities
    
    - 1.5-3.0: Healthy range
    - < 1.0: May have trouble meeting short-term obligations
    - > 3.0: Too much cash not deployed productively
    
    Args:
        current_assets: Cash + AR + Inventory + Other ST assets
        current_liabilities: AP + Short-term debt + Other ST liabilities
        
    Returns:
        Current ratio (higher = better short-term liquidity)
    """
    if current_assets is None or current_liabilities is None:
        logger.warning("current_ratio: None values detected")
        return 0.0
    
    current_assets = max(0, current_assets)
    current_liabilities = max(0, current_liabilities)
    
    if current_liabilities == 0:
        logger.info("current_ratio: Zero current liabilities, returning infinite ratio")
        return 999.99 if current_assets > 0 else 0.0
    
    ratio = current_assets / current_liabilities
    
    logger.info(f"current_ratio: CA={current_assets}, CL={current_liabilities}, ratio={ratio:.2f}")
    return round(ratio, 2)


def quick_ratio(
    current_assets: float,
    inventory: float,
    current_liabilities: float,
) -> float:
    """
    Calculate Quick Ratio (most conservative liquidity metric).
    
    Quick Ratio = (Current Assets - Inventory) / Current Liabilities
    
    More conservative than current ratio (excludes inventory which takes time to convert).
    
    Args:
        current_assets: Total current assets
        inventory: Value of inventory (excluded)
        current_liabilities: Current liabilities
        
    Returns:
        Quick ratio (1.0+ is good)
    """
    if any(x is None for x in [current_assets, inventory, current_liabilities]):
        logger.warning("quick_ratio: None values detected")
        return 0.0
    
    current_assets = max(0, current_assets)
    inventory = max(0, min(inventory, current_assets))  # Can't exceed CA
    current_liabilities = max(0, current_liabilities)
    
    if current_liabilities == 0:
        return 999.99 if (current_assets - inventory) > 0 else 0.0
    
    quick_assets = current_assets - inventory
    ratio = quick_assets / current_liabilities
    
    logger.info(f"quick_ratio: CA={current_assets}, Inv={inventory}, CL={current_liabilities}, ratio={ratio:.2f}")
    return round(ratio, 2)


def working_capital(
    current_assets: float,
    current_liabilities: float,
) -> float:
    """
    Calculate Working Capital (absolute amount).
    
    WC = Current Assets - Current Liabilities
    
    Positive WC means company can meet short-term obligations.
    
    Args:
        current_assets: Total current assets
        current_liabilities: Total current liabilities
        
    Returns:
        Working capital amount
    """
    if current_assets is None or current_liabilities is None:
        logger.warning("working_capital: None values detected")
        return 0.0
    
    current_assets = max(0, current_assets)
    current_liabilities = max(0, current_liabilities)
    
    wc = current_assets - current_liabilities
    
    logger.info(f"working_capital: CA={current_assets}, CL={current_liabilities}, WC={wc}")
    return round(wc, 2)


def working_capital_to_revenue(
    working_capital: float,
    annual_revenue: float,
) -> float:
    """
    Calculate Working Capital as % of Annual Revenue.
    
    WC % = Working Capital / Annual Revenue
    
    Shows how much capital is tied up in operations:
    - 0-20%: Good (efficient working capital management)
    - 20-40%: Okay
    - 40%+: Poor (too much cash tied up)
    
    Args:
        working_capital: Net working capital amount
        annual_revenue: Annual revenue
        
    Returns:
        Working capital as % of revenue (0.0-1.0 range)
    """
    if working_capital is None or annual_revenue is None:
        logger.warning("working_capital_to_revenue: None values detected")
        return 0.0
    
    annual_revenue = max(0.01, annual_revenue)  # Avoid zero
    
    percentage = working_capital / annual_revenue
    percentage = max(-1.0, min(1.0, percentage))  # Cap to -100% to +100%
    
    logger.info(f"working_capital_to_revenue: WC={working_capital}, Revenue={annual_revenue}, pct={percentage:.2%}")
    return round(percentage, 4)


# ============================================================================
# CATEGORY 3: PROFITABILITY ANALYSIS (5 Functions)
# ============================================================================

def gross_profit(
    revenue: float,
    cost_of_goods_sold: float,
) -> float:
    """
    Calculate Gross Profit (before operating expenses).
    
    Gross Profit = Revenue - COGS
    
    Args:
        revenue: Total revenue
        cost_of_goods_sold: Direct costs of production
        
    Returns:
        Gross profit amount
    """
    if revenue is None or cost_of_goods_sold is None:
        logger.warning("gross_profit: None values detected")
        return 0.0
    
    revenue = max(0, revenue)
    cogs = max(0, min(cost_of_goods_sold, revenue))
    
    gp = revenue - cogs
    
    logger.info(f"gross_profit: Revenue={revenue}, COGS={cogs}, GP={gp}")
    return round(gp, 2)


def operating_profit(
    gross_profit: float,
    operating_expenses: float,
) -> float:
    """
    Calculate Operating Profit (EBIT - Earnings Before Interest & Taxes).
    
    Operating Profit = Gross Profit - Operating Expenses
    
    Shows profitability from core business operations (before financing).
    
    Args:
        gross_profit: Gross profit amount
        operating_expenses: R&D, Sales, G&A, etc.
        
    Returns:
        Operating profit (EBIT)
    """
    if gross_profit is None or operating_expenses is None:
        logger.warning("operating_profit: None values detected")
        return 0.0
    
    gross_profit = max(0, gross_profit)
    opex = max(0, operating_expenses)
    
    op_profit = gross_profit - opex
    
    logger.info(f"operating_profit: GP={gross_profit}, OpEx={opex}, EBIT={op_profit}")
    return round(op_profit, 2)


def net_profit(
    operating_profit: float,
    interest_expense: float,
    tax_expense: float,
) -> float:
    """
    Calculate Net Profit (bottom line).
    
    Net Profit = Operating Profit - Interest - Taxes
    
    Args:
        operating_profit: Operating profit (EBIT)
        interest_expense: Interest on debt
        tax_expense: Income taxes
        
    Returns:
        Net profit (net income)
    """
    if any(x is None for x in [operating_profit, interest_expense, tax_expense]):
        logger.warning("net_profit: None values detected")
        return 0.0
    
    # Allow negative values (losses) for realistic P&L behavior.
    interest_expense = max(0, interest_expense)
    tax_expense = max(0, tax_expense)
    
    net = operating_profit - interest_expense - tax_expense
    
    logger.info(f"net_profit: EBIT={operating_profit}, Interest={interest_expense}, Tax={tax_expense}, NI={net}")
    return round(net, 2)


def ebitda(
    operating_profit: float,
    depreciation: float,
    amortization: float,
) -> float:
    """
    Calculate EBITDA (Earnings Before Interest, Taxes, Depreciation, Amortization).
    
    EBITDA = Operating Profit + D&A
    
    Shows operational cash profitability (ignores capital structure & non-cash items).
    
    Args:
        operating_profit: Operating profit
        depreciation: Depreciation expense
        amortization: Amortization expense
        
    Returns:
        EBITDA
    """
    if any(x is None for x in [operating_profit, depreciation, amortization]):
        logger.warning("ebitda: None values detected")
        return 0.0
    
    operating_profit = max(0, operating_profit)
    da = max(0, depreciation + amortization)
    
    ebitda = operating_profit + da
    
    logger.info(f"ebitda: EBIT={operating_profit}, D&A={da}, EBITDA={ebitda}")
    return round(ebitda, 2)


def profit_margins(
    revenue: float,
    gross_profit: float,
    operating_profit: float,
    net_profit: float,
) -> Dict[str, float]:
    """
    Calculate all profit margins as % of revenue.
    
    Args:
        revenue: Total revenue
        gross_profit: Gross profit
        operating_profit: Operating profit (EBIT)
        net_profit: Net profit
        
    Returns:
        Dict with:
        - gross_margin: Gross profit margin %
        - operating_margin: Operating profit margin %
        - net_margin: Net profit margin %
    """
    if revenue is None:
        logger.warning("profit_margins: Revenue is None")
        return {
            "gross_margin": 0.0,
            "operating_margin": 0.0,
            "net_margin": 0.0,
            "gross_profit_margin": 0.0,
            "operating_profit_margin": 0.0,
            "net_profit_margin": 0.0,
            "gross_margin_pct": 0.0,
            "operating_margin_pct": 0.0,
            "net_margin_pct": 0.0,
        }
    
    revenue = max(0.01, revenue)

    gross_ratio = gross_profit / revenue
    operating_ratio = operating_profit / revenue
    net_ratio = net_profit / revenue

    margins = {
        # Ratio-based fields (0-1) for compatibility with existing tests/callers.
        "gross_margin": round(gross_ratio, 4),
        "operating_margin": round(operating_ratio, 4),
        "net_margin": round(net_ratio, 4),
        "gross_profit_margin": round(gross_ratio, 4),
        "operating_profit_margin": round(operating_ratio, 4),
        "net_profit_margin": round(net_ratio, 4),
        # Percentage convenience fields retained for UIs/reporting.
        "gross_margin_pct": round(gross_ratio * 100, 2),
        "operating_margin_pct": round(operating_ratio * 100, 2),
        "net_margin_pct": round(net_ratio * 100, 2),
    }
    
    logger.info(f"profit_margins: GM={margins['gross_margin']}%, OM={margins['operating_margin']}%, NM={margins['net_margin']}%")
    return margins


# ============================================================================
# CATEGORY 4: LEVERAGE & SOLVENCY ANALYSIS (4 Functions)
# ============================================================================

def debt_to_equity_ratio(
    total_debt: float,
    total_equity: float,
) -> float:
    """
    Calculate Debt-to-Equity Ratio.
    
    D/E = Total Debt / Total Equity
    
    - < 1.0: Conservative (more equity than debt)
    - 1.0-2.0: Moderate (common for healthy companies)
    - > 2.0: Aggressive (may have trouble in downturn)
    
    Args:
        total_debt: All debt (ST + LT)
        total_equity: Shareholder equity
        
    Returns:
        Debt-to-equity ratio
    """
    if total_debt is None or total_equity is None:
        logger.warning("debt_to_equity_ratio: None values detected")
        return 0.0
    
    total_debt = max(0, total_debt)
    total_equity = max(0, total_equity)
    
    if total_equity == 0:
        return 999.99 if total_debt > 0 else 0.0
    
    de_ratio = total_debt / total_equity
    
    logger.info(f"debt_to_equity_ratio: Debt={total_debt}, Equity={total_equity}, D/E={de_ratio:.2f}")
    return de_ratio


def debt_to_assets_ratio(
    total_debt: float,
    total_assets: float,
) -> float:
    """
    Calculate Debt-to-Assets Ratio.
    
    D/A = Total Debt / Total Assets
    
    Shows % of assets financed by debt vs equity:
    - < 0.3: Conservative (30% debt)
    - 0.3-0.6: Moderate
    - > 0.6: Aggressive
    
    Args:
        total_debt: Total debt
        total_assets: Total assets
        
    Returns:
        Debt-to-assets ratio (0.0-1.0)
    """
    if total_debt is None or total_assets is None:
        logger.warning("debt_to_assets_ratio: None values detected")
        return 0.0
    
    total_debt = max(0, total_debt)
    total_assets = max(0.01, total_assets)
    
    da_ratio = total_debt / total_assets
    da_ratio = max(0.0, min(1.0, da_ratio))
    
    logger.info(f"debt_to_assets_ratio: Debt={total_debt}, Assets={total_assets}, D/A={da_ratio:.2%}")
    return round(da_ratio, 4)


def interest_coverage_ratio(
    operating_profit: float,
    interest_expense: float,
) -> float:
    """
    Calculate Interest Coverage Ratio.
    
    ICR = Operating Profit / Interest Expense
    
    How many times operating profit covers interest payments:
    - > 5.0: Excellent (comfortable debt service)
    - 2.5-5.0: Adequate
    - < 2.5: Risky (may struggle to pay interest)
    - < 1.5: Critical
    
    Args:
        operating_profit: EBIT
        interest_expense: Annual interest payments
        
    Returns:
        Interest coverage ratio (higher = safer)
    """
    if operating_profit is None or interest_expense is None:
        logger.warning("interest_coverage_ratio: None values detected")
        return 0.0
    
    operating_profit = max(0, operating_profit)
    interest_expense = max(0.01, interest_expense)
    
    if interest_expense == 0:
        return 999.99 if operating_profit > 0 else 0.0
    
    icr = operating_profit / interest_expense
    
    logger.info(f"interest_coverage_ratio: EBIT={operating_profit}, Interest={interest_expense}, ICR={icr:.2f}x")
    return round(icr, 2)


def debt_service_coverage_ratio(
    operating_cash_flow: float,
    debt_principal_payment: float,
    interest_payment: float,
) -> float:
    """
    Calculate Debt Service Coverage Ratio (DSCR).
    
    DSCR = Operating Cash Flow / (Principal + Interest)
    
    How many times operating cash flow covers debt payments:
    - > 1.25: Healthy (can service debt comfortably)
    - 1.0-1.25: Adequate
    - < 1.0: At risk (insufficient cash to pay debt)
    
    Args:
        operating_cash_flow: Cash flow from operations
        debt_principal_payment: Principal payments due
        interest_payment: Interest payments due
        
    Returns:
        Debt service coverage ratio
    """
    if any(x is None for x in [operating_cash_flow, debt_principal_payment, interest_payment]):
        logger.warning("debt_service_coverage_ratio: None values detected")
        return 0.0
    
    operating_cash_flow = max(0, operating_cash_flow)
    total_debt_service = max(0.01, debt_principal_payment + interest_payment)
    
    dscr = operating_cash_flow / total_debt_service
    
    logger.info(f"debt_service_coverage_ratio: OCF={operating_cash_flow}, Debt Service={total_debt_service}, DSCR={dscr:.2f}x")
    return round(dscr, 2)


# ============================================================================
# CATEGORY 5: EFFICIENCY & ACTIVITY ANALYSIS (4 Functions)
# ============================================================================

def asset_turnover_ratio(
    revenue: float,
    average_total_assets: float,
) -> float:
    """
    Calculate Asset Turnover Ratio.
    
    ATR = Annual Revenue / Average Total Assets
    
    How efficiently company uses assets to generate revenue:
    - > 1.0: Using assets efficiently
    - > 2.0: Excellent (typical for tech/SaaS)
    
    Args:
        revenue: Annual revenue
        average_total_assets: (Beginning Assets + Ending Assets) / 2
        
    Returns:
        Asset turnover ratio
    """
    if revenue is None or average_total_assets is None:
        logger.warning("asset_turnover_ratio: None values detected")
        return 0.0
    
    revenue = max(0, revenue)
    average_total_assets = max(0.01, average_total_assets)
    
    atr = revenue / average_total_assets
    
    logger.info(f"asset_turnover_ratio: Revenue={revenue}, Avg Assets={average_total_assets}, ATR={atr:.2f}x")
    return round(atr, 2)


def inventory_turnover_ratio(
    cost_of_goods_sold: float,
    average_inventory: float,
) -> float:
    """
    Calculate Inventory Turnover Ratio.
    
    ITR = COGS / Average Inventory
    
    How many times inventory is sold and replaced:
    - Higher = More efficient inventory management
    - Lower = Inventory sitting on shelves (cash tied up)
    
    Args:
        cost_of_goods_sold: Annual COGS
        average_inventory: (Beginning Inventory + Ending Inventory) / 2
        
    Returns:
        Inventory turnover ratio
    """
    if cost_of_goods_sold is None or average_inventory is None:
        logger.warning("inventory_turnover_ratio: None values detected")
        return 0.0
    
    cogs = max(0, cost_of_goods_sold)
    avg_inv = max(0.01, average_inventory)
    
    itr = cogs / avg_inv
    
    logger.info(f"inventory_turnover_ratio: COGS={cogs}, Avg Inventory={avg_inv}, ITR={itr:.2f}x")
    return round(itr, 2)


def receivables_turnover_ratio(
    revenue: float,
    average_accounts_receivable: float,
) -> float:
    """
    Calculate Receivables Turnover Ratio.
    
    RTR = Annual Revenue / Average Accounts Receivable
    
    How many times AR is collected during the year:
    - Higher = Faster collections
    - Lower = Slow-paying customers
    
    Args:
        revenue: Annual revenue
        average_accounts_receivable: (Beginning AR + Ending AR) / 2
        
    Returns:
        Receivables turnover ratio
    """
    if revenue is None or average_accounts_receivable is None:
        logger.warning("receivables_turnover_ratio: None values detected")
        return 0.0
    
    revenue = max(0, revenue)
    avg_ar = max(0.01, average_accounts_receivable)
    
    rtr = revenue / avg_ar
    
    logger.info(f"receivables_turnover_ratio: Revenue={revenue}, Avg AR={avg_ar}, RTR={rtr:.2f}x")
    return round(rtr, 2)


def return_on_assets(
    net_profit: float,
    average_total_assets: float,
) -> float:
    """
    Calculate Return on Assets (ROA).
    
    ROA = Net Profit / Average Total Assets
    
    How much profit is generated per dollar of assets:
    - > 0.10: Excellent (10%+ return)
    - 0.05-0.10: Good
    - < 0.05: Poor
    
    Args:
        net_profit: Net income
        average_total_assets: Average assets for period
        
    Returns:
        ROA as decimal (0.10 = 10% return)
    """
    if net_profit is None or average_total_assets is None:
        logger.warning("return_on_assets: None values detected")
        return 0.0
    
    net_profit = max(0, net_profit)
    avg_assets = max(0.01, average_total_assets)
    
    roa = net_profit / avg_assets
    roa = max(-1.0, min(1.0, roa))  # Cap at +/- 100%
    
    logger.info(f"return_on_assets: NI={net_profit}, Avg Assets={avg_assets}, ROA={roa:.2%}")
    return round(roa, 4)


# ============================================================================
# CATEGORY 6: VALUATION MODELS (3 Functions)
# ============================================================================

def price_to_earnings_ratio(
    market_capitalization: float,
    net_profit: float,
) -> float:
    """
    Calculate Price-to-Earnings (P/E) Ratio.
    
    P/E = Market Cap / Net Income
    
    How much investors willing to pay per dollar of earnings:
    - < 15: Cheap (undervalued or low growth)
    - 15-25: Fair value
    - > 25: Expensive (high growth or overvalued)
    - Negative earnings = N/A
    
    Args:
        market_capitalization: Company valuation in market
        net_profit: Annual net income
        
    Returns:
        P/E ratio (use None if earnings are negative)
    """
    if market_capitalization is None or net_profit is None:
        logger.warning("price_to_earnings_ratio: None values detected")
        return None
    
    market_cap = max(0, market_capitalization)
    
    # Can't calculate P/E with negative or zero earnings
    if net_profit <= 0:
        logger.warning(f"price_to_earnings_ratio: Non-positive earnings {net_profit}, P/E not calculable")
        return None
    
    pe_ratio = market_cap / net_profit
    
    logger.info(f"price_to_earnings_ratio: Market Cap={market_cap}, NI={net_profit}, P/E={pe_ratio:.2f}x")
    return round(pe_ratio, 2)


def price_to_sales_ratio(
    market_capitalization: float,
    annual_revenue: float,
) -> float:
    """
    Calculate Price-to-Sales (P/S) Ratio.
    
    P/S = Market Cap / Annual Revenue
    
    Useful for unprofitable companies (focuses on revenue):
    - < 1.0: Cheap relative to sales
    - 1-3: Fair value
    - > 3: Expensive
    
    Args:
        market_capitalization: Company valuation
        annual_revenue: Annual revenue
        
    Returns:
        P/S ratio
    """
    if market_capitalization is None or annual_revenue is None:
        logger.warning("price_to_sales_ratio: None values detected")
        return None
    
    market_cap = max(0, market_capitalization)
    revenue = max(0.01, annual_revenue)
    
    ps_ratio = market_cap / revenue
    
    logger.info(f"price_to_sales_ratio: Market Cap={market_cap}, Revenue={revenue}, P/S={ps_ratio:.2f}x")
    return round(ps_ratio, 2)


def enterprise_value_to_ebitda(
    enterprise_value: float,
    ebitda: float,
) -> float:
    """
    Calculate EV/EBITDA Multiple.
    
    EV/EBITDA = Enterprise Value / EBITDA
    
    Compares valuation to operational profitability:
    - < 5: Cheap
    - 5-10: Fair value
    - > 10: Expensive
    
    Args:
        enterprise_value: Market Cap + Net Debt
        ebitda: Operating cash profitability
        
    Returns:
        EV/EBITDA multiple
    """
    if enterprise_value is None or ebitda is None:
        logger.warning("enterprise_value_to_ebitda: None values detected")
        return None
    
    ev = max(0, enterprise_value)
    
    # Can't calculate with negative/zero EBITDA
    if ebitda <= 0:
        logger.warning(f"enterprise_value_to_ebitda: Non-positive EBITDA {ebitda}, multiple not calculable")
        return None
    
    multiple = ev / ebitda
    
    logger.info(f"enterprise_value_to_ebitda: EV={ev}, EBITDA={ebitda}, Multiple={multiple:.2f}x")
    return round(multiple, 2)


# ============================================================================
# CATEGORY 7: BENCHMARKING (2 Functions)
# ============================================================================

def metric_vs_benchmark(
    actual_value: float,
    benchmark_value: float,
    direction: str = "higher_is_better",
) -> Dict[str, Union[float, str]]:
    """
    Compare metric to industry benchmark.
    
    Args:
        actual_value: Company's actual metric value
        benchmark_value: Industry average/benchmark
        direction: "higher_is_better" or "lower_is_better"
        
    Returns:
        Dict with:
        - difference: Absolute difference
        - percent_difference: % difference
        - status: "Above Benchmark", "Below Benchmark", "At Benchmark"
    """
    if actual_value is None or benchmark_value is None:
        logger.warning("metric_vs_benchmark: None values detected")
        return {
            "difference": 0,
            "percent_difference": 0,
            "variance_pct": 0,
            "status": "Unknown",
        }
    
    benchmark = max(0.01, benchmark_value)
    
    diff = actual_value - benchmark
    pct_diff = (diff / benchmark) * 100
    
    if abs(pct_diff) < 2:
        status = "At Benchmark"
    elif (direction == "higher_is_better" and actual_value > benchmark) or \
         (direction == "lower_is_better" and actual_value < benchmark):
        status = "Above Benchmark"
    else:
        status = "Below Benchmark"
    
    result = {
        "difference": round(diff, 2),
        "percent_difference": round(pct_diff, 2),
        "variance_pct": round(pct_diff, 2),
        "status": status,
    }
    
    logger.info(f"metric_vs_benchmark: Actual={actual_value}, Benchmark={benchmark}, Diff={diff} ({pct_diff:.1f}%), Status={status}")
    return result


def financial_health_score(
    profitability: float,  # 0-1 (net margin)
    liquidity: float,  # 0-1 (current ratio / 3)
    leverage: float,  # 0-1 (1 - debt_to_assets)
    efficiency: float,  # 0-1 (asset_turnover / 2)
) -> Dict[str, Union[float, str]]:
    """
    Calculate overall Financial Health Score (0-100).
    
    Weighted average of:
    - Profitability: 35% - Net profit margin
    - Liquidity: 25% - Short-term payment ability
    - Leverage: 25% - Debt levels
    - Efficiency: 15% - Asset utilization
    
    Args:
        profitability: Normalized 0-1 (e.g., 0.15 = 15% net margin)
        liquidity: Normalized 0-1 (e.g., 1.5 / 3 = 0.5)
        leverage: Normalized 0-1 (e.g., 1 - 0.4 = 0.6)
        efficiency: Normalized 0-1 (e.g., 1.5 / 2 = 0.75)
        
    Returns:
        Dict with:
        - score: 0-100 health score
        - rating: "Excellent" / "Good" / "Fair" / "Poor" / "Critical"
        - details: Breakdown by category
    """
    if any(x is None for x in [profitability, liquidity, leverage, efficiency]):
        logger.warning("financial_health_score: None values detected")
        return {"score": 0, "rating": "Unknown", "details": {}}
    
    # Normalize all inputs to 0-1 range
    p = max(0, min(1, profitability))
    l = max(0, min(1, liquidity))
    le = max(0, min(1, leverage))
    e = max(0, min(1, efficiency))
    
    # Calculate weighted score
    score = (p * 0.35 + l * 0.25 + le * 0.25 + e * 0.15) * 100
    
    # Determine rating
    if score >= 80:
        rating = "Excellent"
    elif score >= 60:
        rating = "Good"
    elif score >= 40:
        rating = "Fair"
    elif score >= 20:
        rating = "Poor"
    else:
        rating = "Critical"
    
    result = {
        "score": round(score, 1),
        "rating": rating,
        "details": {
            "profitability_component": round(p * 0.35 * 100, 1),
            "liquidity_component": round(l * 0.25 * 100, 1),
            "leverage_component": round(le * 0.25 * 100, 1),
            "efficiency_component": round(e * 0.15 * 100, 1),
        }
    }
    
    logger.info(f"financial_health_score: Score={score:.1f}, Rating={rating}")
    return result
