"""
Inventory Management Router
Inventory valuation (FIFO/LIFO) and COGS calculation for product companies
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal
import uuid
from collections import deque

import database
import models
from auth import get_current_user

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.post("/items", response_model=dict)
def create_inventory_item(
    company_id: uuid.UUID,
    sku: str,
    name: str,
    description: Optional[str],
    category: Optional[str],
    unit_cost: Decimal,
    quantity_on_hand: Decimal = Decimal("0"),
    reorder_point: Optional[Decimal] = None,
    costing_method: str = "FIFO",
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a new inventory item"""
    
    # Check for duplicate SKU
    existing = db.query(models.InventoryItem).filter(
        models.InventoryItem.sku == sku
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="SKU already exists")
    
    item = models.InventoryItem(
        company_id=company_id,
        sku=sku,
        name=name,
        description=description,
        category=category,
        unit_cost=unit_cost,
        quantity_on_hand=quantity_on_hand,
        reorder_point=reorder_point,
        costing_method=costing_method
    )
    
    db.add(item)
    db.commit()
    db.refresh(item)
    
    return {
        "item_id": str(item.id),
        "sku": item.sku,
        "name": item.name,
        "unit_cost": float(item.unit_cost),
        "quantity_on_hand": float(item.quantity_on_hand),
        "costing_method": item.costing_method
    }


