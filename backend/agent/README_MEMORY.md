# Memory Module (`backend/agent/memory.py`)

Handles conversation memory, session management, and company financial context refresh for the CFO agent.

## Core Concept

The memory module ensures:
1. **Persistent conversation history** - Via LangGraph checkpointers (SQLite or in-memory)
2. **Fresh company context each turn** - Latest financial data injected into system prompt
3. **Session isolation** - Each user conversation gets a unique `thread_id`

## API Reference

### Checkpointer Management

```python
from backend.agent.memory import get_checkpointer

checkpointer = get_checkpointer()
# Returns: SqliteSaver (persistent) or MemorySaver (fallback)
```

**Implementation:**
- Creates `/data` directory if missing
- Uses `langgraph-checkpoint-sqlite` if installed (persistent storage)
- Falls back to `MemorySaver` (in-memory) if not available
- Database path configurable via `SESSION_DB_PATH` env var (default: `./data/sessions.db`)

---

### Company Context Loader

```python
from backend.agent.memory import get_company_context, refresh_company_context

# Both functions return the same dict:
context = get_company_context()  # Live call to /scorecard
context = refresh_company_context()  # Alias with debug logging
```

**Returns:**
```python
{
    "name": "SeedlingLabs",
    "cash": 485000,                    # Cash on hand ($)
    "monthly_burn": 93000,             # Monthly cash burn ($)
    "runway_months": 5.2,              # Months of runway
    "mrr": 42000,                      # Monthly recurring revenue ($)
    "arr": 504000,                     # Annual recurring revenue ($)
    "last_updated": "2026-03-15T..."  # ISO timestamp
}
```

**Fallback Profile** (if backend unreachable at `BACKEND_URL/scorecard`):
```python
{
    "name": "SeedlingLabs",
    "cash": 485000,
    "monthly_burn": 93000,
    "runway_months": 5.2,
    "mrr": 42000,
    "arr": 504000,
    "last_updated": "unavailable — backend offline"
}
```

**Key Design:**
- Company context is **FRESH per turn**, not cached between turns
- Ensures LLM always operates on latest financial snapshot
- Graceful fallback prevents agent crashes if backend is down

---

### Session Configuration

```python
from backend.agent.memory import build_config, new_session_id

# Create a unique session ID
session_id = new_session_id()
# Returns: "cfo-session-20260315-105706"

# Build LangGraph config for the session
config = build_config(session_id)
# Returns: {"configurable": {"thread_id": "cfo-session-20260315-105706"}}
```

**Session ID Format:** `cfo-session-{YYYYMMDD}-{HHMMSS}`

**Config Structure:**
- `configurable.thread_id` - LangGraph uses this to retrieve conversation history
- One thread_id per user per conversation
- Thread_id maps to persistent checkpointer (SQLite)

---

### Context Formatting for Prompts

```python
from backend.agent.memory import format_company_context_for_prompt, get_company_context

context = get_company_context()
formatted = format_company_context_for_prompt(context)
```

**Output:**
```
Current Financial Snapshot (2026-03-15T10:57:06.123456):
- Company: SeedlingLabs
- Cash on Hand: $485,000
- Monthly Burn: $93,000
- Runway: 5.2 months
- MRR: $42,000
- ARR: $504,000
```

This string is injected into the CFO system prompt to give the LLM current context.

---

## Integration Pattern

Typical usage in the LangGraph agent:

```python
from backend.agent.memory import (
    get_checkpointer,
    refresh_company_context,
    build_config,
    new_session_id,
    format_company_context_for_prompt
)
from backend.agent.prompts import build_cfo_system_prompt
from backend.agent.tools import get_all_tools
from backend.agent.routing import get_routing_decision

# 1. Start a new conversation session
session_id = new_session_id()
config = build_config(session_id)

# 2. Initialize LangGraph with checkpointer
checkpointer = get_checkpointer()
graph = StateGraph(...)
graph.compile(checkpointer=checkpointer)

# 3. For each user turn, refresh context
company_context = refresh_company_context()

# 4. Build system prompt with fresh context
system_prompt = build_cfo_system_prompt(company_context)

# 5. Determine routing and model
routing = get_routing_decision(user_message)

# 6. Run graph with session config
result = graph.invoke(
    {"messages": [{"role": "user", "content": user_message}]},
    config=config
)
```

