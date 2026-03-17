"""
Company Profile Configuration
===========================
Financial context for SeedlingLabs that's injected into every agent prompt.
"""

import httpx
from typing import Dict, Optional
from config.settings import BACKEND_URL, COMPANY_NAME


# Fallback company profile when backend is unreachable
FALLBACK_COMPANY_PROFILE = {
    "name": "SeedlingLabs",
    "cash": 485000,
    "monthly_burn": 93000,
    "runway_months": 5.2,
    "mrr": 42000,
    "arr": 504000,
    "last_updated": "unavailable — backend offline"
}


def get_company_context() -> Dict:
    """
    Get the default company financial snapshot.
    The router handles injecting live DB context when available.
    
    Returns:
        Dictionary with company financial context
    """
    return FALLBACK_COMPANY_PROFILE.copy()


def get_seedlinglabs_profile() -> Dict:
    """
    Get the default SeedlingLabs profile for demonstration.
    This is used when no backend connection is available.
    
    Returns:
        Default company profile dictionary
    """
    return {
        "name": "SeedlingLabs",
        "industry": "B2B SaaS",
        "stage": "Series A",
        "founded": "2022",
        "employees": 12,
        "current_cash": 485000,
        "monthly_burn": 93000,
        "runway_months": 5.2,
        "mrr": 42000,
        "arr": 504000,
        "growth_rate": 0.08,
        "gross_margin": 0.72,
        "burn_multiple": 2.2,
        "primary_expense_categories": [
            "payroll",
            "aws",
            "saas",
            "marketing",
            "office"
        ],
        "key_metrics": {
            "magic_number": 1.2,
            "cac_payback_months": 14,
            "ltv_cac_ratio": 4.5,
            "net_revenue_retention": 1.15
        }
    }
