"""
Cloud / AWS cost generator.
Creates per-service expense breakdowns with organic growth.
Anomaly #1 (AWS spike in Month 8) is injected by the anomaly injector,
but baseline growth is handled here.
"""

from dateutil.relativedelta import relativedelta
import random

from simulation.config import (
    CLOUD_BASELINE, CLOUD_MONTHLY_GROWTH, START_DATE, NUM_MONTHS,
)
from simulation.models import Expense, ExpenseLine, _date_iso


def generate_cloud_costs(
    accounts: list,
    vendor_contacts: dict,
    seed: int = 42,
) -> dict:
    """
    Generate monthly cloud infrastructure expenses.

    Returns:
        dict with:
            'expenses': list of Expense objects (one per month)
            'monthly_cloud': dict of month_num → total cloud cost
    """
    rng = random.Random(seed)

    # Find relevant accounts
    cloud_account = bank_account = None
    for acct in accounts:
        if acct.name == "Cloud & Infrastructure":
            cloud_account = acct
        elif acct.name == "Operating Checking Account":
            bank_account = acct

    aws_contact = vendor_contacts.get("Amazon Web Services")
    aws_id = aws_contact.id if aws_contact else None

    expenses = []
    monthly_cloud = {}

    for month_num in range(1, NUM_MONTHS + 1):
        month_date = START_DATE + relativedelta(months=month_num - 1)
        # Bill arrives on the 3rd of the following month
        bill_date = (month_date + relativedelta(months=1)).replace(day=3)

        lines = []
        month_total = 0.0

        for service_name, base_cost in CLOUD_BASELINE.items():
            # Apply compound growth
            grown_cost = base_cost * (1 + CLOUD_MONTHLY_GROWTH) ** (month_num - 1)
            # Add random daily variance (±5%)
            grown_cost *= (1 + rng.uniform(-0.05, 0.05))
            grown_cost = round(grown_cost, 2)

            month_total += grown_cost

            lines.append(ExpenseLine(
                description=f"AWS — {service_name} — {month_date.strftime('%B %Y')}",
                net_amount=grown_cost,
                total_amount=grown_cost,
                account=cloud_account.id if cloud_account else None,
                contact=aws_id,
            ))

        month_total = round(month_total, 2)
        monthly_cloud[month_num] = month_total

        expense = Expense(
            transaction_date=_date_iso(bill_date),
            remote_created_at=_date_iso(bill_date),
            account=bank_account.id if bank_account else None,
            contact=aws_id,
            total_amount=-month_total,
            sub_total=-month_total,
            currency="USD",
            memo=f"AWS Invoice — {month_date.strftime('%B %Y')}",
            lines=lines,
        )
        expenses.append(expense)

    return {
        "expenses": expenses,
        "monthly_cloud": monthly_cloud,
    }
