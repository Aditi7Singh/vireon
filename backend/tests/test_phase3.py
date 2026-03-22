import unittest
import sys
import os
from datetime import date, datetime, timedelta
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import models
import anomaly_detection
from anomaly import tasks
from services import loan_service, depreciation_service

# Setup Test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class TestPhase3Features(unittest.TestCase):
    def setUp(self):
        models.Base.metadata.create_all(bind=engine)
        self.db = TestingSessionLocal()
        
        # Create test company
        self.company = models.Company(name="Phase 3 Corp")
        self.db.add(self.company)
        self.db.commit()
        self.db.refresh(self.company)

    def tearDown(self):
        self.db.close()
        models.Base.metadata.drop_all(bind=engine)

    def test_automated_depreciation_task(self):
        # Create an asset
        purchase_date = date.today() - timedelta(days=60)
        asset = models.FixedAsset(
            company_id=self.company.id,
            asset_name="Server Rack",
            purchase_date=purchase_date,
            purchase_cost=12000,
            useful_life_years=5,
            status="active",
            depreciation_method="straight_line"
        )
        self.db.add(asset)
        self.db.commit()
        
        # Manually call the service function that the task uses
        # We use today's date for month-end calculation
        result = depreciation_service.post_depreciation_to_gl(self.db, self.company.id, date.today())
        
        self.assertEqual(result["status"], "posted")
        self.assertEqual(result["assets_processed"], 1)
        
        # Check GL entries
        gl_entries = self.db.query(models.GeneralLedger).filter(
            models.GeneralLedger.source_type == "depreciation_auto"
        ).all()
        self.assertEqual(len(gl_entries), 2) # One Debit, One Credit
        
        dep_amount = 12000 / (5 * 12) # 200
        self.assertEqual(float(gl_entries[0].debit_amount or gl_entries[0].credit_amount), 200.0)

    def test_automated_loan_posting(self):
        # Create a loan
        start_date = date.today() - timedelta(days=32) # Last month
        loan = models.Loan(
            company_id=self.company.id,
            loan_name="Growth Loan",
            principal_amount=100000,
            interest_rate=12, # 1% per month
            term_months=12,
            start_date=start_date,
            status="active",
            remaining_balance=100000
        )
        self.db.add(loan)
        self.db.commit()
        
        # Call loan auto-post service
        result = loan_service.auto_post_due_payments(self.db, self.company.id)
        
        self.assertEqual(result["payments_posted"], 1)
        
        # Check GL entries (3 entries: Principal, Interest, Cash)
        gl_entries = self.db.query(models.GeneralLedger).filter(
            models.GeneralLedger.source_type == "loan_auto"
        ).all()
        self.assertEqual(len(gl_entries), 3)
        
        # Check payment record
        payment = self.db.query(models.LoanPayment).filter(models.LoanPayment.loan_id == loan.id).first()
        self.assertIsNotNone(payment)
        self.assertEqual(float(payment.interest_paid), 1000.0) # 1% of 100k

    def test_advanced_anomalies(self):
        # Seed 90 days of baseline revenue
        for i in range(12): # 12 weeks of data
            self.db.add(models.GeneralLedger(
                company_id=self.company.id,
                account_code=models.GLAccountCode.SUBSCRIPTION_REVENUE,
                account_name="Revenue",
                transaction_date=date.today() - timedelta(days=7*i + 30),
                credit_amount=1000,
                description="Baseline revenue",
                debit_amount=0
            ))
        self.db.commit()
        
        # Add a spike (250% higher)
        self.db.add(models.GeneralLedger(
            company_id=self.company.id,
            account_code=models.GLAccountCode.SUBSCRIPTION_REVENUE,
            account_name="Revenue",
            transaction_date=date.today(),
            credit_amount=3500,
            description="Spike revenue",
            debit_amount=0
        ))
        
        # Add a duplicate
        dup_date = date.today() - timedelta(days=5)
        self.db.add(models.GeneralLedger(
            company_id=self.company.id,
            account_code=models.GLAccountCode.OFFICE_EXPENSE, # Expense
            account_name="Office Exp",
            transaction_date=dup_date,
            debit_amount=500,
            description="Office supply",
            credit_amount=0
        ))
        self.db.add(models.GeneralLedger(
            company_id=self.company.id,
            account_code=models.GLAccountCode.OFFICE_EXPENSE,
            account_name="Office Exp",
            transaction_date=dup_date,
            debit_amount=500,
            description="Office supply (duplicate)",
            credit_amount=0
        ))
        self.db.commit()
        
        # Run detection
        anomaly_detection.detect_revenue_anomalies(self.db, self.company.id)
        anomaly_detection.detect_duplicate_invoices(self.db, self.company.id)
        
        # Check anomalies
        anomalies = self.db.query(models.Anomaly).all()
        
        types = [a.type for a in anomalies]
        self.assertIn("revenue_spike", types)
        self.assertIn("duplicate_gl_entry", types)
        
        spike = next(a for a in anomalies if a.type == "revenue_spike")
        self.assertEqual(spike.actual_value, 3500.0)

if __name__ == "__main__":
    unittest.main()
