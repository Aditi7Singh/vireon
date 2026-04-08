"""
Purchase Orders Router
PO system with 3-way matching (PO, Receipt, Invoice)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal
import uuid

import database
import models
from auth import get_current_user

router = APIRouter(prefix="/purchase-orders", tags=["purchase-orders"])


@router.post("/", response_model=dict)
def create_purchase_order(
    company_id: uuid.UUID,
    vendor_id: uuid.UUID,
    po_date: date,
    expected_delivery_date: Optional[date],
    requested_by: str,
    department: Optional[str],
    budget_id: Optional[uuid.UUID],
    line_items: List[dict],
    notes: Optional[str],
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a new purchase order"""
    
    # Verify vendor exists
    vendor = db.query(models.Contact).filter(
        and_(
            models.Contact.id == vendor_id,
            models.Contact.type == "VENDOR"
        )
    ).first()
    
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    # Generate PO number
    po_count = db.query(models.PurchaseOrder).filter(
        models.PurchaseOrder.company_id == company_id
    ).count()
    po_number = f"PO-{po_count + 1:06d}"
    
    # Calculate total
    total_amount = sum(Decimal(str(item["quantity"])) * Decimal(str(item["unit_price"])) for item in line_items)
    
    # Create PO
    po = models.PurchaseOrder(
        company_id=company_id,
        po_number=po_number,
        vendor_id=vendor_id,
        po_date=po_date,
        expected_delivery_date=expected_delivery_date,
        total_amount=total_amount,
        status=models.POStatus.DRAFT,
        requested_by=requested_by,
        department=department,
        budget_id=budget_id,
        notes=notes
    )
    
    db.add(po)
    db.flush()
    
    # Create line items
    for item in line_items:
        line = models.POLineItem(
            po_id=po.id,
            description=item["description"],
            quantity=Decimal(str(item["quantity"])),
            unit_price=Decimal(str(item["unit_price"])),
            total_price=Decimal(str(item["quantity"])) * Decimal(str(item["unit_price"])),
            account_code=item.get("account_code")
        )
        db.add(line)
    
    db.commit()
    db.refresh(po)
    
    return {
        "po_id": str(po.id),
        "po_number": po_number,
        "vendor_id": str(vendor_id),
        "vendor_name": vendor.name,
        "total_amount": float(total_amount),
        "status": po.status.value,
        "line_items_count": len(line_items)
    }


