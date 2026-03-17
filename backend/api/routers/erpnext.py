import os
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from uuid import UUID
import logging

import models
import database
import auth
from erpnext_client.client import ERPNextClient
from analytics import metrics

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["erpnext"])

def get_erpnext_client() -> ERPNextClient:
    """Get configured ERPNext client from environment variables."""
    from config import settings
    
    base_url = settings.erpnext_url
    api_key = settings.erpnext_api_key
    api_secret = settings.erpnext_api_secret
    site_name = settings.erpnext_site_name

    
    if not base_url or not api_key or not api_secret:
        raise HTTPException(
            status_code=500,
            detail="ERPNext not configured. Set ERPNEXT_URL, ERPNEXT_API_KEY, and ERPNEXT_API_SECRET in environment."
        )
    return ERPNextClient(base_url, api_key, api_secret, site_name=site_name)

@router.get("/sync/erpnext/status")
async def get_erpnext_status(
    current_user: str = Depends(auth.get_current_user)
):
    """Check ERPNext connectivity and return available doctypes."""
    client = get_erpnext_client()
    try:
        customers = await client.get_resource_list("Customer", fields=["name"], use_cache=False)
        return {
            "status": "connected",
            "customers_count": len(customers),
            "message": "Successfully connected to ERPNext"
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Failed to connect to ERPNext: {str(e)}"
        )
    finally:
        await client.close()

