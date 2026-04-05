"""
Finance Agent
=============
Daily operational finance agent for invoices, payments, collections, reconciliation, and tax prep.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Optional, TypedDict, Literal, Dict

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from agent.memory import (
    build_config,
    get_checkpointer,
    load_session_messages,
    new_session_id,
    persist_session_turn,
    persist_tool_audit,
)
from agent.prompts import build_finance_operating_system_prompt
from agent.routing import classify_query, should_use_thinking_mode
from agent.tools import (
    FINANCE_OPERATIONS_TOOLS,
    clear_active_company_context,
    set_active_company_context,
)
from config.company_profile import get_company_context
from config.settings import get_llm


class FinanceOpsState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    query_type: str
    company_context: dict
    session_id: str
    company_id: Optional[str]
    chain_id: str
    tool_error_count: int


def classify_node(state: FinanceOpsState) -> FinanceOpsState:
    last_message = state["messages"][-1].content if state["messages"] else ""
    return {
        "query_type": classify_query(last_message),
        "chain_id": state.get("chain_id")
        or f"{state.get('session_id', 'session')}-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
    }


def agent_node(state: FinanceOpsState) -> FinanceOpsState:
    llm = get_llm(thinking=should_use_thinking_mode(state["query_type"]))
    system_message = SystemMessage(content=build_finance_operating_system_prompt(state["company_context"]))
    all_messages = [system_message] + state["messages"]
    response = llm.bind_tools(FINANCE_OPERATIONS_TOOLS).invoke(all_messages[-15:])
    return {"messages": [response]}


def tools_node(state: FinanceOpsState) -> FinanceOpsState:
    result = ToolNode(FINANCE_OPERATIONS_TOOLS).invoke(state)
    msgs = result if isinstance(result, list) else result.get("messages", [])

    error_count = 0
    for msg in msgs:
        if isinstance(msg, ToolMessage) and "error" in str(msg.content or "").lower():
            error_count += 1

    tool_calls = []
    last_message = state["messages"][-1] if state.get("messages") else None
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        tool_calls = last_message.tool_calls

    for idx, msg in enumerate(msgs):
        if idx < len(tool_calls):
            call = tool_calls[idx]
            persist_tool_audit(
                state.get("session_id", ""),
                getattr(msg, "name", call.get("name", "unknown")),
                call.get("args", {}) if isinstance(call, dict) else {},
                getattr(msg, "content", None),
                company_id=state.get("company_id"),
                chain_id=state.get("chain_id"),
                status="error" if "error" in str(getattr(msg, "content", "")).lower() else "ok",
            )

    return {
        "messages": msgs,
        "tool_error_count": state.get("tool_error_count", 0) + error_count,
        "chain_id": state.get("chain_id", ""),
    }


def should_continue_tools(state: FinanceOpsState) -> Literal["tools", "end"]:
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return "end"


def should_retry_after_tools(state: FinanceOpsState) -> Literal["agent", "end"]:
    if state.get("tool_error_count", 0) >= 3:
        return "end"
    return "agent"


def build_graph():
    graph = StateGraph(FinanceOpsState)
    graph.add_node("classify", classify_node)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tools_node)
    graph.set_entry_point("classify")
    graph.add_edge("classify", "agent")
    graph.add_conditional_edges("agent", should_continue_tools, {"tools": "tools", "end": END})
    graph.add_conditional_edges("tools", should_retry_after_tools, {"agent": "agent", "end": END})
    return graph.compile(checkpointer=get_checkpointer())


def run_finance_query(
    user_message: str,
    session_id: Optional[str] = None,
    company_context: Optional[Dict] = None,
    company_id: Optional[str] = None,
    conversation_context: Optional[str] = None,
) -> str:
    if session_id is None:
        session_id = new_session_id()
    if company_context is None:
        company_context = get_company_context()
    if company_id is None and isinstance(company_context, dict):
        company_id = company_context.get("company_id")

    if conversation_context:
        company_context = dict(company_context or {})
        company_context["conversation_context"] = conversation_context

    set_active_company_context(company_id=company_id)

    state = {
        "messages": load_session_messages(session_id) + [HumanMessage(content=user_message)],
        "query_type": "simple",
        "company_context": company_context,
        "session_id": session_id,
        "company_id": company_id,
        "chain_id": f"{session_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
        "tool_error_count": 0,
    }

    try:
        result = build_graph().invoke(state, config=build_config(session_id))
        msgs = result.get("messages", []) if isinstance(result, dict) else result
        for msg in reversed(msgs):
            if isinstance(msg, AIMessage) and msg.content:
                persist_session_turn(
                    session_id,
                    user_message,
                    msg.content,
                    company_id=company_id,
                    summary=msg.content[:500],
                    chain_id=state["chain_id"],
                    query_type=state["query_type"],
                )
                return msg.content
        return "I was unable to process that finance operations request."
    except Exception as exc:
        return f"I encountered an error processing your finance operations request: {exc}"
    finally:
        clear_active_company_context()
