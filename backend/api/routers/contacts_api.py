from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

import auth
import database
import models

router = APIRouter(prefix="/contacts", tags=["contacts"])


class ContactCreate(BaseModel):
    name: str
    type: str  # VENDOR | CUSTOMER
    email: Optional[str] = None
    phone: Optional[str] = None
    payment_terms: Optional[str] = None
    currency: str = "USD"
    tax_number: Optional[str] = None
    billing_address: Optional[dict] = None


class ContactUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    payment_terms: Optional[str] = None
    status: Optional[str] = None
    tax_number: Optional[str] = None
    billing_address: Optional[dict] = None


def _serialize(c: models.Contact) -> dict:
    return {
        "id": str(c.id),
        "name": c.name,
        "type": c.type,
        "email": c.email,
        "phone": c.phone,
        "status": c.status,
        "payment_terms": c.payment_terms,
        "currency": c.currency,
        "tax_number": c.tax_number,
        "billing_address": c.billing_address,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }


@router.get("")
def list_contacts(
    company_id: UUID,
    type: Optional[str] = Query(None, description="VENDOR or CUSTOMER"),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    q = db.query(models.Contact).filter(models.Contact.company_id == company_id)
    if type:
        q = q.filter(models.Contact.type == type)
    if status:
        q = q.filter(models.Contact.status == status)
    if search:
        q = q.filter(models.Contact.name.ilike(f"%{search}%"))
    contacts = q.order_by(models.Contact.name).limit(limit).all()
    return {"count": len(contacts), "contacts": [_serialize(c) for c in contacts]}


@router.get("/{contact_id}")
def get_contact(
    contact_id: UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    c = db.query(models.Contact).filter(models.Contact.id == contact_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Contact not found")
    return _serialize(c)


@router.post("", status_code=201)
def create_contact(
    company_id: UUID,
    payload: ContactCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    c = models.Contact(
        id=uuid4(),
        company_id=company_id,
        remote_id=f"manual-{uuid4()}",
        name=payload.name,
        type=payload.type,
        email=payload.email,
        phone=payload.phone,
        payment_terms=payload.payment_terms,
        currency=payload.currency,
        tax_number=payload.tax_number,
        billing_address=payload.billing_address,
        status="active",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return _serialize(c)


@router.patch("/{contact_id}")
def update_contact(
    contact_id: UUID,
    payload: ContactUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    c = db.query(models.Contact).filter(models.Contact.id == contact_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Contact not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(c, field, value)
    c.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(c)
    return _serialize(c)


@router.delete("/{contact_id}", status_code=204)
def delete_contact(
    contact_id: UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    c = db.query(models.Contact).filter(models.Contact.id == contact_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Contact not found")
    c.status = "inactive"
    db.commit()
