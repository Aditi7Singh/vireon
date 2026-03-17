"""
LangGraph CFO Agent
================
Main LangGraph StateGraph for the AI CFO agent.
"""

from typing import TypedDict, Annotated, Literal
from datetime import datetime
import json
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages

from config.settings import get_llm, USE_LOCAL_LLM, GROQ_MODEL_FAST
from config.company_profile import get_company_context
from agent.tools import ALL_TOOLS
from agent.prompts import build_cfo_system_prompt
from agent.routing import classify_query, should_use_thinking_mode
from agent.memory import get_checkpointer, build_config, new_session_id


# Define the agent state
class AgentState(TypedDict):
    """State schema for the LangGraph agent."""
    messages: Annotated[list[BaseMessage], add_messages]  # Full conversation history
    query_type: str  # "simple" | "complex" | "alert"
    company_context: dict  # Live financial snapshot
    session_id: str
    tool_error_count: int  # Safety: stop if tools fail 3+ times


# Node functions
def classify_node(state: AgentState) -> AgentState:
    """
    Classify the user query to determine routing.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with query_type
    """
    last_message = state["messages"][-1].content if state["messages"] else ""
    query_type = classify_query(last_message)
    print(f"[AGENT] Query classified as: {query_type}")
    return {"query_type": query_type}


def agent_node(state: AgentState) -> AgentState:
    """
    Run the LLM with tools to generate a response.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with AI response message
    """
    # Decide which model to use based on query type
    thinking = should_use_thinking_mode(state["query_type"])
    use_thinking = USE_LOCAL_LLM or thinking
    
    print(f"[AGENT] Using {'thinking' if use_thinking else 'fast'} mode")
    llm = get_llm(thinking=use_thinking)
    
    # Build system prompt with fresh company context
    system_prompt = build_cfo_system_prompt(state["company_context"])
    system_message = SystemMessage(content=system_prompt)
    
    # Get all messages and prepend system prompt
    all_messages = [system_message] + state["messages"]
    
    # Bind tools to the LLM
    llm_with_tools = llm.bind_tools(ALL_TOOLS)
    
    # Invoke the LLM
    # Prune memory to keep context window clean
    current_messages = prune_memory(all_messages)
    
    response = llm_with_tools.invoke(current_messages)
    
    return {"messages": [response]}


def tools_node(state: AgentState) -> AgentState:
    """
    Execute tool calls from the LLM response.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with tool results
    """
    tool_executor = ToolNode(ALL_TOOLS)
    result = tool_executor.invoke(state)
    
    # ToolNode might return a list of messages or a dict with "messages"
    msgs = result if isinstance(result, list) else result.get("messages", [])
    
    # Check for errors
    error_count = 0
    for msg in msgs:
        if isinstance(msg, ToolMessage) and "error" in str(msg.content or "").lower():
            error_count += 1
    
    new_error_count = state.get("tool_error_count", 0) + error_count
    
    return {
        "messages": msgs,
        "tool_error_count": new_error_count
    }


def analyze_node(state: AgentState) -> AgentState:
    """
    Reasoning step: Analyze tool results before generating final response.
    """
    last_msg = state["messages"][-1]
    if not isinstance(last_msg, ToolMessage):
        return state
        
    print(f"[AGENT] Analyzing tool output for reasoning...")
    
    # We can inject a hidden reasoning prompt if needed, 
    # but for now we'll let the next agent_node handle it
    return state

def prune_memory(messages: list[BaseMessage], max_messages: int = 15) -> list[BaseMessage]:
    """Prune old messages while keeping the system prompt and latest context."""
    if len(messages) <= max_messages:
        return messages
    
    # Keep the first message (usually system/initial) and the last N-1
    return [messages[0]] + messages[-(max_messages-1):]

