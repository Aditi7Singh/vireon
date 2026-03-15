from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
import models, schemas, database, anomaly_detection, auth
import uuid
from uuid import UUID
from datetime import timedelta, datetime
from analytics import metrics, scenarios
from agent.agent_runner import AgentRunner
import os
from typing import List, Dict, Any, Optional
from erpnext_client.client import ERPNextClient
from integrations.merge_client import MergeAccountingClient, get_merge_client
import logging
import json

# Configure logging
logger = logging.getLogger(__name__)

# Import agent components
from agent.cfo_agent import run_cfo_query
from agent.memory import new_session_id, get_checkpointer, build_config
from config.settings import Settings

app = FastAPI(title="SeedlingLabs CFO AI API", docs_url="/docs", redoc_url="/redoc")

# Add CORS middleware for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables if they don't exist
models.Base.metadata.create_all(bind=database.engine)

@app.on_event("startup")
async def startup_event():
    """Health check and configuration logging on startup."""
    logger.info("=" * 70)
    logger.info("Agentic CFO Backend - Startup")
    logger.info("=" * 70)
    logger.info(f"LLM Mode: {'Ollama Local' if Settings.USE_LOCAL_LLM else 'Groq API'}")
    logger.info(f"Groq Model (Fast): {Settings.GROQ_FAST_MODEL}")
    logger.info(f"Groq Model (Thinking): {Settings.GROQ_THINK_MODEL}")
    logger.info(f"Company: {Settings.COMPANY_NAME}")
    logger.info(f"Session DB: {Settings.SESSION_DB_PATH}")
    logger.info("✓ Agentic CFO backend ready")
    logger.info("=" * 70)

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
    api_key = os.getenv("ERPNEXT_API_KEY")
    api_secret = os.getenv("ERPNEXT_API_SECRET")
    
    if not base_url or not api_key or not api_secret:
        raise HTTPException(
            status_code=500,
            detail="ERPNext not configured. Set ERPNEXT_URL, ERPNEXT_API_KEY, and ERPNEXT_API_SECRET in environment."
        )
    return ERPNextClient(base_url, api_key, api_secret, site_name=site_name)


def get_data_client():
    """
    Get configured data client based on DATA_SOURCE environment variable.
    
    This allows seamless switching between:
    - "erpnext": Simulator (development)
    - "merge": Merge.dev production integration (QuickBooks, Xero, etc.)
    
    Environment variable: DATA_SOURCE (default: "erpnext")
    
    To switch to production Merge.dev:
    1. Set DATA_SOURCE=merge in .env
    2. Set MERGE_API_KEY and MERGE_ACCOUNT_TOKEN
    3. Restart the server
    """
    data_source = os.getenv("DATA_SOURCE", "erpnext").lower()
    
    logger.info(f"Using data source: {data_source}")
    
    if data_source == "merge":
        return get_merge_client()
    else:
        # Default to ERPNext simulator
        return get_erpnext_client()

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


# ============================================================================
# AGENT ENDPOINTS - CFO Chat Interface
# ============================================================================

