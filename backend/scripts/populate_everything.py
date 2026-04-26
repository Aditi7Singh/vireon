
import sys
import os
from pathlib import Path
from datetime import date, timedelta
import uuid
from decimal import Decimal

# Add backend to sys.path
backend_path = Path(__file__).parent.parent
sys.path.append(str(backend_path))

import models
from database import SessionLocal, engine

def populate():
    # Ensure tables exist
    models.Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        print("Populating Phase 2 Data (Direct DB)...")
        
        # 0. Clear existing data for 'SeedlingLabs India Private Limited'
        company_name = "SeedlingLabs India Private Limited"
        db_company = db.query(models.Company).filter(models.Company.name == company_name).first()
        if db_company:
            cid = db_company.id
            print(f"Clearing old data for {company_name}...")
            db.query(models.Anomaly).filter(models.Anomaly.company_id == cid).delete()
            db.query(models.MonthlyMetric).filter(models.MonthlyMetric.company_id == cid).delete()
            # Handle FKs for employees, loans, assets
            db.query(models.DepreciationEntry).filter(models.DepreciationEntry.asset_id.in_(
                db.query(models.FixedAsset.id).filter(models.FixedAsset.company_id == cid)
            )).delete(synchronize_session=False)
            db.query(models.FixedAsset).filter(models.FixedAsset.company_id == cid).delete()
            db.query(models.LoanPayment).filter(models.LoanPayment.loan_id.in_(
                db.query(models.Loan.id).filter(models.Loan.company_id == cid)
            )).delete(synchronize_session=False)
            db.query(models.Loan).filter(models.Loan.company_id == cid).delete()
            db.query(models.PayrollEntry).filter(models.PayrollEntry.employee_id.in_(
                db.query(models.Employee.id).filter(models.Employee.company_id == cid)
            )).delete(synchronize_session=False)
            db.query(models.Employee).filter(models.Employee.company_id == cid).delete()
            db.query(models.Invoice).filter(models.Invoice.company_id == cid).delete()
            db.query(models.Expense).filter(models.Expense.company_id == cid).delete()
            db.query(models.Contact).filter(models.Contact.company_id == cid).delete()
            db.query(models.Account).filter(models.Account.company_id == cid).delete()
            db.query(models.Company).filter(models.Company.id == cid).delete()
            db.commit()

        # 1. Company
        company = models.Company(
            name=company_name,
            industry="SaaS / Fintech",
            stage="Growth",
            initial_cash=Decimal("10000000.00"),
            founding_date=date(2024, 1, 1)
        )
        db.add(company)
        db.flush()
        cid = company.id

        # 2. Accounts
        accounts = {
            "bank": models.Account(remote_id="acc_bank_1", company_id=cid, name="HDFC Current", classification="ASSET", type="BANK", current_balance=8300000),
            "ar": models.Account(remote_id="acc_ar_1", company_id=cid, name="Accounts Receivable", classification="ASSET", type="ACCOUNTS_RECEIVABLE"),
            "rev": models.Account(remote_id="acc_rev_1", company_id=cid, name="SaaS Revenue", classification="REVENUE", type="OTHER_INCOME"),
            "cloud": models.Account(remote_id="acc_cloud_1", company_id=cid, name="AWS Cloud", classification="EXPENSE", type="COST_OF_GOODS_SOLD"),
            "salaries": models.Account(remote_id="acc_sal_1", company_id=cid, name="Salaries", classification="EXPENSE", type="OTHER_EXPENSE")
        }
        for acc in accounts.values(): db.add(acc)
        db.flush()

        # 3. Contacts
        contacts = {
            "reliance": models.Contact(remote_id="con_rel", company_id=cid, name="Reliance Industries", type="CUSTOMER"),
            "aws": models.Contact(remote_id="con_aws", company_id=cid, name="Amazon Web Services", type="VENDOR")
        }
        for con in contacts.values(): db.add(con)
        db.flush()

        # 4. Employees & Payroll (Spec 4.9 example)
        # Aditi Singh - 28L CTC
        emp1 = models.Employee(
            company_id=cid, employee_id="EMP001", first_name="Aditi", last_name="Singh",
            email="aditi@seedling.com", hire_date=date(2024, 4, 1), salary=Decimal("2800000"),
            job_title="Senior Engineer", status="active"
        )
        db.add(emp1)
        db.flush()
        
        # Monthly payroll for Aditi (Corrected outflow ₹2,35,466.67)
        for m in range(12):
            pdate = date(2025, 4, 1) + timedelta(days=30*m)
            pentry = models.PayrollEntry(
                employee_id=emp1.id,
                pay_period_start=pdate.replace(day=1),
                pay_period_end=pdate,
                gross_pay=Decimal("217644.00"), # Before employee deductions
                net_pay=Decimal("204577.32"),   # After PF/ESI/PT
                pay_date=pdate,
                status="processed"
            )
            db.add(pentry)

        # 5. Invoices (Reliance ₹7.84L total)
        for m in range(12):
            idate = date(2025, 4, 1) + timedelta(days=30*m)
            inv = models.Invoice(
                remote_id=f"inv_rel_{m}", company_id=cid, invoice_number=f"INL-{2025}-{100+m}",
                contact_id=contacts["reliance"].id, issue_date=idate, due_date=idate + timedelta(days=30),
                status="PAID" if m < 10 else "OPEN", type="ACCOUNTS_RECEIVABLE",
                sub_total=Decimal("665000.00"), tax_amount=Decimal("119700.00"),
                total_amount=Decimal("784700.00"), amount_paid=Decimal("771400.00") if m < 10 else 0,
                amount_due=Decimal("0.00") if m < 10 else Decimal("784700.00"), currency="INR"
            )
            db.add(inv)

        # 6. Expenses (AWS ₹1.5L + GST)
        for m in range(12):
            edate = date(2025, 4, 1) + timedelta(days=30*m)
            exp = models.Expense(
                remote_id=f"exp_aws_{m}", company_id=cid, transaction_date=edate,
                account_id=accounts["cloud"].id, contact_id=contacts["aws"].id,
                total_amount=Decimal("177000.00"), sub_total=Decimal("150000.00"),
                tax_amount=Decimal("27000.00"), category="Cloud", currency="INR"
            )
            db.add(exp)

        # 7. Loan & Asset
        loan = models.Loan(
            company_id=cid, loan_name="HDFC Term", principal_amount=Decimal("5000000"),
            interest_rate=Decimal("10.5"), term_months=36, start_date=date(2024, 10, 1),
            remaining_balance=Decimal("4200000"), status="active"
        )
        db.add(loan)
        
        asset = models.FixedAsset(
            company_id=cid, asset_name="Mac Studio", purchase_date=date(2024, 12, 1),
            purchase_cost=Decimal("450000"), useful_life_years=3, depreciation_method="straight_line"
        )
        db.add(asset)

        db.commit()
        print(f"✅ Successfully populated {company_name} in database.")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    populate()
