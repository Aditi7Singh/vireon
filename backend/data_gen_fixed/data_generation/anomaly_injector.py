"""
Anomaly Injection Engine.
Injects 7 hidden anomalies into the generated financial data.
FIX: company_id propagated to all injected Expense/Contact objects.
FIX: ExpenseLine no longer includes 'contact' field.
"""

from dateutil.relativedelta import relativedelta

from data_generation.config import ANOMALIES, START_DATE
from data_generation.models import (
    Expense, ExpenseLine, Contact, ContactStatus,
    Address, AddressType, PhoneNumber, _date_iso, _uuid, _remote_id, _now_iso,
)


def inject_anomalies(
    data: dict,
    accounts: list,
    vendor_contacts: dict,
    company_id: str = None,
) -> list:
    """
    Inject hidden anomalies into the generated data in-place.
    Returns anomaly manifest (ground-truth list for the detection engine).
    """
    manifest = []

    acct_map      = {a.name: a for a in accounts}
    bank_acct     = acct_map.get("Operating Checking Account")
    cloud_acct    = acct_map.get("Cloud & Infrastructure")
    office_acct   = acct_map.get("Office & Rent")
    saas_acct     = acct_map.get("Software & SaaS Subscriptions")
    marketing_acct= acct_map.get("Marketing & Advertising")
    travel_acct   = acct_map.get("Travel & Entertainment")

    for anomaly in ANOMALIES:
        aid        = anomaly["id"]
        atype      = anomaly["type"]
        month      = anomaly["month"]
        month_date = START_DATE + relativedelta(months=month - 1)

        # ── ANM-001: AWS spike in Month 8 ──────────────────────────────────
        if atype == "absolute_spike":
            cloud_expenses = data.get("cloud_expenses", [])
            if month - 1 < len(cloud_expenses):
                exp          = cloud_expenses[month - 1]
                spike_amount = anomaly["actual_amount"] - anomaly["expected_amount"]
                exp.lines.append(ExpenseLine(
                    description="AWS — EC2 i3.8xlarge Instances (UNPLANNED)",
                    net_amount=spike_amount,
                    total_amount=spike_amount,
                    account=cloud_acct.id if cloud_acct else None,
                    # FIX: no contact at line level
                ))
                exp.total_amount = -(anomaly["actual_amount"])
                exp.sub_total    = -(anomaly["actual_amount"])
                exp.memo        += " [ANOMALY: Unexpected EC2 spike]"
                if "monthly_cloud" in data:
                    data["monthly_cloud"][month] = anomaly["actual_amount"]

            manifest.append({
                **anomaly,
                "injected": True,
                "detection_hint": "Compare Month 8 cloud cost against 90-day moving average. "
                                  "Variance >50% triggers absolute_spike alert.",
            })

        # ── ANM-002: WeWork duplicate payment Month 6 ───────────────────────
        elif atype == "duplicate_payment":
            wework_id      = vendor_contacts.get("WeWork")
            wework_contact = wework_id.id if wework_id else None

            dup_date    = month_date.replace(day=15)
            dup_expense = Expense(
                transaction_date=_date_iso(dup_date),
                remote_created_at=_date_iso(dup_date),
                account=bank_acct.id if bank_acct else None,
                contact=wework_contact,
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
                company=company_id,     # FIX
            )
            data.setdefault("anomaly_expenses", []).append(dup_expense)

            manifest.append({
                **anomaly,
                "injected": True,
                "detection_hint": "Two WeWork payments in Month 6. "
                                  "Detection: same vendor + same month + same amount.",
            })

        # ── ANM-003: Unknown vendor DataSync Pro charges $25K Month 9 ───────
        elif atype == "new_vendor":
            new_vendor = Contact(
                name="DataSync Pro LLC",
                is_supplier=True,
                is_customer=False,
                email_address="billing@datasyncpro.io",
                status=ContactStatus.ACTIVE,
                company=company_id,     # FIX
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

            exp_date          = month_date.replace(day=12)
            new_vendor_expense= Expense(
                transaction_date=_date_iso(exp_date),
                remote_created_at=_date_iso(exp_date),
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
                company=company_id,     # FIX
            )
            data.setdefault("anomaly_expenses", []).append(new_vendor_expense)

            manifest.append({
                **anomaly,
                "injected": True,
                "detection_hint": "New vendor with no prior history makes a $25K charge. "
                                  "Rule: new_vendor + amount > $5K threshold.",
            })

        # ── ANM-004: Marketing spend 5x from Month 7 ────────────────────────
        elif atype == "trend_anomaly":
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
                    m_str  = m_date.strftime('%B %Y')
                    if "Marketing & Advertising" in exp.memo and m_str in exp.memo:
                        exp.total_amount = -target
                        exp.sub_total    = -target
                        for line in exp.lines:
                            line.net_amount   = target
                            line.total_amount = target
                        break

            manifest.append({
                **anomaly,
                "injected": True,
                "detection_hint": "Marketing spend grows from $3K baseline to $15K by Month 12. "
                                  "Rule: trend >5%/month for 3+ consecutive months.",
            })

        # ── ANM-005: Travel 3x normal in Month 11 ───────────────────────────
        elif atype == "category_spike":
            opex_expenses = data.get("opex_expenses", [])
            m11_date      = START_DATE + relativedelta(months=10)
            m11_str       = m11_date.strftime('%B %Y')

            for exp in opex_expenses:
                if exp.memo and "Travel & Entertainment" in exp.memo and m11_str in exp.memo:
                    exp.total_amount = -6000.0
                    exp.sub_total    = -6000.0
                    for line in exp.lines:
                        line.net_amount   = 6000.0
                        line.total_amount = 6000.0
                    break

            manifest.append({
                **anomaly,
                "injected": True,
                "detection_hint": "Travel in Month 11 is $6,000 vs ~$2,000 average. "
                                  "Rule: category_spike at 3x historical average.",
            })

        # ── ANM-006: Payroll jump in Month 10 (already baked in via config) ─
        elif atype == "payroll_creep":
            payroll_data = data.get("monthly_payroll", {})
            prev_month   = payroll_data.get(month - 1, 0)
            curr_month   = payroll_data.get(month, 0)

            manifest.append({
                **anomaly,
                "expected_amount": round(prev_month, 2),
                "actual_amount":   round(curr_month, 2),
                "injected": True,
                "detection_hint": f"Payroll jumps from ${prev_month:,.0f} to ${curr_month:,.0f} "
                                  f"in Month {month}. Rule: unsustainable payroll growth rate.",
            })

        # ── ANM-007: Acme Corp churns in Month 11 (baked into revenue gen) ──
        elif atype == "revenue_drop":
            mrr_data  = data.get("monthly_mrr", {})
            prev_mrr  = mrr_data.get(month - 1, 0)
            curr_mrr  = mrr_data.get(month, 0)

            manifest.append({
                **anomaly,
                "expected_amount": round(prev_mrr, 2),
                "actual_amount":   round(curr_mrr, 2),
                "injected": True,
                "detection_hint": f"MRR drops from ${prev_mrr:,.0f} to ${curr_mrr:,.0f} "
                                  f"in Month {month}. Acme Corp ($8K/mo) churned.",
            })

    return manifest
