"""
Anomaly Injection Engine.
Injects 7 hidden anomalies into the generated financial data
for the AI detection engine to discover during demos.
"""

from datetime import timedelta
from dateutil.relativedelta import relativedelta

from simulation.config import ANOMALIES, START_DATE
from simulation.models import (
    Expense, ExpenseLine, Contact, ContactStatus,
    Address, AddressType, PhoneNumber, _date_iso, _uuid, _remote_id, _now_iso,
)


def inject_anomalies(
    data: dict,
    accounts: list,
    vendor_contacts: dict,
) -> dict:
    """
    Inject hidden anomalies into the generated data.

    Modifies data in-place and returns an anomaly manifest
    documenting each anomaly for ground-truth testing.

    Args:
        data: dict containing all generated data collections
        accounts: list of Account objects
        vendor_contacts: dict of vendor_name → Contact objects

    Returns:
        list of anomaly manifest entries
    """
    manifest = []

    # Account lookup
    acct_map = {a.name: a for a in accounts}
    bank_acct = acct_map.get("Operating Checking Account")
    cloud_acct = acct_map.get("Cloud & Infrastructure")
    office_acct = acct_map.get("Office & Rent")
    saas_acct = acct_map.get("Software & SaaS Subscriptions")
    marketing_acct = acct_map.get("Marketing & Advertising")
    travel_acct = acct_map.get("Travel & Entertainment")

    for anomaly in ANOMALIES:
        aid = anomaly["id"]
        atype = anomaly["type"]
        month = anomaly["month"]
        month_date = START_DATE + relativedelta(months=month - 1)

        if atype == "absolute_spike":
            # ──────────────────────────────────────────────────────────────
            # ANM-001: AWS cost spike in Month 8
            # Modify the existing cloud expense for month 8 to add $6K+
            # ──────────────────────────────────────────────────────────────
            cloud_expenses = data.get("cloud_expenses", [])
            if month - 1 < len(cloud_expenses):
                exp = cloud_expenses[month - 1]
                # Add rogue instances line
                spike_amount = anomaly["actual_amount"] - anomaly["expected_amount"]
                exp.lines.append(ExpenseLine(
                    description="AWS — EC2 i3.8xlarge Instances (UNPLANNED)",
                    net_amount=spike_amount,
                    total_amount=spike_amount,
                    account=cloud_acct.id if cloud_acct else None,
                ))
                # Update totals
                exp.total_amount = -(anomaly["actual_amount"])
                exp.sub_total = -(anomaly["actual_amount"])
                exp.memo += " [ANOMALY: Unexpected EC2 spike]"

                # Update monthly cloud total
                if "monthly_cloud" in data:
                    data["monthly_cloud"][month] = anomaly["actual_amount"]

            manifest.append({
                **anomaly,
                "injected": True,
                "detection_hint": "Compare Month 8 cloud cost against 90-day moving average. "
                                  "Variance >50% should trigger absolute spike alert.",
            })

        elif atype == "duplicate_payment":
            # ──────────────────────────────────────────────────────────────
            # ANM-002: WeWork rent paid twice in Month 6
            # Add a second rent expense in the same month
            # ──────────────────────────────────────────────────────────────
            wework_contact = vendor_contacts.get("WeWork")
            wework_id = wework_contact.id if wework_contact else None

            duplicate_date = month_date.replace(day=15)  # Second payment mid-month
            dup_expense = Expense(
                transaction_date=_date_iso(duplicate_date),
                remote_created_at=_date_iso(duplicate_date),
                account=bank_acct.id if bank_acct else None,
                contact=wework_id,
                total_amount=-3500.0,
                sub_total=-3500.0,
                currency="USD",
                memo=f"WeWork — Office Rent — {month_date.strftime('%B %Y')} (DUPLICATE)",
                lines=[ExpenseLine(
                    description=f"Office / Co-working (WeWork) — {month_date.strftime('%B %Y')}",
                    net_amount=3500.0,
                    total_amount=3500.0,
                    account=office_acct.id if office_acct else None,
                )],
            )
            data.setdefault("anomaly_expenses", []).append(dup_expense)

            manifest.append({
                **anomaly,
                "injected": True,
                "detection_hint": "Two WeWork payments in Month 6 — compare against expected "
                                  "single monthly payment. Timing anomaly: same vendor, same month.",
            })

        elif atype == "new_vendor":
            # ──────────────────────────────────────────────────────────────
            # ANM-003: Unknown vendor DataSync Pro charges $25K in Month 9
            # Create new contact + expense
            # ──────────────────────────────────────────────────────────────
            new_vendor = Contact(
                name="DataSync Pro LLC",
                is_supplier=True,
                is_customer=False,
                email_address="billing@datasyncpro.io",
                status=ContactStatus.ACTIVE,
                addresses=[Address(
                    type=AddressType.BILLING,
                    street_1="1600 Unknown Blvd",
                    city="Austin",
                    state="TX",
                    country="US",
                    zip_code="78759",
                )],
                phone_numbers=[PhoneNumber(number="+1-512-555-0199")],
            )
            data.setdefault("anomaly_contacts", []).append(new_vendor)

            expense_date = month_date.replace(day=12)
            new_vendor_expense = Expense(
                transaction_date=_date_iso(expense_date),
                remote_created_at=_date_iso(expense_date),
                account=bank_acct.id if bank_acct else None,
                contact=new_vendor.id,
                total_amount=-25000.0,
                sub_total=-25000.0,
                currency="USD",
                memo="DataSync Pro — Enterprise Data Migration License",
                lines=[ExpenseLine(
                    description="Enterprise Data Migration License — Annual",
                    net_amount=25000.0,
                    total_amount=25000.0,
                    account=saas_acct.id if saas_acct else None,
                )],
            )
            data.setdefault("anomaly_expenses", []).append(new_vendor_expense)

            manifest.append({
                **anomaly,
                "injected": True,
                "detection_hint": "New vendor with no prior history makes a $25K charge. "
                                  "Flag: new vendor + amount > $5K threshold.",
            })

        elif atype == "trend_anomaly":
            # ──────────────────────────────────────────────────────────────
            # ANM-004: Marketing spend escalates 5x from Month 7 onward
            # Modify existing marketing expenses in months 7-12
            # ──────────────────────────────────────────────────────────────
            opex_expenses = data.get("opex_expenses", [])
            marketing_escalation = {
                7: 5_000, 8: 7_500, 9: 10_000,
                10: 12_000, 11: 13_500, 12: 15_000,
            }
            for exp in opex_expenses:
                if not exp.memo:
                    continue
                for m, target in marketing_escalation.items():
                    m_date = START_DATE + relativedelta(months=m - 1)
                    m_str = m_date.strftime('%B %Y')
                    if ("Marketing & Advertising" in exp.memo and m_str in exp.memo):
                        exp.total_amount = -target
                        exp.sub_total = -target
                        for line in exp.lines:
                            line.net_amount = target
                            line.total_amount = target
                        break

            manifest.append({
                **anomaly,
                "injected": True,
                "detection_hint": "Marketing spend increases from $3K baseline to $15K by Month 12. "
                                  "Trend detection: >5% sustained monthly increase is unsustainable.",
            })

        elif atype == "category_spike":
            # ──────────────────────────────────────────────────────────────
            # ANM-005: Travel expenses 3x in Month 11 (conference season)
            # Modify existing travel expense for month 11
            # ──────────────────────────────────────────────────────────────
            opex_expenses = data.get("opex_expenses", [])
            m11_date = START_DATE + relativedelta(months=10)
            m11_str = m11_date.strftime('%B %Y')

            for exp in opex_expenses:
                if exp.memo and "Travel & Entertainment" in exp.memo and m11_str in exp.memo:
                    exp.total_amount = -6000.0
                    exp.sub_total = -6000.0
                    for line in exp.lines:
                        line.net_amount = 6000.0
                        line.total_amount = 6000.0
                    break

            manifest.append({
                **anomaly,
                "injected": True,
                "detection_hint": "Travel in Month 11 is $6,000 vs ~$2,000 average. "
                                  "Category spike: 3x historical average triggers alert.",
            })

        elif atype == "payroll_creep":
            # ──────────────────────────────────────────────────────────────
            # ANM-006: Payroll jump in Month 10 (2 new hires)
            # Already handled by the payroll generator (NEW_HIRES config).
            # We just document it in the manifest.
            # ──────────────────────────────────────────────────────────────
            payroll_data = data.get("monthly_payroll", {})
            prev_month = payroll_data.get(month - 1, 0)
            curr_month = payroll_data.get(month, 0)

            manifest.append({
                **anomaly,
                "expected_amount": round(prev_month, 2),
                "actual_amount": round(curr_month, 2),
                "injected": True,
                "detection_hint": f"Payroll jumps from ${prev_month:,.0f} to ${curr_month:,.0f} "
                                  f"in Month {month}. Trend: unsustainable payroll growth rate.",
            })

        elif atype == "revenue_drop":
            # ──────────────────────────────────────────────────────────────
            # ANM-007: Largest customer churns in Month 11
            # Already handled by revenue generator (churned_customer param).
            # We document it in the manifest.
            # ──────────────────────────────────────────────────────────────
            mrr_data = data.get("monthly_mrr", {})
            prev_mrr = mrr_data.get(month - 1, 0)
            curr_mrr = mrr_data.get(month, 0)

            manifest.append({
                **anomaly,
                "expected_amount": round(prev_mrr, 2),
                "actual_amount": round(curr_mrr, 2),
                "injected": True,
                "detection_hint": f"MRR drops from ${prev_mrr:,.0f} to ${curr_mrr:,.0f} "
                                  f"in Month {month}. Customer churn: Acme Corp ($8K/mo) lost.",
            })

    return manifest