---

## Environment Configuration

From `.env.example`:

```bash
# Session Database Path
SESSION_DB_PATH=./data/sessions.db

# Company Configuration
COMPANY_NAME=SeedlingLabs

# Backend URL (source of company context)
BACKEND_URL=http://localhost:8000
```

---

## Testing

Run full memory module test suite:

```bash
cd vireon
python backend/agent/memory.py
```

Expected output:
```
Memory Module Tests
====================================================================
1. Testing get_checkpointer(): [OK] ...
2. Testing get_company_context(): [OK] ...
3. Testing build_config(): [OK] ...
4. Testing new_session_id(): [OK] ...
5. Testing format_company_context_for_prompt(): [OK] ...
====================================================================
Status: Memory module ready
```

---

## Architecture Notes

### Why Fresh Context Per Turn?

The LLM's context window has limited tokens. We optimize by:

1. **Not storing company context in conversation history** - Wastes history tokens
2. **Injecting fresh snapshot at START of each turn** - Latest cash/runway/etc.
3. **Letting LLM reference it directly in tools** - Tools return deltas, context provides baseline

### Why Graceful Fallback?

Production scenarios:
- Backend may restart during long conversations
- Database migrations might cause brief downtime
- Network issues shouldn't crash agent
- SeedlingLabs fallback profile reasonable default

### When to Upgrade to SQLite

Current: `MemorySaver` (in-memory)
- Fine for development and short demo sessions
- conversation lost if Python process restarts

Upgrade to: `SqliteSaver` (persistent)
- Install: `pip install langgraph-checkpoint-sqlite`
- Change in `get_checkpointer()`: Already has try/except for this
- Enables 24/7 agent with permanent session recovery

---

## Common Patterns

### Pattern 1: Get Fresh Context for System Prompt

```python
from backend.agent.memory import refresh_company_context, format_company_context_for_prompt

context = refresh_company_context()  # Fresh from /scorecard
formatted = format_company_context_for_prompt(context)
system_prompt = f"""You are a CFO AI. {formatted}

Your role is to..."""
```

### Pattern 2: Create New Conversation Session

```python
from backend.agent.memory import new_session_id, build_config

session_id = new_session_id()  # Generate unique ID
config = build_config(session_id)  # Build LangGraph config

# Store session_id in database for user session tracking
user_sessions[user_id] = session_id
```

### Pattern 3: Retrieve Existing Session

```python
from backend.agent.memory import build_config

# Look up user's session_id from database
session_id = user_sessions.get(user_id)
if session_id:
    config = build_config(session_id)
    # LangGraph will load conversation history from checkpointer
```

---

## Troubleshooting

### Q: Backend returns 401/403 error when getting company context

**A:** Check `BACKEND_URL` env var and ensure FastAPI server is running. Fallback profile will be used.

### Q: Conversation history not persisting across restarts

**A:** You're using `MemorySaver` (in-memory). Install persistent storage:
```bash
pip install langgraph-checkpoint-sqlite
# No code changes needed - get_checkpointer() auto-detects
```

### Q: Session IDs not unique

**A:** Not an issue - session IDs include timestamp down to second. Collisions essentially impossible.

### Q: Company context too stale for decisions

**A:** Context is refreshed per user turn (not per agent turn). Adjust by calling `refresh_company_context()` more frequently in your graph logic.

---

## Performance Considerations

- **Context fetch latency:** ~50-100ms (httpx with 5s timeout)
- **Checkpointer latency:** <1ms (in-memory), ~5-10ms (SQLite)
- **Fallback profile:** Instant (no network call)

For N concurrent users:
- Memory: ~1KB per session in MemorySaver, ~10KB per session in SQLite
- Database size grows ~5-10KB per conversation (depends on message count)

---

## Related Modules

- `backend/agent/prompts.py` - System prompt templates (uses company context)
- `backend/agent/tools.py` - Financial tools (called by LLM with company context)
- `backend/agent/routing.py` - Query classifier (determines model for context window size)
- `backend/agent/cfo_agent.py` - Main orchestrator (will integrate memory + routing + prompts + tools)