@app.post("/agent/chat", response_model=schemas.AgentChatResponse)
async def agent_chat(request: schemas.AgentChatRequest):
    """
    Main CFO agent chat endpoint.
    
    Accepts a natural language query and returns CFO-quality financial analysis.
    Supports multi-turn conversations via session_id.
    
    Args:
        request: AgentChatRequest with message and optional session_id
    
    Returns:
        AgentChatResponse with response, session_id, query_type, timestamp
    """
    try:
        logger.info(f"[AGENT] Chat request: {request.message[:60]}...")
        
        # Generate session if not provided
        session_id = request.session_id or new_session_id()
        
        # Run the CFO agent
        response = run_cfo_query(
            user_message=request.message,
            session_id=session_id
        )
        
        # Get routing decision to include query_type in response
        from agent.routing import classify_query
        query_type = classify_query(request.message)
        
        logger.info(f"[AGENT] Response generated ({query_type})")
        
        return schemas.AgentChatResponse(
            response=response,
            session_id=session_id,
            query_type=query_type,
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
    
    except ValueError as e:
        logger.error(f"[AGENT] Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        logger.error(f"[AGENT] Agent execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"[AGENT] Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Agent processing failed")


@app.post("/agent/chat/stream")
async def agent_chat_stream(request: schemas.AgentChatRequest):
    """
    Streaming version of CFO agent chat.
    
    Returns Server-Sent Events (SSE) stream with reasoning steps and final response.
    Useful for real-time UI updates while agent is thinking.
    
    Args:
        request: AgentChatRequest with message and optional session_id
    
    Returns:
        StreamingResponse with text/event-stream media type
    """
    async def event_generator():
        try:
            session_id = request.session_id or new_session_id()
            logger.info(f"[STREAM] Starting stream for session {session_id[:30]}...")
            
            # Build graph and stream execution
            from agent.cfo_agent import build_graph
            from agent.memory import get_company_context, build_config
            from langchain_core.messages import HumanMessage
            
            graph = build_graph()
            config = build_config(session_id)
            company_context = get_company_context()
            
            from agent.routing import classify_query
            query_type = classify_query(request.message)
            
            initial_state = {
                "messages": [HumanMessage(content=request.message)],
                "query_type": query_type,
                "company_context": company_context,
                "session_id": session_id,
                "tool_error_count": 0,
            }
            
            # Stream the graph execution
            full_response = ""
            for event in graph.stream(initial_state, config=config):
                # Extract response as events complete
                if event:
                    # Yield streaming event
                    yield f"data: {json.dumps({'token': '', 'done': False})}\n\n"
            
            # After graph completes, extract final response
            from langchain_core.messages import AIMessage
            result = graph.invoke(initial_state, config=config)
            for msg in reversed(result.get("messages", [])):
                if isinstance(msg, AIMessage) and msg.content:
                    full_response = msg.content
                    break
            
            # Send final chunk
            yield f"data: {json.dumps({'token': full_response, 'done': True, 'session_id': session_id})}\n\n"
            logger.info(f"[STREAM] Stream completed for session {session_id[:30]}...")
            
        except Exception as e:
            logger.error(f"[STREAM] Error during streaming: {e}", exc_info=True)
            yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"}
    )


@app.get("/agent/history/{session_id}", response_model=schemas.AgentHistoryResponse)
async def agent_history(session_id: str):
    """
    Get full conversation history for a session.
    
    Retrieves all messages (user and assistant) from the session's checkpointer.
    Useful for viewing past conversations or resuming context.
    
    Args:
        session_id: Session identifier (format: cfo-session-*)
    
    Returns:
        AgentHistoryResponse with session_id and list of messages
    """
    try:
        logger.info(f"[HISTORY] Retrieving history for session {session_id[:30]}...")
        
        # Load checkpointer and retrieve state
        checkpointer = get_checkpointer()
        from langchain_core.messages import AIMessage, HumanMessage
        
        # Try to load the saved state
        try:
            config = build_config(session_id)
            values = checkpointer.get(config, "values") or {}
            messages = values.get("messages", [])
        except Exception:
            # Session may not exist yet
            messages = []
        
        # Convert LangChain messages to readable schema
        conversation = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                conversation.append(schemas.ConversationMessage(
                    role="user",
                    content=msg.content,
                    timestamp=datetime.utcnow().isoformat() + "Z"
                ))
            elif isinstance(msg, AIMessage):
                conversation.append(schemas.ConversationMessage(
                    role="assistant",
                    content=msg.content,
                    timestamp=datetime.utcnow().isoformat() + "Z"
                ))
        
        logger.info(f"[HISTORY] Retrieved {len(conversation)} messages for session {session_id[:30]}")
        
        return schemas.AgentHistoryResponse(
            session_id=session_id,
            messages=conversation
        )
    
    except Exception as e:
        logger.error(f"[HISTORY] Error retrieving history: {e}", exc_info=True)
        # Return empty history on error instead of failing the whole request
        return schemas.AgentHistoryResponse(
            session_id=session_id,
            messages=[]
        )


