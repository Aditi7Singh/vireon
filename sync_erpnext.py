#!/usr/bin/env python3
"""
ERPNext → Neon DB Sync Script
==============================
Runs on the HOST machine (not inside Docker) so it can reach both:
  - ERPNext at localhost:8080
  - Neon PostgreSQL via connection string

Usage:
  python3 sync_erpnext.py
"""

import urllib.request
import json
import os
import sys
from datetime import date, datetime
from decimal import Decimal

# ─── Config ──────────────────────────────────────────────────────────────────
ERPNEXT_URL    = "http://localhost:8080"
ERPNEXT_API_KEY    = "3d75d09dd4d87d0"
ERPNEXT_API_SECRET = "0dd4760b7f185ec"
DATABASE_URL = "postgresql://neondb_owner:npg_zoT29lPNSvtU@ep-fancy-cell-ai8o0gjs-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require"

HEADERS = {"Authorization": f"token {ERPNEXT_API_KEY}:{ERPNEXT_API_SECRET}"}

# ─── ERPNext Helpers ─────────────────────────────────────────────────────────
def erp_get(endpoint: str) -> dict:
    url = f"{ERPNEXT_URL}{endpoint}"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f"  ⚠️  ERPNext request failed: {endpoint} → {e}")
        return {"data": []}

def erp_list(doctype: str, fields: list, limit: int = 500, filters: list = None) -> list:
    fields_str = json.dumps(fields).replace(" ", "")
    url = f"/api/resource/{doctype.replace(' ', '%20')}?fields={urllib.request.quote(fields_str)}&limit={limit}"
    if filters:
        url += f"&filters={urllib.request.quote(json.dumps(filters))}"
    return erp_get(url).get("data", [])

# ─── DB Setup ────────────────────────────────────────────────────────────────
def get_conn():
    import psycopg2
    return psycopg2.connect(DATABASE_URL)

def safe_float(v, default=0.0):
    try:
        return float(v) if v is not None else default
    except:
        return default

def safe_date(v):
    if not v:
        return None
    try:
        return datetime.strptime(str(v), "%Y-%m-%d").date()
    except:
        return None

# ─── Sync Functions ──────────────────────────────────────────────────────────
def sync_company(conn):
    print("\n📦 Syncing Company...")
    companies = erp_list("Company", ["name", "default_currency", "creation"])
    if not companies:
        print("  No companies found in ERPNext. Using default.")
        companies = [{"name": "SeedlingLabs"}]

    cur = conn.cursor()
    cur.execute("SELECT id FROM companies LIMIT 1")
    row = cur.fetchone()

    if row:
        company_id = str(row[0])
        print(f"  ✓ Existing company ID: {company_id}")
    else:
        cur.execute("""
            INSERT INTO companies (name, industry, stage)
            VALUES (%s, 'SaaS', 'seed')
            RETURNING id
        """, (companies[0]["name"],))
        company_id = str(cur.fetchone()[0])
        print(f"  ✓ Created company: {companies[0]['name']} (ID: {company_id})")

    conn.commit()
    cur.close()
    return company_id


