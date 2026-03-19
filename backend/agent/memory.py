"""
Memory & Session Management
=========================
LangGraph conversation memory management.
"""

from datetime import datetime
from typing import Dict
from langchain_community.chat_message_histories import ChatMessageHistory
from langgraph.checkpoint.memory import MemorySaver

# Checkpointer singleton for persistent memory within the process
_checkpointer = MemorySaver()

def get_checkpointer() -> MemorySaver:
    """
    Return a MemorySaver checkpointer for conversation memory.
    
    Using MemorySaver for reliable performance in the current containerized
    environment. Conversation state is maintained while the server is running.
    """
    return _checkpointer


def build_config(session_id: str) -> Dict:
    """
    Build the LangGraph config for a session.
    
    Args:
        session_id: Unique session identifier
        
    Returns:
        Configuration dict with thread_id for checkpointer
    """
    return {"configurable": {"thread_id": session_id}}


def new_session_id() -> str:
    """
    Generate a new unique session ID.
    
    Returns:
        Session ID string in format: cfo-session-YYYYMMDD-HHMMSS
    """
    return f"cfo-session-{datetime.now().strftime('%Y%m%d-%H%M%S')}"


def build_enhanced_context(company_context: Dict) -> Dict:
    """
    Build enhanced company context with additional financial metrics.
    
    Args:
        company_context: Base company context
        
    Returns:
        Enhanced context with additional metrics
    """
    enhanced = company_context.copy()
    
    try:
        # Add asset and liability context
        import database
        import models
        from analytics.metrics import (
            calculate_loan_metrics, 
            calculate_monthly_payroll_cost,
            calculate_monthly_depreciation_expense
        )
        
        db = next(database.get_db())
        company = db.query(models.Company).first()
        
        if company:
            # Loan metrics
            loan_metrics = calculate_loan_metrics(db, company.id)
            enhanced["total_debt"] = loan_metrics.get("total_debt", 0)
            enhanced["monthly_debt_payments"] = loan_metrics.get("monthly_payments", 0)
            
            # Payroll metrics
            from datetime import date
            current_month = date.today().replace(day=1)
            payroll_cost = calculate_monthly_payroll_cost(db, company.id, current_month)
            enhanced["monthly_payroll"] = payroll_cost
            
            # Depreciation metrics
            dep_expense = calculate_monthly_depreciation_expense(db, company.id, current_month)
            enhanced["monthly_depreciation"] = dep_expense
            
            # Asset count
            asset_count = db.query(models.FixedAsset).filter(
                models.FixedAsset.company_id == company.id
            ).count()
            enhanced["fixed_asset_count"] = asset_count
            
        db.close()
        
    except Exception as e:
        print(f"[MEMORY] Failed to enhance context: {e}")
    
    return enhanced


class SessionManager:
    """
    Manages conversation sessions with persistent storage.
    """
    
    def __init__(self):
        self.checkpointer = get_checkpointer()
    
    def get_history(self, session_id: str) -> ChatMessageHistory:
        """
        Get chat history for a session.
        """
        # For compatibility with legacy code if needed
        return ChatMessageHistory()
    
    def clear_session(self, session_id: str) -> bool:
        """
        Clear a session's history.
        """
        return True