@router.get("/items", response_model=List[dict])
def list_inventory_items(
    company_id: uuid.UUID,
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    low_stock_only: bool = False,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List inventory items"""
    query = db.query(models.InventoryItem).filter(
        models.InventoryItem.company_id == company_id
    )
    
    if category:
        query = query.filter(models.InventoryItem.category == category)
    
    if is_active is not None:
        query = query.filter(models.InventoryItem.is_active == is_active)
    
    items = query.all()
    
    result = []
    for item in items:
        # Check if below reorder point
        needs_reorder = False
        if item.reorder_point and item.quantity_on_hand <= item.reorder_point:
            needs_reorder = True
        
        if low_stock_only and not needs_reorder:
            continue
        
        # Calculate inventory value
        inventory_value = item.quantity_on_hand * item.unit_cost
        
        result.append({
            "id": str(item.id),
            "sku": item.sku,
            "name": item.name,
            "category": item.category,
            "unit_cost": float(item.unit_cost),
            "quantity_on_hand": float(item.quantity_on_hand),
            "inventory_value": float(inventory_value),
            "reorder_point": float(item.reorder_point) if item.reorder_point else None,
            "needs_reorder": needs_reorder,
            "costing_method": item.costing_method,
            "is_active": item.is_active
        })
    
    return result


@router.get("/items/{item_id}", response_model=dict)
def get_inventory_item(
    item_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get inventory item details"""
    item = db.query(models.InventoryItem).filter(
        models.InventoryItem.id == item_id
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    
    # Get transaction history
    transactions = db.query(models.InventoryTransaction).filter(
        models.InventoryTransaction.item_id == item_id
    ).order_by(models.InventoryTransaction.transaction_date.desc()).limit(20).all()
    
    return {
        "id": str(item.id),
        "company_id": str(item.company_id),
        "sku": item.sku,
        "name": item.name,
        "description": item.description,
        "category": item.category,
        "unit_cost": float(item.unit_cost),
        "quantity_on_hand": float(item.quantity_on_hand),
        "inventory_value": float(item.quantity_on_hand * item.unit_cost),
        "reorder_point": float(item.reorder_point) if item.reorder_point else None,
        "costing_method": item.costing_method,
        "is_active": item.is_active,
        "recent_transactions": [
            {
                "date": t.transaction_date.isoformat(),
                "type": t.transaction_type,
                "quantity": float(t.quantity),
                "unit_cost": float(t.unit_cost),
                "total_cost": float(t.total_cost)
            }
            for t in transactions
        ]
    }


@router.post("/transactions", response_model=dict)
def record_inventory_transaction(
    item_id: uuid.UUID,
    transaction_date: date,
    transaction_type: str,
    quantity: Decimal,
    unit_cost: Decimal,
    reference_type: Optional[str] = None,
    reference_id: Optional[uuid.UUID] = None,
    notes: Optional[str] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Record inventory transaction (purchase, sale, adjustment, write-off)"""
    
    item = db.query(models.InventoryItem).filter(
        models.InventoryItem.id == item_id
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    
    # Calculate total cost
    total_cost = quantity * unit_cost
    
    # Create transaction
    transaction = models.InventoryTransaction(
        item_id=item_id,
        transaction_date=transaction_date,
        transaction_type=transaction_type,
        quantity=quantity,
        unit_cost=unit_cost,
        total_cost=total_cost,
        reference_type=reference_type,
        reference_id=reference_id,
        notes=notes
    )
    
    db.add(transaction)
    
    # Update item quantity and cost
    if transaction_type == "purchase":
        # Increase inventory
        old_qty = item.quantity_on_hand
        old_cost = item.unit_cost
        
        # Weighted average cost
        new_qty = old_qty + quantity
        if new_qty > 0:
            item.unit_cost = ((old_qty * old_cost) + (quantity * unit_cost)) / new_qty
        item.quantity_on_hand = new_qty
        
    elif transaction_type == "sale":
        # Decrease inventory
        if item.quantity_on_hand < quantity:
            raise HTTPException(status_code=400, detail="Insufficient inventory")
        item.quantity_on_hand -= quantity
        
    elif transaction_type == "adjustment":
        # Direct adjustment
        item.quantity_on_hand += quantity  # Can be negative for decreases
        
    elif transaction_type == "write_off":
        # Write off inventory
        if item.quantity_on_hand < quantity:
            raise HTTPException(status_code=400, detail="Insufficient inventory to write off")
        item.quantity_on_hand -= quantity
    
    item.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(transaction)
    
    return {
        "transaction_id": str(transaction.id),
        "item_id": str(item_id),
        "transaction_type": transaction_type,
        "quantity": float(quantity),
        "unit_cost": float(unit_cost),
        "total_cost": float(total_cost),
        "new_quantity_on_hand": float(item.quantity_on_hand),
        "new_unit_cost": float(item.unit_cost)
    }


@router.post("/calculate-cogs", response_model=dict)
def calculate_cogs(
    item_id: uuid.UUID,
    quantity_sold: Decimal,
    sale_date: date,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Calculate COGS using item's costing method (FIFO/LIFO)"""
    
    item = db.query(models.InventoryItem).filter(
        models.InventoryItem.id == item_id
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    
    if item.quantity_on_hand < quantity_sold:
        raise HTTPException(status_code=400, detail="Insufficient inventory")
    
    # Get purchase transactions to calculate COGS
    purchases = db.query(models.InventoryTransaction).filter(
        and_(
            models.InventoryTransaction.item_id == item_id,
            models.InventoryTransaction.transaction_type == "purchase",
            models.InventoryTransaction.transaction_date <= sale_date
        )
    ).order_by(
        models.InventoryTransaction.transaction_date.asc()  # FIFO
    ).all()
    
    if item.costing_method == "LIFO":
        purchases = list(reversed(purchases))  # LIFO - reverse order
    
    cogs = Decimal("0")
    remaining_qty = quantity_sold
    layers_used = []
    
    for purchase in purchases:
        if remaining_qty <= 0:
            break
        
        qty_to_use = min(purchase.quantity, remaining_qty)
        layer_cogs = qty_to_use * purchase.unit_cost
        cogs += layer_cogs
        
        layers_used.append({
            "date": purchase.transaction_date.isoformat(),
            "quantity": float(qty_to_use),
            "unit_cost": float(purchase.unit_cost),
            "layer_cogs": float(layer_cogs)
        })
        
        remaining_qty -= qty_to_use
    
    # If we still have remaining qty, use current unit cost
    if remaining_qty > 0:
        additional_cogs = remaining_qty * item.unit_cost
        cogs += additional_cogs
        layers_used.append({
            "date": sale_date.isoformat(),
            "quantity": float(remaining_qty),
            "unit_cost": float(item.unit_cost),
            "layer_cogs": float(additional_cogs),
            "note": "Used current unit cost"
        })
    
    return {
        "item_id": str(item_id),
        "sku": item.sku,
        "quantity_sold": float(quantity_sold),
        "costing_method": item.costing_method,
        "total_cogs": float(cogs),
        "average_unit_cost": float(cogs / quantity_sold) if quantity_sold > 0 else 0,
        "layers_used": layers_used
    }


@router.get("/valuation", response_model=dict)
def get_inventory_valuation(
    company_id: uuid.UUID,
    as_of_date: Optional[date] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get total inventory valuation"""
    
    as_of = as_of_date or date.today()
    
    items = db.query(models.InventoryItem).filter(
        and_(
            models.InventoryItem.company_id == company_id,
            models.InventoryItem.is_active == True
        )
    ).all()
    
    total_value = Decimal("0")
    total_units = Decimal("0")
    by_category = {}
    items_detail = []
    
    for item in items:
        item_value = item.quantity_on_hand * item.unit_cost
        total_value += item_value
        total_units += item.quantity_on_hand
        
        # Aggregate by category
        category = item.category or "Uncategorized"
        if category not in by_category:
            by_category[category] = {"value": Decimal("0"), "units": Decimal("0"), "items": 0}
        
        by_category[category]["value"] += item_value
        by_category[category]["units"] += item.quantity_on_hand
        by_category[category]["items"] += 1
        
        items_detail.append({
            "sku": item.sku,
            "name": item.name,
            "category": category,
            "quantity": float(item.quantity_on_hand),
            "unit_cost": float(item.unit_cost),
            "total_value": float(item_value),
            "costing_method": item.costing_method
        })
    
    # Convert category aggregations
    category_summary = {
        cat: {
            "value": float(data["value"]),
            "units": float(data["units"]),
            "items": data["items"]
        }
        for cat, data in by_category.items()
    }
    
    return {
        "as_of_date": as_of.isoformat(),
        "total_inventory_value": float(total_value),
        "total_units": float(total_units),
        "total_items": len(items),
        "by_category": category_summary,
        "top_items_by_value": sorted(items_detail, key=lambda x: x["total_value"], reverse=True)[:10]
    }


@router.get("/turnover", response_model=dict)
def calculate_inventory_turnover(
    company_id: uuid.UUID,
    start_date: date,
    end_date: date,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Calculate inventory turnover ratio"""
    
    # Get all sales transactions in period
    items = db.query(models.InventoryItem).filter(
        models.InventoryItem.company_id == company_id
    ).all()
    
    total_cogs = Decimal("0")
    
    for item in items:
        sales = db.query(models.InventoryTransaction).filter(
            and_(
                models.InventoryTransaction.item_id == item.id,
                models.InventoryTransaction.transaction_type == "sale",
                models.InventoryTransaction.transaction_date >= start_date,
                models.InventoryTransaction.transaction_date <= end_date
            )
        ).all()
        
        for sale in sales:
            total_cogs += sale.total_cost
    
    # Calculate average inventory
    beginning_inventory = get_inventory_value_at_date(db, company_id, start_date)
    ending_inventory = get_inventory_value_at_date(db, company_id, end_date)
    average_inventory = (beginning_inventory + ending_inventory) / 2
    
    # Calculate turnover ratio
    turnover_ratio = total_cogs / average_inventory if average_inventory > 0 else Decimal("0")
    
    # Days in inventory
    days_in_period = (end_date - start_date).days
    days_in_inventory = days_in_period / turnover_ratio if turnover_ratio > 0 else Decimal("0")
    
    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "total_cogs": float(total_cogs),
        "beginning_inventory": float(beginning_inventory),
        "ending_inventory": float(ending_inventory),
        "average_inventory": float(average_inventory),
        "turnover_ratio": float(turnover_ratio),
        "days_in_inventory": float(days_in_inventory)
    }


# Helper functions

def get_inventory_value_at_date(db: Session, company_id: uuid.UUID, target_date: date) -> Decimal:
    """Calculate total inventory value at a specific date"""
    items = db.query(models.InventoryItem).filter(
        models.InventoryItem.company_id == company_id
    ).all()
    
    total_value = Decimal("0")
    
    for item in items:
        # Get all transactions up to target date
        transactions = db.query(models.InventoryTransaction).filter(
            and_(
                models.InventoryTransaction.item_id == item.id,
                models.InventoryTransaction.transaction_date <= target_date
            )
        ).all()
        
        # Calculate quantity at date
        qty_at_date = Decimal("0")
        for txn in transactions:
            if txn.transaction_type in ["purchase", "adjustment"]:
                qty_at_date += txn.quantity
            elif txn.transaction_type in ["sale", "write_off"]:
                qty_at_date -= txn.quantity
        
        # Use current unit cost (simplified)
        total_value += qty_at_date * item.unit_cost
    
    return total_value
