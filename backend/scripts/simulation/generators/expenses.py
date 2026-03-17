"""
Operating expenses generator.
Creates monthly expenses for rent, SaaS tools, legal, insurance,
marketing, travel, and miscellaneous categories.
"""

from dateutil.relativedelta import relativedelta
import random

from simulation.config import (
    OPERATING_EXPENSES, SAAS_TOOLS, MARKETING_GROWTH_RATE,
    START_DATE, NUM_MONTHS,
)
from simulation.models import Expense, ExpenseLine, _date_iso


# Account name → config key mapping
_CATEGORY_ACCOUNT_MAP = {
    "Office / Co-working (WeWork)": "Office & Rent",
    "SaaS Subscriptions": "Software & SaaS Subscriptions",
    "Legal Retainer": "Legal & Professional",
    "Business Insurance": "Insurance",
    "Marketing & Advertising": "Marketing & Advertising",
    "Travel & Entertainment": "Travel & Entertainment",
    "Office Supplies & Misc": "Office Supplies & Miscellaneous",
}

# Category → vendor name mapping
_CATEGORY_VENDOR_MAP = {
    "Office / Co-working (WeWork)": "WeWork",
    "Legal Retainer": "Mitchell & Associates LLP",
    "Business Insurance": "Sentinel Insurance Co",
    "Travel & Entertainment": "ClearView Travel",
    "Office Supplies & Misc": "Staples Business",
}


def generate_operating_expenses(
    accounts: list,
    vendor_contacts: dict,
    seed: int = 42,
) -> dict:
    """
    Generate monthly operating expenses.

    Returns:
        dict with:
            'expenses': list of Expense objects
            'monthly_opex': dict of month_num → {category: amount}
    """
    rng = random.Random(seed)

    # Build account lookup
    account_map = {}
    bank_account = None
    for acct in accounts:
        account_map[acct.name] = acct
        if acct.name == "Operating Checking Account":
            bank_account = acct

    expenses = []
    monthly_opex = {}

    for month_num in range(1, NUM_MONTHS + 1):
        month_date = START_DATE + relativedelta(months=month_num - 1)
        month_categories = {}

        for category, base_amount in OPERATING_EXPENSES.items():
            # ── Determine the amount for this month ──
            amount = base_amount

            # Marketing grows over time
            if category == "Marketing & Advertising":
                amount = base_amount * (1 + MARKETING_GROWTH_RATE) ** (month_num - 1)

            # Travel & Entertainment: more variable
            if category == "Travel & Entertainment":
                amount *= rng.uniform(0.6, 1.5)

            # Office Supplies: random variance
            if category == "Office Supplies & Misc":
                amount *= rng.uniform(0.5, 1.8)

            amount = round(amount, 2)
            month_categories[category] = amount

            # ── Build expense lines ──
            lines = []

            # SaaS Subscriptions get broken into individual tools
            if category == "SaaS Subscriptions":
                for tool_name, tool_cost in SAAS_TOOLS.items():
                    # Small variance per tool
                    t_cost = round(tool_cost * rng.uniform(0.95, 1.05), 2)
                    target_acct = account_map.get("Software & SaaS Subscriptions")
                    lines.append(ExpenseLine(
                        description=f"{tool_name} — Monthly Subscription",
                        net_amount=t_cost,
                        total_amount=t_cost,
                        account=target_acct.id if target_acct else None,
                    ))
                # Recalculate total from individual tools
                amount = round(sum(l.total_amount for l in lines), 2)
                month_categories[category] = amount
            else:
                acct_name = _CATEGORY_ACCOUNT_MAP.get(category, category)
                target_acct = account_map.get(acct_name)
                lines.append(ExpenseLine(
                    description=f"{category} — {month_date.strftime('%B %Y')}",
                    net_amount=amount,
                    total_amount=amount,
                    account=target_acct.id if target_acct else None,
                ))

            # ── Find the vendor ──
            vendor_name = _CATEGORY_VENDOR_MAP.get(category)
            vendor_contact = vendor_contacts.get(vendor_name) if vendor_name else None
            vendor_id = vendor_contact.id if vendor_contact else None

            # Payment date varies (rent on 1st, others scattered)
            if category == "Office / Co-working (WeWork)":
                pay_day = 1
            else:
                pay_day = rng.randint(1, 25)
            pay_date = month_date.replace(day=min(pay_day, 28))

            expense = Expense(
                transaction_date=_date_iso(pay_date),
                remote_created_at=_date_iso(pay_date),
                account=bank_account.id if bank_account else None,
                contact=vendor_id,
                total_amount=-amount,
                sub_total=-amount,
                currency="USD",
                memo=f"{category} — {month_date.strftime('%B %Y')}",
                lines=lines,
            )
            expenses.append(expense)

        monthly_opex[month_num] = month_categories

    return {
        "expenses": expenses,
        "monthly_opex": monthly_opex,
    }
