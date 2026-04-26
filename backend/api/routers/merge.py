from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

import models
import database
import auth
from services.merge_service import MergeService

router = APIRouter(prefix="/integrations/merge", tags=["integrations"])

@router.post("/sync")
def sync_merge_data(
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    """
    Trigger manual sync from Merge.dev (QuickBooks, Xero, etc.)
    """
    company = db.query(models.Company).first()
    if not company:
        raise HTTPException(status_code=404, detail="No company found")
        
    service = MergeService(db, company.id)
    result = service.sync_all()
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
        
    return result

@router.get("/status")
def get_merge_status(
    db: Session = Depends(database.get_db),
    current_user: str = Depends(auth.get_current_user)
):
    """Check last sync status for Merge.dev."""
    company = db.query(models.Company).first()
    if not company:
        return {"status": "unconfigured"}
        
    return {
        "last_sync": company.last_sync_merge.isoformat() if company.last_sync_merge else None,
        "configured": company.last_sync_merge is not None
    }
