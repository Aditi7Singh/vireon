"""Session memory management for CFO agent using LangGraph checkpointers.

Handles:
- SQLite-based conversation memory (persistent across sessions)
- Live company financial context (refreshed each turn)
- Session configuration for LangGraph thread management
"""

import logging
import httpx
from pathlib import Path
from datetime import datetime
from typing import Optional

# Use sqlite checkpoint from langgraph-checkpoint-sqlite if available, else fall back
try:
    from langgraph_checkpoint_sqlite import SqliteSaver
except ImportError:
    from langgraph.checkpoint.memory import MemorySaver as SqliteSaver

from backend.config.settings import Settings

logger = logging.getLogger(__name__)

# Cache for company context (refreshed each turn, not across turns)
_company_context_cache = None
_cache_timestamp = None


def get_checkpointer() -> SqliteSaver:
    """
    Initialize and return SQLite checkpointer for conversation memory.
    
    Creates the session database directory if it doesn't exist.
    
    Returns:
        SqliteSaver instance for storing conversation threads
    """
    db_path = Settings.SESSION_DB_PATH
    
    # Ensure directory exists
    db_dir = Path(db_path).parent
    db_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize checkpointer
    try:
        # Try to use SqliteSaver from langgraph-checkpoint-sqlite
        from langgraph_checkpoint_sqlite import SqliteSaver as SQLiteCheckpointer
        checkpointer = SQLiteCheckpointer(conn_string=f"sqlite:///{db_path}")
        logger.info(f"Checkpointer initialized: {db_path}")
    except ImportError:
        # Fall back to MemorySaver (in-memory)
        from langgraph.checkpoint.memory import MemorySaver
        checkpointer = MemorySaver()
        logger.warning("Using in-memory MemorySaver (install langgraph-checkpoint-sqlite for persistent storage)")
    
    return checkpointer


def get_company_context() -> dict:
    """
    Get live company financial snapshot from backend, with fallback to cached profile.
    
    This should be called FRESH at the start of each conversation turn to ensure
    the LLM always has the latest financial data in its context window.
    
    Returns:
        Dictionary with company financial snapshot:
        {
            "name": str,
            "cash": float,
            "monthly_burn": float,
            "runway_months": float,
            "mrr": float,
            "arr": float,
            "last_updated": str
        }
    """
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(f"{Settings.BACKEND_URL}/scorecard")
            response.raise_for_status()
            data = response.json()
            
            # Extract key metrics from scorecard
            context = {
                "name": Settings.COMPANY_NAME,
                "cash": data.get("cash_balance", 0),
                "monthly_burn": data.get("monthly_burn", 0),
                "runway_months": data.get("runway_months", 0),
                "mrr": data.get("mrr", 0),
                "arr": data.get("arr", 0),
                "last_updated": datetime.now().isoformat(),
            }
            
            logger.info(f"Company context loaded: {Settings.COMPANY_NAME} | Cash: ${context['cash']:,.0f} | Runway: {context['runway_months']:.1f} months")
            return context
    
    except Exception as e:
        # Fall back to hardcoded profile if backend is unreachable
        logger.warning(f"Backend unreachable ({str(e)[:50]}). Using cached company profile.")
        
        fallback_context = {
            "name": "SeedlingLabs",
            "cash": 485000,
            "monthly_burn": 93000,
            "runway_months": 5.2,
            "mrr": 42000,
            "arr": 504000,
            "last_updated": "unavailable — backend offline",
        }
        
        logger.warning("⚠️ Backend unreachable. Using cached company profile.")
        return fallback_context


def build_config(session_id: str) -> dict:
    """
    Build LangGraph configuration for a conversation session.
    
    Args:
        session_id: Unique identifier for the conversation session
    
    Returns:
        Configuration dict for LangGraph with thread mapping
    """
    config = {
        "configurable": {
            "thread_id": session_id,
        }
    }
    
    logger.info(f"Session config built: thread_id={session_id}")
    return config


def new_session_id() -> str:
    """
    Generate a new unique session ID.
    
    Returns:
        Session ID in format: cfo-session-YYYYMMDD-HHMMSS
    """
    session_id = f"cfo-session-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    logger.info(f"New session created: {session_id}")
    return session_id


def refresh_company_context() -> dict:
    """
    Explicitly refresh the company context for injection into system prompt.
    
    This should be called at the START of each conversation turn to ensure
    the LLM always has up-to-date financial metrics in its context.
    
    Returns:
        Fresh company context snapshot
    """
    logger.info("Refreshing company context for new turn")
    return get_company_context()


def format_company_context_for_prompt(company_context: dict) -> str:
    """
    Format company context as a readable string for inclusion in system prompt.
    
    Args:
        company_context: Dictionary from get_company_context()
    
    Returns:
        Formatted string for prompt injection
    """
    return f"""
Current Financial Snapshot ({company_context.get('last_updated', 'unknown')}):
- Company: {company_context.get('name', 'Unknown')}
- Cash on Hand: ${company_context.get('cash', 0):,.0f}
- Monthly Burn: ${company_context.get('monthly_burn', 0):,.0f}
- Runway: {company_context.get('runway_months', 0):.1f} months
- MRR: ${company_context.get('mrr', 0):,.0f}
- ARR: ${company_context.get('arr', 0):,.0f}
""".strip()


if __name__ == "__main__":
    # Test the memory module
    print("Memory Module Tests")
    print("=" * 70)
    
    # Test 1: Checkpointer
    print("\n1. Testing get_checkpointer():")
    try:
        checkpointer = get_checkpointer()
        print(f"   [OK] Checkpointer initialized: {type(checkpointer).__name__}")
    except Exception as e:
        print(f"   [FAIL] {str(e)}")
    
    # Test 2: Company context
    print("\n2. Testing get_company_context():")
    try:
        context = get_company_context()
        print(f"   [OK] Context loaded:")
        print(f"       Name: {context.get('name')}")
        print(f"       Cash: ${context.get('cash', 0):,.0f}")
        print(f"       Runway: {context.get('runway_months', 0):.1f} months")
    except Exception as e:
        print(f"   [FAIL] {str(e)}")
    
    # Test 3: Session config
    print("\n3. Testing build_config():")
    try:
        config = build_config("test-session-123")
        print(f"   [OK] Config built: {config}")
    except Exception as e:
        print(f"   [FAIL] {str(e)}")
    
    # Test 4: Session ID generation
    print("\n4. Testing new_session_id():")
    try:
        session_id = new_session_id()
        print(f"   [OK] Session ID: {session_id}")
        # Verify format
        assert session_id.startswith("cfo-session-"), "Invalid format"
        print(f"       Format check: PASS")
    except Exception as e:
        print(f"   [FAIL] {str(e)}")
    
    # Test 5: Context formatting
    print("\n5. Testing format_company_context_for_prompt():")
    try:
        formatted = format_company_context_for_prompt(context)
        print(f"   [OK] Formatted context:")
        for line in formatted.split("\n"):
            print(f"       {line}")
    except Exception as e:
        print(f"   [FAIL] {str(e)}")
    
    print("\n" + "=" * 70)
    print("Status: Memory module ready")