def sync_contacts(conn, company_id: str):
    print("\n👥 Syncing Contacts (Customers + Suppliers)...")
    customers = erp_list("Customer", ["name", "customer_name", "email_id", "mobile_no"])
    suppliers = erp_list("Supplier", ["name", "supplier_name", "email_id", "mobile_no"])

    cur = conn.cursor()
    contact_map = {}
    inserted = 0

    for c in customers:
        remote_id = c["name"]
        name = c.get("customer_name") or remote_id
        email = c.get("email_id")
        phone = c.get("mobile_no")

        cur.execute("SELECT id FROM contacts WHERE remote_id = %s", (remote_id,))
        existing = cur.fetchone()
        if existing:
            contact_map[remote_id] = str(existing[0])
            continue

        cur.execute("""
            INSERT INTO contacts (remote_id, company_id, name, type, email, phone)
            VALUES (%s, %s, %s, 'CUSTOMER', %s, %s)
            RETURNING id
        """, (remote_id, company_id, name, email, phone))
        cid = str(cur.fetchone()[0])
        contact_map[remote_id] = cid
        inserted += 1

    for s in suppliers:
        remote_id = s["name"]
        name = s.get("supplier_name") or remote_id
        email = s.get("email_id")
        phone = s.get("mobile_no")

        cur.execute("SELECT id FROM contacts WHERE remote_id = %s", (remote_id,))
        existing = cur.fetchone()
        if existing:
            contact_map[remote_id] = str(existing[0])
            continue

        cur.execute("""
            INSERT INTO contacts (remote_id, company_id, name, type, email, phone)
            VALUES (%s, %s, %s, 'VENDOR', %s, %s)
            RETURNING id
        """, (remote_id, company_id, name, email, phone))
        cid = str(cur.fetchone()[0])
        contact_map[remote_id] = cid
        inserted += 1

    conn.commit()
    cur.close()
    print(f"  ✓ {inserted} new contacts synced ({len(contact_map)} total)")
    return contact_map


