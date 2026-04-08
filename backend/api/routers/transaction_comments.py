"""
Transaction Comments Router
Comment threading on financial transactions
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
import uuid
import re

import database
import models
from auth import get_current_user

router = APIRouter(prefix="/transaction-comments", tags=["transaction-comments"])


@router.post("/", response_model=dict)
def create_comment(
    company_id: uuid.UUID,
    entity_type: str,
    entity_id: uuid.UUID,
    comment_text: str,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a comment on a transaction"""
    
    # Extract @mentions
    mentioned_users = extract_mentions(comment_text)
    
    comment = models.TransactionComment(
        company_id=company_id,
        entity_type=entity_type,
        entity_id=entity_id,
        comment_text=comment_text,
        created_by=current_user.username,
        mentioned_users=mentioned_users
    )
    
    db.add(comment)
    db.commit()
    db.refresh(comment)
    
    # In production, send notifications to mentioned users
    if mentioned_users:
        send_mention_notifications(db, mentioned_users, comment)
    
    return {
        "comment_id": str(comment.id),
        "entity_type": entity_type,
        "entity_id": str(entity_id),
        "comment_text": comment_text,
        "created_by": current_user.username,
        "mentioned_users": mentioned_users,
        "created_at": comment.created_at.isoformat()
    }


