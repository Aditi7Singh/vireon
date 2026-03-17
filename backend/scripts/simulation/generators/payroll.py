"""
Payroll generator.
Generates monthly payroll expenses with realistic salary, benefits, taxes,
and hiring events that create detectable burn-rate changes.
"""

from datetime import timedelta
from dateutil.relativedelta import relativedelta
import random

from simulation.config import (
    INITIAL_TEAM, NEW_HIRES, BENEFITS_RATE, PAYROLL_TAX_RATE,
    EQUIPMENT_COST_PER_HIRE, RECRUITING_COST_PER_HIRE,
    START_DATE, NUM_MONTHS,
)
from simulation.models import (
    Expense, ExpenseLine, _date_iso,
)


def generate_payroll(
    accounts: list,
    vendor_contacts: dict,
    seed: int = 42,
) -> dict:
    """
    Generate monthly payroll expenses for all employees.

    Returns:
        dict with:
            'expenses': list of Expense objects (one per month)
            'monthly_payroll': dict of month_num → total payroll cost
            'headcount_history': dict of month_num → employee count
            'hiring_expenses': list of one-time hiring Expense objects
    """
    rng = random.Random(seed)

    # Find relevant accounts
    payroll_account = benefits_account = taxes_account = None
    recruiting_account = bank_account = None
    for acct in accounts:
        if acct.name == "Payroll Expense":
            payroll_account = acct
        elif acct.name == "Employee Benefits":
            benefits_account = acct
        elif acct.name == "Payroll Taxes":
            taxes_account = acct
        elif acct.name == "Recruiting & Hiring":
            recruiting_account = acct
        elif acct.name == "Operating Checking Account":
            bank_account = acct

    # Gusto payroll vendor
    gusto_contact = vendor_contacts.get("Gusto Payroll")
    gusto_id = gusto_contact.id if gusto_contact else None

    # Build the team roster with start months
    all_employees = INITIAL_TEAM + NEW_HIRES

    expenses = []
    hiring_expenses = []
    monthly_payroll = {}
    headcount_history = {}

    for month_num in range(1, NUM_MONTHS + 1):
        month_date = START_DATE + relativedelta(months=month_num - 1)

        # Active employees this month
        active = [emp for emp in all_employees if emp["start_month"] <= month_num]
        headcount_history[month_num] = len(active)

        lines = []
        total_salary = 0.0
        total_benefits = 0.0
        total_taxes = 0.0

        for emp in active:
            monthly_salary = emp["salary"] / 12
            # Add small random variance (±2%) for realistic-looking payroll
            monthly_salary *= (1 + rng.uniform(-0.02, 0.02))
            monthly_salary = round(monthly_salary, 2)

            monthly_benefits = round(monthly_salary * BENEFITS_RATE, 2)
            monthly_taxes = round(monthly_salary * PAYROLL_TAX_RATE, 2)

            total_salary += monthly_salary
            total_benefits += monthly_benefits
            total_taxes += monthly_taxes

            # Salary line
            lines.append(ExpenseLine(
                description=f"Salary — {emp['role']}",
                net_amount=monthly_salary,
                total_amount=monthly_salary,
                account=payroll_account.id if payroll_account else None,
            ))

        # Benefits line (aggregate)
        lines.append(ExpenseLine(
            description="Employee Benefits (Health, 401k, etc.)",
            net_amount=round(total_benefits, 2),
            total_amount=round(total_benefits, 2),
            account=benefits_account.id if benefits_account else None,
        ))

        # Payroll taxes line (aggregate)
        lines.append(ExpenseLine(
            description="Employer Payroll Taxes (FICA, FUTA, SUTA)",
            net_amount=round(total_taxes, 2),
            total_amount=round(total_taxes, 2),
            account=taxes_account.id if taxes_account else None,
        ))

        total_amount = round(total_salary + total_benefits + total_taxes, 2)
        monthly_payroll[month_num] = total_amount

        # Payroll runs on the 15th and last day of month — we aggregate as one expense
        payroll_date = month_date.replace(day=15)

        expense = Expense(
            transaction_date=_date_iso(payroll_date),
            remote_created_at=_date_iso(payroll_date),
            account=bank_account.id if bank_account else None,
            contact=gusto_id,
            total_amount=-total_amount,   # Negative = purchase/outflow
            sub_total=-round(total_salary, 2),
            total_tax_amount=round(total_taxes, 2),
            currency="USD",
            memo=f"Payroll — {month_date.strftime('%B %Y')} ({len(active)} employees)",
            lines=lines,
        )
        expenses.append(expense)

        # ── One-time hiring costs for new employees starting this month ──
        new_this_month = [emp for emp in NEW_HIRES if emp["start_month"] == month_num]
        for emp in new_this_month:
            hire_cost = EQUIPMENT_COST_PER_HIRE + RECRUITING_COST_PER_HIRE
            hire_date = month_date.replace(day=rng.randint(1, 10))

            hire_expense = Expense(
                transaction_date=_date_iso(hire_date),
                remote_created_at=_date_iso(hire_date),
                account=bank_account.id if bank_account else None,
                contact=None,  # Internal expense
                total_amount=-hire_cost,
                sub_total=-hire_cost,
                currency="USD",
                memo=f"Hiring costs — {emp['role']} (equipment + recruiting)",
                lines=[
                    ExpenseLine(
                        description=f"Equipment & Setup — {emp['role']}",
                        net_amount=EQUIPMENT_COST_PER_HIRE,
                        total_amount=EQUIPMENT_COST_PER_HIRE,
                        account=recruiting_account.id if recruiting_account else None,
                    ),
                    ExpenseLine(
                        description=f"Recruiting Fee — {emp['role']}",
                        net_amount=RECRUITING_COST_PER_HIRE,
                        total_amount=RECRUITING_COST_PER_HIRE,
                        account=recruiting_account.id if recruiting_account else None,
                    ),
                ],
            )
            hiring_expenses.append(hire_expense)

    return {
        "expenses": expenses,
        "monthly_payroll": monthly_payroll,
        "headcount_history": headcount_history,
        "hiring_expenses": hiring_expenses,
    }