# --- Phase 4: Anomaly Detection Endpoints ---

@app.post("/alerts/scan-now")
async def trigger_scan_now():
    """
    Trigger an on-demand anomaly detection scan.
    
    Useful for manual verification or testing without waiting for daily schedule.
    Returns immediately with task ID; actual scan runs in background.
    
    Returns:
        dict: Task ID and status message
    
    Example response:
        {
            "task_id": "abc123def456",
            "message": "Anomaly scan started",
            "status": "queued"
        }
    """
    try:
        from backend.anomaly.tasks import trigger_scan_now as celery_trigger_scan
        
        logger.info("[ALERTS] On-demand scan triggered from API")
        
        # Queue the scan to run immediately
        task = celery_trigger_scan.delay()
        
        logger.info(f"[ALERTS] Scan queued with task_id: {task.id}")
        
        return {
            "task_id": str(task.id),
            "message": "Anomaly scan queued",
            "status": "queued",
            "endpoint": "/alerts/scan-status/{task_id}"
        }
    
    except Exception as e:
        logger.error(f"[ALERTS] Failed to trigger scan: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger anomaly scan: {str(e)}"
        )


@app.get("/alerts/scan-status/{task_id}")
async def get_scan_status(task_id: str):
    """
    Get the status of an on-demand anomaly scan task.
    
    Polls the Celery task to check status and retrieve results when complete.
    
    Args:
        task_id: Task ID from trigger_scan_now response
    
    Returns:
        dict: Task status (pending/started/success/failure) and results if complete
    
    Example responses:
        {"status": "pending", "task_id": "abc123"}
        {"status": "success", "alerts_found": 3, "critical_count": 1, ...}
        {"status": "failure", "error": "..."}
    """
    try:
        from backend.anomaly.celery_app import app as celery_app
        
        # Get task result from Celery
        task = celery_app.AsyncResult(task_id)
        
        if task.state == 'PENDING':
            return {
                "status": "pending",
                "task_id": task_id,
                "message": "Scan in progress..."
            }
        
        elif task.state == 'STARTED':
            return {
                "status": "started",
                "task_id": task_id,
                "message": "Scan started, processing..."
            }
        
        elif task.state == 'SUCCESS':
            logger.info(f"[ALERTS] Scan completed: {task.result.get('alerts_found', 0)} alerts")
            return {
                "status": "success",
                "task_id": task_id,
                "result": task.result
            }
        
        elif task.state == 'FAILURE':
            logger.error(f"[ALERTS] Scan failed: {task.result}")
            return {
                "status": "failure",
                "task_id": task_id,
                "error": str(task.result)
            }
        
        else:
            return {
                "status": task.state,
                "task_id": task_id
            }
    
    except Exception as e:
        logger.error(f"[ALERTS] Error getting scan status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving scan status: {str(e)}"
        )