@router.get("/", response_model=List[dict])
def list_comments(
    company_id: uuid.UUID,
    entity_type: Optional[str] = None,
    entity_id: Optional[uuid.UUID] = None,
    created_by: Optional[str] = None,
    is_resolved: Optional[bool] = None,
    limit: int = 100,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List comments with filters"""
    query = db.query(models.TransactionComment).filter(
        models.TransactionComment.company_id == company_id
    )
    
    if entity_type:
        query = query.filter(models.TransactionComment.entity_type == entity_type)
    
    if entity_id:
        query = query.filter(models.TransactionComment.entity_id == entity_id)
    
    if created_by:
        query = query.filter(models.TransactionComment.created_by == created_by)
    
    if is_resolved is not None:
        query = query.filter(models.TransactionComment.is_resolved == is_resolved)
    
    comments = query.order_by(models.TransactionComment.created_at.desc()).limit(limit).all()
    
    result = []
    for comment in comments:
        result.append({
            "id": str(comment.id),
            "entity_type": comment.entity_type,
            "entity_id": str(comment.entity_id),
            "comment_text": comment.comment_text,
            "created_by": comment.created_by,
            "mentioned_users": comment.mentioned_users,
            "is_resolved": comment.is_resolved,
            "resolved_at": comment.resolved_at.isoformat() if comment.resolved_at else None,
            "resolved_by": comment.resolved_by,
            "created_at": comment.created_at.isoformat()
        })
    
    return result


@router.get("/{entity_type}/{entity_id}", response_model=List[dict])
def get_entity_comments(
    entity_type: str,
    entity_id: uuid.UUID,
    company_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get all comments for a specific entity"""
    comments = db.query(models.TransactionComment).filter(
        and_(
            models.TransactionComment.company_id == company_id,
            models.TransactionComment.entity_type == entity_type,
            models.TransactionComment.entity_id == entity_id
        )
    ).order_by(models.TransactionComment.created_at.asc()).all()
    
    result = []
    for comment in comments:
        result.append({
            "id": str(comment.id),
            "comment_text": comment.comment_text,
            "created_by": comment.created_by,
            "mentioned_users": comment.mentioned_users,
            "is_resolved": comment.is_resolved,
            "resolved_at": comment.resolved_at.isoformat() if comment.resolved_at else None,
            "resolved_by": comment.resolved_by,
            "created_at": comment.created_at.isoformat()
        })
    
    return result


@router.get("/comment/{comment_id}", response_model=dict)
def get_comment(
    comment_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get comment details"""
    comment = db.query(models.TransactionComment).filter(
        models.TransactionComment.id == comment_id
    ).first()
    
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Get entity details
    entity_details = get_entity_details(db, comment.entity_type, comment.entity_id)
    
    return {
        "id": str(comment.id),
        "company_id": str(comment.company_id),
        "entity_type": comment.entity_type,
        "entity_id": str(comment.entity_id),
        "entity_details": entity_details,
        "comment_text": comment.comment_text,
        "created_by": comment.created_by,
        "mentioned_users": comment.mentioned_users,
        "is_resolved": comment.is_resolved,
        "resolved_at": comment.resolved_at.isoformat() if comment.resolved_at else None,
        "resolved_by": comment.resolved_by,
        "created_at": comment.created_at.isoformat()
    }


@router.put("/{comment_id}/resolve", response_model=dict)
def resolve_comment(
    comment_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Mark comment as resolved"""
    comment = db.query(models.TransactionComment).filter(
        models.TransactionComment.id == comment_id
    ).first()
    
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    comment.is_resolved = True
    comment.resolved_at = datetime.utcnow()
    comment.resolved_by = current_user.username
    
    db.commit()
    
    return {
        "message": "Comment resolved",
        "comment_id": str(comment_id),
        "resolved_by": current_user.username,
        "resolved_at": comment.resolved_at.isoformat()
    }


@router.put("/{comment_id}/unresolve", response_model=dict)
def unresolve_comment(
    comment_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Mark comment as unresolved"""
    comment = db.query(models.TransactionComment).filter(
        models.TransactionComment.id == comment_id
    ).first()
    
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    comment.is_resolved = False
    comment.resolved_at = None
    comment.resolved_by = None
    
    db.commit()
    
    return {
        "message": "Comment marked as unresolved",
        "comment_id": str(comment_id)
    }


@router.delete("/{comment_id}", response_model=dict)
def delete_comment(
    comment_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete a comment"""
    comment = db.query(models.TransactionComment).filter(
        models.TransactionComment.id == comment_id
    ).first()
    
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Only creator can delete
    if comment.created_by != current_user.username:
        raise HTTPException(status_code=403, detail="Only comment creator can delete")
    
    db.delete(comment)
    db.commit()
    
    return {
        "message": "Comment deleted",
        "comment_id": str(comment_id)
    }


@router.get("/mentions/me", response_model=List[dict])
def get_my_mentions(
    company_id: uuid.UUID,
    is_resolved: Optional[bool] = False,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get comments where current user is mentioned"""
    
    # Query comments where user is in mentioned_users array
    comments = db.query(models.TransactionComment).filter(
        and_(
            models.TransactionComment.company_id == company_id,
            models.TransactionComment.is_resolved == is_resolved
        )
    ).all()
    
    # Filter for mentions (JSON array contains username)
    mentioned_comments = []
    for comment in comments:
        if comment.mentioned_users and current_user.username in comment.mentioned_users:
            entity_details = get_entity_details(db, comment.entity_type, comment.entity_id)
            mentioned_comments.append({
                "id": str(comment.id),
                "entity_type": comment.entity_type,
                "entity_id": str(comment.entity_id),
                "entity_details": entity_details,
                "comment_text": comment.comment_text,
                "created_by": comment.created_by,
                "is_resolved": comment.is_resolved,
                "created_at": comment.created_at.isoformat()
            })
    
    # Sort by created_at desc
    mentioned_comments.sort(key=lambda x: x["created_at"], reverse=True)
    
    return mentioned_comments


@router.get("/stats", response_model=dict)
def get_comment_stats(
    company_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get comment statistics"""
    
    all_comments = db.query(models.TransactionComment).filter(
        models.TransactionComment.company_id == company_id
    ).all()
    
    total_comments = len(all_comments)
    resolved = sum(1 for c in all_comments if c.is_resolved)
    unresolved = total_comments - resolved
    
    # Count by entity type
    by_entity_type = {}
    for comment in all_comments:
        entity_type = comment.entity_type
        by_entity_type[entity_type] = by_entity_type.get(entity_type, 0) + 1
    
    # Count by user
    by_user = {}
    for comment in all_comments:
        user = comment.created_by
        by_user[user] = by_user.get(user, 0) + 1
    
    return {
        "total_comments": total_comments,
        "resolved": resolved,
        "unresolved": unresolved,
        "resolution_rate": (resolved / total_comments * 100) if total_comments > 0 else 0,
        "by_entity_type": by_entity_type,
        "by_user": by_user,
        "top_commenters": sorted(by_user.items(), key=lambda x: x[1], reverse=True)[:5]
    }


# Helper functions

def extract_mentions(comment_text: str) -> List[str]:
    """Extract @mentions from comment text"""
    # Find all @username patterns
    pattern = r'@([a-zA-Z0-9_]+)'
    mentions = re.findall(pattern, comment_text)
    return list(set(mentions))  # Remove duplicates


def send_mention_notifications(db: Session, mentioned_users: List[str], comment: models.TransactionComment):
    """Send notifications to mentioned users"""
    # In production, create notifications or send emails
    # For now, just create a notification record
    for username in mentioned_users:
        notification = models.Notification(
            company_id=comment.company_id,
            recipient=username,
            title="You were mentioned in a comment",
            message=f"{comment.created_by} mentioned you: {comment.comment_text[:100]}",
            notification_type="mention",
            related_entity_type=comment.entity_type,
            related_entity_id=comment.entity_id
        )
        db.add(notification)
    
    try:
        db.commit()
    except:
        # Notification table might not exist, ignore
        db.rollback()


def get_entity_details(db: Session, entity_type: str, entity_id: uuid.UUID) -> dict:
    """Get basic details about the commented entity"""
    
    if entity_type == "ledger_entry":
        entry = db.query(models.FinancialLedgerEntry).filter(
            models.FinancialLedgerEntry.id == entity_id
        ).first()
        if entry:
            return {
                "description": entry.description,
                "amount": float(entry.amount),
                "date": entry.transaction_date.isoformat(),
                "category": entry.category.value
            }
    
    elif entity_type == "invoice":
        invoice = db.query(models.Invoice).filter(
            models.Invoice.id == entity_id
        ).first()
        if invoice:
            return {
                "invoice_number": invoice.invoice_number,
                "total_amount": float(invoice.total_amount),
                "status": invoice.status,
                "due_date": invoice.due_date.isoformat()
            }
    
    elif entity_type == "expense":
        expense = db.query(models.Expense).filter(
            models.Expense.id == entity_id
        ).first()
        if expense:
            return {
                "amount": float(expense.total_amount),
                "date": expense.transaction_date.isoformat(),
                "category": expense.category,
                "memo": expense.memo
            }
    
    elif entity_type == "contract":
        contract = db.query(models.Contract).filter(
            models.Contract.id == entity_id
        ).first()
        if contract:
            return {
                "contract_number": contract.contract_number,
                "vendor_name": contract.vendor_name,
                "status": contract.status.value
            }
    
    return {"entity_type": entity_type, "entity_id": str(entity_id)}
