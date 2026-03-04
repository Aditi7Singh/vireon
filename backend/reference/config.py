"""
Finance Agent - Data Generator Configuration
Defines company profiles, expense categories, and generation parameters
"""

from datetime import datetime, timedelta
from decimal import Decimal
import random

# ============================================================================
# COMPANY PROFILES
# ============================================================================

COMPANY_PROFILES = [
    {
        "name": "SeedlingLabs",
        "industry": "B2B SaaS",
        "stage": "series_a",
        "initial_cash": Decimal("1000000"),  # $1M
        "founding_date": datetime(2023, 1, 1),
        "monthly_revenue_base": Decimal("45000"),  # Starting MRR
        "revenue_growth_rate": 0.08,  # 8% monthly growth
        "burn_rate_base": Decimal("80000"),  # $80k/month
        "employee_count": 8,
        "customers_count": 25,
    },
    {
        "name": "CloudMetrics Inc",
        "industry": "DevOps Tools",
        "stage": "seed",
        "initial_cash": Decimal("500000"),
        "founding_date": datetime(2023, 6, 1),
        "monthly_revenue_base": Decimal("12000"),
        "revenue_growth_rate": 0.12,  # 12% monthly growth (early stage)
        "burn_rate_base": Decimal("45000"),
        "employee_count": 4,
        "customers_count": 15,
    },
    {
        "name": "DataPulse Analytics",
        "industry": "Data Analytics",
        "stage": "series_b",
        "initial_cash": Decimal("3000000"),
        "founding_date": datetime(2022, 3, 1),
        "monthly_revenue_base": Decimal("180000"),
        "revenue_growth_rate": 0.05,  # 5% monthly growth (more mature)
        "burn_rate_base": Decimal("220000"),
        "employee_count": 35,
        "customers_count": 120,
    },
    {
        "name": "APIFlow Systems",
        "industry": "API Infrastructure",
        "stage": "seed",
        "initial_cash": Decimal("750000"),
        "founding_date": datetime(2023, 9, 1),
        "monthly_revenue_base": Decimal("8000"),
        "revenue_growth_rate": 0.15,  # 15% monthly growth (high growth)
        "burn_rate_base": Decimal("55000"),
        "employee_count": 5,
        "customers_count": 8,
    },
    {
        "name": "SecureAuth Platform",
        "industry": "Cybersecurity",
        "stage": "series_a",
        "initial_cash": Decimal("1500000"),
        "founding_date": datetime(2022, 11, 1),
        "monthly_revenue_base": Decimal("75000"),
        "revenue_growth_rate": 0.06,
        "burn_rate_base": Decimal("120000"),
        "employee_count": 15,
        "customers_count": 45,
    },
]

# ============================================================================
# EXPENSE CATEGORIES & VENDORS
# ============================================================================