@router.get("/sync/erpnext/financials")
async def sync_financials_from_erpnext(
    from_date: str = None,
    to_date: str = None,
    current_user: str = Depends(auth.get_current_user)
):
    """
    Fetch financial data from ERPNext and return summary.
    If no dates provided, defaults to last 12 months.
    """
    client = get_erpnext_client()
    try:
        from datetime import datetime
        from dateutil.relativedelta import relativedelta
        
        if not to_date:
            to_date = datetime.now().strftime("%Y-%m-%d")
        if not from_date:
            from_date = (datetime.now() - relativedelta(months=12)).strftime("%Y-%m-%d")
        
        sales_invoices = await client.get_sales_invoices()
        purchase_invoices = await client.get_purchase_invoices()
        payment_entries = await client.get_payment_entries()
        
        total_revenue = sum(float(inv.get("grand_total", 0)) for inv in sales_invoices if inv.get("status") == "Paid")
        total_expenses = sum(float(inv.get("grand_total", 0)) for inv in purchase_invoices if inv.get("status") == "Paid")
        
        cash_in = sum(float(p.get("received_amount", 0)) for p in payment_entries if p.get("payment_type") == "Receive")
        cash_out = sum(float(p.get("paid_amount", 0)) for p in payment_entries if p.get("payment_type") == "Pay")
        
        return {
            "period": {
                "from": from_date,
                "to": to_date
            },
            "sales_invoices": {
                "count": len(sales_invoices),
                "total": total_revenue
            },
            "purchase_invoices": {
                "count": len(purchase_invoices),
                "total": total_expenses
            },
            "payments": {
                "cash_in": cash_in,
                "cash_out": cash_out,
                "net_cash_flow": cash_in - cash_out
            },
            "summary": {
                "total_revenue": total_revenue,
                "total_expenses": total_expenses,
                "net_burn": total_expenses - total_revenue
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch financial data: {str(e)}"
        )
    finally:
        await client.close()

@router.get("/metrics/financials/erpnext/{company_id}")
async def get_financial_summary_from_erpnext(
    company_id: UUID,
    current_user: str = Depends(auth.get_current_user)
):
    """
    Get financial metrics from ERPNext (bypasses local database).
    """
    client = get_erpnext_client()
    try:
        from datetime import datetime, timedelta
        from dateutil.relativedelta import relativedelta
        
        today = datetime.now()
        last_month = today - relativedelta(months=1)
        from_date = last_month.replace(day=1).strftime("%Y-%m-%d")
        to_date = (today - timedelta(days=1)).strftime("%Y-%m-%d")
        
        sales_invoices = await client.get_sales_invoices()
        purchase_invoices = await client.get_purchase_invoices()
        payment_entries = await client.get_payment_entries()
        
        paid_sales = [inv for inv in sales_invoices if inv.get("status") == "Paid"]
        total_revenue = sum(float(inv.get("grand_total", 0)) for inv in paid_sales)
        
        paid_purchases = [inv for inv in purchase_invoices if inv.get("status") == "Paid"]
        total_expenses = sum(float(inv.get("grand_total", 0)) for inv in paid_purchases)
        
        net_burn = metrics.calculate_net_burn(total_revenue, total_expenses)
        
        cash_in = sum(float(p.get("received_amount", 0)) for p in payment_entries if p.get("payment_type") == "Receive")
        cash_out = sum(float(p.get("paid_amount", 0)) for p in payment_entries if p.get("payment_type") == "Pay")
        cash_balance = cash_in - cash_out
        
        runway = metrics.calculate_runway(cash_balance, net_burn) if net_burn > 0 else float('inf')
        arr = metrics.calculate_arr(total_revenue)
        
        return {
            "company_id": str(company_id),
            "source": "erpnext",
            "total_cash": cash_balance,
            "monthly_revenue": total_revenue,
            "monthly_gross_burn": total_expenses,
            "monthly_net_burn": net_burn,
            "runway_months": runway,
            "arr": arr,
            "as_of": to_date,
            "data_points": {
                "sales_invoices": len(paid_sales),
                "purchase_invoices": len(paid_purchases),
                "payment_entries": len(payment_entries)
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch financial summary from ERPNext: {str(e)}"
        )
    finally:
        await client.close()

@router.post("/webhooks/erpnext", status_code=status.HTTP_200_OK)
async def erpnext_webhook(request: Request, db: Session = Depends(database.get_db)):
    """
    Handle real-time updates (webhooks) from ERPNext.
    ERPNext sends a JSON payload when a document is created/updated/deleted.
    """
    try:
        data = await request.json()
        doctype = data.get("doctype")
        docname = data.get("name")
        event = data.get("event")
        
        print(f"Received ERPNext Webhook: {doctype} {docname} - Event: {event}")
        
        if event == "on_trash":
            if doctype in ["Sales Invoice", "Purchase Invoice"]:
                db.query(models.Invoice).filter(models.Invoice.remote_id == docname).delete()
            elif doctype in ["Customer", "Supplier"]:
                db.query(models.Contact).filter(models.Contact.remote_id == docname).delete()
            db.commit()
            return {"status": "success", "message": "Deleted locally"}

        company = db.query(models.Company).first()
        if not company:
            return {"status": "ignored", "message": "No company found to associate with"}

        if doctype in ["Sales Invoice", "Purchase Invoice"]:
            is_ar = doctype == "Sales Invoice"
            inv_data = {
                "remote_id": docname,
                "invoice_number": data.get("name"),
                "issue_date": data.get("posting_date"),
                "due_date": data.get("due_date") or data.get("posting_date"),
                "status": data.get("status"),
                "type": "ACCOUNTS_RECEIVABLE" if is_ar else "ACCOUNTS_PAYABLE",
                "total_amount": data.get("grand_total"),
                "amount_paid": data.get("grand_total", 0) - data.get("outstanding_amount", 0),
                "amount_due": data.get("outstanding_amount"),
                "currency": data.get("currency", "USD"),
                "company_id": company.id
            }
            db_inv = db.query(models.Invoice).filter(models.Invoice.remote_id == docname).first()
            if db_inv:
                for key, value in inv_data.items():
                    setattr(db_inv, key, value)
            else:
                db_inv = models.Invoice(**inv_data)
                db.add(db_inv)
            
        elif doctype in ["Customer", "Supplier"]:
            contact_data = {
                "remote_id": docname,
                "name": data.get("customer_name") or data.get("supplier_name") or data.get("name"),
                "type": "CUSTOMER" if doctype == "Customer" else "VENDOR",
                "email": data.get("email_id"),
                "phone": data.get("phone"),
                "company_id": company.id
            }
            db_contact = db.query(models.Contact).filter(models.Contact.remote_id == docname).first()
            if db_contact:
                for key, value in contact_data.items():
                    setattr(db_contact, key, value)
            else:
                db_contact = models.Contact(**contact_data)
                db.add(db_contact)

        db.commit()
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error", "message": str(e)}

@router.post("/sync/erpnext")
async def manual_sync_erpnext(db: Session = Depends(database.get_db), current_user: str = Depends(auth.get_current_user)):
    """
    Trigger a manual bidirectional sync with ERPNext.
    This fetches all key docs (Accounts, Contacts, and Invoices) and updates the Neon system of record.
    """
    client = get_erpnext_client()
    
    try:
        company = db.query(models.Company).first()
        if not company:
            company = models.Company(name="My ERPNext Company", stage="seed")
            db.add(company)
            db.flush()
        
        print("Syncing Accounts...")
        accounts = await client.get_resource_list("Account", fields=["name", "report_type", "account_type", "root_type"])
        for acc in accounts:
            acc_data = {
                "remote_id": acc["name"],
                "name": acc["name"],
                "classification": acc.get("root_type"),
                "type": acc.get("account_type"),
                "company_id": company.id
            }
            db_acc = db.query(models.Account).filter(models.Account.remote_id == acc["name"]).first()
            if db_acc:
                for key, val in acc_data.items(): setattr(db_acc, key, val)
            else:
                db.add(models.Account(**acc_data))

        print("Syncing Contacts...")
        customers = await client.get_resource_list("Customer", fields=["name", "email_id", "phone"])
        suppliers = await client.get_resource_list("Supplier", fields=["name", "email_id", "phone"])
        
        contact_id_map = {}
        
        for c in customers:
            contact_data = {
                "remote_id": c["name"],
                "name": c["name"],
                "type": "CUSTOMER",
                "email": c.get("email_id"),
                "phone": c.get("phone"),
                "company_id": company.id
            }
            db_contact = db.query(models.Contact).filter(models.Contact.remote_id == c["name"]).first()
            if db_contact:
                for key, val in contact_data.items(): setattr(db_contact, key, val)
            else:
                db_contact = models.Contact(**contact_data)
                db.add(db_contact)
            db.flush()
            contact_id_map[c["name"]] = db_contact.id

        for s in suppliers:
            contact_data = {
                "remote_id": s["name"],
                "name": s["name"],
                "type": "VENDOR",
                "email": s.get("email_id"),
                "phone": s.get("phone"),
                "company_id": company.id
            }
            db_contact = db.query(models.Contact).filter(models.Contact.remote_id == s["name"]).first()
            if db_contact:
                for key, val in contact_data.items(): setattr(db_contact, key, val)
            else:
                db_contact = models.Contact(**contact_data)
                db.add(db_contact)
            db.flush()
            contact_id_map[s["name"]] = db_contact.id

        print("Syncing Sales Invoices...")
        sales_invoices = await client.get_sales_invoices()
        for inv in sales_invoices:
            contact_id = contact_id_map.get(inv.get("customer"))
            inv_data = {
                "remote_id": inv["name"],
                "invoice_number": inv["name"],
                "issue_date": inv["posting_date"],
                "due_date": inv.get("due_date", inv["posting_date"]),
                "status": inv["status"],
                "type": "ACCOUNTS_RECEIVABLE",
                "total_amount": inv["grand_total"],
                "amount_paid": inv.get("grand_total", 0) - inv.get("outstanding_amount", 0),
                "amount_due": inv.get("outstanding_amount", 0),
                "currency": inv.get("currency", "USD"),
                "company_id": company.id,
                "contact_id": contact_id
            }
            db_inv = db.query(models.Invoice).filter(models.Invoice.remote_id == inv["name"]).first()
            if db_inv:
                for key, val in inv_data.items(): setattr(db_inv, key, val)
            else:
                db.add(models.Invoice(**inv_data))

        print("Syncing Purchase Invoices...")
        purchase_invoices = await client.get_purchase_invoices()
        for inv in purchase_invoices:
            contact_id = contact_id_map.get(inv.get("supplier"))
            inv_data = {
                "remote_id": inv["name"],
                "invoice_number": inv["name"],
                "issue_date": inv["posting_date"],
                "due_date": inv.get("due_date", inv["posting_date"]),
                "status": inv["status"],
                "type": "ACCOUNTS_PAYABLE",
                "total_amount": inv["grand_total"],
                "amount_paid": inv.get("grand_total", 0) - inv.get("outstanding_amount", 0),
                "amount_due": inv.get("outstanding_amount", 0),
                "currency": inv.get("currency", "USD"),
                "company_id": company.id,
                "contact_id": contact_id
            }
            db_inv = db.query(models.Invoice).filter(models.Invoice.remote_id == inv["name"]).first()
            if db_inv:
                for key, val in inv_data.items(): setattr(db_inv, key, val)
            else:
                db.add(models.Invoice(**inv_data))

        db.commit()
        return {
            "status": "success", 
            "message": f"Successfully synced {len(customers) + len(suppliers)} Contacts and {len(sales_invoices) + len(purchase_invoices)} Invoices from ERPNext to Neon."
        }
    except Exception as e:
        logger.error(f"Manual sync failed: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await client.close()
