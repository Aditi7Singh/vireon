from __future__ import annotations
import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Any
from uuid import UUID
from sqlalchemy.orm import Session

import models
from integrations.merge_client import MergeAccountingClient

logger = logging.getLogger(__name__)

class MergeService:
    def __init__(self, db: Session, company_id: UUID):
        self.db = db
        self.company_id = company_id
        self.company = db.query(models.Company).filter(models.Company.id == company_id).first()
        self.client = MergeAccountingClient()

    def sync_all(self) -> Dict[str, Any]:
        """Sync data from Merge.dev to local database."""
        if not self.company:
            return {"error": "Company not found"}
            
        stats = {"accounts": 0, "invoices": 0, "gl_entries": 0}
        
        try:
            # 1. Sync GL Accounts
            merge_accounts = self.client.get_gl_accounts()
            account_map = {} # remote_id -> local_db_obj
            for acc in merge_accounts:
                remote_id = acc.get("id")
                db_acc = self.db.query(models.Account).filter(models.Account.remote_id == remote_id).first()
                if not db_acc:
                    db_acc = models.Account(remote_id=remote_id, company_id=self.company_id)
                    self.db.add(db_acc)
                db_acc.name = acc.get("name")
                db_acc.classification = acc.get("classification")
                db_acc.type = acc.get("type")
                account_map[remote_id] = db_acc
                stats["accounts"] += 1
            
            self.db.flush() # Ensure accounts have IDs for relationships
            
            # 2. Sync Journal Entries (GL)
            journal_entries = self.client.get_journal_entries()
            for entry in journal_entries:
                remote_id = entry.get("id")
                db_gl = self.db.query(models.GeneralLedger).filter(models.GeneralLedger.reference_id == remote_id).first()
                if not db_gl:
                    # In a real sync, we'd handle debits/credits from line items
                    # For this prototype, we'll map the main entry
                    db_gl = models.GeneralLedger(
                        company_id=self.company_id,
                        reference_id=remote_id,
                        source_type="merge"
                    )
                    self.db.add(db_gl)
                
                db_gl.transaction_date = datetime.strptime(entry["transaction_date"][:10], "%Y-%m-%d").date() if entry.get("transaction_date") else datetime.utcnow().date()
                db_gl.description = entry.get("memo") or f"Merge Sync: {remote_id}"
                
                # Simplified mapping: use first line item for amount
                lines = entry.get("lines", [])
                if lines:
                    line = lines[0]
                    amount = Decimal(str(line.get("net_amount", 0)))
                    if amount >= 0:
                        db_gl.debit_amount = amount
                        db_gl.credit_amount = 0
                    else:
                        db_gl.debit_amount = 0
                        db_gl.credit_amount = abs(amount)
                    
                    # Try to map account code
                    db_gl.account_name = line.get("account", {}).get("name", "Unknown")
                    # Use a default code based on classification if available
                    db_gl.account_code = models.GLAccountCode.MISC 
                
                stats["gl_entries"] += 1

            # 3. Sync Invoices (simplified mapping)
            # Merge API 'invoices' endpoint
            merge_invoices = self.client._request("GET", "invoices").get("results", [])
            for inv in merge_invoices:
                remote_id = inv.get("id")
                db_inv = self.db.query(models.Invoice).filter(models.Invoice.remote_id == remote_id).first()
                
                inv_type = "ACCOUNTS_RECEIVABLE" if inv.get("type") == "SALES_INVOICE" else "ACCOUNTS_PAYABLE"
                
                inv_data = {
                    "invoice_number": inv.get("number"),
                    "issue_date": datetime.strptime(inv["issue_date"][:10], "%Y-%m-%d").date() if inv.get("issue_date") else None,
                    "due_date": datetime.strptime(inv["due_date"][:10], "%Y-%m-%d").date() if inv.get("due_date") else None,
                    "status": inv.get("status"),
                    "type": inv_type,
                    "total_amount": Decimal(str(inv.get("total_amount", 0))),
                    "amount_paid": Decimal(str(inv.get("total_amount", 0) - inv.get("outstanding_balance", 0))),
                    "amount_due": Decimal(str(inv.get("outstanding_balance", 0))),
                    "currency": inv.get("currency", "USD")
                }
                
                if db_inv:
                    for k, v in inv_data.items(): setattr(db_inv, k, v)
                else:
                    db_inv = models.Invoice(remote_id=remote_id, company_id=self.company_id, **inv_data)
                    self.db.add(db_inv)
                stats["invoices"] += 1

            self.company.last_sync_merge = datetime.utcnow()
            self.db.commit()
            return {"status": "success", "stats": stats}
            
        except Exception as e:
            logger.error(f"Merge Sync Failed: {e}")
            self.db.rollback()
            return {"error": str(e)}