EXPENSE_CATEGORIES = {
    "Cloud": {
        "vendors": {
            "Amazon Web Services": {
                "base_monthly": Decimal("12000"),
                "variance": 0.15,  # ±15%
                "services": ["EC2", "S3", "RDS", "Lambda", "CloudFront"]
            },
            "Google Cloud Platform": {
                "base_monthly": Decimal("8000"),
                "variance": 0.12,
                "services": ["Compute Engine", "Cloud Storage", "BigQuery", "Cloud Functions"]
            },
            "Vercel": {
                "base_monthly": Decimal("500"),
                "variance": 0.20,
                "services": ["Hosting", "Edge Functions", "Analytics"]
            },
            "MongoDB Atlas": {
                "base_monthly": Decimal("800"),
                "variance": 0.10,
                "services": ["Database"]
            },
        }
    },
    "Software": {
        "vendors": {
            "GitHub": {"base_monthly": Decimal("200"), "variance": 0.05},
            "Slack": {"base_monthly": Decimal("300"), "variance": 0.10},
            "Notion": {"base_monthly": Decimal("150"), "variance": 0.05},
            "Figma": {"base_monthly": Decimal("180"), "variance": 0.05},
            "Linear": {"base_monthly": Decimal("100"), "variance": 0.05},
            "Postman": {"base_monthly": Decimal("80"), "variance": 0.05},
            "DataDog": {"base_monthly": Decimal("1200"), "variance": 0.15},
            "Sentry": {"base_monthly": Decimal("300"), "variance": 0.10},
            "Auth0": {"base_monthly": Decimal("600"), "variance": 0.12},
            "Stripe": {"base_monthly": Decimal("400"), "variance": 0.08},
        }
    },
    "Marketing": {
        "vendors": {
            "Google Ads": {"base_monthly": Decimal("5000"), "variance": 0.30},
            "LinkedIn Ads": {"base_monthly": Decimal("3000"), "variance": 0.25},
            "HubSpot": {"base_monthly": Decimal("800"), "variance": 0.10},
            "Mailchimp": {"base_monthly": Decimal("200"), "variance": 0.15},
            "SEMrush": {"base_monthly": Decimal("300"), "variance": 0.05},
        }
    },
    "Sales": {
        "vendors": {
            "Salesforce": {"base_monthly": Decimal("1200"), "variance": 0.10},
            "ZoomInfo": {"base_monthly": Decimal("900"), "variance": 0.05},
            "Apollo.io": {"base_monthly": Decimal("600"), "variance": 0.10},
            "Calendly": {"base_monthly": Decimal("100"), "variance": 0.05},
        }
    },
    "Office": {
        "vendors": {
            "WeWork": {"base_monthly": Decimal("3500"), "variance": 0.05},
            "Office Depot": {"base_monthly": Decimal("400"), "variance": 0.30},
            "Regus Virtual Office": {"base_monthly": Decimal("200"), "variance": 0.05},
        }
    },
    "Professional Services": {
        "vendors": {
            "Wilson Sonsini Law Firm": {"base_monthly": Decimal("5000"), "variance": 0.50},
            "Deloitte Accounting": {"base_monthly": Decimal("2500"), "variance": 0.30},
            "TechRecruiter Inc": {"base_monthly": Decimal("8000"), "variance": 0.60},
        }
    },
    "Travel": {
        "vendors": {
            "Delta Airlines": {"base_monthly": Decimal("1200"), "variance": 0.80},
            "Marriott Hotels": {"base_monthly": Decimal("800"), "variance": 0.70},
            "Uber": {"base_monthly": Decimal("300"), "variance": 0.50},
        }
    },
}

# ============================================================================
# EMPLOYEE PROFILES
# ============================================================================

EMPLOYEE_TEMPLATES = [
    # Engineering
    {"title": "Senior Software Engineer", "department": "Engineering", "salary": Decimal("150000"), "type": "full_time"},
    {"title": "Software Engineer", "department": "Engineering", "salary": Decimal("120000"), "type": "full_time"},
    {"title": "Frontend Engineer", "department": "Engineering", "salary": Decimal("130000"), "type": "full_time"},
    {"title": "DevOps Engineer", "department": "Engineering", "salary": Decimal("140000"), "type": "full_time"},
    {"title": "Engineering Manager", "department": "Engineering", "salary": Decimal("180000"), "type": "full_time"},
    
    # Product
    {"title": "Product Manager", "department": "Product", "salary": Decimal("140000"), "type": "full_time"},
    {"title": "Product Designer", "department": "Product", "salary": Decimal("125000"), "type": "full_time"},
    
    # Sales & Marketing
    {"title": "Head of Sales", "department": "Sales", "salary": Decimal("160000"), "type": "full_time"},
    {"title": "Account Executive", "department": "Sales", "salary": Decimal("110000"), "type": "full_time"},
    {"title": "Marketing Manager", "department": "Marketing", "salary": Decimal("115000"), "type": "full_time"},
    {"title": "Content Marketer", "department": "Marketing", "salary": Decimal("85000"), "type": "full_time"},
    
    # Operations
    {"title": "CEO", "department": "Executive", "salary": Decimal("200000"), "type": "full_time"},
    {"title": "CTO", "department": "Executive", "salary": Decimal("190000"), "type": "full_time"},
    {"title": "Operations Manager", "department": "Operations", "salary": Decimal("100000"), "type": "full_time"},
    
    # Contractors
    {"title": "Contract Designer", "department": "Product", "salary": Decimal("8000"), "type": "contractor"},
    {"title": "Contract Developer", "department": "Engineering", "salary": Decimal("10000"), "type": "contractor"},
]

# ============================================================================
# CUSTOMER PROFILES
# ============================================================================

CUSTOMER_SEGMENTS = {
    "enterprise": {
        "mrr_range": (Decimal("5000"), Decimal("25000")),
        "payment_terms": "net_30",
        "churn_rate": 0.02,  # 2% monthly
        "count_percentage": 0.15,
    },
    "mid_market": {
        "mrr_range": (Decimal("1000"), Decimal("5000")),
        "payment_terms": "net_30",
        "churn_rate": 0.04,
        "count_percentage": 0.35,
    },
    "smb": {
        "mrr_range": (Decimal("200"), Decimal("1000")),
        "payment_terms": "due_on_receipt",
        "churn_rate": 0.06,
        "count_percentage": 0.50,
    },
}