@router.get("/", response_model=List[dict])
def list_purchase_orders(
    company_id: uuid.UUID,
    status: Optional[str] = None,
    vendor_id: Optional[uuid.UUID] = None,
    requested_by: Optional[str] = None,
    department: Optional[str] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List purchase orders with filters"""
    query = db.query(models.PurchaseOrder).filter(
        models.PurchaseOrder.company_id == company_id
    )
    
    if status:
        query = query.filter(models.PurchaseOrder.status == status)
    
    if vendor_id:
        query = query.filter(models.PurchaseOrder.vendor_id == vendor_id)
    
    if requested_by:
        query = query.filter(models.PurchaseOrder.requested_by == requested_by)
    
    if department:
        query = query.filter(models.PurchaseOrder.department == department)
    
    pos = query.order_by(models.PurchaseOrder.po_date.desc()).all()
    
    result = []
    for po in pos:
        vendor = db.query(models.Contact).filter(models.Contact.id == po.vendor_id).first()
        
        # Get line items count
        line_items_count = db.query(models.POLineItem).filter(
            models.POLineItem.po_id == po.id
        ).count()
        
        result.append({
            "id": str(po.id),
            "po_number": po.po_number,
            "vendor_name": vendor.name if vendor else "Unknown",
            "po_date": po.po_date.isoformat(),
            "total_amount": float(po.total_amount),
            "status": po.status.value,
            "requested_by": po.requested_by,
            "department": po.department,
            "line_items_count": line_items_count
        })
    
    return result


@router.get("/{po_id}", response_model=dict)
def get_purchase_order(
    po_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get purchase order details"""
    po = db.query(models.PurchaseOrder).filter(
        models.PurchaseOrder.id == po_id
    ).first()
    
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    
    # Get vendor
    vendor = db.query(models.Contact).filter(models.Contact.id == po.vendor_id).first()
    
    # Get line items
    line_items = db.query(models.POLineItem).filter(
        models.POLineItem.po_id == po_id
    ).all()
    
    return {
        "id": str(po.id),
        "company_id": str(po.company_id),
        "po_number": po.po_number,
        "vendor": {
            "id": str(vendor.id) if vendor else None,
            "name": vendor.name if vendor else "Unknown",
            "email": vendor.email if vendor else None
        },
        "po_date": po.po_date.isoformat(),
        "expected_delivery_date": po.expected_delivery_date.isoformat() if po.expected_delivery_date else None,
        "total_amount": float(po.total_amount),
        "currency": po.currency,
        "status": po.status.value,
        "requested_by": po.requested_by,
        "approved_by": po.approved_by,
        "approved_at": po.approved_at.isoformat() if po.approved_at else None,
        "rejection_reason": po.rejection_reason,
        "department": po.department,
        "budget_id": str(po.budget_id) if po.budget_id else None,
        "notes": po.notes,
        "line_items": [
            {
                "id": str(item.id),
                "description": item.description,
                "quantity": float(item.quantity),
                "unit_price": float(item.unit_price),
                "total_price": float(item.total_price),
                "quantity_received": float(item.quantity_received),
                "account_code": item.account_code
            }
            for item in line_items
        ],
        "created_at": po.created_at.isoformat(),
        "updated_at": po.updated_at.isoformat()
    }


@router.post("/{po_id}/submit", response_model=dict)
def submit_purchase_order(
    po_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Submit PO for approval"""
    po = db.query(models.PurchaseOrder).filter(
        models.PurchaseOrder.id == po_id
    ).first()
    
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    
    if po.status != models.POStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Only draft POs can be submitted")
    
    po.status = models.POStatus.SUBMITTED
    po.updated_at = datetime.utcnow()
    
    db.commit()
    
    # In production, trigger approval workflow
    
    return {
        "message": "Purchase order submitted for approval",
        "po_id": str(po_id),
        "status": po.status.value
    }


@router.post("/{po_id}/approve", response_model=dict)
def approve_purchase_order(
    po_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Approve purchase order"""
    po = db.query(models.PurchaseOrder).filter(
        models.PurchaseOrder.id == po_id
    ).first()
    
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    
    if po.status != models.POStatus.SUBMITTED:
        raise HTTPException(status_code=400, detail="Only submitted POs can be approved")
    
    po.status = models.POStatus.APPROVED
    po.approved_by = current_user.username
    po.approved_at = datetime.utcnow()
    po.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {
        "message": "Purchase order approved",
        "po_id": str(po_id),
        "approved_by": current_user.username,
        "approved_at": po.approved_at.isoformat()
    }


@router.post("/{po_id}/reject", response_model=dict)
def reject_purchase_order(
    po_id: uuid.UUID,
    rejection_reason: str,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Reject purchase order"""
    po = db.query(models.PurchaseOrder).filter(
        models.PurchaseOrder.id == po_id
    ).first()
    
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    
    if po.status != models.POStatus.SUBMITTED:
        raise HTTPException(status_code=400, detail="Only submitted POs can be rejected")
    
    po.status = models.POStatus.REJECTED
    po.rejection_reason = rejection_reason
    po.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {
        "message": "Purchase order rejected",
        "po_id": str(po_id),
        "rejection_reason": rejection_reason
    }


@router.post("/{po_id}/receive", response_model=dict)
def receive_goods(
    po_id: uuid.UUID,
    line_item_id: uuid.UUID,
    quantity_received: Decimal,
    received_date: date,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Record goods receipt"""
    po = db.query(models.PurchaseOrder).filter(
        models.PurchaseOrder.id == po_id
    ).first()
    
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    
    if po.status not in [models.POStatus.APPROVED, models.POStatus.PARTIALLY_RECEIVED]:
        raise HTTPException(status_code=400, detail="PO must be approved to receive goods")
    
    # Get line item
    line_item = db.query(models.POLineItem).filter(
        and_(
            models.POLineItem.id == line_item_id,
            models.POLineItem.po_id == po_id
        )
    ).first()
    
    if not line_item:
        raise HTTPException(status_code=404, detail="Line item not found")
    
    # Check if receiving more than ordered
    total_received = line_item.quantity_received + quantity_received
    if total_received > line_item.quantity:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot receive {float(quantity_received)}. Total would exceed ordered quantity of {float(line_item.quantity)}"
        )
    
    # Update line item
    line_item.quantity_received += quantity_received
    
    # Check if all items fully received
    all_items = db.query(models.POLineItem).filter(
        models.POLineItem.po_id == po_id
    ).all()
    
    all_received = all(item.quantity_received >= item.quantity for item in all_items)
    any_received = any(item.quantity_received > 0 for item in all_items)
    
    if all_received:
        po.status = models.POStatus.RECEIVED
    elif any_received:
        po.status = models.POStatus.PARTIALLY_RECEIVED
    
    po.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {
        "message": "Goods receipt recorded",
        "po_id": str(po_id),
        "line_item_id": str(line_item_id),
        "quantity_received": float(quantity_received),
        "total_received": float(line_item.quantity_received),
        "quantity_ordered": float(line_item.quantity),
        "po_status": po.status.value
    }


@router.post("/{po_id}/match-invoice", response_model=dict)
def three_way_match(
    po_id: uuid.UUID,
    invoice_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Perform 3-way match (PO, Receipt, Invoice)"""
    
    # Get PO
    po = db.query(models.PurchaseOrder).filter(
        models.PurchaseOrder.id == po_id
    ).first()
    
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    
    # Get Invoice
    invoice = db.query(models.Invoice).filter(
        models.Invoice.id == invoice_id
    ).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Verify vendor matches
    if invoice.contact_id != po.vendor_id:
        return {
            "match_status": "failed",
            "reason": "Vendor mismatch",
            "po_vendor": str(po.vendor_id),
            "invoice_vendor": str(invoice.contact_id)
        }
    
    # Check amounts (allow 5% tolerance)
    amount_variance = abs(float(po.total_amount - invoice.total_amount))
    tolerance = float(po.total_amount) * 0.05
    
    if amount_variance > tolerance:
        return {
            "match_status": "failed",
            "reason": "Amount variance exceeds tolerance",
            "po_amount": float(po.total_amount),
            "invoice_amount": float(invoice.total_amount),
            "variance": amount_variance,
            "tolerance": tolerance
        }
    
    # Check receipt status
    line_items = db.query(models.POLineItem).filter(
        models.POLineItem.po_id == po_id
    ).all()
    
    receipt_status = "complete"
    for item in line_items:
        if item.quantity_received < item.quantity:
            receipt_status = "partial"
            break
    
    if receipt_status != "complete":
        return {
            "match_status": "warning",
            "reason": "Goods not fully received",
            "receipt_status": receipt_status,
            "can_proceed": False
        }
    
    # All checks passed
    po.status = models.POStatus.CLOSED
    po.updated_at = datetime.utcnow()
    
    # Update invoice status
    invoice.status = "APPROVED"
    
    db.commit()
    
    return {
        "match_status": "success",
        "po_id": str(po_id),
        "invoice_id": str(invoice_id),
        "po_amount": float(po.total_amount),
        "invoice_amount": float(invoice.total_amount),
        "variance": amount_variance,
        "matched_at": datetime.utcnow().isoformat()
    }


@router.get("/dashboard/summary", response_model=dict)
def get_po_dashboard(
    company_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get PO dashboard summary"""
    
    all_pos = db.query(models.PurchaseOrder).filter(
        models.PurchaseOrder.company_id == company_id
    ).all()
    
    # Calculate summary
    total_pos = len(all_pos)
    draft = sum(1 for po in all_pos if po.status == models.POStatus.DRAFT)
    submitted = sum(1 for po in all_pos if po.status == models.POStatus.SUBMITTED)
    approved = sum(1 for po in all_pos if po.status == models.POStatus.APPROVED)
    received = sum(1 for po in all_pos if po.status == models.POStatus.RECEIVED)
    partially_received = sum(1 for po in all_pos if po.status == models.POStatus.PARTIALLY_RECEIVED)
    closed = sum(1 for po in all_pos if po.status == models.POStatus.CLOSED)
    
    total_value = sum(float(po.total_amount) for po in all_pos if po.status != models.POStatus.REJECTED)
    
    # Pending approvals
    pending_approvals = [
        {
            "po_id": str(po.id),
            "po_number": po.po_number,
            "total_amount": float(po.total_amount),
            "requested_by": po.requested_by,
            "po_date": po.po_date.isoformat()
        }
        for po in all_pos
        if po.status == models.POStatus.SUBMITTED
    ]
    
    return {
        "summary": {
            "total_pos": total_pos,
            "draft": draft,
            "submitted": submitted,
            "approved": approved,
            "partially_received": partially_received,
            "received": received,
            "closed": closed,
            "total_value": total_value
        },
        "pending_approvals": pending_approvals,
        "pending_receipts": approved + partially_received
    }


@router.get("/vendor/{vendor_id}/history", response_model=dict)
def get_vendor_po_history(
    vendor_id: uuid.UUID,
    company_id: uuid.UUID,
    limit: int = 20,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get PO history for a vendor"""
    
    vendor = db.query(models.Contact).filter(models.Contact.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    pos = db.query(models.PurchaseOrder).filter(
        and_(
            models.PurchaseOrder.company_id == company_id,
            models.PurchaseOrder.vendor_id == vendor_id
        )
    ).order_by(models.PurchaseOrder.po_date.desc()).limit(limit).all()
    
    total_spend = sum(float(po.total_amount) for po in pos if po.status not in [models.POStatus.REJECTED, models.POStatus.CANCELLED])
    
    return {
        "vendor": {
            "id": str(vendor.id),
            "name": vendor.name,
            "email": vendor.email
        },
        "total_pos": len(pos),
        "total_spend": total_spend,
        "purchase_orders": [
            {
                "po_number": po.po_number,
                "po_date": po.po_date.isoformat(),
                "total_amount": float(po.total_amount),
                "status": po.status.value
            }
            for po in pos
        ]
    }