@app.patch("/alerts/{alert_id}/dismiss")
async def dismiss_alert(alert_id: int):
    """
    Dismiss an alert (mark as 'dismissed' in PostgreSQL).
    
    Used to manually dismiss false positives or alerts that have been reviewed.
    
    Args:
        alert_id: ID of the alert to dismiss
    
    Returns:
        dict: Updated alert status and details
    
    Example response:
        {
            "status": "success",
            "alert_id": 123,
            "alert_status": "dismissed",
            "message": "Alert 123 dismissed"
        }
    """
    try:
        import psycopg2
        
        logger.info(f"[ALERTS] Dismissing alert {alert_id}")
        
        # Connect to alerts database
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            raise ValueError("DATABASE_URL not configured")
        
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        # Update alert status
        cursor.execute("""
            UPDATE alerts 
            SET status = 'dismissed', updated_at = NOW()
            WHERE id = %s
            RETURNING id, status, severity, alert_type, category, updated_at
        """, (alert_id,))
        
        result = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        
        if result:
            logger.info(f"[ALERTS] ✓ Alert {alert_id} dismissed")
            return {
                "status": "success",
                "alert_id": result[0],
                "alert_status": result[1],
                "severity": result[2],
                "alert_type": result[3],
                "category": result[4],
                "updated_at": result[5].isoformat() if result[5] else None,
                "message": f"Alert {alert_id} dismissed"
            }
        else:
            logger.warning(f"[ALERTS] Alert {alert_id} not found")
            raise HTTPException(
                status_code=404,
                detail=f"Alert {alert_id} not found"
            )
    
    except psycopg2.Error as e:
        logger.error(f"[ALERTS] Database error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"[ALERTS] Error dismissing alert: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error dismissing alert: {str(e)}"
        )


