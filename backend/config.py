from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from datetime import date

class Settings(BaseSettings):
    # App config
    api_v1_prefix: str = "/api/v1"
    
    # Auth
    secret_key: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440 # 1 day
    
    # ERPNext Configuration
    erpnext_url: Optional[str] = None
    erpnext_api_key: Optional[str] = None
    erpnext_api_secret: Optional[str] = None
    erpnext_site_name: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

# ── Company Identity ──────────────────────────────────────────────────────────
COMPANY_LEGAL_NAME = "SeedlingLabs India Private Limited"
COMPANY_CIN        = "U72900KA2024PTC185432"
COMPANY_PAN        = "AAKCS1234R"
COMPANY_GSTIN      = "29AAKCS1234R1Z5"      # 29 = Karnataka state code
COMPANY_TAN        = "BLRS12345B"
COMPANY_HQ         = "Bengaluru, Karnataka"

# ── Fiscal Year ───────────────────────────────────────────────────────────────
START_DATE         = date(2025, 4, 1)        # April 1 = FY start
END_DATE           = date(2026, 3, 31)       # March 31 = FY end
FISCAL_YEAR        = "FY 2025-26"

# ── Currency ──────────────────────────────────────────────────────────────────
CURRENCY           = "INR"
STARTING_CASH      = 8_300_000               # ₹83L seed round

# ── GST ───────────────────────────────────────────────────────────────────────
GST_RATE_SAAS             = 0.18            # SAC 998314 — B2B SaaS
GST_RATE_SERVICES         = 0.18            # Professional services
# IGST for inter-state; CGST 9% + SGST 9% for intra-state (same 18% total)

# ── TDS ───────────────────────────────────────────────────────────────────────
TDS_RATE_PROFESSIONAL     = 0.10            # Sec 194J — CA, lawyers, IT consultants
TDS_RATE_CONTRACT         = 0.02            # Sec 194C — contracts (company-to-company)
TDS_THRESHOLD_194J        = 30_000          # ₹30K single transaction
TDS_THRESHOLD_194C_SINGLE = 30_000          # ₹30K single transaction
TDS_THRESHOLD_194C_ANNUAL = 1_00_000        # ₹1L aggregate annual

# ── PF ────────────────────────────────────────────────────────────────────────
PF_EMPLOYER_RATE          = 0.12            # 12% of basic
PF_ADMIN_CHARGES          = 0.005           # 0.50% administrative charges
EDLI_RATE                 = 0.005           # 0.50% EDLI premium
# Total employer PF outflow: 13% of basic (12% PF + 0.5% admin + 0.5% EDLI)

# ── ESI ───────────────────────────────────────────────────────────────────────
ESI_EMPLOYER_RATE         = 0.0325          # 3.25% employer contribution
ESI_EMPLOYEE_RATE         = 0.0075          # 0.75% employee contribution
ESI_WAGE_CEILING          = 21_000          # ₹21,000/month gross — above this, no ESI

# ── Gratuity ──────────────────────────────────────────────────────────────────
GRATUITY_RATE             = 0.0481          # 4.81% of monthly basic = 15/26/12 × 12
# Payable after 5 years of service. Provision monthly regardless.

# ── Professional Tax (Karnataka) ─────────────────────────────────────────────
PT_SLAB = [
    (15_000, 0),             # ≤ ₹15K gross/month → ₹0 PT
    (20_000, 150),           # ₹15K–₹20K → ₹150/month
    (float('inf'), 200),     # > ₹20K → ₹200/month (Karnataka maximum)
]

# ── Labour Welfare Fund ───────────────────────────────────────────────────────
LWF_EMPLOYER_ANNUAL       = 20              # ₹20/employee annually (December)

# ── CTC Structure ─────────────────────────────────────────────────────────────
BASIC_AS_PCT_OF_CTC       = 0.40            # Basic = 40% of CTC
HRA_AS_PCT_OF_BASIC       = 0.50            # HRA = 50% of Basic (Bengaluru metro)
GHI_PER_EMPLOYEE_MONTHLY  = 1_200           # ₹1,200/employee/month employer share

# ── Hiring Costs ──────────────────────────────────────────────────────────────
EQUIPMENT_COST_PER_HIRE   = 80_000          # ₹80K laptop + peripherals
RECRUITING_COST_PER_HIRE  = 1_50_000        # ₹1.5L agency fee (TeamLease ~8.33% CTC)

# ── Revenue ───────────────────────────────────────────────────────────────────
STARTING_MRR              = 24_90_000       # ₹24.9L MRR (April 2025)
MRR_GROWTH_RATE           = 0.04            # 4% monthly organic growth
MONTHLY_CHURN_RATE        = 0.03            # 3% monthly churn

# ── Cloud (AWS AISPL ap-south-1) ──────────────────────────────────────────────
CLOUD_MONTHLY_GROWTH      = 0.04            # 4% MoM compound growth

# ── Anomaly Baseline ──────────────────────────────────────────────────────────
ANOMALY_VARIANCE_THRESHOLD = 0.15           # 15% variance triggers monitoring alert
ANOMALY_ALERT_THRESHOLD    = 0.50           # 50% variance triggers immediate alert
ANOMALY_BASELINE_MONTHS    = 3              # Use trailing 3-month window for baselines

# ── Fiscal Year ───────────────────────────────────────────────────────────────
FISCAL_YEAR                = "FY 2025-26"   # April 2025 - March 2026
