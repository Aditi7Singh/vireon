"""
Chart of Accounts generator.
Creates ~25 accounts covering a realistic seed-stage SaaS startup ledger.
"""

from simulation.models import Account, AccountClassification, AccountType, AccountStatus


def generate_accounts() -> list[Account]:
    """Generate the full Chart of Accounts for SeedlingLabs."""

    definitions = [
        # ── ASSET accounts ──
        {
            "name": "Operating Checking Account",
            "description": "Primary bank account for day-to-day operations",
            "classification": AccountClassification.ASSET,
            "account_type": AccountType.BANK,
        },
        {
            "name": "Savings Account",
            "description": "High-yield savings for reserve cash",
            "classification": AccountClassification.ASSET,
            "account_type": AccountType.BANK,
        },
        {
            "name": "Accounts Receivable",
            "description": "Amounts owed by customers for delivered services",
            "classification": AccountClassification.ASSET,
            "account_type": AccountType.ACCOUNTS_RECEIVABLE,
        },
        {
            "name": "Prepaid Expenses",
            "description": "Advance payments for services not yet received",
            "classification": AccountClassification.ASSET,
            "account_type": AccountType.OTHER_CURRENT_ASSET,
        },

        # ── LIABILITY accounts ──
        {
            "name": "Accounts Payable",
            "description": "Amounts owed to vendors and suppliers",
            "classification": AccountClassification.LIABILITY,
            "account_type": AccountType.ACCOUNTS_PAYABLE,
        },
        {
            "name": "Corporate Credit Card",
            "description": "Company credit card for operational purchases",
            "classification": AccountClassification.LIABILITY,
            "account_type": AccountType.CREDIT_CARD,
        },
        {
            "name": "Accrued Liabilities",
            "description": "Expenses incurred but not yet paid",
            "classification": AccountClassification.LIABILITY,
            "account_type": AccountType.OTHER_CURRENT_LIABILITY,
        },
        {
            "name": "Payroll Liabilities",
            "description": "Withheld taxes, benefits, and other payroll obligations",
            "classification": AccountClassification.LIABILITY,
            "account_type": AccountType.OTHER_CURRENT_LIABILITY,
        },

        # ── EQUITY accounts ──
        {
            "name": "Common Stock",
            "description": "Equity issued to founders and investors",
            "classification": AccountClassification.EQUITY,
            "account_type": "EQUITY",
        },
        {
            "name": "Retained Earnings",
            "description": "Cumulative net income less distributions",
            "classification": AccountClassification.EQUITY,
            "account_type": "EQUITY",
        },

        # ── REVENUE accounts ──
        {
            "name": "SaaS Subscription Revenue",
            "description": "Monthly and annual subscription revenue from customers",
            "classification": AccountClassification.REVENUE,
            "account_type": AccountType.OTHER_INCOME,
        },
        {
            "name": "Professional Services Revenue",
            "description": "Revenue from consulting and implementation services",
            "classification": AccountClassification.REVENUE,
            "account_type": AccountType.OTHER_INCOME,
        },
        {
            "name": "Other Income",
            "description": "Interest income and miscellaneous revenue",
            "classification": AccountClassification.REVENUE,
            "account_type": AccountType.OTHER_INCOME,
        },

        # ── EXPENSE accounts ──
        {
            "name": "Payroll Expense",
            "description": "Salaries, wages, and compensation",
            "classification": AccountClassification.EXPENSE,
            "account_type": AccountType.OTHER_EXPENSE,
        },
        {
            "name": "Employee Benefits",
            "description": "Health insurance, 401k, and other benefits",
            "classification": AccountClassification.EXPENSE,
            "account_type": AccountType.OTHER_EXPENSE,
        },
        {
            "name": "Payroll Taxes",
            "description": "Employer-side payroll taxes (FICA, FUTA, SUTA)",
            "classification": AccountClassification.EXPENSE,
            "account_type": AccountType.OTHER_EXPENSE,
        },
        {
            "name": "Cloud & Infrastructure",
            "description": "AWS, GCP, and cloud service costs",
            "classification": AccountClassification.EXPENSE,
            "account_type": AccountType.OTHER_EXPENSE,
        },
        {
            "name": "Office & Rent",
            "description": "Co-working space, office rent, and utilities",
            "classification": AccountClassification.EXPENSE,
            "account_type": AccountType.OTHER_EXPENSE,
        },
        {
            "name": "Marketing & Advertising",
            "description": "Digital ads, content marketing, conferences",
            "classification": AccountClassification.EXPENSE,
            "account_type": AccountType.OTHER_EXPENSE,
        },
        {
            "name": "Software & SaaS Subscriptions",
            "description": "Slack, GitHub, HubSpot, and other SaaS tools",
            "classification": AccountClassification.EXPENSE,
            "account_type": AccountType.OTHER_EXPENSE,
        },
        {
            "name": "Legal & Professional",
            "description": "Legal retainer, accounting, and advisory fees",
            "classification": AccountClassification.EXPENSE,
            "account_type": AccountType.OTHER_EXPENSE,
        },
        {
            "name": "Travel & Entertainment",
            "description": "Business travel, meals, and entertainment",
            "classification": AccountClassification.EXPENSE,
            "account_type": AccountType.OTHER_EXPENSE,
        },
        {
            "name": "Insurance",
            "description": "Business liability, D&O, and other insurance",
            "classification": AccountClassification.EXPENSE,
            "account_type": AccountType.OTHER_EXPENSE,
        },
        {
            "name": "Recruiting & Hiring",
            "description": "Recruiting agency fees, job postings, hiring costs",
            "classification": AccountClassification.EXPENSE,
            "account_type": AccountType.OTHER_EXPENSE,
        },
        {
            "name": "Office Supplies & Miscellaneous",
            "description": "Office supplies, equipment, and miscellaneous expenses",
            "classification": AccountClassification.EXPENSE,
            "account_type": AccountType.OTHER_EXPENSE,
        },
    ]

    accounts = []
    for defn in definitions:
        acct = Account(
            name=defn["name"],
            description=defn["description"],
            classification=defn["classification"],
            account_type=defn["account_type"],
            status=AccountStatus.ACTIVE,
            current_balance=0.0,
            currency="USD",
        )
        accounts.append(acct)

    return accounts


def get_account_by_name(accounts: list[Account], name: str) -> Account:
    """Look up an account by its name. Raises ValueError if not found."""
    for acct in accounts:
        if acct.name == name:
            return acct
    raise ValueError(f"Account not found: {name}")
