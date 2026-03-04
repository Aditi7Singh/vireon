from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
import models, schemas, database, anomaly_detection, auth
import uuid
from uuid import UUID
from datetime import timedelta

app = FastAPI(title="SeedlingLabs CFO AI API")

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
    current_user: str = Depends(auth.get_current_user)
):
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

@app.get("/metrics/runway/{company_id}")
def get_runway(
    company_id: UUID, 
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    # 1. Get latest metrics for cash balance
    latest_metric = db.query(models.MonthlyMetric).filter(
        models.MonthlyMetric.company_id == company_id
    ).order_by(models.MonthlyMetric.metric_month.desc()).first()

    if not latest_metric:
        # Fallback to checking BANK accounts if no metrics table exists yet
        total_cash_rows = db.query(models.Account).filter(
            models.Account.company_id == company_id,
            models.Account.type.in_(["BANK", "CREDIT_CARD"]) # Simple heuristic
        ).all()
        cash_sum = sum([float(acc.current_balance) for acc in total_cash_rows])
        return {"company_id": str(company_id), "total_cash": cash_sum, "runway_months": "N/A", "message": "No historical metrics found"}

    cash_balance = float(latest_metric.ending_cash)
    
    # 2. Calculate average burn from last 3 months
    recent_metrics = db.query(models.MonthlyMetric).filter(
        models.MonthlyMetric.company_id == company_id
    ).order_by(models.MonthlyMetric.metric_month.desc()).limit(3).all()
    
    if not recent_metrics:
        return {"company_id": str(company_id), "total_cash": cash_balance, "runway_months": "N/A"}

    avg_burn = sum([float(m.burn_rate) for m in recent_metrics]) / len(recent_metrics)
    
    # 3. Calculate runway
    # If avg_burn is negative or zero, business is profitable/break-even
    if avg_burn <= 0:
        runway = 999.0 # Effectively infinite
    else:
        runway = cash_balance / avg_burn
    
    return {
        "company_id": str(company_id),
        "total_cash": round(cash_balance, 2),
        "avg_monthly_burn": round(avg_burn, 2),
        "runway_months": round(runway, 1),
        "as_of": latest_metric.metric_month.isoformat()
    }
