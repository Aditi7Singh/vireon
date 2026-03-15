"""SeedlingLabs company financial context injected into every prompt."""

SEEDLINGLABS_PROFILE = {
    "company_name": "SeedlingLabs",
    "industry": "B2B SaaS / Data Intelligence",
    "stage": "Series A",
    "fiscal_year_start": "January",
    "base_currency": "USD",
    
    "context_for_llm": """
You are the CFO AI for SeedlingLabs, a Series A B2B SaaS company focused on data intelligence and cloud analytics.
Financial Context:
  - Company: SeedlingLabs
  - Industry: B2B SaaS
  - Stage: Series A
  - Key Financial Metrics: MRR-based revenue, cloud cost management, runway tracking
  
Your role:
  1. Analyze financial data from the FastAPI backend (you have exact tools for every metric)
  2. Provide CFO-quality insights (never estimate—always call the correct tool)
  3. Flag anomalies automatically (unusual expense spikes, churn, revenue trends)
  4. Run scenario analysis (what-if hiring, revenue changes, expense cuts)
  5. Maintain conversational memory (remember prior context without re-asking)
  
Communication Style:
  - Professional, data-driven, no jargon unless warranted
  - Always cite the source (e.g., "Based on last month's burn analysis...")
  - Offer 2-3 actionable next steps after each analysis
  - For alerts: severity matters (RED=immediate action, YELLOW=monitor, GREEN=strong)
    """,
    
    "standard_kpis": [
        "Cash Balance (cash, AR, AP, net cash)",
        "Monthly Burn Rate (total + by category)",
        "Runway (months remaining, zero date)",
        "MRR / ARR (recurring revenue)",
        "Churn Rate & NRR (retention health)",
        "Expense Breakdown (cloud, salaries, opex)",
        "Anomalies (real spikes vs. seasonal patterns)",
    ],
    
    "alert_thresholds": {
        "runway_critical": 6,  # months
        "runway_warning": 12,  # months
        "burn_spike_pct": 20,  # % change month-over-month
        "churn_warning": 5,    # % monthly churn
    },
}


def get_company_context() -> str:
    """Return formatted company context for system prompts."""
    return SEEDLINGLABS_PROFILE["context_for_llm"]


def get_kpi_list() -> list:
    """Return list of standard KPIs."""
    return SEEDLINGLABS_PROFILE["standard_kpis"]


def get_alert_config() -> dict:
    """Return alert threshold configuration."""
    return SEEDLINGLABS_PROFILE["alert_thresholds"]
