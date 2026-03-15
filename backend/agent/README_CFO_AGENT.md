# CFO Agent (`backend/agent/cfo_agent.py`)

Complete LangGraph orchestrator for the CFO AI agent. This is the core engine that coordinates query classification, LLM reasoning, tool execution, and safety guardrails.

## Architecture Overview

```
START
  ↓
[CLASSIFY_NODE]
  - Extract query type: simple/complex/alert
  - Uses keyword pre-filtering + Groq fallback
  ↓
[AGENT_NODE]
  - Build LLM with dynamic model selection
  - Inject fresh company context into system prompt
  - Invoke LLM with full message history + tools
  ↓
[CONDITIONAL: should_continue]
  - If AI response has tool_calls → TOOLS_NODE
  - Else → END
  ↓
[TOOLS_NODE]
  - Execute all tool calls via ToolNode
  - Append ToolMessages to history
  ↓
[SAFETY_NODE]
  - Check for tool errors
  - Increment error counter
  - If >= 3 errors → inject stop message
  ↓
[CONDITIONAL: should_continue_from_tools]
  - If error_count >= 3 → END
  - Else → AGENT_NODE (loop back for more reasoning)
  ↓
END
  - Extract final AI response
  - Return to caller
```

## State Definition

```python
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    # Full conversation history. LangGraph automatically merges new messages.
    
    query_type: str
    # One of: "simple", "complex", "alert"
    # Determines which LLM model to use (qwen2-32b or qwq-32b)
    
    company_context: dict
    # Live financial snapshot from GET /scorecard
    # Keys: name, cash, monthly_burn, runway_months, mrr, arr, last_updated
    # Injected fresh into system prompt at START of each user turn
    
    session_id: str
    # Unique session identifier (e.g., "cfo-session-20260315-110546")
    # Used by checkpointer to retrieve conversation history
    
    tool_error_count: int
    # Safety counter. Agent stops if >= 3
    # Prevents infinite loops on repeated API failures
```

## Nodes

### 1. classify_node(state) → {"query_type": str}

**Purpose:** Determine query complexity from the user message.

**Logic:**
1. Extract last HumanMessage from state
2. Call `classify_query()` from routing.py
   - Uses keyword pre-filter (85-90% of queries classified instantly)
   - Falls back to Groq qwen2-32b for borderline cases
3. Return updated query_type

**Example:**
```python
Input:  "What happens if we hire 10 engineers?"
Output: {"query_type": "complex"}
```

### 2. agent_node(state) → {"messages": [AIMessage]}

**Purpose:** Run LLM with tools to reason and generate tool calls.

**Process:**
1. Determine thinking mode based on query_type:
   - `complex` → thinking=True, model=qwq-32b (expensive tokens, thorough)
   - `simple` or `alert` → thinking=False, model=qwen2-32b (fast, cost-effective)

2. Build LLM with `build_llm(thinking)`
   - LLM binds all 10 financial tools
   - Creates ChatGroq instance with api_key from env

3. Build system prompt via `build_cfo_system_prompt(company_context)`
   - Inserts FRESH company context (cash, runway, etc.)
   - Includes 8 sections: IDENTITY, CONTEXT, ROLE, TOOLS, RULES, FORMAT, TONE, PRINCIPLE
   - Prepend as SystemMessage

4. Invoke LLM with full message chain:
   ```python
   messages = [SystemMessage(context)] + state["messages"]
   ai_response = llm.invoke(messages)
   ```

5. Return response to append to message history

**Example output:**
```
AIMessage(
    content="Based on current cash of $485k and burn of $93k/month...",
    tool_calls=[
        {"name": "simulate_hire", "args": {"n_engineers": 2, "salary": 130000}},
    ]
)
```

### 3. ToolNode (LangGraph prebuilt)

**Purpose:** Execute all tool calls from the LLM response.

**Implementation:**
- Uses LangGraph's `ToolNode(get_all_tools())`
- Automatically handles tool execution
- Converts tool results to ToolMessages
- Appends to message history

