from __future__ import annotations
import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session

import models
from erpnext_client.client import ERPNextClient

logger = logging.getLogger(__name__)

class ERPNextService:
    def __init__(self, db: Session, company_id: UUID):
        self.db = db
        self.company_id = company_id
        self.company = db.query(models.Company).filter(models.Company.id == company_id).first()
        
    async def _get_client(self) -> ERPNextClient:
        from config import settings
        return ERPNextClient(
            base_url=settings.erpnext_url,
            api_key=settings.erpnext_api_key,
            api_secret=settings.erpnext_api_secret,
            site_name=settings.erpnext_site_name
        )

    async def sync_all(self, incremental: bool = True) -> Dict[str, Any]:
        """Orchestrate sync of all relevant ERPNext resources."""
        if not self.company:
            return {"error": "Company not found"}
            
        client = await self._get_client()
        stats = {"accounts": 0, "contacts": 0, "invoices": 0, "employees": 0}
        
        try:
            # 1. Accounts
            accounts = await client.get_resource_list("Account", fields=["name", "account_type", "root_type"])
            for acc in accounts:
                db_acc = self.db.query(models.Account).filter(models.Account.remote_id == acc["name"]).first()
                if not db_acc:
                    db_acc = models.Account(remote_id=acc["name"], company_id=self.company_id)
                    self.db.add(db_acc)
                db_acc.name = acc["name"]
                db_acc.classification = acc.get("root_type")
                
                # Enhanced type detection
                acc_type = acc.get("account_type")
                acc_name_upper = acc["name"].upper()
                if "COGS" in acc_name_upper or "COST OF GOODS SOLD" in acc_name_upper:
                    db_acc.type = "COST_OF_GOODS_SOLD"
                else:
                    db_acc.type = acc_type
                    
                stats["accounts"] += 1
            self.db.flush()

            # 2. Contacts (Customers & Suppliers)
            customers = await client.get_resource_list("Customer", fields=["name", "email_id", "phone"])
            suppliers = await client.get_resource_list("Supplier", fields=["name", "email_id", "phone"])
            
            contact_id_map = {}
            for items, c_type in [(customers, "CUSTOMER"), (suppliers, "VENDOR")]:
                for item in items:
                    db_contact = self.db.query(models.Contact).filter(models.Contact.remote_id == item["name"]).first()
                    if not db_contact:
                        db_contact = models.Contact(remote_id=item["name"], company_id=self.company_id, type=c_type)
                        self.db.add(db_contact)
                    db_contact.name = item["name"]
                    db_contact.email = item.get("email_id")
                    db_contact.phone = item.get("phone")
                    self.db.flush()
                    contact_id_map[item["name"]] = db_contact.id
                    stats["contacts"] += 1

            # 3. Invoices
            sales = await client.get_sales_invoices()
            purchases = await client.get_purchase_invoices()
            for inv_list, inv_type in [(sales, "ACCOUNTS_RECEIVABLE"), (purchases, "ACCOUNTS_PAYABLE")]:
                party_key = "customer" if inv_type == "ACCOUNTS_RECEIVABLE" else "supplier"
                for inv in inv_list:
                    # Incremental check: if incremental=True, skip if modified timestamp hasn't changed
                    # (Simplified for now: always update existing, but only fetch filtered in real prod)
                    db_inv = self.db.query(models.Invoice).filter(models.Invoice.remote_id == inv["name"]).first()
                    inv_data = {
                        "invoice_number": inv["name"],
                        "issue_date": datetime.strptime(inv["posting_date"], "%Y-%m-%d").date() if inv.get("posting_date") else None,
                        "due_date": datetime.strptime(inv.get("due_date", inv["posting_date"]), "%Y-%m-%d").date() if inv.get("posting_date") else None,
                        "status": inv["status"],
                        "type": inv_type,
                        "total_amount": Decimal(str(inv["grand_total"])),
                        "amount_paid": Decimal(str(inv["grand_total"] - inv.get("outstanding_amount", 0))),
                        "amount_due": Decimal(str(inv.get("outstanding_amount", 0))),
                        "currency": inv.get("currency", "INR"),
                        "contact_id": contact_id_map.get(inv.get(party_key))
                    }
                    if db_inv:
                        for k, v in inv_data.items(): setattr(db_inv, k, v)
                    else:
                        db_inv = models.Invoice(remote_id=inv["name"], company_id=self.company_id, **inv_data)
                        self.db.add(db_inv)
                    stats["invoices"] += 1
            self.db.flush()

            self.company.last_sync_erpnext = datetime.utcnow()
            self.db.commit()
            return {"status": "success", "stats": stats}
            
        except Exception as e:
            logger.error(f"ERPNext Sync Failed: {e}")
            self.db.rollback()
            return {"error": str(e)}
        finally:
            await client.close()
