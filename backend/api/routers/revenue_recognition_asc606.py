"""
Revenue Recognition Router (ASC 606)
Revenue recognition engine for SaaS companies following ASC 606
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal
import uuid
from dateutil.relativedelta import relativedelta

import database
import models
from auth import get_current_user

router = APIRouter(prefix="/revenue-recognition", tags=["revenue-recognition"])


@router.post("/", response_model=dict)
def create_revenue_recognition(
    company_id: uuid.UUID,
    contract_id: Optional[uuid.UUID],
    invoice_id: Optional[uuid.UUID],
    total_contract_value: Decimal,
    recognition_start: date,
    recognition_end: date,
    recognition_method: str = "straight_line",
    performance_obligations: Optional[List[dict]] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create revenue recognition schedule"""
    
    if not contract_id and not invoice_id:
        raise HTTPException(status_code=400, detail="Either contract_id or invoice_id required")
    
    # Create recognition record
    recognition = models.RevenueRecognition(
        company_id=company_id,
        contract_id=contract_id,
        invoice_id=invoice_id,
        total_contract_value=total_contract_value,
        recognized_to_date=Decimal("0"),
        deferred_revenue=total_contract_value,
        recognition_start=recognition_start,
        recognition_end=recognition_end,
        recognition_method=recognition_method,
        performance_obligations=performance_obligations or []
    )
    
    db.add(recognition)
    db.commit()
    db.refresh(recognition)
    
    # Generate monthly schedule
    if recognition_method == "straight_line":
        generate_straight_line_schedule(db, recognition)
    elif recognition_method == "performance_obligation":
        generate_performance_obligation_schedule(db, recognition)
    
    return {
        "recognition_id": str(recognition.id),
        "total_contract_value": float(total_contract_value),
        "deferred_revenue": float(total_contract_value),
        "recognition_start": recognition_start.isoformat(),
        "recognition_end": recognition_end.isoformat(),
        "recognition_method": recognition_method,
        "schedule_generated": True
    }


