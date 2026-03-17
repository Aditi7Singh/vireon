"""
Configuration constants for SeedlingLabs financial data generation.
All parameters controlling the simulation live here.
"""

from datetime import date

# ─── Company Identity ──────────────────────────────────────────────────────────
COMPANY_NAME = "SeedlingLabs"
COMPANY_LEGAL_NAME = "SeedlingLabs, Inc."
COMPANY_TAX_ID = "84-2345678"
COMPANY_INDUSTRY = "B2B SaaS"
COMPANY_STAGE = "Seed"

# ─── Simulation Window ────────────────────────────────────────────────────────
START_DATE = date(2025, 3, 1)   # Month 1
END_DATE   = date(2026, 2, 28)  # Month 12
NUM_MONTHS = 12

# ─── Cash & Burn ──────────────────────────────────────────────────────────────
STARTING_CASH = 1_000_000       # $1M from seed round
MONTHLY_BURN_BASE = 80_000      # ~$80K/month baseline burn rate

# ─── Currency ─────────────────────────────────────────────────────────────────
CURRENCY = "USD"

# ─── Revenue Parameters ──────────────────────────────────────────────────────
STARTING_MRR = 30_000           # $30K MRR at Month 1
MRR_GROWTH_RATE = 0.04          # 4% monthly MRR growth
MONTHLY_CHURN_RATE = 0.03       # ~3% monthly churn

# ─── Payroll Parameters ──────────────────────────────────────────────────────
BENEFITS_RATE = 0.20            # 20% of base salary for benefits
PAYROLL_TAX_RATE = 0.10         # 10% of base salary for employer taxes
EQUIPMENT_COST_PER_HIRE = 3_000 # One-time: laptop + peripherals
RECRUITING_COST_PER_HIRE = 8_000 # Average recruiting fee

# Initial team (Month 1)
INITIAL_TEAM = [
    {"role": "CEO / Founder",       "salary": 100_000, "start_month": 1},
    {"role": "Senior Engineer",     "salary": 140_000, "start_month": 1},
    {"role": "Senior Engineer",     "salary": 140_000, "start_month": 1},
    {"role": "Product Manager",     "salary": 120_000, "start_month": 1},
    {"role": "Product Designer",    "salary": 110_000, "start_month": 1},
]

# Hires during the 12-month window
NEW_HIRES = [
    {"role": "Mid-Level Engineer",  "salary": 130_000, "start_month": 4},
    {"role": "Marketing Manager",   "salary": 105_000, "start_month": 7},
    {"role": "Mid-Level Engineer",  "salary": 135_000, "start_month": 10},
    {"role": "Junior Engineer",     "salary": 110_000, "start_month": 10},
]

# ─── Cloud Cost Parameters ───────────────────────────────────────────────────
CLOUD_BASELINE = {
    "EC2 Compute":      5_000,
    "RDS Database":     2_000,
    "S3 Storage":       1_000,
    "Lambda Functions":   500,
    "CloudFront CDN":     400,
    "Other Services":   1_100,
}
CLOUD_MONTHLY_GROWTH = 0.04  # 4% month-over-month (mirrors user growth)

# ─── Operating Expense Baselines ─────────────────────────────────────────────
OPERATING_EXPENSES = {
    "Office / Co-working (WeWork)":     3_500,
    "SaaS Subscriptions":               2_500,
    "Legal Retainer":                    1_500,
    "Business Insurance":                 800,
    "Marketing & Advertising":          3_000,  # grows over time
    "Travel & Entertainment":           1_500,  # variable
    "Office Supplies & Misc":             750,  # variable
}
MARKETING_GROWTH_RATE = 0.05  # 5% monthly increase on marketing

# ─── SaaS Tool Breakdown (sub-lines of SaaS Subscriptions) ──────────────────
SAAS_TOOLS = {
    "Slack":         250,
    "GitHub":        400,
    "HubSpot":       600,
    "Adobe CC":      300,
    "Figma":         150,
    "Notion":        120,
    "Zoom":          200,
    "Datadog":       480,
}