def sync_invoices(conn, company_id: str, contact_map: dict):
    print("\n🧾 Syncing Sales and Purchase Invoices...")
    sales = erp_list("Sales Invoice", [
        "name", "status", "posting_date", "due_date", "customer",
        "grand_total", "outstanding_amount", "currency"
    ])
    purchases = erp_list("Purchase Invoice", [
        "name", "status", "posting_date", "due_date", "supplier",
        "grand_total", "outstanding_amount", "currency"
    ])

    cur = conn.cursor()
    inserted = 0

    def upsert_invoice(remote_id, inv_number, issue_date, due_date, status,
                       inv_type, total, outstanding, currency, contact_id):
        nonlocal inserted
        cur.execute("SELECT id FROM invoices WHERE remote_id = %s", (remote_id,))
        if cur.fetchone():
            return

        amount_paid = total - outstanding
        cur.execute("""
            INSERT INTO invoices
                (remote_id, company_id, invoice_number, issue_date, due_date,
                 status, type, sub_total, total_amount, amount_paid, amount_due,
                 currency, contact_id)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (remote_id, company_id, inv_number,
              issue_date or date.today(), due_date or date.today(),
              status, inv_type, total, total,
              max(0, amount_paid), max(0, outstanding),
              currency or "USD", contact_id))
        inserted += 1

    for inv in sales:
        cid = contact_map.get(inv.get("customer"))
        upsert_invoice(
            inv["name"], inv["name"],
            safe_date(inv.get("posting_date")),
            safe_date(inv.get("due_date")),
            inv.get("status", "Draft"),
            "ACCOUNTS_RECEIVABLE",
            safe_float(inv.get("grand_total")),
            safe_float(inv.get("outstanding_amount")),
            inv.get("currency", "USD"),
            cid
        )

    for inv in purchases:
        cid = contact_map.get(inv.get("supplier"))
        upsert_invoice(
            inv["name"], inv["name"],
            safe_date(inv.get("posting_date")),
            safe_date(inv.get("due_date")),
            inv.get("status", "Draft"),
            "ACCOUNTS_PAYABLE",
            safe_float(inv.get("grand_total")),
            safe_float(inv.get("outstanding_amount")),
            inv.get("currency", "USD"),
            cid
        )

    conn.commit()
    cur.close()
    print(f"  ✓ {inserted} invoices synced ({len(sales)} AR + {len(purchases)} AP)")
    return sales, purchases


def sync_expenses(conn, company_id: str):
    print("\n💸 Syncing Expenses (Purchase Invoices as Expense records)...")
    purchases = erp_list("Purchase Invoice", [
        "name", "posting_date", "grand_total", "currency",
        "expense_account", "bill_no"
    ])

    # Try to also get expense items for category breakdown
    expense_items = erp_list("Purchase Invoice Item", [
        "parent", "item_name", "amount", "expense_account"
    ], limit=1000)
    
    item_by_parent = {}
    for item in expense_items:
        parent = item.get("parent")
        if parent not in item_by_parent:
            item_by_parent[parent] = []
        item_by_parent[parent].append(item)

    cur = conn.cursor()
    inserted = 0

    for inv in purchases:
        remote_id = f"exp-{inv['name']}"
        cur.execute("SELECT id FROM expenses WHERE remote_id = %s", (remote_id,))
        if cur.fetchone():
            continue

        total = safe_float(inv.get("grand_total"))
        posting_date = safe_date(inv.get("posting_date")) or date.today()
        
        # Try to determine category from expense_account
        account = inv.get("expense_account") or ""
        items = item_by_parent.get(inv["name"], [])
        
        if items:
            for item in items:
                category = _categorize(item.get("expense_account", ""), item.get("item_name", ""))
                item_amount = safe_float(item.get("amount"))
                if item_amount > 0:
                    cur.execute("""
                        INSERT INTO expenses
                            (remote_id, company_id, transaction_date, total_amount, currency, category)
                        VALUES (%s,%s,%s,%s,%s,%s)
                    """, (f"{remote_id}-{item.get('item_name','')[:20]}", company_id,
                          posting_date, item_amount, inv.get("currency","USD"), category))
                    inserted += 1
        else:
            category = _categorize(account, inv.get("bill_no", ""))
            cur.execute("""
                INSERT INTO expenses
                    (remote_id, company_id, transaction_date, total_amount, currency, category)
                VALUES (%s,%s,%s,%s,%s,%s)
            """, (remote_id, company_id, posting_date, total,
                  inv.get("currency","USD"), category))
            inserted += 1

    conn.commit()
    cur.close()
    print(f"  ✓ {inserted} expense records synced")


def _categorize(account: str, name: str = "") -> str:
    text = (account + " " + name).lower()
    if any(k in text for k in ["aws", "cloud", "azure", "gcp", "server", "hosting"]): return "Cloud/AWS"
    if any(k in text for k in ["salary", "payroll", "wage", "hr", "employee"]): return "Payroll"
    if any(k in text for k in ["saas", "software", "subscription", "license"]): return "SaaS"
    if any(k in text for k in ["market", "advert", "promo", "seo"]): return "Marketing"
    if any(k in text for k in ["office", "rent", "facility"]): return "Office"
    if any(k in text for k in ["travel", "flight", "hotel"]): return "Travel"
    return "Operations"


def sync_monthly_metrics(conn, company_id: str, sales: list, purchases: list):
    print("\n📊 Computing and syncing Monthly Metrics...")
    from collections import defaultdict

    monthly_revenue: dict = defaultdict(float)
    monthly_expenses: dict = defaultdict(float)

    for inv in sales:
        d = safe_date(inv.get("posting_date"))
        if d:
            key = d.strftime("%Y-%m-01")
            monthly_revenue[key] += safe_float(inv.get("grand_total"))

    for inv in purchases:
        d = safe_date(inv.get("posting_date"))
        if d:
            key = d.strftime("%Y-%m-01")
            monthly_expenses[key] += safe_float(inv.get("grand_total"))

    all_months = sorted(set(list(monthly_revenue.keys()) + list(monthly_expenses.keys())))

    cur = conn.cursor()
    inserted = 0
    running_cash = 500000.0  # Starting cash estimate

    for month_str in all_months:
        rev = monthly_revenue.get(month_str, 0.0)
        exp = monthly_expenses.get(month_str, 0.0)
        net_flow = rev - exp
        burn = max(0, exp - rev)
        running_cash += net_flow
        runway = (running_cash / burn) if burn > 0 else 999.0

        month_date = datetime.strptime(month_str, "%Y-%m-%d").date()

        cur.execute("""
            SELECT id FROM monthly_metrics
            WHERE company_id = %s AND metric_month = %s
        """, (company_id, month_date))

        if cur.fetchone():
            cur.execute("""
                UPDATE monthly_metrics
                SET total_revenue=%s, total_expenses=%s, net_cash_flow=%s,
                    burn_rate=%s, runway_months=%s, ending_cash=%s
                WHERE company_id=%s AND metric_month=%s
            """, (rev, exp, net_flow, burn, min(runway, 999), running_cash,
                  company_id, month_date))
        else:
            cur.execute("""
                INSERT INTO monthly_metrics
                    (company_id, metric_month, total_revenue, total_expenses,
                     net_cash_flow, burn_rate, runway_months, ending_cash)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """, (company_id, month_date, rev, exp, net_flow,
                  burn, min(runway, 999), running_cash))
            inserted += 1

    conn.commit()
    cur.close()
    print(f"  ✓ {len(all_months)} months of metrics synced ({inserted} new)")
    
    if all_months:
        last = all_months[-1]
        rev = monthly_revenue.get(last, 0)
        exp = monthly_expenses.get(last, 0)
        print(f"\n  📈 Latest month ({last}): Revenue=${rev:,.0f} | Expenses=${exp:,.0f} | Cash≈${running_cash:,.0f}")


def sync_anomalies(conn, company_id: str, purchases: list):
    print("\n🚨 Detecting anomalies from purchase data...")
    from collections import defaultdict

    monthly: dict = defaultdict(float)
    for inv in purchases:
        d = safe_date(inv.get("posting_date"))
        if d:
            key = d.strftime("%Y-%m")
            monthly[key] += safe_float(inv.get("grand_total"))

    months = sorted(monthly.keys())
    cur = conn.cursor()
    inserted = 0

    for i in range(2, len(months)):
        current = monthly[months[i]]
        avg_prev = (monthly[months[i-1]] + monthly[months[i-2]]) / 2
        if avg_prev > 0 and current > avg_prev * 1.3:
            delta_pct = ((current / avg_prev) - 1) * 100
            severity = "critical" if delta_pct > 50 else "warning"
            remote_id = f"anomaly-{months[i]}-expense-spike"

            cur.execute("SELECT id FROM anomalies WHERE remote_id = %s", (remote_id,))
            if not cur.fetchone():
                cur.execute("""
                    INSERT INTO anomalies
                        (remote_id, company_id, anomaly_date, severity, type,
                         description, expected_value, actual_value, status)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'open')
                """, (remote_id, company_id,
                      datetime.strptime(months[i] + "-01", "%Y-%m-%d").date(),
                      severity, "expense_spike",
                      f"Monthly expenses in {months[i]} were {delta_pct:.0f}% above prior 2-month average",
                      round(avg_prev, 2), round(current, 2)))
                inserted += 1

    conn.commit()
    cur.close()
    print(f"  ✓ {inserted} anomaly alerts generated")


# ─── Entry Point ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  Vireon ↔ ERPNext Sync Tool")
    print("=" * 60)

    try:
        conn = get_conn()
        print("✅ Connected to Neon PostgreSQL")
    except Exception as e:
        print(f"❌ DB connection failed: {e}")
        sys.exit(1)

    try:
        company_id = sync_company(conn)
        contact_map = sync_contacts(conn, company_id)
        sales, purchases = sync_invoices(conn, company_id, contact_map)
        sync_expenses(conn, company_id)
        sync_monthly_metrics(conn, company_id, sales, purchases)
        sync_anomalies(conn, company_id, purchases)

        print("\n" + "=" * 60)
        print("✅ Sync complete! Vireon database is now populated.")
        print("   Refresh the dashboard at http://localhost:3000")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Sync failed: {e}")
        import traceback; traceback.print_exc()
    finally:
        conn.close()
