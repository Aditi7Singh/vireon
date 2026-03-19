from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import logging

import models
import schemas
import database
import auth
import anomaly_detection

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sandbox", tags=["ingest"])

@router.post("/ingest", response_model=dict)
def ingest_sandbox_data(
    data: schemas.SandboxData, 
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user),
    clear_existing: bool = True,
):
    try:
        # 0. Clear existing data for this company if requested
        if clear_existing:
            logger.info(f"Clearing existing data for company: {data.company.name}")
            db_company = db.query(models.Company).filter(models.Company.name == data.company.name).first()
            if db_company:
                company_id = db_company.id
                db.query(models.Anomaly).filter(models.Anomaly.company_id == company_id).delete()
                db.query(models.MonthlyMetric).filter(models.MonthlyMetric.company_id == company_id).delete()
                db.query(models.DepreciationEntry).filter(models.DepreciationEntry.asset_id.in_(
                    db.query(models.FixedAsset.id).filter(models.FixedAsset.company_id == company_id)
                )).delete(synchronize_session=False)
                db.query(models.FixedAsset).filter(models.FixedAsset.company_id == company_id).delete()
                db.query(models.LoanPayment).filter(models.LoanPayment.loan_id.in_(
                    db.query(models.Loan.id).filter(models.Loan.company_id == company_id)
                )).delete(synchronize_session=False)
                db.query(models.Loan).filter(models.Loan.company_id == company_id).delete()
                db.query(models.PayrollEntry).filter(models.PayrollEntry.employee_id.in_(
                    db.query(models.Employee.id).filter(models.Employee.company_id == company_id)
                )).delete(synchronize_session=False)
                db.query(models.Employee).filter(models.Employee.company_id == company_id).delete()
                db.query(models.Invoice).filter(models.Invoice.company_id == company_id).delete()
                db.query(models.Expense).filter(models.Expense.company_id == company_id).delete()
                db.query(models.Contact).filter(models.Contact.company_id == company_id).delete()
                db.query(models.Account).filter(models.Account.company_id == company_id).delete()
                db.query(models.Company).filter(models.Company.id == company_id).delete()
                db.commit()
                
        # 1. Ingest Company (Upsert)
        db_company = db.query(models.Company).filter(models.Company.name == data.company.name).first()
        if db_company:
            for key, value in data.company.dict().items():
                setattr(db_company, key, value)
        else:
            db_company = models.Company(**data.company.dict())
            db.add(db_company)
        
        db.flush()
        company_id = db_company.id

        # 2. Ingest Accounts (Upsert)
        account_map = {}
        for acc_data in data.accounts:
            db_acc = db.query(models.Account).filter(models.Account.remote_id == acc_data.remote_id).first()
            acc_dict = acc_data.dict()
            acc_dict["company_id"] = company_id
            
            if db_acc:
                for key, value in acc_dict.items():
                    setattr(db_acc, key, value)
            else:
                db_acc = models.Account(**acc_dict)
                db.add(db_acc)
            db.flush()
            account_map[acc_data.remote_id] = db_acc.id
        
        # 3. Ingest Contacts (Upsert)
        contact_map = {}
        for contact_data in data.contacts:
            db_contact = db.query(models.Contact).filter(models.Contact.remote_id == contact_data.remote_id).first()
            contact_dict = contact_data.dict()
            contact_dict["company_id"] = company_id
            
            if db_contact:
                for key, value in contact_dict.items():
                    setattr(db_contact, key, value)
            else:
                db_contact = models.Contact(**contact_dict)
                db.add(db_contact)
            db.flush()
            contact_map[contact_data.remote_id] = db_contact.id
        
        # 4. Ingest Invoices (Upsert)
        for inv_data in data.invoices:
            contact_id = contact_map.get(inv_data.contact_remote_id)
            if not contact_id:
                logger.warning(f"Contact {inv_data.contact_remote_id} not found for Invoice {inv_data.remote_id}")
                continue

            db_inv = db.query(models.Invoice).filter(models.Invoice.remote_id == inv_data.remote_id).first()
            inv_dict = inv_data.dict()
            inv_dict["company_id"] = company_id
            inv_dict["contact_id"] = contact_id
            inv_dict.pop("contact_remote_id")

            if db_inv:
                for key, value in inv_dict.items():
                    setattr(db_inv, key, value)
            else:
                db_inv = models.Invoice(**inv_dict)
                db.add(db_inv)

        # 5. Ingest Expenses (Upsert)
        for exp_data in data.expenses:
            account_id = account_map.get(exp_data.account_remote_id)
            contact_id = contact_map.get(exp_data.contact_remote_id) if exp_data.contact_remote_id else None
            
            if not account_id:
                logger.warning(f"Account {exp_data.account_remote_id} not found for Expense {exp_data.remote_id}")
                continue

            db_exp = db.query(models.Expense).filter(models.Expense.remote_id == exp_data.remote_id).first()
            exp_dict = exp_data.dict()
            exp_dict["company_id"] = company_id
            exp_dict["account_id"] = account_id
            exp_dict["contact_id"] = contact_id
            exp_dict.pop("account_remote_id")
            exp_dict.pop("contact_remote_id")

            if db_exp:
                for key, value in exp_dict.items():
                    setattr(db_exp, key, value)
            else:
                db_exp = models.Expense(**exp_dict)
                db.add(db_exp)

        # 7. Ingest Employees
        employee_map = {}
        for emp_data in data.employees:
            db_emp = db.query(models.Employee).filter(models.Employee.employee_id == emp_data.employee_id).first()
            emp_dict = emp_data.dict()
            emp_dict["company_id"] = company_id
            if db_emp:
                for key, value in emp_dict.items():
                    setattr(db_emp, key, value)
            else:
                db_emp = models.Employee(**emp_dict)
                db.add(db_emp)
            db.flush()
            employee_map[emp_data.employee_id] = db_emp.id

        # 8. Ingest Payroll Entries
        for pr_data in data.payroll_entries:
            # Note: We assume the incoming employee_id is the company-specific string ID
            # But the schema uses UUID for employee_id. We'll use a mapping if needed.
            # For simplicity, we assume employee_id in PayrollEntryCreate is a UUID 
            # OR we try to resolve it from the map if it's a string.
            db_pr = models.PayrollEntry(**pr_data.dict())
            db.add(db_pr)

        # 9. Ingest Loans
        loan_map = {}
        for loan_data in data.loans:
            db_loan = models.Loan(**loan_data.dict())
            db_loan.company_id = company_id
            db.add(db_loan)
            db.flush()
            loan_map[loan_data.loan_name] = db_loan.id

        # 10. Ingest Fixed Assets
        for asset_data in data.fixed_assets:
            db_asset = models.FixedAsset(**asset_data.dict())
            db_asset.company_id = company_id
            db.add(db_asset)

        # 11. Ingest Metrics
        for m in data.metrics:
            db_metric = db.query(models.MonthlyMetric).filter(
                models.MonthlyMetric.company_id == company_id,
                models.MonthlyMetric.metric_month == m.metric_month
            ).first()
            if db_metric:
                for key, value in m.dict().items():
                    if key != "company_id":
                        setattr(db_metric, key, value)
            else:
                db_metric = models.MonthlyMetric(**m.dict())
                db_metric.company_id = company_id
                db.add(db_metric)

        # 12. Ingest Anomalies
        for a in data.anomalies:
            db_anomaly = db.query(models.Anomaly).filter(models.Anomaly.remote_id == a.remote_id).first()
            if db_anomaly:
                for key, value in a.dict().items():
                    if key != "company_id":
                        setattr(db_anomaly, key, value)
            else:
                db_anomaly = models.Anomaly(**a.dict())
                db_anomaly.company_id = company_id
                db.add(db_anomaly)

        db.commit()
        logger.info(f"Successfully ingested data for {data.company.name}")
        
    except SQLAlchemyError as database_error:
        db.rollback()
        logger.error(f"Database error during ingestion: {str(database_error)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to persist data due to a database error."
        )
    except Exception as general_error:
        db.rollback()
        logger.error(f"Unexpected error during ingestion: {str(general_error)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during data ingestion."
        )
        
    # Trigger Anomaly Detection after ingestion
    try:
        anomaly_detection.detect_expense_anomalies(db, company_id=company_id)
        anomaly_detection.detect_revenue_anomalies(db, company_id=company_id)
        anomaly_detection.detect_duplicate_invoices(db, company_id=company_id)
        logger.info(f"Anomaly detection completed for company_id: {company_id}")
    except Exception as eval_error:
        logger.warning(f"Anomaly detection failed: {eval_error}", exc_info=True)

    return {"status": "success", "message": f"Data for {data.company.name} ingested successfully", "company_id": str(company_id)}