def safety_node(state: AgentState) -> AgentState:
    """
    Guardrail check after tool execution.
    If tools failed 3+ times, inject a message to stop the agent.
    """
    if state.get("tool_error_count", 0) >= 3:
        print(f"[AGENT] Safety: {state['tool_error_count']} tool errors, stopping")
        error_message = HumanMessage(
            content="I've encountered multiple errors retrieving data. "
                   "Please check the backend connection and try again."
        )
        return {"messages": [error_message]}
    
    return state


def should_continue_tools(state: AgentState) -> Literal["agent_node", "end"]:
    """
    Determine whether to continue to tools or end.
    
    Args:
        state: Current agent state
        
    Returns:
        Next step: "agent_node" or "end"
    """
    last_message = state["messages"][-1]
    
    # If last message has tool calls, go to tools
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools_node"
    
    return "end"


def should_retry_after_tools(state: AgentState) -> Literal["agent_node", "end"]:
    """
    Determine whether to retry after tool execution or end.
    
    Args:
        state: Current agent state
        
    Returns:
        Next step: "agent_node" or "end"
    """
    # If too many errors, stop
    if state.get("tool_error_count", 0) >= 3:
        return "end"
    
    # Otherwise, continue to generate final response
    return "agent_node"


def build_graph():
    """
    Build and compile the LangGraph StateGraph.
    
    Returns:
        Compiled LangGraph application
    """
    checkpointer = get_checkpointer()
    
    graph = StateGraph(AgentState)
    
    # Add nodes
    graph.add_node("classify", classify_node)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tools_node)
    graph.add_node("safety", safety_node)
    graph.add_node("analyze", analyze_node)
    
    # Set entry point
    graph.set_entry_point("classify")
    
    # Add edges
    graph.add_edge("classify", "agent")
    graph.add_conditional_edges(
        "agent",
        should_continue_tools,
        {
            "tools_node": "tools",
            "end": END
        }
    )
    graph.add_edge("tools", "safety")
    graph.add_conditional_edges(
        "safety",
        should_retry_after_tools,
        {
            "agent_node": "analyze",
            "end": END
        }
    )
    graph.add_edge("analyze", "agent")
    
    return graph.compile(checkpointer=checkpointer)


def run_cfo_query(
    user_message: str,
    session_id: str = None,
    company_context: dict = None
) -> str:
    """
    Main entry point to run a CFO query.
    
    Args:
        user_message: The user's question
        session_id: Optional session ID (generates new if missing)
        company_context: Optional company context (fetches fresh if missing)
        
    Returns:
        CFO response as a string
    """
    if session_id is None:
        session_id = new_session_id()
    if company_context is None:
        company_context = get_company_context()
    
    graph = build_graph()
    config = build_config(session_id)
    
    initial_state = {
        "messages": [HumanMessage(content=user_message)],
        "query_type": "simple",
        "company_context": company_context,
        "session_id": session_id,
        "tool_error_count": 0,
    }
    
    try:
        result = graph.invoke(initial_state, config=config)
        
        # Extract last AI message content
        # LangGraph invoke returns the final state (dict)
        msgs = result.get("messages", []) if isinstance(result, dict) else result
        
        for msg in reversed(msgs):
            if isinstance(msg, AIMessage) and msg.content:
                return msg.content
        
        return "I was unable to process that query. Please try again."
    
    except Exception as e:
        print(f"[AGENT] Error: {e}")
        return f"I encountered an error processing your request: {str(e)}"


# CLI test runner
if __name__ == "__main__":
    test_queries = [
        "What is our current cash balance and runway?",
        "What happens if we hire 2 engineers at $130,000 salary?",
        "Why did our expenses increase last month?",
        "Give me a full financial health overview."
    ]
    
    session = new_session_id()
    print(f"\n{'='*60}")
    print(f"Starting CFO Agent Session: {session}")
    print(f"{'='*60}\n")
    
    for q in test_queries:
        print(f"\nFOUNDER: {q}")
        print(f"CFO: {run_cfo_query(q, session_id=session)}")
        print(f"\n{'-'*60}")
