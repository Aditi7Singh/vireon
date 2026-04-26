#!/usr/bin/env python3
"""
Seed sample invoice and payroll data for tax calculations.
Enables tax liability generation to show real (demo) tax obligations.
"""

import sys
from datetime import datetime, date, timedelta
from pathlib import Path
from decimal import Decimal
import random
import uuid

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import Company, Invoice, InvoiceStatus, InvoiceType

def seed_invoices():
    """Create sample invoice records for tax calculations."""
    db = SessionLocal()
    
    print("\n📑 Seeding Invoices for Tax Calculations...")
    
    try:
        # Initialize database
        Base.metadata.create_all(bind=engine)
        
        # Get default company
        company = db.query(Company).first()
        if not company:
            print("❌ No companies found")
            return
        
        print(f"✓ Company: {company.name}")
        
        # Create sample invoices
        print("\n📄 Creating invoices...")
        invoice_count = 0
        for month_offset in range(3, 0, -1):
            month_date = datetime.now() - timedelta(days=30 * month_offset)
            
            for i in range(3):
                # Generate unique invoice date
                invoice_date = month_date.replace(day=min(random.randint(1, 28), 28))
                
                # Check if invoice with this number already exists
                invoice_num = f"INV{month_offset:02d}{i+1:02d}"
                existing = db.query(Invoice).filter(
                    Invoice.invoice_number == invoice_num
                ).first()
                
                if existing:
                    continue
                
                sub_total = Decimal(random.randint(100000, 500000))  # ₹1L to ₹5L
                tax_amount = sub_total * Decimal("0.18")  # 18% GST
                total = sub_total + tax_amount
                
                invoice = Invoice(
                    id=uuid.uuid4(),
                    company_id=company.id,
                    invoice_number=invoice_num,
                    issue_date=invoice_date.date(),
                    due_date=invoice_date.date() + timedelta(days=30),
                    status="paid" if random.random() > 0.4 else "open",
                    type="AR",
                    sub_total=sub_total,
                    tax_amount=tax_amount,
                    total_amount=total,
                    amount_paid=total if random.random() > 0.4 else Decimal(0),
                    amount_due=Decimal(0) if random.random() > 0.4 else total,
                    currency="INR",
                    memo=f"Professional Services - Month {month_offset}",
                )
                db.add(invoice)
                invoice_count += 1
                print(f"   ✓ Invoice {invoice_num}: ₹{sub_total:,.0f} + ₹{tax_amount:,.0f} GST = ₹{total:,.0f}")
        
        db.commit()
        print(f"\n✅ Seeded {invoice_count} invoices!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Tax Data Seeding Script")
    print("=" * 60)
    
    seed_invoices()
    
    print("\n" + "=" * 60)
    print("✨ Tax data ready for calculations!")
    print("=" * 60)
