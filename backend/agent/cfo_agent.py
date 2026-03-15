"""CFO AI Agent using LangGraph.

Full orchestration of:
- Query routing (simple/complex/alert classification)
- LLM reasoning with dynamic model selection
- Tool execution with error handling
- Safety guardrails and loop termination
"""

import logging
from typing import Annotated, Literal, TypedDict

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_groq import ChatGroq

from .memory import (
    get_checkpointer,
    build_config,
    new_session_id,
    get_company_context,
)
from backend.agent.tools import get_all_tools
from backend.agent.routing import classify_query, should_use_thinking_mode
from backend.agent.prompts import build_cfo_system_prompt
from backend.config.settings import Settings

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """Complete state for CFO agent conversation."""
    
    messages: Annotated[list[BaseMessage], add_messages]
    # Full conversation history with latest context prepended
    
    query_type: str
    # Classification: "simple" | "complex" | "alert"
    
    company_context: dict
    # Live financial snapshot {name, cash, burn, runway, mrr, arr, last_updated}
    
    session_id: str
    # Unique session identifier for multi-turn conversations
    
    tool_error_count: int
    # Safety counter: stop reasoning if >= 3


def build_llm(thinking: bool = False):
    """
    Build language model with appropriate configuration.
    
    Args:
        thinking: If True, use qwq-32b (expensive, thorough reasoning).
                 If False, use qwen2-32b (fast, cost-effective).
    
    Returns:
        ChatGroq instance with tools bound
    """
    if thinking:
        model = "qwq-32b"
        logger.info("[BUILD_LLM] Using qwq-32b (thinking mode for complex queries)")
    else:
        model = "qwen2-32b"
        logger.info("[BUILD_LLM] Using qwen2-32b (fast mode for simple/alert queries)")
    
    llm = ChatGroq(
        model=model,
        temperature=0,
        api_key=Settings.GROQ_API_KEY,
    )
    
    # Bind all available tools to LLM
    tools = get_all_tools()
    llm_with_tools = llm.bind_tools(tools)
    
    logger.info(f"[BUILD_LLM] LLM compiled with {len(tools)} tools")
    return llm_with_tools


# ============================================================================
# NODES
# ============================================================================

def classify_node(state: AgentState) -> dict:
    """
    Classify query type from the last user message.
    
    Uses keyword pre-filtering + fallback to Groq classifier.
    Updates state["query_type"] for downstream routing.
    
    Args:
        state: Current agent state
    
    Returns:
        {"query_type": str} - Updated state
    """
    # Extract last user message
    last_user_message = None
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            last_user_message = msg.content
            break
    
    if not last_user_message:
        logger.warning("[CLASSIFY] No user message found in state")
        return {"query_type": "simple"}
    
    # Classify using routing module
    query_type = classify_query(last_user_message)
    logger.info(f"[CLASSIFY] '{last_user_message[:50]}...' → {query_type}")
    
    return {"query_type": query_type}


def agent_node(state: AgentState) -> dict:
    """
    Run LLM with tools to generate reasoning and plan tool calls.
    
    Key steps:
    1. Decide thinking mode based on query_type
    2. Build LLM with appropriate model
    3. Prepend fresh CFO system prompt
    4. Invoke LLM
    5. Append AI response to messages
    
    Args:
        state: Current agent state
    
    Returns:
        {"messages": [AIMessage]} - Appended to state.messages
    """
    # Step 1: Determine reasoning depth
    use_thinking = should_use_thinking_mode(state["query_type"])
    logger.info(f"[AGENT] Query type '{state['query_type']}' → thinking_mode={use_thinking}")
    
    # Step 2: Build LLM
    llm_with_tools = build_llm(thinking=use_thinking)
    
    # Step 3: Build system prompt with fresh company context
    system_prompt = build_cfo_system_prompt(state["company_context"])
    logger.info(f"[AGENT] System prompt built ({len(system_prompt)} chars)")
    
    # Step 4: Prepare full message history with system prompt
    messages = [SystemMessage(content=system_prompt)] + state["messages"]
    logger.info(f"[AGENT] Invoking LLM with {len(state['messages'])} messages + system prompt")
    
    # Step 5: Invoke LLM
    ai_response = llm_with_tools.invoke(messages)
    
    # Log tool call info
    tool_calls = getattr(ai_response, 'tool_calls', [])
    logger.info(f"[AGENT] LLM response: {len(ai_response.content) if isinstance(ai_response.content, str) else 'non-string'} response + {len(tool_calls)} tool calls")
    
    return {"messages": [ai_response]}


