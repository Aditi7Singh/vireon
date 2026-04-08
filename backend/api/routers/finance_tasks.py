"""
Finance Tasks Router
Task management for finance team with close checklists
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal
import uuid

import database
import models
from auth import get_current_user

router = APIRouter(prefix="/finance-tasks", tags=["finance-tasks"])


@router.post("/", response_model=dict)
def create_task(
    company_id: uuid.UUID,
    title: str,
    description: Optional[str],
    task_type: str,
    assigned_to: str,
    due_date: Optional[date],
    priority: str = "medium",
    depends_on: Optional[List[str]] = None,
    checklist_items: Optional[List[dict]] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a new finance task"""
    
    task = models.FinanceTask(
        company_id=company_id,
        title=title,
        description=description,
        task_type=task_type,
        assigned_to=assigned_to,
        due_date=due_date,
        status="pending",
        priority=priority,
        depends_on=depends_on or [],
        checklist_items=checklist_items or []
    )
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    return {
        "task_id": str(task.id),
        "title": task.title,
        "task_type": task.type,
        "assigned_to": task.assigned_to,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "status": task.status
    }


@router.get("/", response_model=List[dict])
def list_tasks(
    company_id: uuid.UUID,
    status: Optional[str] = None,
    task_type: Optional[str] = None,
    assigned_to: Optional[str] = None,
    priority: Optional[str] = None,
    overdue_only: bool = False,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List finance tasks with filters"""
    query = db.query(models.FinanceTask).filter(
        models.FinanceTask.company_id == company_id
    )
    
    if status:
        query = query.filter(models.FinanceTask.status == status)
    
    if task_type:
        query = query.filter(models.FinanceTask.task_type == task_type)
    
    if assigned_to:
        query = query.filter(models.FinanceTask.assigned_to == assigned_to)
    
    if priority:
        query = query.filter(models.FinanceTask.priority == priority)
    
    if overdue_only:
        query = query.filter(
            and_(
                models.FinanceTask.due_date < date.today(),
                models.FinanceTask.status.in_(["pending", "in_progress"])
            )
        )
    
    tasks = query.order_by(
        models.FinanceTask.due_date.asc().nullslast(),
        models.FinanceTask.priority.desc()
    ).all()
    
    result = []
    for task in tasks:
        result.append({
            "id": str(task.id),
            "title": task.title,
            "task_type": task.task_type,
            "assigned_to": task.assigned_to,
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "status": task.status,
            "priority": task.priority,
            "is_overdue": task.due_date < date.today() if task.due_date and task.status in ["pending", "in_progress"] else False,
            "checklist_completion": calculate_checklist_completion(task.checklist_items),
            "created_at": task.created_at.isoformat()
        })
    
    return result


@router.get("/{task_id}", response_model=dict)
def get_task(
    task_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get task details"""
    task = db.query(models.FinanceTask).filter(
        models.FinanceTask.id == task_id
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Check dependencies
    blocked_by = []
    if task.depends_on:
        for dep_id in task.depends_on:
            dep_task = db.query(models.FinanceTask).filter(
                models.FinanceTask.id == uuid.UUID(dep_id)
            ).first()
            if dep_task and dep_task.status != "completed":
                blocked_by.append({
                    "task_id": str(dep_task.id),
                    "title": dep_task.title,
                    "status": dep_task.status
                })
    
    return {
        "id": str(task.id),
        "company_id": str(task.company_id),
        "title": task.title,
        "description": task.description,
        "task_type": task.task_type,
        "assigned_to": task.assigned_to,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "status": task.status,
        "priority": task.priority,
        "depends_on": task.depends_on,
        "blocked_by": blocked_by,
        "checklist_items": task.checklist_items,
        "checklist_completion": calculate_checklist_completion(task.checklist_items),
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "completed_by": task.completed_by,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat()
    }


@router.put("/{task_id}", response_model=dict)
def update_task(
    task_id: uuid.UUID,
    status: Optional[str] = None,
    assigned_to: Optional[str] = None,
    due_date: Optional[date] = None,
    priority: Optional[str] = None,
    checklist_items: Optional[List[dict]] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update task"""
    task = db.query(models.FinanceTask).filter(
        models.FinanceTask.id == task_id
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if status is not None:
        task.status = status
        if status == "completed":
            task.completed_at = datetime.utcnow()
            task.completed_by = current_user.username
    
    if assigned_to is not None:
        task.assigned_to = assigned_to
    
    if due_date is not None:
        task.due_date = due_date
    
    if priority is not None:
        task.priority = priority
    
    if checklist_items is not None:
        task.checklist_items = checklist_items
    
    task.updated_at = datetime.utcnow()
    db.commit()
    
    return {
        "message": "Task updated successfully",
        "task_id": str(task_id),
        "status": task.status
    }


@router.post("/{task_id}/checklist/{item_index}/complete", response_model=dict)
def complete_checklist_item(
    task_id: uuid.UUID,
    item_index: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Mark checklist item as complete"""
    task = db.query(models.FinanceTask).filter(
        models.FinanceTask.id == task_id
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if not task.checklist_items or item_index >= len(task.checklist_items):
        raise HTTPException(status_code=400, detail="Invalid checklist item index")
    
    task.checklist_items[item_index]["completed"] = True
    task.checklist_items[item_index]["completed_by"] = current_user.username
    task.checklist_items[item_index]["completed_at"] = datetime.utcnow().isoformat()
    
    # Mark modified for SQLAlchemy to detect JSON change
    task.checklist_items = list(task.checklist_items)
    task.updated_at = datetime.utcnow()
    
    db.commit()
    
    # Check if all items completed
    completion = calculate_checklist_completion(task.checklist_items)
    if completion == 100 and task.status != "completed":
        task.status = "completed"
        task.completed_at = datetime.utcnow()
        task.completed_by = current_user.username
        db.commit()
    
    return {
        "message": "Checklist item completed",
        "task_id": str(task_id),
        "checklist_completion": completion
    }


@router.post("/close-checklist", response_model=dict)
def create_month_end_close_checklist(
    company_id: uuid.UUID,
    period: str,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Generate month-end close checklist"""
    
    # Standard close checklist items
    checklist_template = [
        {"title": "Complete bank reconciliations", "completed": False, "required": True},
        {"title": "Review accounts receivable aging", "completed": False, "required": True},
        {"title": "Review accounts payable aging", "completed": False, "required": True},
        {"title": "Record all revenue transactions", "completed": False, "required": True},
        {"title": "Record all expense transactions", "completed": False, "required": True},
        {"title": "Calculate and record depreciation", "completed": False, "required": True},
        {"title": "Reconcile credit card statements", "completed": False, "required": True},
        {"title": "Review prepaid expenses", "completed": False, "required": True},
        {"title": "Review accrued expenses", "completed": False, "required": True},
        {"title": "Calculate tax liability", "completed": False, "required": True},
        {"title": "Review intercompany transactions", "completed": False, "required": False},
        {"title": "Generate financial statements", "completed": False, "required": True},
        {"title": "Variance analysis", "completed": False, "required": True},
        {"title": "CFO review and approval", "completed": False, "required": True}
    ]
    
    # Create main close task
    close_task = models.FinanceTask(
        company_id=company_id,
        title=f"Month-End Close - {period}",
        description=f"Complete all month-end close procedures for {period}",
        task_type="close_checklist",
        assigned_to="finance_team",
        due_date=get_close_due_date(period),
        status="pending",
        priority="high",
        checklist_items=checklist_template
    )
    
    db.add(close_task)
    db.commit()
    db.refresh(close_task)
    
    return {
        "task_id": str(close_task.id),
        "period": period,
        "total_items": len(checklist_template),
        "due_date": close_task.due_date.isoformat() if close_task.due_date else None,
        "checklist_items": checklist_template
    }


@router.get("/dashboard/summary", response_model=dict)
def get_tasks_dashboard(
    company_id: uuid.UUID,
    assigned_to: Optional[str] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get task summary for dashboard"""
    query = db.query(models.FinanceTask).filter(
        models.FinanceTask.company_id == company_id
    )
    
    if assigned_to:
        query = query.filter(models.FinanceTask.assigned_to == assigned_to)
    
    all_tasks = query.all()
    
    # Calculate summary
    total_tasks = len(all_tasks)
    pending = sum(1 for t in all_tasks if t.status == "pending")
    in_progress = sum(1 for t in all_tasks if t.status == "in_progress")
    completed = sum(1 for t in all_tasks if t.status == "completed")
    blocked = sum(1 for t in all_tasks if t.status == "blocked")
    
    overdue = sum(
        1 for t in all_tasks
        if t.due_date and t.due_date < date.today() and t.status in ["pending", "in_progress"]
    )
    
    due_today = sum(
        1 for t in all_tasks
        if t.due_date == date.today() and t.status in ["pending", "in_progress"]
    )
    
    high_priority = [
        {
            "id": str(t.id),
            "title": t.title,
            "due_date": t.due_date.isoformat() if t.due_date else None,
            "status": t.status
        }
        for t in all_tasks
        if t.priority == "high" and t.status in ["pending", "in_progress"]
    ]
    
    return {
        "summary": {
            "total_tasks": total_tasks,
            "pending": pending,
            "in_progress": in_progress,
            "completed": completed,
            "blocked": blocked,
            "overdue": overdue,
            "due_today": due_today
        },
        "high_priority_tasks": sorted(high_priority, key=lambda x: x["due_date"] or "9999-12-31")[:5],
        "completion_rate": (completed / total_tasks * 100) if total_tasks > 0 else 0
    }


# Helper functions

def calculate_checklist_completion(checklist_items: List[dict]) -> int:
    """Calculate checklist completion percentage"""
    if not checklist_items:
        return 0
    
    completed = sum(1 for item in checklist_items if item.get("completed", False))
    return int((completed / len(checklist_items)) * 100)


def get_close_due_date(period: str) -> date:
    """Calculate due date for period close (5 business days after month end)"""
    # Parse period (YYYY-MM format)
    try:
        year, month = map(int, period.split("-"))
        # Get last day of month
        if month == 12:
            next_month = date(year + 1, 1, 1)
        else:
            next_month = date(year, month + 1, 1)
        
        from datetime import timedelta
        last_day = next_month - timedelta(days=1)
        
        # Add 5 business days
        due_date = last_day
        business_days = 0
        while business_days < 5:
            due_date += timedelta(days=1)
            if due_date.weekday() < 5:  # Monday = 0, Friday = 4
                business_days += 1
        
        return due_date
    except:
        # Default to today + 5 days
        from datetime import timedelta
        return date.today() + timedelta(days=5)
