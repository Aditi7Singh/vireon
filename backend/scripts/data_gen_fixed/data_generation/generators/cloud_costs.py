"""
Cloud / AWS cost generator.
FIX: company field populated on every Expense.
FIX: ExpenseLine no 'contact' at line level.
"""

from dateutil.relativedelta import relativedelta
import random

from data_generation.config import CLOUD_BASELINE, CLOUD_MONTHLY_GROWTH, START_DATE, NUM_MONTHS
from data_generation.models import Expense, ExpenseLine, _date_iso


def generate_cloud_costs(
    accounts: list,
    vendor_contacts: dict,
    company_id: str = None,
    seed: int = 42,
) -> dict:
    rng = random.Random(seed)

    acct_map      = {a.name: a for a in accounts}
    cloud_account = acct_map.get("Cloud & Infrastructure")
    bank_account  = acct_map.get("Operating Checking Account")

    aws_contact = vendor_contacts.get("Amazon Web Services")
    aws_id      = aws_contact.id if aws_contact else None

    expenses     = []
    monthly_cloud= {}

    for month_num in range(1, NUM_MONTHS + 1):
        month_date = START_DATE + relativedelta(months=month_num - 1)
        # AWS bills arrive on 3rd of following month
        bill_date  = (month_date + relativedelta(months=1)).replace(day=3)

        lines       = []
        month_total = 0.0

        for service_name, base_cost in CLOUD_BASELINE.items():
            grown_cost  = base_cost * (1 + CLOUD_MONTHLY_GROWTH) ** (month_num - 1)
            grown_cost *= (1 + rng.uniform(-0.05, 0.05))
            grown_cost  = round(grown_cost, 2)
            month_total += grown_cost

            lines.append(ExpenseLine(
                description=f"AWS — {service_name} — {month_date.strftime('%B %Y')}",
                net_amount=grown_cost,
                total_amount=grown_cost,
                account=cloud_account.id if cloud_account else None,
                # FIX: no contact at line level
            ))

        month_total           = round(month_total, 2)
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
            company=company_id,     # FIX: was always null
        )
        expenses.append(expense)

    return {"expenses": expenses, "monthly_cloud": monthly_cloud}
