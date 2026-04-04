"""
Memory & Session Management
=========================
LangGraph conversation memory management.
"""

from datetime import datetime
from uuid import UUID
from typing import Any, Dict, List, Optional

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
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


def _get_session_db():
    import database

    return next(database.get_db())


def _normalize_uuid(value: Optional[str]) -> Optional[UUID]:
    if value is None or value == "":
        return None
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


def _conversation_role_to_message(role: str, content: str) -> BaseMessage:
    role_normalized = (role or "").lower()
    if role_normalized == "user":
        return HumanMessage(content=content)
    if role_normalized == "assistant":
        return AIMessage(content=content)
    return SystemMessage(content=content)


def _serialize_message_metadata(metadata: Any) -> Dict[str, Any]:
    if isinstance(metadata, dict):
        return metadata
    return {"raw": metadata}


def load_session_messages(session_id: str) -> List[BaseMessage]:
    """Load persisted conversation messages for a session."""
    db = None
    try:
        import models

        db = _get_session_db()
        conversation = (
            db.query(models.AgentConversation)
            .filter(models.AgentConversation.session_id == session_id)
            .first()
        )
        if not conversation:
            return []

        persisted_messages = (
            db.query(models.AgentConversationMessage)
            .filter(models.AgentConversationMessage.conversation_id == conversation.id)
            .order_by(models.AgentConversationMessage.created_at.asc())
            .all()
        )
        return [_conversation_role_to_message(message.role, message.content) for message in persisted_messages]
    except Exception as exc:
        print(f"[MEMORY] Failed to load session history: {exc}")
        return []
    finally:
        if db:
            db.close()


def persist_session_turn(
    session_id: str,
    user_message: str,
    assistant_message: str,
    *,
    company_id: Optional[str] = None,
    user_id: Optional[str] = None,
    summary: Optional[str] = None,
    chain_id: Optional[str] = None,
    query_type: Optional[str] = None,
) -> bool:
    """Persist a user/assistant turn to the database."""
    db = None
    try:
        import models

        db = _get_session_db()
        conversation = (
            db.query(models.AgentConversation)
            .filter(models.AgentConversation.session_id == session_id)
            .first()
        )
        if conversation is None:
            conversation = models.AgentConversation(
                session_id=session_id,
                company_id=_normalize_uuid(company_id),
                user_id=_normalize_uuid(user_id),
                title=(user_message[:120] if user_message else None),
                summary=summary,
                query_count=0,
                last_message_at=datetime.utcnow(),
            )
            db.add(conversation)
            db.flush()
        else:
            if company_id is not None:
                conversation.company_id = _normalize_uuid(company_id)
            if user_id is not None:
                conversation.user_id = _normalize_uuid(user_id)
            if summary:
                conversation.summary = summary

        db.add(
            models.AgentConversationMessage(
                conversation_id=conversation.id,
                role="user",
                content=user_message,
                message_metadata={"query_type": query_type, "chain_id": chain_id},
            )
        )
        db.add(
            models.AgentConversationMessage(
                conversation_id=conversation.id,
                role="assistant",
                content=assistant_message,
                message_metadata={"query_type": query_type, "chain_id": chain_id},
            )
        )
        conversation.query_count = (conversation.query_count or 0) + 1
        conversation.last_message_at = datetime.utcnow()
        db.commit()
        return True
    except Exception as exc:
        if db:
            db.rollback()
        print(f"[MEMORY] Failed to persist session turn: {exc}")
        return False
    finally:
        if db:
            db.close()


def persist_tool_audit(
    session_id: str,
    tool_name: str,
    tool_input: Dict[str, Any],
    tool_output: Any,
    *,
    company_id: Optional[str] = None,
    chain_id: Optional[str] = None,
    status: str = "ok",
    data_timestamp: Optional[datetime] = None,
) -> bool:
    """Persist a tool call audit row."""
    db = None
    try:
        import models

        db = _get_session_db()
        conversation = (
            db.query(models.AgentConversation)
            .filter(models.AgentConversation.session_id == session_id)
            .first()
        )
        if conversation is None:
            conversation = models.AgentConversation(
                session_id=session_id,
                company_id=_normalize_uuid(company_id),
                query_count=0,
                last_message_at=datetime.utcnow(),
            )
            db.add(conversation)
            db.flush()

        db.add(
            models.AgentToolAudit(
                conversation_id=conversation.id,
                company_id=_normalize_uuid(company_id),
                tool_name=tool_name,
                tool_input=tool_input or {},
                tool_output=_serialize_message_metadata(tool_output),
                chain_id=chain_id,
                status=status,
                data_timestamp=data_timestamp,
            )
        )
        db.commit()
        return True
    except Exception as exc:
        if db:
            db.rollback()
        print(f"[MEMORY] Failed to persist tool audit: {exc}")
        return False
    finally:
        if db:
            db.close()


def build_enhanced_context(company_context: Dict, company_id: Optional[str] = None) -> Dict:
    """
    Build enhanced company context with additional financial metrics.
    
    Args:
        company_context: Base company context
        
    Returns:
        Enhanced context with additional metrics
    """
    enhanced = company_context.copy()
    if company_id is not None:
        enhanced["company_id"] = str(company_id)
    enhanced.setdefault("source_system", "erpnext")
    enhanced.setdefault("confidence", "medium")
    
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
        normalized_company_id = _normalize_uuid(company_id)
        company = None
        if normalized_company_id is not None:
            company = db.query(models.Company).filter(models.Company.id == normalized_company_id).first()
        if company is None:
            company = db.query(models.Company).first()
        
        if company:
            enhanced["company_id"] = str(company.id)
            enhanced["company_name"] = company.name
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
            enhanced["data_as_of"] = current_month.isoformat()
            
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
        history = ChatMessageHistory()
        for message in load_session_messages(session_id):
            history.add_message(message)
        return history
    
    def clear_session(self, session_id: str) -> bool:
        """
        Clear a session's history.
        """
        db = None
        try:
            import models

            db = _get_session_db()
            conversation = (
                db.query(models.AgentConversation)
                .filter(models.AgentConversation.session_id == session_id)
                .first()
            )
            if not conversation:
                return True
            db.query(models.AgentConversationMessage).filter(
                models.AgentConversationMessage.conversation_id == conversation.id
            ).delete(synchronize_session=False)
            db.query(models.AgentToolAudit).filter(
                models.AgentToolAudit.conversation_id == conversation.id
            ).delete(synchronize_session=False)
            db.delete(conversation)
            db.commit()
            return True
        except Exception as exc:
            if db:
                db.rollback()
            print(f"[MEMORY] Failed to clear session: {exc}")
            return False
        finally:
            if db:
                db.close()
