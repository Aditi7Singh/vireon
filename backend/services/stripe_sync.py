from typing import List, Dict, Any
import models
from sqlalchemy.orm import Session
from datetime import date, timedelta
import uuid

def sync_stripe_invoices(db: Session, company_id: UUID) -> Dict[str, Any]:
    """
    Sync invoices and payments from Stripe (Stub).
    """
    # In production, this would use the stripe-python library
    # to fetch Invoice and Charge objects.
    
    # For this stub, we ensure the company has some recent invoices
    new_invoices_count = 0
    
    # Check for existing invoices to avoid duplicates in this demo
    existing_count = db.query(models.Invoice).filter(models.Invoice.company_id == company_id).count()
    
    if existing_count < 10:
        # Create 5 sample Stripe invoices
        for i in range(5):
            invoice_date = date.today() - timedelta(days=i*15)
            due_date = invoice_date + timedelta(days=30)
            
            # Create Invoice
            invoice = models.Invoice(
                company_id=company_id,
                remote_id=f"stri_{uuid.uuid4().hex[:8]}",
                invoice_number=f"INV-STRIPE-{i+100}",
                contact_id=None, # In reality, would link to a customer
                issue_date=invoice_date,
                due_date=due_date,
                status="OPEN" if i == 0 else "PAID",
                type="ACCOUNTS_RECEIVABLE",
                sub_total=1000.0 * (i + 1),
                tax_amount=180.0 * (i + 1),
                total_amount=1180.0 * (i + 1),
                amount_due=1180.0 * (i + 1) if i == 0 else 0.0,
                currency="USD"
            )
            db.add(invoice)
            new_invoices_count += 1
            
        db.commit()
        
    return {
        "status": "success",
        "new_invoices": new_invoices_count,
        "source": "stripe_api_stub"
    }

def get_stripe_balance(company_id: UUID) -> float:
    """Get current Stripe balance (Stub)."""
    return 15400.50