COMPANY_NAME_TEMPLATES = [
    "{adjective} {noun}",
    "{noun} {suffix}",
    "{tech_term} {suffix}",
]

ADJECTIVES = ["Acme", "Global", "Advanced", "Strategic", "Dynamic", "Innovative", "Premier", "Elite", "Quantum"]
NOUNS = ["Solutions", "Systems", "Technologies", "Enterprises", "Industries", "Corporation", "Group"]
TECH_TERMS = ["Cloud", "Data", "Cyber", "Digital", "Smart", "Tech", "Net", "Soft"]
SUFFIXES = ["Inc", "LLC", "Corp", "Co", "Labs", "Systems", "Platform"]

# ============================================================================
# ANOMALY INJECTION TEMPLATES
# ============================================================================

ANOMALY_TEMPLATES = [
    {
        "name": "AWS Cost Spike",
        "type": "expense_spike",
        "category": "Cloud",
        "vendor": "Amazon Web Services",
        "month": 8,  # Month 8 of 12
        "multiplier": 1.52,  # 52% increase
        "description": "Unoptimized EC2 instances - t3.2xlarge left running 24/7 after load test",
        "severity": "warning",
    },
    {
        "name": "Duplicate Vendor Payment",
        "type": "duplicate_payment",
        "category": "Professional Services",
        "vendor": "Wilson Sonsini Law Firm",
        "month": 5,
        "amount": Decimal("5000"),
        "description": "Same invoice paid twice - accounting system glitch",
        "severity": "critical",
    },
    {
        "name": "Marketing Budget Overrun",
        "type": "expense_spike",
        "category": "Marketing",
        "vendor": "Google Ads",
        "month": 10,
        "multiplier": 2.3,  # 130% increase
        "description": "Campaign budget cap removed accidentally",
        "severity": "critical",
    },
    {
        "name": "Unauthorized SaaS Subscription",
        "type": "new_vendor",
        "category": "Software",
        "vendor": "RandomTool Pro",
        "month": 7,
        "amount": Decimal("2500"),
        "description": "Department subscribed without approval",
        "severity": "warning",
    },
    {
        "name": "Database Cost Explosion",
        "type": "expense_spike",
        "category": "Cloud",
        "vendor": "MongoDB Atlas",
        "month": 9,
        "multiplier": 3.2,  # 220% increase
        "description": "Upgraded to M60 cluster without cost analysis",
        "severity": "critical",
    },
    {
        "name": "Large Customer Churn",
        "type": "revenue_drop",
        "month": 11,
        "amount": Decimal("15000"),
        "description": "Enterprise customer churned - contracted to competitor",
        "severity": "critical",
    },
    {
        "name": "Payroll Processing Error",
        "type": "expense_spike",
        "category": "Payroll",
        "month": 6,
        "multiplier": 1.85,  # 85% increase
        "description": "Bonus payments processed twice in same month",
        "severity": "critical",
    },
    {
        "name": "Unusual Legal Fees",
        "type": "expense_spike",
        "category": "Professional Services",
        "vendor": "Wilson Sonsini Law Firm",
        "month": 4,
        "multiplier": 2.8,
        "description": "Patent filing emergency - expedited processing",
        "severity": "warning",
    },
]

# ============================================================================
# GENERATION PARAMETERS
# ============================================================================

GENERATION_CONFIG = {
    "months_to_generate": 12,
    "start_date": datetime(2024, 1, 1),
    "currency": "USD",
    
    # Randomization
    "revenue_variance": 0.10,  # ±10% variance in revenue
    "expense_variance": 0.08,  # ±8% variance in regular expenses
    
    # Growth patterns
    "seasonal_revenue_boost": {
        11: 1.15,  # 15% boost in November (holiday sales)
        12: 1.20,  # 20% boost in December
    },
    "seasonal_expense_increase": {
        12: 1.10,  # 10% increase in December (end-of-year spending)
    },
    
    # Invoice patterns
    "invoice_payment_delay_days": {
        "due_on_receipt": (0, 5),
        "net_15": (10, 20),
        "net_30": (25, 40),
        "net_60": (55, 70),
    },
    "late_payment_probability": 0.25,  # 25% of invoices paid late
    
    # Anomaly injection
    "inject_anomalies": True,
    "anomalies_per_company": 5,  # Number of anomalies to inject per company
}
