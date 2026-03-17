import os
import sys
import asyncio

# Add current and parent directory to path to handle varied execution contexts
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models
from erpnext_client.client import ERPNextClient
from dotenv import load_dotenv
from datetime import datetime
from decimal import Decimal

# Load .env from the same directory as this script
load_dotenv(os.path.join(current_dir, ".env"))

async def sync_data():
    """
    Standalone script to sync ERPNext data to the Neon (PostgreSQL) database.
    Run this via: python sync_erpnext_neon.py
    
    This handles:
    1. Company creation (if missing)
    2. Accounts (Chart of Accounts)
    3. Contacts (Customers & Suppliers)
    4. Invoices (Sales & Purchase)
    5. GL Entries (mapped to Expenses/Revenue)
    """
    print("🚀 Starting ERPNext to Neon sync...")
    
    db = SessionLocal()
    client = ERPNextClient(
        base_url=os.getenv("ERPNEXT_URL"),
        api_key=os.getenv("ERPNEXT_API_KEY"),
        api_secret=os.getenv("ERPNEXT_API_SECRET"),
        site_name=os.getenv("ERPNEXT_SITE_NAME")
    )
    
    try:
        # 0. Company Sync
        company = db.query(models.Company).filter(models.Company.name == "Seedlinglabs").first()
        if not company:
            # Check if any company exists and rename it, or create new
            company = db.query(models.Company).first()
            if company:
                print(f"Updating existing company '{company.name}' to 'Seedlinglabs'...")
                company.name = "Seedlinglabs"
            else:
                print("Creating Seedlinglabs company...")
                company = models.Company(name="Seedlinglabs", stage="series_a")
                db.add(company)
            db.flush()
        else:
            print(f"Found existing company: {company.name}")
        
        # 1. Accounts Sync
        print("📊 Syncing Accounts...")
        erp_accounts = await client.get_resource_list("Account", fields=["name", "account_type", "root_type"])
        for acc in erp_accounts:
            db_acc = db.query(models.Account).filter(models.Account.remote_id == acc["name"]).first()
            acc_data = {
                "remote_id": acc["name"],
                "name": acc["name"],
                "classification": acc.get("root_type"),
                "type": acc.get("account_type"),
                "company_id": company.id
            }
            if db_acc:
                for k, v in acc_data.items(): setattr(db_acc, k, v)
            else:
                db_acc = models.Account(**acc_data)
                db.add(db_acc)
        db.flush()

        # 2. Contacts Sync
        print("🤝 Syncing Contacts...")
        customers = await client.get_resource_list("Customer", fields=["name"])
        suppliers = await client.get_resource_list("Supplier", fields=["name"])
        
        contact_id_map = {}
        for c_list, c_type in [(customers, "CUSTOMER"), (suppliers, "VENDOR")]:
            for item in c_list:
                db_contact = db.query(models.Contact).filter(models.Contact.remote_id == item["name"]).first()
                contact_data = {
                    "remote_id": item["name"],
                    "name": item["name"],
                    "type": c_type,
                    "email": item.get("email_id"),
                    "phone": item.get("phone"),
                    "company_id": company.id
                }
                if db_contact:
                    for k, v in contact_data.items(): setattr(db_contact, k, v)
                else:
                    db_contact = models.Contact(**contact_data)
                    db.add(db_contact)
                db.flush()
                contact_id_map[item["name"]] = db_contact.id

        # 3. Invoices Sync
        print("📄 Syncing Invoices...")
        sales = await client.get_sales_invoices()
        purchases = await client.get_purchase_invoices()
        for inv_list, inv_type in [(sales, "ACCOUNTS_RECEIVABLE"), (purchases, "ACCOUNTS_PAYABLE")]:
            party_key = "customer" if inv_type == "ACCOUNTS_RECEIVABLE" else "supplier"
            for inv in inv_list:
                db_inv = db.query(models.Invoice).filter(models.Invoice.remote_id == inv["name"]).first()
                inv_data = {
                    "remote_id": inv["name"],
                    "invoice_number": inv["name"],
                    "issue_date": datetime.strptime(inv["posting_date"], "%Y-%m-%d").date() if inv.get("posting_date") else None,
                    "due_date": datetime.strptime(inv.get("due_date", inv["posting_date"]), "%Y-%m-%d").date() if inv.get("posting_date") else None,
                    "status": inv["status"],
                    "type": inv_type,
                    "total_amount": Decimal(str(inv["grand_total"])),
                    "sub_total": Decimal(str(inv.get("total", inv["grand_total"]))),
                    "tax_amount": Decimal(str(inv.get("total_taxes_and_charges", 0))),
                    "amount_paid": Decimal(str(inv["grand_total"] - inv.get("outstanding_amount", 0))),
                    "amount_due": Decimal(str(inv.get("outstanding_amount", 0))),
                    "currency": inv.get("currency", "USD"),
                    "company_id": company.id,
                    "contact_id": contact_id_map.get(inv.get(party_key))
                }
                if db_inv:
                    for k, v in inv_data.items(): setattr(db_inv, k, v)
                else:
                    db.add(models.Invoice(**inv_data))
        db.flush()

        # 4. Employee Sync
        print("🧑‍💻 Syncing Employees...")
        erp_employees = await client.get_resource_list("Employee", fields=["name", "first_name", "last_name", "user_id", "department", "designation", "ctc"])
        for emp in erp_employees:
            db_emp = db.query(models.Employee).filter(models.Employee.remote_id == emp["name"]).first()
            emp_data = {
                "remote_id": emp["name"],
                "company_id": company.id,
                "first_name": emp.get("first_name", "Unknown"),
                "last_name": emp.get("last_name", ""),
                "email": emp.get("user_id"),
                "department": emp.get("department"),
                "job_title": emp.get("designation"),
                "salary": Decimal(str(emp.get("ctc", 0))),
                "pay_frequency": "Monthly"
            }
            if db_emp:
                for k, v in emp_data.items(): setattr(db_emp, k, v)
            else:
                db_emp = models.Employee(**emp_data)
                db.add(db_emp)
        
        db.commit()
        print("✨ Sync Complete. Your Neon database is now populated with real ERPNext data.")

    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()
        await client.close()

if __name__ == "__main__":
    asyncio.run(sync_data())