def should_continue(state: AgentState) -> Literal["tools", "END"]:
    """
    Conditional edge: determine if we should call tools or END.
    
    Checks if the last AI message contains tool calls.
    
    Args:
        state: Current agent state
    
    Returns:
        "tools" if tool calls present, else "END"
    """
    last_message = state["messages"][-1]
    
    if isinstance(last_message, AIMessage) and getattr(last_message, 'tool_calls', None):
        logger.info(f"[ROUTE] AI message has {len(last_message.tool_calls)} tool calls → tools_node")
        return "tools"
    else:
        logger.info(f"[ROUTE] No tool calls in AI message → END")
        return "END"


def safety_node(state: AgentState) -> dict:
    """
    Check for tool errors and enforce safety limits.
    
    Increments error counter if ToolMessage contains error dict.
    If counter >= 3, injects HumanMessage to stop agent.
    
    Args:
        state: Current agent state
    
    Returns:
        {"tool_error_count": int[, "messages": [HumanMessage]]}
    """
    # Find last ToolMessage and check for errors
    error_found = False
    for msg in reversed(state["messages"]):
        if isinstance(msg, ToolMessage):
            # Check if tool returned an error
            if isinstance(msg.content, dict) and "error" in msg.content:
                error_found = True
                logger.warning(f"[SAFETY] Tool error detected: {msg.content.get('error', 'unknown')}")
                break
            # Also check string content
            elif isinstance(msg.content, str) and "error" in msg.content.lower():
                error_found = True
                logger.warning(f"[SAFETY] Tool error in response: {msg.content[:100]}")
                break
    
    # Update error count
    new_error_count = state.get("tool_error_count", 0)
    updates = {}
    
    if error_found:
        new_error_count += 1
        logger.warning(f"[SAFETY] Tool error count: {new_error_count}/3")
        
        # If too many errors, tell agent to stop and use available data
        if new_error_count >= 3:
            logger.error("[SAFETY] Max tool errors reached (3+). Stopping tool execution.")
            stop_message = HumanMessage(
                content=(
                    "I've encountered too many errors trying to retrieve live data. "
                    "Please provide your best financial analysis using the context "
                    "and information we currently have, and flag which data points you couldn't verify."
                )
            )
            updates["messages"] = [stop_message]
    
    updates["tool_error_count"] = new_error_count
    return updates


def should_continue_from_tools(state: AgentState) -> Literal["agent", "END"]:
    """
    Conditional edge after tool execution: loop back or END.
    
    If too many errors occurred, END the agent.
    Otherwise, loop back to agent_node for continued reasoning.
    
    Args:
        state: Current agent state
    
    Returns:
        "agent" to continue reasoning, or "END" to stop
    """
    if state.get("tool_error_count", 0) >= 3:
        logger.info(f"[ROUTE] Too many tool errors → END")
        return "END"
    else:
        logger.info(f"[ROUTE] Tools executed successfully → agent (loop back)")
        return "agent"


# ============================================================================
# GRAPH BUILDING
# ============================================================================

def build_graph():
    """
    Build and compile the CFO agent StateGraph.
    
    Defines:
    - 4 nodes: classify → agent → tools → safety
    - Conditional edges for tool calls and error handling
    - Persistent checkpointer for session memory
    
    Returns:
        Compiled StateGraph ready to invoke
    """
    # Get persistent checkpointer
    checkpointer = get_checkpointer()
    logger.info("[BUILD_GRAPH] Checkpointer initialized")
    
    # Create state graph
    graph = StateGraph(AgentState)
    
    # Add nodes
    graph.add_node("classify", classify_node)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(get_all_tools()))
    graph.add_node("safety", safety_node)
    
    logger.info("[BUILD_GRAPH] 4 nodes added: classify, agent, tools, safety")
    
    # Add edges
    graph.add_edge(START, "classify")
    graph.add_edge("classify", "agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", "END": END})
    graph.add_edge("tools", "safety")
    graph.add_conditional_edges("safety", should_continue_from_tools, {"agent": "agent", "END": END})
    
    logger.info("[BUILD_GRAPH] Edges configured with conditionals")
    
    # Compile with checkpointer
    compiled_graph = graph.compile(checkpointer=checkpointer)
    logger.info("[BUILD_GRAPH] Graph compiled with persistent checkpointer")
    
    return compiled_graph


