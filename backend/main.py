from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
import models, schemas, database, anomaly_detection, auth
import uuid
from uuid import UUID
from datetime import timedelta
from analytics import metrics, scenarios
from agent.agent_runner import AgentRunner
import os
from typing import List, Dict, Any, Optional
from erpnext_client.client import ERPNextClient

app = FastAPI(title="SeedlingLabs CFO AI API", docs_url="/docs", redoc_url="/redoc")

# Create tables if they don't exist
models.Base.metadata.create_all(bind=database.engine)

@app.get("/")
def read_root():
    return {"message": "Welcome to SeedlingLabs CFO AI API"}

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"message": "An unexpected error occurred", "detail": str(exc)},
    )

# --- Authentication Endpoints ---

@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(db: Session = Depends(database.get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(username=user.username, email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users/me/", response_model=schemas.User)
async def read_users_me(current_user: str = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.username == current_user).first()
    return user

# --- Data Ingestion ---

@app.post("/sandbox/ingest", response_model=dict)
def ingest_sandbox_data(
    data: schemas.SandboxData, 
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user),
    clear_existing: bool = True,  # Clear existing data before ingesting new data
):
    # 0. Clear existing data for this company if requested
    if clear_existing:
        db_company = db.query(models.Company).filter(models.Company.name == data.company.name).first()
        if db_company:
            company_id = db_company.id
            # Delete in reverse order of dependencies
            db.query(models.Anomaly).filter(models.Anomaly.company_id == company_id).delete()
            db.query(models.MonthlyMetric).filter(models.MonthlyMetric.company_id == company_id).delete()
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
    
    db.flush() # Ensure db_company has an ID
    company_id = db_company.id

    # 2. Ingest Accounts (Upsert)
    account_map = {} # remote_id -> internal_id
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
    contact_map = {} # remote_id -> internal_id
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

    # 6. Ingest Metrics
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

    # 7. Ingest Anomalies
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
    
    # Trigger Anomaly Detection after ingestion
    try:
        anomaly_detection.detect_expense_anomalies(db, company_id=company_id)
    except Exception as e:
        print(f"Warning: Anomaly detection failed: {e}")

    return {"status": "success", "message": f"Data for {data.company.name} ingested successfully", "company_id": str(company_id)}

@app.get("/metrics/financials/{company_id}")
def get_financial_summary(
    company_id: UUID, 
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    """
    Get core financial metrics using the Math Engine.
    """
    latest_metric = db.query(models.MonthlyMetric).filter(
        models.MonthlyMetric.company_id == company_id
    ).order_by(models.MonthlyMetric.metric_month.desc()).first()

    if not latest_metric:
        raise HTTPException(status_code=404, detail="No financial metrics found for this company")

    cash_balance = float(latest_metric.ending_cash)
    revenue = float(latest_metric.total_revenue)
    gross_burn = float(latest_metric.total_expenses)
    
    # Use Math Engine for calculations
    net_burn = metrics.calculate_net_burn(revenue, gross_burn)
    runway = metrics.calculate_runway(cash_balance, net_burn)
    arr = metrics.calculate_arr(revenue) # Assuming revenue is MRR for now
    
    return {
        "company_id": str(company_id),
        "total_cash": cash_balance,
        "monthly_revenue": revenue,
        "monthly_gross_burn": gross_burn,
        "monthly_net_burn": net_burn,
        "runway_months": runway,
        "arr": arr,
        "as_of": latest_metric.metric_month.isoformat()
    }

@app.post("/scenarios/simulate-hiring", response_model=schemas.ScenarioResponse)
def simulate_hiring_scenario(
    request: schemas.HiringScenarioRequest,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    """
    Simulate impact of hiring on runway.
    """
    latest_metric = db.query(models.MonthlyMetric).filter(
        models.MonthlyMetric.company_id == request.company_id
    ).order_by(models.MonthlyMetric.metric_month.desc()).first()

    if not latest_metric:
        raise HTTPException(status_code=404, detail="No financial data found")

    result = scenarios.simulate_hiring(
        current_cash=float(latest_metric.ending_cash),
        current_revenue=float(latest_metric.total_revenue),
        current_gross_burn=float(latest_metric.total_expenses),
        new_salary_annual=request.avg_salary,
        count=request.num_employees
    )
    
    return {
        "scenario": result["scenario"],
        "impact_metrics": {
            "additional_monthly_burn": result["additional_monthly_burn"],
            "new_net_burn": result["new_net_burn"]
        },
        "new_runway": result["new_runway"]
    }

@app.post("/scenarios/simulate-revenue", response_model=schemas.ScenarioResponse)
def simulate_revenue_scenario(
    request: schemas.RevenueScenarioRequest,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    """
    Simulate impact of revenue growth/contraction on runway.
    """
    latest_metric = db.query(models.MonthlyMetric).filter(
        models.MonthlyMetric.company_id == request.company_id
    ).order_by(models.MonthlyMetric.metric_month.desc()).first()

    if not latest_metric:
        raise HTTPException(status_code=404, detail="No financial data found")

    result = scenarios.simulate_revenue_change(
        current_cash=float(latest_metric.ending_cash),
        current_revenue=float(latest_metric.total_revenue),
        current_gross_burn=float(latest_metric.total_expenses),
        percentage_change=request.percentage_change
    )
    
@app.post("/chat", response_model=dict)
async def chat_with_cfo(
    request: schemas.ChatRequest,
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    """
    Chat with the AI CFO agent.
    """
    latest_metric = db.query(models.MonthlyMetric).filter(
        models.MonthlyMetric.company_id == request.company_id
    ).order_by(models.MonthlyMetric.metric_month.desc()).first()

    if not latest_metric:
        raise HTTPException(status_code=404, detail="No financial data found")

    # Prepare context for the agent
    context_data = {
        "cash": float(latest_metric.ending_cash),
        "revenue": float(latest_metric.total_revenue),
        "gross_burn": float(latest_metric.total_expenses),
        "summary": {
            "total_cash": float(latest_metric.ending_cash),
            "monthly_revenue": float(latest_metric.total_revenue),
            "monthly_gross_burn": float(latest_metric.total_expenses),
            "runway": str(metrics.calculate_runway(float(latest_metric.ending_cash), metrics.calculate_net_burn(float(latest_metric.total_revenue), float(latest_metric.total_expenses))))
        }
    }

    agent = AgentRunner()
    answer = await agent.run_query(request.query, context_data)
    
    return {"answer": answer}

# --- ERPNext Sync Endpoints ---

def get_erpnext_client() -> ERPNextClient:
    """Get configured ERPNext client from environment variables."""
    base_url = os.getenv("ERPNEXT_URL")
    site_name = os.getenv("ERPNEXT_SITE_NAME")
    
    if not base_url or not api_key or not api_secret:
        raise HTTPException(
            status_code=500,
            detail="ERPNext not configured. Set ERPNEXT_URL, ERPNEXT_API_KEY, and ERPNEXT_API_SECRET in environment."
        )
    return ERPNextClient(base_url, api_key, api_secret, site_name=site_name)

@app.get("/sync/erpnext/status")
async def get_erpnext_status(
    current_user: str = Depends(auth.get_current_user)
):
    """Check ERPNext connectivity and return available doctypes."""
    client = get_erpnext_client()
    try:
        # Test connection by fetching a simple resource
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

@app.get("/sync/erpnext/financials")
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
        from datetime import datetime, timedelta
        from dateutil.relativedelta import relativedelta
        
        if not to_date:
            to_date = datetime.now().strftime("%Y-%m-%d")
        if not from_date:
            from_date = (datetime.now() - relativedelta(months=12)).strftime("%Y-%m-%d")
        
        # Fetch all financial data in parallel
        sales_invoices = await client.get_sales_invoices()
        purchase_invoices = await client.get_purchase_invoices()
        payment_entries = await client.get_payment_entries()
        
        # Calculate totals
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

@app.get("/metrics/financials/erpnext/{company_id}")
async def get_financial_summary_from_erpnext(
    company_id: UUID,
    current_user: str = Depends(auth.get_current_user)
):
    """
    Get financial metrics from ERPNext (bypasses local database).
    """
    client = get_erpnext_client()
    try:
        # Get last month's data
        from datetime import datetime, timedelta
        from dateutil.relativedelta import relativedelta
        
        today = datetime.now()
        last_month = today - relativedelta(months=1)
        from_date = last_month.replace(day=1).strftime("%Y-%m-%d")
        to_date = (today - timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Fetch financial data
        sales_invoices = await client.get_sales_invoices()
        purchase_invoices = await client.get_purchase_invoices()
        payment_entries = await client.get_payment_entries()
        
        # Get only paid invoices for revenue
        paid_sales = [inv for inv in sales_invoices if inv.get("status") == "Paid"]
        total_revenue = sum(float(inv.get("grand_total", 0)) for inv in paid_sales)
        
        # Get paid purchase invoices
        paid_purchases = [inv for inv in purchase_invoices if inv.get("status") == "Paid"]
        total_expenses = sum(float(inv.get("grand_total", 0)) for inv in paid_purchases)
        
        # Calculate metrics using math engine
        net_burn = metrics.calculate_net_burn(total_revenue, total_expenses)
        
        # Estimate cash balance from payments
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

# --- ERPNext Integration & Webhooks ---

@app.post("/webhooks/erpnext", status_code=status.HTTP_200_OK)
async def erpnext_webhook(request: Request, db: Session = Depends(database.get_db)):
    """
    Handle real-time updates (webhooks) from ERPNext.
    ERPNext sends a JSON payload when a document is created/updated/deleted.
    """
    try:
        data = await request.json()
        doctype = data.get("doctype")
        docname = data.get("name")
        event = data.get("event") # e.g., "after_insert", "on_update", "on_trash"
        
        print(f"Received ERPNext Webhook: {doctype} {docname} - Event: {event}")
        
        if event == "on_trash":
            if doctype in ["Sales Invoice", "Purchase Invoice"]:
                db.query(models.Invoice).filter(models.Invoice.remote_id == docname).delete()
            elif doctype in ["Customer", "Supplier"]:
                db.query(models.Contact).filter(models.Contact.remote_id == docname).delete()
            db.commit()
            return {"status": "success", "message": "Deleted locally"}

        # For create/update, we fetch the full doc to ensure we have latest data
        # In a real app, you'd map these to a specific company_id
        # For demo, we'll pick the first company
        company = db.query(models.Company).first()
        if not company:
            return {"status": "ignored", "message": "No company found to associate with"}

        if doctype in ["Sales Invoice", "Purchase Invoice"]:
            is_ar = doctype == "Sales Invoice"
            # Map ERPNext fields to our Invoice model
            # Note: In a production app, we'd use the ERPNextClient to fetch the full doc if payload is partial
            inv_data = {
                "remote_id": docname,
                "invoice_number": data.get("name"),
                "issue_date": data.get("posting_date"),
                "due_date": data.get("due_date") or data.get("posting_date"),
                "status": data.get("status"),
                "type": "ACCOUNTS_RECEIVABLE" if is_ar else "ACCOUNTS_PAYABLE",
                "total_amount": data.get("grand_total"),
                "amount_paid": data.get("grand_total") - data.get("outstanding_amount", 0),
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
        # Return 200 anyway to prevent ERPNext from retrying indefinitely on logic errors, 
        # but in production you might want actual error codes for retryable issues.
        return {"status": "error", "message": str(e)}

@app.post("/sync/erpnext")
async def manual_sync_erpnext(db: Session = Depends(database.get_db), current_user: str = Depends(auth.get_current_user)):
    """
    Trigger a manual bidirectional sync with ERPNext.
    This fetches all key docs (Accounts, Contacts, and Invoices) and updates the Neon system of record.
    """
    client = get_erpnext_client()
    
    try:
        # 0. Ensure a Company exists
        company = db.query(models.Company).first()
        if not company:
            company = models.Company(name="My ERPNext Company", stage="seed")
            db.add(company)
            db.flush()
        
        # 1. Sync Accounts (Chart of Accounts)
        print("Syncing Accounts...")
        accounts = await client.get_resource_list("Account", fields=["name", "report_type", "account_type", "root_type"])
        for acc in accounts:
            acc_data = {
                "remote_id": acc["name"],
                "name": acc["name"],
                "classification": acc.get("root_type"), # e.g., Asset, Liability, Equity, Revenue, Expense
                "type": acc.get("account_type"),
                "company_id": company.id
            }
            db_acc = db.query(models.Account).filter(models.Account.remote_id == acc["name"]).first()
            if db_acc:
                for key, val in acc_data.items(): setattr(db_acc, key, val)
            else:
                db.add(models.Account(**acc_data))

        # 2. Sync Contacts (Customers & Suppliers)
        print("Syncing Contacts...")
        customers = await client.get_resource_list("Customer", fields=["name", "email_id", "phone"])
        suppliers = await client.get_resource_list("Supplier", fields=["name", "email_id", "phone"])
        
        contact_id_map = {} # remote_name -> local_uuid
        
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

        # 2. Sync Sales Invoices
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
                "amount_paid": inv["grand_total"] - inv.get("outstanding_amount", 0),
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

        # 3. Sync Purchase Invoices
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
                "amount_paid": inv["grand_total"] - inv.get("outstanding_amount", 0),
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
