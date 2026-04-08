"""
Contract and Vendor Management Router
Handles SaaS subscriptions, vendor contracts, renewal alerts
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from datetime import datetime, timedelta, date
from decimal import Decimal
import uuid

import database
import models
import schemas
from auth import get_current_user

router = APIRouter(prefix="/contracts", tags=["contracts"])


@router.post("/", response_model=schemas.Contract)
def create_contract(
    contract: schemas.ContractCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a new contract"""
    # Generate contract number if not provided
    if not contract.contract_number:
        contract_count = db.query(models.Contract).filter(
            models.Contract.company_id == contract.company_id
        ).count()
        contract.contract_number = f"CNT-{contract_count + 1:05d}"
    
    db_contract = models.Contract(**contract.dict())
    db.add(db_contract)
    db.commit()
    db.refresh(db_contract)
    
    # Create renewal alerts
    create_renewal_alerts(db, db_contract)
    
    return db_contract


@router.get("/", response_model=List[schemas.Contract])
def list_contracts(
    company_id: uuid.UUID,
    status: Optional[str] = None,
    category: Optional[str] = None,
    expiring_within_days: Optional[int] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List contracts with optional filters"""
    query = db.query(models.Contract).filter(models.Contract.company_id == company_id)
    
    if status:
        query = query.filter(models.Contract.status == status)
    
    if category:
        query = query.filter(models.Contract.category == category)
    
    if expiring_within_days:
        expiry_date = date.today() + timedelta(days=expiring_within_days)
        query = query.filter(
            and_(
                models.Contract.end_date <= expiry_date,
                models.Contract.end_date >= date.today(),
                models.Contract.status == models.ContractStatus.ACTIVE
            )
        )
    
    return query.order_by(models.Contract.end_date).all()


@router.get("/{contract_id}", response_model=schemas.Contract)
def get_contract(
    contract_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get contract details"""
    contract = db.query(models.Contract).filter(models.Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return contract


@router.put("/{contract_id}", response_model=schemas.Contract)
def update_contract(
    contract_id: uuid.UUID,
    contract_update: schemas.ContractUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update contract"""
    db_contract = db.query(models.Contract).filter(models.Contract.id == contract_id).first()
    if not db_contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    for key, value in contract_update.dict(exclude_unset=True).items():
        setattr(db_contract, key, value)
    
    db_contract.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_contract)
    
    # Recreate alerts if dates changed
    if contract_update.end_date or contract_update.renewal_notice_days:
        db.query(models.ContractAlert).filter(
            models.ContractAlert.contract_id == contract_id
        ).delete()
        create_renewal_alerts(db, db_contract)
    
    return db_contract


@router.delete("/{contract_id}")
def delete_contract(
    contract_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete contract"""
    db.query(models.Contract).filter(models.Contract.id == contract_id).delete()
    db.commit()
    return {"message": "Contract deleted successfully"}


@router.get("/{company_id}/alerts", response_model=List[dict])
def get_renewal_alerts(
    company_id: uuid.UUID,
    days_ahead: int = 90,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get upcoming renewal alerts"""
    cutoff_date = date.today() + timedelta(days=days_ahead)
    
    alerts = db.query(models.ContractAlert, models.Contract).join(
        models.Contract
    ).filter(
        and_(
            models.Contract.company_id == company_id,
            models.ContractAlert.alert_date <= cutoff_date,
            models.ContractAlert.alert_date >= date.today()
        )
    ).all()
    
    result = []
    for alert, contract in alerts:
        result.append({
            "alert_id": str(alert.id),
            "contract_id": str(contract.id),
            "contract_number": contract.contract_number,
            "vendor_name": contract.vendor_name,
            "category": contract.category,
            "amount": float(contract.amount),
            "end_date": contract.end_date.isoformat(),
            "days_until_expiry": alert.days_until_expiry,
            "auto_renewal": contract.auto_renewal,
            "alert_sent": alert.alert_sent
        })
    
    return result


@router.get("/{company_id}/spend-analysis", response_model=dict)
def get_spend_analysis(
    company_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Analyze spend by vendor and category"""
    from sqlalchemy import func
    
    # Spend by vendor
    vendor_spend = db.query(
        models.Contract.vendor_name,
        func.sum(models.Contract.amount).label("total_spend"),
        func.count(models.Contract.id).label("contract_count")
    ).filter(
        and_(
            models.Contract.company_id == company_id,
            models.Contract.status == models.ContractStatus.ACTIVE
        )
    ).group_by(models.Contract.vendor_name).all()
    
    # Spend by category
    category_spend = db.query(
        models.Contract.category,
        func.sum(models.Contract.amount).label("total_spend"),
        func.count(models.Contract.id).label("contract_count")
    ).filter(
        and_(
            models.Contract.company_id == company_id,
            models.Contract.status == models.ContractStatus.ACTIVE
        )
    ).group_by(models.Contract.category).all()
    
    # SaaS seat optimization
    seat_optimization = db.query(models.Contract).filter(
        and_(
            models.Contract.company_id == company_id,
            models.Contract.status == models.ContractStatus.ACTIVE,
            models.Contract.seats_licensed.isnot(None),
            models.Contract.seats_used.isnot(None)
        )
    ).all()
    
    unused_seats = []
    for contract in seat_optimization:
        if contract.seats_used < contract.seats_licensed:
            unused_count = contract.seats_licensed - contract.seats_used
            unused_seats.append({
                "vendor_name": contract.vendor_name,
                "seats_licensed": contract.seats_licensed,
                "seats_used": contract.seats_used,
                "unused_seats": unused_count,
                "potential_savings": float(contract.amount * (unused_count / contract.seats_licensed))
            })
    
    return {
        "vendor_spend": [
            {"vendor": v.vendor_name, "total_spend": float(v.total_spend), "contracts": v.contract_count}
            for v in vendor_spend
        ],
        "category_spend": [
            {"category": c.category, "total_spend": float(c.total_spend), "contracts": c.contract_count}
            for c in category_spend
        ],
        "unused_seats": unused_seats,
        "total_active_contracts": db.query(models.Contract).filter(
            and_(
                models.Contract.company_id == company_id,
                models.Contract.status == models.ContractStatus.ACTIVE
            )
        ).count(),
        "total_annual_spend": float(
            db.query(func.sum(models.Contract.amount)).filter(
                and_(
                    models.Contract.company_id == company_id,
                    models.Contract.status == models.ContractStatus.ACTIVE
                )
            ).scalar() or 0
        )
    }


@router.post("/{company_id}/check-renewals")
def check_and_send_renewal_alerts(
    company_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Check for upcoming renewals and send alerts"""
    today = date.today()
    
    # Get unsent alerts that are due
    due_alerts = db.query(models.ContractAlert, models.Contract).join(
        models.Contract
    ).filter(
        and_(
            models.Contract.company_id == company_id,
            models.ContractAlert.alert_date <= today,
            models.ContractAlert.alert_sent == False
        )
    ).all()
    
    sent_count = 0
    for alert, contract in due_alerts:
        # In production, send actual email/notification here
        # For now, mark as sent
        alert.alert_sent = True
        alert.sent_at = datetime.utcnow()
        sent_count += 1
    
    db.commit()
    
    return {
        "alerts_sent": sent_count,
        "message": f"Sent {sent_count} renewal alerts"
    }


def create_renewal_alerts(db: Session, contract: models.Contract):
    """Create renewal alerts for a contract"""
    # Create alerts at 90, 60, and 30 days before expiry
    alert_days = [90, 60, 30]
    
    for days in alert_days:
        alert_date = contract.end_date - timedelta(days=days)
        if alert_date >= date.today():
            alert = models.ContractAlert(
                contract_id=contract.id,
                alert_date=alert_date,
                days_until_expiry=days,
                alert_sent=False
            )
            db.add(alert)
    
    db.commit()