@router.get("/", response_model=List[dict])
def list_revenue_recognitions(
    company_id: uuid.UUID,
    contract_id: Optional[uuid.UUID] = None,
    invoice_id: Optional[uuid.UUID] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List revenue recognition schedules"""
    query = db.query(models.RevenueRecognition).filter(
        models.RevenueRecognition.company_id == company_id
    )
    
    if contract_id:
        query = query.filter(models.RevenueRecognition.contract_id == contract_id)
    
    if invoice_id:
        query = query.filter(models.RevenueRecognition.invoice_id == invoice_id)
    
    recognitions = query.order_by(models.RevenueRecognition.recognition_start.desc()).all()
    
    result = []
    for rec in recognitions:
        result.append({
            "id": str(rec.id),
            "contract_id": str(rec.contract_id) if rec.contract_id else None,
            "invoice_id": str(rec.invoice_id) if rec.invoice_id else None,
            "total_contract_value": float(rec.total_contract_value),
            "recognized_to_date": float(rec.recognized_to_date),
            "deferred_revenue": float(rec.deferred_revenue),
            "recognition_start": rec.recognition_start.isoformat(),
            "recognition_end": rec.recognition_end.isoformat(),
            "recognition_method": rec.recognition_method,
            "recognition_percentage": float((rec.recognized_to_date / rec.total_contract_value) * 100) if rec.total_contract_value > 0 else 0
        })
    
    return result


@router.get("/{recognition_id}", response_model=dict)
def get_revenue_recognition(
    recognition_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get revenue recognition details"""
    recognition = db.query(models.RevenueRecognition).filter(
        models.RevenueRecognition.id == recognition_id
    ).first()
    
    if not recognition:
        raise HTTPException(status_code=404, detail="Revenue recognition not found")
    
    # Get schedule
    schedule = db.query(models.RevenueSchedule).filter(
        models.RevenueSchedule.recognition_id == recognition_id
    ).order_by(models.RevenueSchedule.schedule_date).all()
    
    return {
        "id": str(recognition.id),
        "company_id": str(recognition.company_id),
        "contract_id": str(recognition.contract_id) if recognition.contract_id else None,
        "invoice_id": str(recognition.invoice_id) if recognition.invoice_id else None,
        "total_contract_value": float(recognition.total_contract_value),
        "recognized_to_date": float(recognition.recognized_to_date),
        "deferred_revenue": float(recognition.deferred_revenue),
        "recognition_start": recognition.recognition_start.isoformat(),
        "recognition_end": recognition.recognition_end.isoformat(),
        "recognition_method": recognition.recognition_method,
        "performance_obligations": recognition.performance_obligations,
        "schedule": [
            {
                "date": s.schedule_date.isoformat(),
                "amount": float(s.amount),
                "is_recognized": s.is_recognized,
                "recognized_at": s.recognized_at.isoformat() if s.recognized_at else None
            }
            for s in schedule
        ],
        "created_at": recognition.created_at.isoformat()
    }


@router.get("/{recognition_id}/schedule", response_model=List[dict])
def get_revenue_schedule(
    recognition_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get revenue recognition schedule"""
    schedule = db.query(models.RevenueSchedule).filter(
        models.RevenueSchedule.recognition_id == recognition_id
    ).order_by(models.RevenueSchedule.schedule_date).all()
    
    result = []
    for s in schedule:
        result.append({
            "id": str(s.id),
            "schedule_date": s.schedule_date.isoformat(),
            "amount": float(s.amount),
            "is_recognized": s.is_recognized,
            "recognized_at": s.recognized_at.isoformat() if s.recognized_at else None,
            "gl_entry_id": str(s.gl_entry_id) if s.gl_entry_id else None
        })
    
    return result


@router.post("/recognize-due", response_model=dict)
def recognize_due_revenue(
    company_id: uuid.UUID,
    recognition_date: Optional[date] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Recognize all revenue due as of date"""
    
    target_date = recognition_date or date.today()
    
    # Get all unrecognized schedule items due
    due_items = db.query(models.RevenueSchedule).join(
        models.RevenueRecognition
    ).filter(
        and_(
            models.RevenueRecognition.company_id == company_id,
            models.RevenueSchedule.schedule_date <= target_date,
            models.RevenueSchedule.is_recognized == False
        )
    ).all()
    
    recognized_count = 0
    total_recognized = Decimal("0")
    
    for item in due_items:
        # Create GL entry for recognition
        gl_entry = models.FinancialLedgerEntry(
            company_id=company_id,
            transaction_date=item.schedule_date,
            amount=item.amount,
            currency="USD",
            amount_inr=item.amount,  # TODO: Apply exchange rate
            entry_type=models.LedgerEntryType.CREDIT,
            category=models.LedgerCategory.REVENUE,
            source=models.LedgerSource.SYSTEM,
            reference_id=str(item.recognition_id),
            reference_type="revenue_recognition",
            description=f"Revenue recognition - {item.schedule_date.strftime('%B %Y')}",
            entered_by_role=models.LedgerEnteredByRole.SYSTEM
        )
        db.add(gl_entry)
        db.flush()
        
        # Mark as recognized
        item.is_recognized = True
        item.recognized_at = datetime.utcnow()
        item.gl_entry_id = gl_entry.id
        
        # Update recognition totals
        recognition = db.query(models.RevenueRecognition).filter(
            models.RevenueRecognition.id == item.recognition_id
        ).first()
        
        if recognition:
            recognition.recognized_to_date += item.amount
            recognition.deferred_revenue -= item.amount
            recognition.updated_at = datetime.utcnow()
        
        recognized_count += 1
        total_recognized += item.amount
    
    db.commit()
    
    return {
        "message": f"Recognized {recognized_count} revenue items",
        "recognized_count": recognized_count,
        "total_amount": float(total_recognized),
        "recognition_date": target_date.isoformat()
    }


@router.get("/deferred-revenue/summary", response_model=dict)
def get_deferred_revenue_summary(
    company_id: uuid.UUID,
    as_of_date: Optional[date] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get deferred revenue summary"""
    
    as_of = as_of_date or date.today()
    
    # Get all active recognitions
    recognitions = db.query(models.RevenueRecognition).filter(
        and_(
            models.RevenueRecognition.company_id == company_id,
            models.RevenueRecognition.deferred_revenue > 0
        )
    ).all()
    
    total_deferred = Decimal("0")
    current_portion = Decimal("0")  # Due within 12 months
    long_term_portion = Decimal("0")  # Due after 12 months
    twelve_months_out = as_of + relativedelta(months=12)
    
    for rec in recognitions:
        total_deferred += rec.deferred_revenue
        
        # Check schedule to determine current vs long-term
        schedule = db.query(models.RevenueSchedule).filter(
            and_(
                models.RevenueSchedule.recognition_id == rec.id,
                models.RevenueSchedule.is_recognized == False
            )
        ).all()
        
        for item in schedule:
            if item.schedule_date <= twelve_months_out:
                current_portion += item.amount
            else:
                long_term_portion += item.amount
    
    return {
        "as_of_date": as_of.isoformat(),
        "total_deferred_revenue": float(total_deferred),
        "current_portion": float(current_portion),
        "long_term_portion": float(long_term_portion),
        "total_contracts": len(recognitions)
    }


@router.post("/{recognition_id}/adjust", response_model=dict)
def adjust_revenue_recognition(
    recognition_id: uuid.UUID,
    adjustment_amount: Decimal,
    adjustment_reason: str,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Adjust revenue recognition for contract modifications"""
    
    recognition = db.query(models.RevenueRecognition).filter(
        models.RevenueRecognition.id == recognition_id
    ).first()
    
    if not recognition:
        raise HTTPException(status_code=404, detail="Revenue recognition not found")
    
    # Adjust total contract value
    old_value = recognition.total_contract_value
    recognition.total_contract_value += adjustment_amount
    recognition.deferred_revenue += adjustment_amount
    recognition.updated_at = datetime.utcnow()
    
    # Re-calculate remaining schedule
    remaining_schedule = db.query(models.RevenueSchedule).filter(
        and_(
            models.RevenueSchedule.recognition_id == recognition_id,
            models.RevenueSchedule.is_recognized == False
        )
    ).all()
    
    if remaining_schedule:
        # Redistribute adjustment across remaining periods
        adjustment_per_period = adjustment_amount / len(remaining_schedule)
        
        for item in remaining_schedule:
            item.amount += adjustment_per_period
    
    db.commit()
    
    return {
        "message": "Revenue recognition adjusted",
        "recognition_id": str(recognition_id),
        "old_value": float(old_value),
        "adjustment": float(adjustment_amount),
        "new_value": float(recognition.total_contract_value),
        "adjustment_reason": adjustment_reason
    }


@router.get("/metrics/arr-mrr", response_model=dict)
def calculate_arr_mrr(
    company_id: uuid.UUID,
    as_of_date: Optional[date] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Calculate ARR and MRR from revenue recognition"""
    
    as_of = as_of_date or date.today()
    
    # Get all active recognitions
    recognitions = db.query(models.RevenueRecognition).filter(
        and_(
            models.RevenueRecognition.company_id == company_id,
            models.RevenueRecognition.recognition_start <= as_of,
            models.RevenueRecognition.recognition_end >= as_of
        )
    ).all()
    
    total_arr = Decimal("0")
    
    for rec in recognitions:
        # Calculate ARR for this contract
        contract_months = (rec.recognition_end - rec.recognition_start).days / 30.44  # Avg days per month
        if contract_months > 0:
            monthly_value = rec.total_contract_value / Decimal(str(contract_months))
            contract_arr = monthly_value * 12
            total_arr += contract_arr
    
    mrr = total_arr / 12
    
    return {
        "as_of_date": as_of.isoformat(),
        "arr": float(total_arr),
        "mrr": float(mrr),
        "active_contracts": len(recognitions)
    }


# Helper functions

def generate_straight_line_schedule(db: Session, recognition: models.RevenueRecognition):
    """Generate straight-line monthly revenue schedule"""
    
    # Calculate number of months
    start = recognition.recognition_start
    end = recognition.recognition_end
    
    current_date = start
    months = []
    
    while current_date <= end:
        months.append(current_date)
        current_date = current_date + relativedelta(months=1)
    
    if not months:
        return
    
    # Calculate monthly amount
    monthly_amount = recognition.total_contract_value / len(months)
    
    # Create schedule entries
    for month_date in months:
        schedule = models.RevenueSchedule(
            recognition_id=recognition.id,
            schedule_date=month_date,
            amount=monthly_amount,
            is_recognized=False
        )
        db.add(schedule)
    
    db.commit()


def generate_performance_obligation_schedule(db: Session, recognition: models.RevenueRecognition):
    """Generate schedule based on performance obligations"""
    
    if not recognition.performance_obligations:
        # Fallback to straight line
        generate_straight_line_schedule(db, recognition)
        return
    
    # Each performance obligation specifies amount and date
    for po in recognition.performance_obligations:
        schedule = models.RevenueSchedule(
            recognition_id=recognition.id,
            schedule_date=datetime.strptime(po["date"], "%Y-%m-%d").date(),
            amount=Decimal(str(po["amount"])),
            is_recognized=False
        )
        db.add(schedule)
    
    db.commit()