@app.get("/alerts")
async def get_active_alerts(
    severity: str = None,
    category: str = None,
    limit: int = 20,
    status_filter: str = "active"
):
    """
    Get financial anomaly alerts from Phase 4 scanner.
    
    Queries PostgreSQL for active alerts with optional filtering.
    Used by Phase 3 agent's get_active_alerts() tool.
    
    Query Parameters:
        severity: Filter by severity (critical, warning, info) - optional
        category: Filter by category (aws, payroll, saas, etc.) - optional
        limit: Max alerts to return (default 20, max 100)
        status_filter: Alert status (default 'active')
    
    Returns:
        dict: Structured response with alerts list and metadata
    
    Example response:
        {
            "alerts": [
                {
                    "id": "uuid",
                    "severity": "critical",
                    "alert_type": "spike",
                    "category": "aws",
                    "description": "AWS $18,245 vs expected $12,100 (+50.6%)",
                    "amount": 18245.00,
                    "baseline": 12100.00,
                    "delta_pct": 50.6,
                    "runway_impact": -0.4,
                    "suggested_owner": "CTO",
                    "created_at": "2025-01-15T02:00:00Z"
                }
            ],
            "total": 3,
            "critical_count": 1,
            "warning_count": 2,
            "info_count": 0,
            "last_scan_at": "2025-01-15T02:00:00Z"
        }
    """
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        # Validate limit
        limit = min(int(limit), 100) if limit else 20
        limit = max(limit, 1)
        
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            raise ValueError("DATABASE_URL not configured")
        
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Build WHERE clause with filters
        where_clauses = [f"status = '{status_filter}'"]
        params = []
        
        if severity:
            where_clauses.append("LOWER(severity) = %s")
            params.append(severity.lower())
        
        if category:
            where_clauses.append("LOWER(category) = %s")
            params.append(category.lower())
        
        where_sql = " AND ".join(where_clauses)
        
        # Get alerts ordered by severity then recency
        query = f"""
            SELECT 
                id, 
                severity, 
                alert_type, 
                category, 
                amount, 
                baseline, 
                delta_pct, 
                description, 
                runway_impact,
                suggested_owner,
                status, 
                created_at,
                updated_at
            FROM alerts
            WHERE {where_sql}
            ORDER BY 
                CASE LOWER(severity) 
                    WHEN 'critical' THEN 1 
                    WHEN 'warning' THEN 2 
                    ELSE 3 
                END,
                created_at DESC
            LIMIT %s
        """
        
        cursor.execute(query, params + [limit])
        alert_rows = cursor.fetchall()
        
        # Get severity counts for metadata
        count_query = """
            SELECT 
                LOWER(severity) as severity,
                COUNT(*) as count
            FROM alerts
            WHERE status = %s
            GROUP BY LOWER(severity)
        """
        cursor.execute(count_query, [status_filter])
        severity_counts = cursor.fetchall()
        
        # Get last scan timestamp
        cursor.execute("""
            SELECT run_at 
            FROM anomaly_runs 
            WHERE status = 'success'
            ORDER BY run_at DESC 
            LIMIT 1
        """)
        last_scan_row = cursor.fetchone()
        last_scan_at = last_scan_row["run_at"].isoformat() if last_scan_row and last_scan_row["run_at"] else None
        
        cursor.close()
        conn.close()
        
        # Build alerts list
        alerts = []
        for row in alert_rows:
            alerts.append({
                "id": row["id"],
                "severity": row["severity"],
                "alert_type": row["alert_type"],
                "category": row["category"],
                "amount": float(row["amount"]) if row["amount"] else None,
                "baseline": float(row["baseline"]) if row["baseline"] else None,
                "delta_pct": float(row["delta_pct"]) if row["delta_pct"] else None,
                "description": row["description"],
                "runway_impact": float(row["runway_impact"]) if row["runway_impact"] else None,
                "suggested_owner": row["suggested_owner"],
                "created_at": row["created_at"].isoformat() if row["created_at"] else None,
            })
        
        # Build severity counts
        total_count = 0
        critical_count = 0
        warning_count = 0
        info_count = 0
        
        for count_row in severity_counts:
            severity = count_row["severity"].lower()
            count = count_row["count"]
            total_count += count
            
            if severity == "critical":
                critical_count = count
            elif severity == "warning":
                warning_count = count
            elif severity == "info":
                info_count = count
        
        logger.info(f"[ALERTS] Retrieved {len(alerts)} alerts (total: {total_count}, critical: {critical_count})")
        
        return {
            "alerts": alerts,
            "total": total_count,
            "critical_count": critical_count,
            "warning_count": warning_count,
            "info_count": info_count,
            "last_scan_at": last_scan_at,
            "filtered": {
                "severity": severity.lower() if severity else None,
                "category": category.lower() if category else None,
                "limit": limit
            }
        }
    
    except psycopg2.Error as e:
        logger.error(f"[ALERTS] Database error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"[ALERTS] Error retrieving alerts: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving alerts: {str(e)}"
        )
        config = build_config(session_id)
        
        # Get saved state from checkpointer
        # Note: This depends on LangGraph's persistence layer
        try:
            # Try to get state directly from checkpointer
            from langgraph.graph import StateGraph
            saved_state = None
            
            # For MemorySaver, we need to iterate through saved states
            if hasattr(checkpointer, 'storage'):
                # MemorySaver has a storage dict
                saved_state = checkpointer.storage.get(session_id)
            
            # If no state found, try alternative approach
            if not saved_state:
                # Return empty history if session not found
                logger.warning(f"Session {session_id} not found in storage")
                return schemas.AgentHistoryResponse(
                    session_id=session_id,
                    messages=[]
                )
            
            # Convert saved state messages to response format
            messages = []
            if "messages" in saved_state.get("values", {}):
                from langchain_core.messages import AIMessage, HumanMessage
                for msg in saved_state["values"]["messages"]:
                    if isinstance(msg, HumanMessage):
                        role = "user"
                    elif isinstance(msg, AIMessage):
                        role = "assistant"
                    else:
                        continue
                    
                    messages.append(schemas.ConversationMessage(
                        role=role,
                        content=msg.content if isinstance(msg.content, str) else str(msg.content),
                        timestamp=datetime.utcnow().isoformat() + "Z"
                    ))
            
            logger.info(f"[HISTORY] Retrieved {len(messages)} messages for session {session_id[:30]}...")
            
            return schemas.AgentHistoryResponse(
                session_id=session_id,
                messages=messages
            )
        
        except AttributeError:
            # Checkpointer doesn't expose state directly
            logger.warning(f"Checkpointer doesn't expose state retrieval")
            return schemas.AgentHistoryResponse(
                session_id=session_id,
                messages=[]
            )
    
    except Exception as e:
        logger.error(f"[HISTORY] Error retrieving history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve conversation history: {str(e)}")