**Example:**
```
Input ToolCall:  simulate_hire(n_engineers=2, salary=130000)
Output ToolMessage: "New runway: 3.8 months (down from 5.2)"
```

### 4. safety_node(state) → {"tool_error_count": int[, "messages": [...]]}

**Purpose:** Check for tool failures and enforce error limits.

**Logic:**
1. Scan reversed message history for last ToolMessage
2. Check content for error patterns:
   - If dict with "error" key → error found
   - If string containing "error" → error found
3. Increment error counter
4. If counter >= 3:
   - Inject HumanMessage telling agent to stop
   - Return updated state to trigger END
5. Otherwise continue

**Example:**
```python
if msg.content == {"error": "GET /runway returned 500", "tool": "get_runway"}:
    error_count += 1
    if error_count >= 3:
        messages.append(HumanMessage(
            "Too many errors. Provide best analysis with available data."
        ))
```

## Conditional Edges

### should_continue(state) → "tools" | "END"

Decides whether to execute tools after agent reasoning.

```python
def should_continue(state: AgentState) -> Literal["tools", "END"]:
    last_message = state["messages"][-1]
    if isinstance(last_message, AIMessage) and getattr(last_message, 'tool_calls', None):
        return "tools"
    else:
        return "END"
```

### should_continue_from_tools(state) → "agent" | "END"

Decides whether to loop back to agent for more reasoning or end.

```python
def should_continue_from_tools(state: AgentState) -> Literal["agent", "END"]:
    if state.get("tool_error_count", 0) >= 3:
        return "END"  # Stop on too many errors
    else:
        return "agent"  # Loop back for more reasoning
```

## Public Entry Point

### run_cfo_query(user_message, session_id=None, company_context=None) → str

**Main API for the CFO agent.**

**Args:**
- `user_message`: Natural language query from founder
- `session_id`: Existing session ID (creates new if None)
- `company_context`: Existing context (fetches fresh if None)

**Process:**
1. Generate or retrieve session_id
2. Get fresh company_context if not provided
3. Build and compile graph
4. Initialize state with user message
5. Invoke graph via `graph.invoke(initial_state, config)`
6. Extract final AI response
7. Return as string

**Returns:** CFO's response as string

**Raises:**
- `ValueError`: If user_message is empty
- `RuntimeError`: If graph execution fails

**Example:**
```python
response = run_cfo_query(
    "What's our cash balance?",
    session_id="cfo-session-20260315-110546"
)
# Returns: "Your current cash position is $485,000..."
```

## LLM Model Selection

### build_llm(thinking: bool = False) → ChatGroq

**Fast Mode (thinking=False) - qwen2-32b:**
- Cost: ~$0.02 per 1K tokens
- Latency: ~500ms
- Best for: Simple queries, cash balance, basic metrics
- Use case: 85-90% of queries (via keyword pre-filter)

**Thinking Mode (thinking=True) - qwq-32b:**
- Cost: ~$0.30 per 1K tokens (includes thinking tokens)
- Latency: ~2-3 seconds
- Best for: Complex scenarios, financial modeling, strategic questions
- Use case: 10-15% of queries (complex classification)

**Selection Logic:**
```python
use_thinking = should_use_thinking_mode(state["query_type"])
# simple/alert → False, complex → True
llm = build_llm(thinking=use_thinking)
```

## Graph Building

### build_graph() → CompiledStateGraph

Constructs the complete agent graph with all nodes and edges.

**Steps:**
1. Get checkpointer from memory module
2. Create StateGraph(AgentState)
3. Add 4 nodes: classify, agent, tools, safety
4. Add edges and conditional edges
5. Compile with checkpointer for persistence

**State Persistence:**
- MemorySaver: In-memory (development)
- SqliteSaver: Persistent (production, requires `langgraph-checkpoint-sqlite`)

## Error Handling

### Tool Errors (3-strike rule)

If a tool fails, LangGraph automatically handles:
1. Wraps error in ToolMessage
2. Appends to message history
3. safety_node detects error pattern
4. Increments counter
5. If >= 3 errors:
   - safety_node injects stop message
   - Agent receives "stop and summarize" instruction
   - Graph reaches END

