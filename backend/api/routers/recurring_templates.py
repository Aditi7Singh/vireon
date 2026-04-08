"""
Recurring Transaction Templates Router
Auto-generate recurring transactions (subscriptions, payroll, etc)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from datetime import datetime, date, timedelta
from decimal import Decimal
import uuid
from dateutil.relativedelta import relativedelta

import database
import models
from auth import get_current_user

router = APIRouter(prefix="/recurring-templates", tags=["recurring-templates"])


@router.post("/", response_model=dict)
def create_template(
    company_id: uuid.UUID,
    name: str,
    description: Optional[str],
    entry_type: models.LedgerEntryType,
    category: models.LedgerCategory,
    amount: Decimal,
    currency: str,
    frequency: str,
    start_date: date,
    end_date: Optional[date],
    auto_generate: bool = True,
    escalation_rate: Optional[Decimal] = None,
    product_tag: Optional[models.LedgerProductTag] = None,
    office_tag: Optional[models.LedgerOfficeTag] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a new recurring transaction template"""
    next_gen_date = calculate_next_date(start_date, frequency)
    
    template = models.TransactionTemplate(
        company_id=company_id,
        name=name,
        description=description,
        entry_type=entry_type,
        category=category,
        amount=amount,
        currency=currency,
        frequency=frequency,
        start_date=start_date,
        end_date=end_date,
        auto_generate=auto_generate,
        escalation_rate=escalation_rate or Decimal("0.00"),
        next_generation_date=next_gen_date,
        product_tag=product_tag or models.LedgerProductTag.UNALLOCATED,
        office_tag=office_tag or models.LedgerOfficeTag.NA
    )
    
    db.add(template)
    db.commit()
    db.refresh(template)
    
    return {
        "template_id": str(template.id),
        "name": template.name,
        "frequency": template.frequency,
        "next_generation_date": template.next_generation_date.isoformat() if template.next_generation_date else None,
        "amount": float(template.amount)
    }


