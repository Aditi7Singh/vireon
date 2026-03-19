from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from pydantic import BaseModel

from database import get_db
from models import FixedAsset, DepreciationEntry
from schemas import FixedAssetCreate, FixedAsset as FixedAssetSchema, DepreciationEntry as DepreciationEntrySchema
from analytics.metrics import generate_depreciation_schedule, calculate_monthly_depreciation_expense

router = APIRouter(prefix="/depreciation", tags=["depreciation"])

@router.post("/assets", response_model=FixedAssetSchema)
def create_asset(asset: FixedAssetCreate, db: Session = Depends(get_db)):
    """Create a new fixed asset."""
    db_asset = FixedAsset(**asset.dict())
    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)
    return db_asset

@router.get("/assets", response_model=List[FixedAssetSchema])
def get_assets(company_id: str, db: Session = Depends(get_db)):
    """Get all assets for a company."""
    assets = db.query(FixedAsset).filter(FixedAsset.company_id == company_id).all()
    return assets

@router.get("/assets/{asset_id}", response_model=FixedAssetSchema)
def get_asset(asset_id: str, db: Session = Depends(get_db)):
    """Get a specific asset."""
    asset = db.query(FixedAsset).filter(FixedAsset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset

@router.put("/assets/{asset_id}", response_model=FixedAssetSchema)
def update_asset(asset_id: str, asset_update: FixedAssetCreate, db: Session = Depends(get_db)):
    """Update an asset."""
    asset = db.query(FixedAsset).filter(FixedAsset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    for key, value in asset_update.dict().items():
        setattr(asset, key, value)
    
    db.commit()
    db.refresh(asset)
    return asset

@router.delete("/assets/{asset_id}")
def delete_asset(asset_id: str, db: Session = Depends(get_db)):
    """Delete an asset."""
    asset = db.query(FixedAsset).filter(FixedAsset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    db.delete(asset)
    db.commit()
    return {"message": "Asset deleted"}

@router.post("/assets/{asset_id}/generate-schedule")
def generate_asset_schedule(asset_id: str, db: Session = Depends(get_db)):
    """Generate depreciation schedule for an asset."""
    schedule = generate_depreciation_schedule(asset_id, db)
    
    if not schedule:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Save depreciation entries to database
    for entry in schedule:
        dep_entry = DepreciationEntry(**entry)
        db.add(dep_entry)
    
    db.commit()
    return {"message": f"Generated {len(schedule)} depreciation entries"}

@router.get("/entries", response_model=List[DepreciationEntrySchema])
def get_depreciation_entries(
    company_id: str, 
    asset_id: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Get depreciation entries with optional filters."""
    query = db.query(DepreciationEntry).join(FixedAsset).filter(FixedAsset.company_id == company_id)
    
    if asset_id:
        query = query.filter(DepreciationEntry.asset_id == asset_id)
    
    if start_date:
        query = query.filter(DepreciationEntry.depreciation_date >= start_date)
    
    if end_date:
        query = query.filter(DepreciationEntry.depreciation_date <= end_date)
    
    entries = query.all()
    return entries

@router.get("/monthly-expense")
def get_monthly_depreciation_expense(
    company_id: str, 
    month: date, 
    db: Session = Depends(get_db)
):
    """Get total depreciation expense for a specific month."""
    expense = calculate_monthly_depreciation_expense(db, company_id, month)
    return {"month": month, "depreciation_expense": expense}