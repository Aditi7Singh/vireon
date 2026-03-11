"""
Chart of Accounts generator.
FIX: Use Account.type (not account_type) per Merge.dev spec.
FIX: Populate company field on every Account.
"""

from data_generation.models import Account, AccountClassification, AccountType, AccountStatus


def generate_accounts(company_id: str = None) -> list:
    """Generate the full Chart of Accounts for SeedlingLabs."""

    definitions = [
        # ── ASSET ──
        {"name": "Operating Checking Account",    "description": "Primary bank account for day-to-day operations",       "classification": AccountClassification.ASSET,     "type": AccountType.BANK},
        {"name": "Savings Account",               "description": "High-yield savings for reserve cash",                  "classification": AccountClassification.ASSET,     "type": AccountType.BANK},
        {"name": "Accounts Receivable",           "description": "Amounts owed by customers for delivered services",     "classification": AccountClassification.ASSET,     "type": AccountType.ACCOUNTS_RECEIVABLE},
        {"name": "Prepaid Expenses",              "description": "Advance payments for services not yet received",       "classification": AccountClassification.ASSET,     "type": AccountType.OTHER_CURRENT_ASSET},

        # ── LIABILITY ──
        {"name": "Accounts Payable",              "description": "Amounts owed to vendors and suppliers",                "classification": AccountClassification.LIABILITY,  "type": AccountType.ACCOUNTS_PAYABLE},
        {"name": "Corporate Credit Card",         "description": "Company credit card for operational purchases",        "classification": AccountClassification.LIABILITY,  "type": AccountType.CREDIT_CARD},
        {"name": "Accrued Liabilities",           "description": "Expenses incurred but not yet paid",                  "classification": AccountClassification.LIABILITY,  "type": AccountType.OTHER_CURRENT_LIABILITY},
        {"name": "Payroll Liabilities",           "description": "Withheld taxes, benefits, and payroll obligations",   "classification": AccountClassification.LIABILITY,  "type": AccountType.OTHER_CURRENT_LIABILITY},

        # ── EQUITY ──
        {"name": "Common Stock",                  "description": "Equity issued to founders and investors",             "classification": AccountClassification.EQUITY,     "type": AccountType.EQUITY},
        {"name": "Retained Earnings",             "description": "Cumulative net income less distributions",            "classification": AccountClassification.EQUITY,     "type": AccountType.EQUITY},

        # ── REVENUE ──
        {"name": "SaaS Subscription Revenue",    "description": "Monthly and annual subscription revenue",             "classification": AccountClassification.REVENUE,    "type": AccountType.OTHER_INCOME},
        {"name": "Professional Services Revenue","description": "Revenue from consulting and implementation services",  "classification": AccountClassification.REVENUE,    "type": AccountType.OTHER_INCOME},
        {"name": "Other Income",                  "description": "Interest income and miscellaneous revenue",           "classification": AccountClassification.REVENUE,    "type": AccountType.OTHER_INCOME},

        # ── EXPENSE ──
        {"name": "Payroll Expense",               "description": "Salaries, wages, and compensation",                   "classification": AccountClassification.EXPENSE,    "type": AccountType.OTHER_EXPENSE},
        {"name": "Employee Benefits",             "description": "Health insurance, 401k, and other benefits",          "classification": AccountClassification.EXPENSE,    "type": AccountType.OTHER_EXPENSE},
        {"name": "Payroll Taxes",                 "description": "Employer-side payroll taxes (FICA, FUTA, SUTA)",      "classification": AccountClassification.EXPENSE,    "type": AccountType.OTHER_EXPENSE},
        {"name": "Cloud & Infrastructure",        "description": "AWS, GCP, and cloud service costs",                   "classification": AccountClassification.EXPENSE,    "type": AccountType.OTHER_EXPENSE},
        {"name": "Office & Rent",                 "description": "Co-working space, office rent, and utilities",        "classification": AccountClassification.EXPENSE,    "type": AccountType.OTHER_EXPENSE},
        {"name": "Marketing & Advertising",       "description": "Digital ads, content marketing, conferences",         "classification": AccountClassification.EXPENSE,    "type": AccountType.OTHER_EXPENSE},
        {"name": "Software & SaaS Subscriptions", "description": "Slack, GitHub, HubSpot, and other SaaS tools",        "classification": AccountClassification.EXPENSE,    "type": AccountType.OTHER_EXPENSE},
        {"name": "Legal & Professional",          "description": "Legal retainer, accounting, and advisory fees",       "classification": AccountClassification.EXPENSE,    "type": AccountType.OTHER_EXPENSE},
        {"name": "Travel & Entertainment",        "description": "Business travel, meals, and entertainment",           "classification": AccountClassification.EXPENSE,    "type": AccountType.OTHER_EXPENSE},
        {"name": "Insurance",                     "description": "Business liability, D&O, and other insurance",        "classification": AccountClassification.EXPENSE,    "type": AccountType.OTHER_EXPENSE},
        {"name": "Recruiting & Hiring",           "description": "Recruiting agency fees, job postings, hiring costs",  "classification": AccountClassification.EXPENSE,    "type": AccountType.OTHER_EXPENSE},
        {"name": "Office Supplies & Miscellaneous","description": "Office supplies, equipment, and miscellaneous",      "classification": AccountClassification.EXPENSE,    "type": AccountType.OTHER_EXPENSE},
    ]

    accounts = []
    for defn in definitions:
        acct = Account(
            name=defn["name"],
            description=defn["description"],
            classification=defn["classification"],
            type=defn["type"],          # FIX: was account_type=
            status=AccountStatus.ACTIVE,
            current_balance=0.0,
            currency="USD",
            company=company_id,         # FIX: propagate company ID
        )
        accounts.append(acct)

    return accounts


def get_account_by_name(accounts: list, name: str) -> Account:
    for acct in accounts:
        if acct.name == name:
            return acct
    raise ValueError(f"Account not found: {name}")