# ============================================================================
# PUBLIC INTERFACE
# ============================================================================

def run_cfo_query(
    user_message: str,
    session_id: str = None,
    company_context: dict = None
) -> str:
    """
    Main entry point for the CFO agent.
    
    Runs a complete query through the agent graph:
    1. Classify query type
    2. Invoke LLM with appropriate model
    3. Execute tools if needed
    4. Apply safety guardrails
    5. Return final response
    
    For multi-turn conversations, use same session_id to maintain
    conversation history in persistent storage.
    
    Args:
        user_message: Query from founder/user
        session_id: Existing session ID for multi-turn (creates new if None)
        company_context: Existing financial context (fetches fresh if None)
    
    Returns:
        CFO's response as string
    
    Raises:
        ValueError: If user_message is empty
        RuntimeError: If graph execution fails
    """
    if not user_message or not user_message.strip():
        raise ValueError("user_message cannot be empty")
    
    # Generate or retrieve session
    if session_id is None:
        session_id = new_session_id()
        logger.info(f"[RUN] Created new session: {session_id}")
    else:
        logger.info(f"[RUN] Using existing session: {session_id}")
    
    # Get fresh company context if not provided
    if company_context is None:
        company_context = get_company_context()
        logger.info(f"[RUN] Fresh company context loaded")
    
    # Build graph and config
    graph = build_graph()
    config = build_config(session_id)
    logger.info(f"[RUN] Graph and config prepared")
    
    # Initialize agent state
    initial_state = {
        "messages": [HumanMessage(content=user_message)],
        "query_type": "simple",  # Will be updated in classify_node
        "company_context": company_context,
        "session_id": session_id,
        "tool_error_count": 0,
    }
    
    logger.info(f"[RUN] Starting agent with query: '{user_message[:60]}...'")
    
    # Invoke graph
    try:
        result = graph.invoke(initial_state, config=config)
    except Exception as e:
        logger.error(f"[RUN] Graph execution failed: {e}", exc_info=True)
        raise RuntimeError(f"Agent graph execution failed: {e}")
    
    # Extract final AI response
    logger.info(f"[RUN] Graph completed. Processing {len(result['messages'])} final messages")
    
    for msg in reversed(result["messages"]):
        if isinstance(msg, AIMessage):
            # Ensure content is a string (not a list of content blocks)
            if isinstance(msg.content, str) and msg.content.strip():
                logger.info(f"[RUN] Extracted AI response ({len(msg.content)} chars)")
                return msg.content
    
    # Fallback if no suitable response found
    logger.warning("[RUN] No suitable AI response found in result messages")
    return "I was unable to process that query. Please try again."


# ============================================================================
# CLI TEST RUNNER
# ============================================================================

if __name__ == "__main__":
    """Interactive CLI test of the CFO agent."""
    
    # Configure logging for CLI
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)-8s | %(name)s | %(message)s"
    )
    
    print("\n" + "=" * 70)
    print("CFO AGENT - CLI TEST RUNNER")
    print("=" * 70)
    
    # Test queries
    test_queries = [
        "What is our current cash balance and runway?",
        "What happens if we hire 2 engineers at $130,000 salary?",
        "Why did our expenses increase last month?",
        "Give me a full financial health overview."
    ]
    
    # Create persistent session
    session = new_session_id()
    print(f"\nSession ID: {session}")
    print("(Multi-turn messages will share this session)")
    print("-" * 70)
    
    # Run test queries
    for i, query in enumerate(test_queries, 1):
        print(f"\n[{i}/{len(test_queries)}] FOUNDER: {query}")
        print("-" * 70)
        
        try:
            response = run_cfo_query(query, session_id=session)
            print(f"CFO: {response}")
        except Exception as e:
            print(f"ERROR: {e}")
            logger.error(f"Query execution failed", exc_info=True)
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70 + "\n")