# ─── Customer Definitions ────────────────────────────────────────────────────
CUSTOMERS = [
    {"name": "Acme Corp",           "mrr": 8_000,  "start_month": 1,  "billing": "monthly",   "payment_terms": 30},
    {"name": "TechFlow Solutions",  "mrr": 5_000,  "start_month": 1,  "billing": "annual",    "payment_terms": 30},
    {"name": "DataBridge Inc",      "mrr": 4_500,  "start_month": 1,  "billing": "monthly",   "payment_terms": 15},
    {"name": "CloudNine Analytics", "mrr": 3_500,  "start_month": 2,  "billing": "monthly",   "payment_terms": 30},
    {"name": "GreenLeaf Ventures",  "mrr": 2_800,  "start_month": 2,  "billing": "annual",    "payment_terms": 45},
    {"name": "Quantum Dynamics",    "mrr": 2_000,  "start_month": 3,  "billing": "monthly",   "payment_terms": 30},
    {"name": "NexaPoint",           "mrr": 2_200,  "start_month": 4,  "billing": "monthly",   "payment_terms": 30},
    {"name": "SilverStack Labs",    "mrr": 1_500,  "start_month": 5,  "billing": "monthly",   "payment_terms": 15},
    {"name": "Meridian Health",     "mrr": 3_000,  "start_month": 6,  "billing": "annual",    "payment_terms": 30},
    {"name": "Orion Platforms",     "mrr": 1_800,  "start_month": 8,  "billing": "monthly",   "payment_terms": 30},
]

# ─── Vendor Definitions ──────────────────────────────────────────────────────
VENDORS = [
    {"name": "Amazon Web Services",   "category": "Cloud",          "email": "billing@aws.amazon.com"},
    {"name": "Google Cloud Platform",  "category": "Cloud",         "email": "billing@cloud.google.com"},
    {"name": "WeWork",                "category": "Office",         "email": "accounts@wework.com"},
    {"name": "Gusto Payroll",         "category": "Payroll",        "email": "billing@gusto.com"},
    {"name": "HubSpot Inc",           "category": "SaaS",           "email": "billing@hubspot.com"},
    {"name": "Slack Technologies",    "category": "SaaS",           "email": "billing@slack.com"},
    {"name": "GitHub Inc",            "category": "SaaS",           "email": "billing@github.com"},
    {"name": "Adobe Systems",         "category": "SaaS",           "email": "billing@adobe.com"},
    {"name": "Figma Inc",             "category": "SaaS",           "email": "billing@figma.com"},
    {"name": "Mitchell & Associates LLP", "category": "Legal",      "email": "ar@mitchelllaw.com"},
    {"name": "Sentinel Insurance Co", "category": "Insurance",      "email": "billing@sentinelins.com"},
    {"name": "TalentBridge Recruiting", "category": "Recruiting",   "email": "invoices@talentbridge.io"},
    {"name": "Staples Business",      "category": "Office Supplies","email": "accounts@staples.com"},
    {"name": "ClearView Travel",      "category": "Travel",         "email": "billing@clearviewtravel.com"},
    {"name": "Notion Labs",           "category": "SaaS",           "email": "billing@notion.so"},
]

# ─── Anomaly Definitions ─────────────────────────────────────────────────────
ANOMALIES = [
    {
        "id": "ANM-001",
        "type": "absolute_spike",
        "month": 8,
        "category": "Cloud",
        "description": "AWS costs spike from ~$12K baseline to $18,245 (+50%) — rogue i3.8xlarge instances",
        "expected_amount": 12_100,
        "actual_amount": 18_245,
    },
    {
        "id": "ANM-002",
        "type": "duplicate_payment",
        "month": 6,
        "category": "Office",
        "description": "WeWork rent paid twice in same month ($7,000 instead of $3,500)",
        "expected_amount": 3_500,
        "actual_amount": 7_000,
    },
    {
        "id": "ANM-003",
        "type": "new_vendor",
        "month": 9,
        "category": "Software",
        "description": "Unknown vendor 'DataSync Pro' charges $25,000 — single large transaction, verify legitimacy",
        "expected_amount": 0,
        "actual_amount": 25_000,
    },
    {
        "id": "ANM-004",
        "type": "trend_anomaly",
        "month": 7,  # starts month 7, escalates through month 12
        "category": "Marketing",
        "description": "Marketing spend escalates 5x ($3K → $15K/mo) without proportional revenue increase",
        "expected_amount": 3_500,
        "actual_amount": 15_000,
    },
    {
        "id": "ANM-005",
        "type": "category_spike",
        "month": 11,
        "category": "Travel",
        "description": "Travel expenses 3x normal ($6,000 vs $2,000 avg) — conference season",
        "expected_amount": 2_000,
        "actual_amount": 6_000,
    },
    {
        "id": "ANM-006",
        "type": "payroll_creep",
        "month": 10,
        "category": "Payroll",
        "description": "Payroll jumps ~$25K/month with 2 simultaneous new hires — unsustainable at current revenue",
        "expected_amount": None,  # computed dynamically
        "actual_amount": None,
    },
    {
        "id": "ANM-007",
        "type": "revenue_drop",
        "month": 11,
        "category": "Revenue",
        "description": "Largest customer Acme Corp ($8K/mo) churns — MRR drops ~15%",
        "expected_amount": None,
        "actual_amount": None,
    },
]

# ─── Random Seed ──────────────────────────────────────────────────────────────
SEED = 42