### Graceful Degradation

When company context backend is unreachable:
- `get_company_context()` returns cached SeedlingLabs profile
- Agent continues with fallback data
- No crash, just a WARNING in logs

### Missing Tool Responses

If a tool doesn't return expected format:
- Tool wrapper catches exception
- Returns `{"error": str, "tool": name}`
- safety_node detects and counts as error
- After 3 errors, agent stops

## Integration Points

### With Memory Module
```python
from backend.agent.memory import (
    get_checkpointer,        # Checkpointer for persistent state
    build_config,            # Build {"configurable": {"thread_id": id}}
    new_session_id,          # Generate "cfo-session-..."
    get_company_context,     # Fetch fresh company financial data
)
```

### With Routing Module
```python
from backend.agent.routing import (
    classify_query,              # Classify query type
    should_use_thinking_mode,    # Decide model based on type
)
```

### With Prompts Module
```python
from backend.agent.prompts import build_cfo_system_prompt
# Builds 8-section system prompt with fresh company context
```

### With Tools Module
```python
from backend.agent.tools import get_all_tools  # Returns 10 @tool functions
```

## Testing

### Unit Tests

```python
from backend.agent.cfo_agent import classify_node, agent_node, safety_node

# Test individual nodes
state = {"messages": [...], "query_type": "simple", ...}
result = classify_node(state)
assert "query_type" in result
```

### Graph Tests

```python
from backend.agent.cfo_agent import build_graph

graph = build_graph()  # Should not raise
# Graph is ready to invoke
```

### Integration Tests

```python
from backend.agent.cfo_agent import run_cfo_query

response = run_cfo_query("What's our cash balance?")
assert isinstance(response, str)
assert len(response) > 0
```

### CLI Test Runner

```bash
cd vireon/backend/agent
python cfo_agent.py
```

Tests 4 sample queries:
- "What is our current cash balance and runway?"
- "What happens if we hire 2 engineers at $130,000 salary?"
- "Why did our expenses increase last month?"
- "Give me a full financial health overview."

## Logs

All operations log with [LABEL] prefixes for debugging:

- `[BUILD_LLM]` - Model selection and binding
- `[BUILD_GRAPH]` - Graph construction steps
- `[CLASSIFY]` - Query type classification
- `[AGENT]` - LLM invocation
- `[ROUTE]` - Conditional edge decisions
- `[SAFETY]` - Error detection and counting
- `[RUN]` - Main entry point operations

Example:
```
INFO | [BUILD_LLM] Using qwen2-32b (fast mode for simple/alert queries)
INFO | [CLASSIFY] 'What is our cash...' → simple
INFO | [ROUTE] AI message has 0 tool calls → END
INFO | [RUN] Starting agent with query: 'What is our cash...'
```

## Performance

- **Graph compilation**: ~200ms (one-time)
- **Classify node**: <50ms (keyword match) or ~500ms (Groq fallback)
- **Agent node - fast**: ~500-800ms (qwen2-32b)
- **Agent node - thinking**: ~2-3s (qwq-32b)
- **Tool execution**: 50-200ms per tool (depends on backend)
- **Total per query**: 1-5 seconds (fast) or 3-8 seconds (thinking)

## Next Steps

### Short-term
1. Create FastAPI `/ask` endpoint
2. Wire request → `run_cfo_query()` → response
3. Add authentication/session tracking

### Medium-term
1. Implement persistent SQLite checkpointer
2. Add multi-user session management
3. Add response caching for common queries

### Long-term
1. Add more specialized agents (Tax CFO, Ops CFO, etc.)
2. Implement multi-agent orchestration
3. Add voice interface
4. Deploy to production with load balancing

---

## Related Files

- `backend/agent/memory.py` - Session persistence & company context
- `backend/agent/routing.py` - Query classification logic
- `backend/agent/prompts.py` - CFO system prompt templates
- `backend/agent/tools.py` - Financial tool wrappers
- `backend/config/settings.py` - Configuration & env vars
