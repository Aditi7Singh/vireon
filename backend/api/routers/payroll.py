from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from datetime import date, timedelta

import models
import schemas
import database
import auth
from analytics.metrics import calculate_payroll_taxes, calculate_monthly_payroll_cost

router = APIRouter(prefix="/payroll", tags=["payroll"])


@router.get("/employees", response_model=List[schemas.Employee])
def get_employees(
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    """Get all employees for the company."""
    company = db.query(models.Company).first()
    if not company:
        raise HTTPException(status_code=404, detail="No company found")
    
    employees = db.query(models.Employee).filter(models.Employee.company_id == company.id).all()
    return employees


@router.post("/employees", response_model=schemas.Employee)
def create_employee(
    employee: schemas.EmployeeCreate,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    """Create a new employee."""
    company = db.query(models.Company).first()
    if not company:
        raise HTTPException(status_code=404, detail="No company found")
    
    # Check if employee_id already exists
    existing = db.query(models.Employee).filter(
        models.Employee.employee_id == employee.employee_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Employee ID already exists")
    
    db_employee = models.Employee(
        company_id=company.id,
        employee_id=employee.employee_id,
        first_name=employee.first_name,
        last_name=employee.last_name,
        email=employee.email,
        hire_date=employee.hire_date,
        termination_date=employee.termination_date,
        salary=employee.salary,
        pay_frequency=employee.pay_frequency,
        job_title=employee.job_title,
        department=employee.department,
        status=employee.status
    )
    
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)
    return db_employee


@router.post("/payroll-entries", response_model=schemas.PayrollEntry)
def create_payroll_entry(
    entry: schemas.PayrollEntryCreate,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    """Create a payroll entry for an employee."""
    # Verify employee exists and belongs to company
    company = db.query(models.Company).first()
    if not company:
        raise HTTPException(status_code=404, detail="No company found")
    
    employee = db.query(models.Employee).filter(
        models.Employee.id == entry.employee_id,
        models.Employee.company_id == company.id
    ).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Calculate taxes if not provided
    if entry.federal_tax == 0 and entry.state_tax == 0:
        tax_calc = calculate_payroll_taxes(entry.gross_pay)
        # Mapping Indian taxes to existing US-centric fields for compatibility
        entry.federal_tax = tax_calc.get("income_tax_tds", 0) # Mapping to federal_tax field
        entry.social_security = tax_calc["employee_pf"]
        entry.medicare = tax_calc["employee_esi"]
        entry.state_tax = tax_calc["professional_tax"]
        entry.net_pay = tax_calc["net_pay"]
    
    db_entry = models.PayrollEntry(
        employee_id=entry.employee_id,
        pay_period_start=entry.pay_period_start,
        pay_period_end=entry.pay_period_end,
        gross_pay=entry.gross_pay,
        federal_tax=entry.federal_tax,
        state_tax=entry.state_tax,
        social_security=entry.social_security,
        medicare=entry.medicare,
        other_deductions=entry.other_deductions,
        net_pay=entry.net_pay,
        pay_date=entry.pay_date,
        status=entry.status,
        department=employee.department
    )
    
    db.add(db_entry)
    
    # --- Ledger Integration ---
    # Create GeneralLedger entry for payroll disbursement
    ledger_entry = models.GeneralLedger(
        company_id=company.id,
        account_code=models.GLAccountCode.PAYROLL_EXPENSE,
        account_name="Payroll Expense",
        transaction_date=entry.pay_date,
        debit_amount=entry.gross_pay,
        credit_amount=0,
        description=f"Payroll for {employee.first_name} {employee.last_name} - Period {entry.pay_period_start} to {entry.pay_period_end}",
        department=employee.department,
        source_type="payroll",
        reference_id=str(db_entry.id)
    )
    db.add(ledger_entry)
    
    # Create matching credit entry for cash/bank (simplified)
    cash_entry = models.GeneralLedger(
        company_id=company.id,
        account_code=models.GLAccountCode.CASH,
        account_name="Cash & Bank",
        transaction_date=entry.pay_date,
        debit_amount=0,
        credit_amount=entry.net_pay, # Total cash outflow from bank
        description=f"Net salary disbursement - {employee.first_name} {employee.last_name}",
        source_type="payroll",
        reference_id=str(db_entry.id)
    )
    db.add(cash_entry)
    
    # Create credit entries for tax liabilities (PF/ESI/PT/TDS)
    statutory_entry = models.GeneralLedger(
        company_id=company.id,
        account_code=models.GLAccountCode.ACCRUED_EXPENSES,
        account_name="Statutory Dues Payable",
        transaction_date=entry.pay_date,
        debit_amount=0,
        credit_amount=entry.gross_pay - entry.net_pay,
        description=f"Statutory deductions (PF/ESI/PT) - {employee.first_name} {employee.last_name}",
        source_type="payroll",
        reference_id=str(db_entry.id)
    )
    db.add(statutory_entry)
    
    # --- Unified Financial Ledger Integration ---
    # Primary ledger used for burn/runway (FinancialLedgerEntry)
    fl_entry = models.FinancialLedgerEntry(
        company_id=company.id,
        transaction_date=entry.pay_date,
        amount=entry.gross_pay,
        currency="INR",
        amount_inr=entry.gross_pay,
        entry_type=models.LedgerEntryType.DEBIT,
        category=models.LedgerCategory.PAYROLL,
        description=f"Payroll: {employee.first_name} {employee.last_name}",
        department=employee.department,
        source=models.LedgerSource.SYSTEM,
        reference_id=str(db_entry.id),
        reference_type="payroll"
    )
    db.add(fl_entry)
    
    db.commit()
    db.refresh(db_entry)
    return db_entry


@router.get("/payroll-entries", response_model=List[schemas.PayrollEntry])
def get_payroll_entries(
    start_date: date = None,
    end_date: date = None,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    """Get payroll entries, optionally filtered by date range."""
    company = db.query(models.Company).first()
    if not company:
        raise HTTPException(status_code=404, detail="No company found")
    
    query = db.query(models.PayrollEntry).join(models.Employee).filter(
        models.Employee.company_id == company.id
    )
    
    if start_date:
        query = query.filter(models.PayrollEntry.pay_date >= start_date)
    if end_date:
        query = query.filter(models.PayrollEntry.pay_date <= end_date)
    
    entries = query.order_by(models.PayrollEntry.pay_date.desc()).all()
    return entries


@router.get("/tax-calculation")
def calculate_payroll_taxes_endpoint(
    gross_pay: float,
    state_tax_rate: float = 0.05,
    current_user: str = Depends(auth.get_current_user)
):
    """Calculate payroll taxes for a given gross pay amount."""
    return calculate_payroll_taxes(gross_pay, state_tax_rate)


@router.get("/monthly-cost")
def get_monthly_payroll_cost(
    month: date = None,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    """Get monthly payroll cost breakdown."""
    company = db.query(models.Company).first()
    if not company:
        raise HTTPException(status_code=404, detail="No company found")
    
    if not month:
        month = date.today().replace(day=1)
    
    return calculate_monthly_payroll_cost(db, str(company.id), month)