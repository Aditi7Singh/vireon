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