@router.get("/", response_model=List[dict])
def list_templates(
    company_id: uuid.UUID,
    is_active: Optional[bool] = None,
    frequency: Optional[str] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List recurring templates with filters"""
    query = db.query(models.TransactionTemplate).filter(
        models.TransactionTemplate.company_id == company_id
    )
    
    if is_active is not None:
        query = query.filter(models.TransactionTemplate.is_active == is_active)
    
    if frequency:
        query = query.filter(models.TransactionTemplate.frequency == frequency)
    
    templates = query.order_by(models.TransactionTemplate.next_generation_date).all()
    
    result = []
    for t in templates:
        result.append({
            "id": str(t.id),
            "name": t.name,
            "description": t.description,
            "entry_type": t.entry_type.value,
            "category": t.category.value,
            "amount": float(t.amount),
            "currency": t.currency,
            "frequency": t.frequency,
            "start_date": t.start_date.isoformat(),
            "end_date": t.end_date.isoformat() if t.end_date else None,
            "auto_generate": t.auto_generate,
            "escalation_rate": float(t.escalation_rate),
            "next_generation_date": t.next_generation_date.isoformat() if t.next_generation_date else None,
            "last_generated_at": t.last_generated_at.isoformat() if t.last_generated_at else None,
            "is_active": t.is_active
        })
    
    return result


@router.get("/{template_id}", response_model=dict)
def get_template(
    template_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get template details"""
    template = db.query(models.TransactionTemplate).filter(
        models.TransactionTemplate.id == template_id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return {
        "id": str(template.id),
        "company_id": str(template.company_id),
        "name": template.name,
        "description": template.description,
        "entry_type": template.entry_type.value,
        "category": template.category.value,
        "amount": float(template.amount),
        "currency": template.currency,
        "frequency": template.frequency,
        "start_date": template.start_date.isoformat(),
        "end_date": template.end_date.isoformat() if template.end_date else None,
        "auto_generate": template.auto_generate,
        "escalation_rate": float(template.escalation_rate),
        "next_generation_date": template.next_generation_date.isoformat() if template.next_generation_date else None,
        "last_generated_at": template.last_generated_at.isoformat() if template.last_generated_at else None,
        "is_active": template.is_active,
        "product_tag": template.product_tag.value,
        "office_tag": template.office_tag.value
    }


@router.put("/{template_id}", response_model=dict)
def update_template(
    template_id: uuid.UUID,
    amount: Optional[Decimal] = None,
    frequency: Optional[str] = None,
    end_date: Optional[date] = None,
    is_active: Optional[bool] = None,
    escalation_rate: Optional[Decimal] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update template"""
    template = db.query(models.TransactionTemplate).filter(
        models.TransactionTemplate.id == template_id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    if amount is not None:
        template.amount = amount
    if frequency is not None:
        template.frequency = frequency
        template.next_generation_date = calculate_next_date(date.today(), frequency)
    if end_date is not None:
        template.end_date = end_date
    if is_active is not None:
        template.is_active = is_active
    if escalation_rate is not None:
        template.escalation_rate = escalation_rate
    
    template.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Template updated successfully", "template_id": str(template_id)}


@router.delete("/{template_id}", response_model=dict)
def delete_template(
    template_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Deactivate template"""
    template = db.query(models.TransactionTemplate).filter(
        models.TransactionTemplate.id == template_id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    template.is_active = False
    db.commit()
    
    return {"message": "Template deactivated", "template_id": str(template_id)}


@router.post("/generate-due", response_model=dict)
def generate_due_transactions(
    company_id: uuid.UUID,
    as_of_date: Optional[date] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Generate all due recurring transactions"""
    target_date = as_of_date or date.today()
    
    templates = db.query(models.TransactionTemplate).filter(
        and_(
            models.TransactionTemplate.company_id == company_id,
            models.TransactionTemplate.is_active == True,
            models.TransactionTemplate.auto_generate == True,
            models.TransactionTemplate.next_generation_date <= target_date
        )
    ).all()
    
    generated_count = 0
    for template in templates:
        # Check if template has ended
        if template.end_date and template.end_date < target_date:
            template.is_active = False
            continue
        
        # Generate ledger entry
        entry = models.FinancialLedgerEntry(
            company_id=template.company_id,
            transaction_date=template.next_generation_date,
            amount=template.amount,
            currency=template.currency,
            amount_inr=template.amount,  # TODO: Apply exchange rate if needed
            entry_type=template.entry_type,
            category=template.category,
            product_tag=template.product_tag,
            office_tag=template.office_tag,
            source=models.LedgerSource.SYSTEM,
            reference_id=str(template.id),
            reference_type="recurring_template",
            description=f"Auto-generated: {template.name}",
            entered_by_role=models.LedgerEnteredByRole.SYSTEM,
            is_recurring=True
        )
        db.add(entry)
        
        # Update template
        template.last_generated_at = datetime.utcnow()
        template.next_generation_date = calculate_next_date(
            template.next_generation_date,
            template.frequency
        )
        
        # Apply escalation if set
        if template.escalation_rate > 0:
            template.amount = template.amount * (Decimal("1.0") + template.escalation_rate / Decimal("100.0"))
        
        generated_count += 1
    
    db.commit()
    
    return {
        "message": f"Generated {generated_count} recurring transactions",
        "generated_count": generated_count,
        "as_of_date": target_date.isoformat()
    }


@router.post("/{template_id}/generate-now", response_model=dict)
def generate_single_transaction(
    template_id: uuid.UUID,
    transaction_date: Optional[date] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Manually generate a single transaction from template"""
    template = db.query(models.TransactionTemplate).filter(
        models.TransactionTemplate.id == template_id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    txn_date = transaction_date or date.today()
    
    entry = models.FinancialLedgerEntry(
        company_id=template.company_id,
        transaction_date=txn_date,
        amount=template.amount,
        currency=template.currency,
        amount_inr=template.amount,
        entry_type=template.entry_type,
        category=template.category,
        product_tag=template.product_tag,
        office_tag=template.office_tag,
        source=models.LedgerSource.MANUAL_FINANCE,
        reference_id=str(template.id),
        reference_type="recurring_template",
        description=f"Manual generation: {template.name}",
        entered_by_role=models.LedgerEnteredByRole.FINANCE,
        is_recurring=True
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    
    return {
        "message": "Transaction generated successfully",
        "ledger_entry_id": str(entry.id),
        "transaction_date": txn_date.isoformat(),
        "amount": float(template.amount)
    }


# Helper functions

def calculate_next_date(current_date: date, frequency: str) -> date:
    """Calculate next generation date based on frequency"""
    if frequency == "daily":
        return current_date + timedelta(days=1)
    elif frequency == "weekly":
        return current_date + timedelta(weeks=1)
    elif frequency == "monthly":
        return current_date + relativedelta(months=1)
    elif frequency == "quarterly":
        return current_date + relativedelta(months=3)
    elif frequency == "annually":
        return current_date + relativedelta(years=1)
    else:
        # Default to monthly
        return current_date + relativedelta(months=1)
