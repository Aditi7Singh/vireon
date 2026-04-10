"""
LangGraph Strategist Agent
===========================
Multi-step scenario-planning agent powered by the Deterministic Math Engine.

Example query:
  "What happens to our runway if we hire 5 engineers in Dubai and lose our
   biggest SaaS client next quarter?"

Workflow:
  1. parse_scenario_tool  — extract structured parameters from the natural language query
  2. get_financial_baseline — fetch current cash/burn/revenue snapshot
  3. run_scenario_tool    — call MathEngine.run_scenario() with structured inputs
  4. LLM summarises       — narrative insights, never re-doing the math

The LLM NEVER computes numbers itself; it only interprets MathEngine output.
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import asdict
from typing import Annotated, Any, Dict, List, Literal, Optional, TypedDict

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_core.tools import tool
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

from config.settings import get_llm
from services.math_engine import (
    CostEvent,
    HireEvent,
    MathEngine,
    RevenueEvent,
    ScenarioInput,
    fully_loaded_cost_per_month,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Agent State
# ---------------------------------------------------------------------------


class StrategistState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    company_id: Optional[str]
    session_id: str
    scenario_inputs: Optional[Dict]     # serialised ScenarioInput
    scenario_result: Optional[Dict]     # serialised ScenarioResult


# ---------------------------------------------------------------------------
# Tools (deterministic — no LLM math)
# ---------------------------------------------------------------------------


@tool
def get_financial_baseline(company_id: str) -> str:
    """
    Fetch the current financial baseline for a company.
    Returns JSON with: current_cash_usd, current_monthly_revenue_usd,
    current_monthly_burn_usd, runway_months.
    """
    # In production, query models.MonthlyMetric from the database.
    # Demo baseline representing a Series-A SaaS company.
    baseline = {
        "company_id": company_id,
        "current_cash_usd": 4_200_000,
        "current_monthly_revenue_usd": 380_000,
        "current_monthly_burn_usd": 620_000,
        "runway_months": 18.0,
        "headcount": 42,
        "source": "latest_monthly_metric",
    }
    return json.dumps(baseline)


@tool
def get_payroll_tax_data(location: str) -> str:
    """
    Fetch payroll tax / employer-cost data for a given location.
    Returns JSON with: overhead_multiplier, monthly_extras_usd (rough estimate),
    notes.
    """
    data = {
        "US":    {"overhead_multiplier": 1.35, "notes": "FICA 7.65% + benefits + equity"},
        "Dubai": {"overhead_multiplier": 1.15, "notes": "No income tax; visa + housing + insurance"},
        "India": {"overhead_multiplier": 1.25, "notes": "PF 12% + gratuity + benefits"},
        "UK":    {"overhead_multiplier": 1.30, "notes": "NI employer 13.8% + pension + benefits"},
        "EU":    {"overhead_multiplier": 1.40, "notes": "High employer social security contributions"},
        "Canada":{"overhead_multiplier": 1.32, "notes": "CPP + EI + benefits"},
        "Singapore": {"overhead_multiplier": 1.20, "notes": "CPF 17% employer + benefits"},
    }
    loc_title = location.strip().title()
    payload = data.get(loc_title, {"overhead_multiplier": 1.30, "notes": "Default estimate"})
    payload["location"] = loc_title
    return json.dumps(payload)


@tool
def run_scenario_calculation(scenario_json: str) -> str:
    """
    Run the Deterministic Math Engine with the provided scenario configuration.

    scenario_json must be a JSON object with keys:
      current_cash_usd, current_monthly_revenue_usd, current_monthly_burn_usd,
      simulation_months (optional, default 12),
      hires: [{role, count, base_salary_usd, location, start_month}],
      revenue_events: [{description, monthly_delta_usd, start_month}],
      cost_events: [{description, monthly_delta_usd, start_month, one_time}]

    Returns the full ScenarioResult as JSON including monthly projections and key_insights.
    IMPORTANT: Use the numbers in this output directly. Do NOT re-calculate.
    """
    try:
        data = json.loads(scenario_json)
    except json.JSONDecodeError as e:
        return json.dumps({"error": f"Invalid JSON: {e}"})

    try:
        hires = [HireEvent(**h) for h in data.get("hires", [])]
        rev_events = [RevenueEvent(**r) for r in data.get("revenue_events", [])]
        cost_events = [CostEvent(**c) for c in data.get("cost_events", [])]

        inputs = ScenarioInput(
            current_cash_usd=float(data["current_cash_usd"]),
            current_monthly_revenue_usd=float(data["current_monthly_revenue_usd"]),
            current_monthly_burn_usd=float(data["current_monthly_burn_usd"]),
            simulation_months=int(data.get("simulation_months", 12)),
            hires=hires,
            revenue_events=rev_events,
            cost_events=cost_events,
            base_revenue_growth_rate=float(data.get("base_revenue_growth_rate", 0.0)),
        )

        result = MathEngine.run_scenario(inputs)

        # Serialise to dict (dataclasses → dicts)
        result_dict = {
            "baseline_runway_months": result.baseline_runway_months,
            "scenario_runway_months": result.scenario_runway_months,
            "runway_delta_months": result.runway_delta_months,
            "baseline_eom_cash": result.baseline_eom_cash,
            "scenario_eom_cash": result.scenario_eom_cash,
            "total_incremental_headcount_cost": result.total_incremental_headcount_cost,
            "total_incremental_revenue_impact": result.total_incremental_revenue_impact,
            "total_one_time_costs": result.total_one_time_costs,
            "zero_cash_month": result.zero_cash_month,
            "break_even_month": result.break_even_month,
            "key_insights": result.key_insights,
            "monthly_projections": [
                {
                    "month": p.month,
                    "revenue": p.revenue,
                    "burn": p.burn,
                    "net_cash_flow": p.net_cash_flow,
                    "cumulative_cash": p.cumulative_cash,
                }
                for p in result.monthly_projections
            ],
        }
        return json.dumps(result_dict, default=str)

    except Exception as exc:
        logger.error("Math Engine error: %s", exc, exc_info=True)
        return json.dumps({"error": str(exc)})


STRATEGIST_TOOLS = [
    get_financial_baseline,
    get_payroll_tax_data,
    run_scenario_calculation,
]


# ---------------------------------------------------------------------------
# System Prompt
# ---------------------------------------------------------------------------


_STRATEGIST_SYSTEM_PROMPT = """
You are Vireon's Strategist Agent — an autonomous financial scenario planner.

Your role is to answer complex "what-if" questions about runway, cash, and growth.

STRICT RULES:
1. You MUST use get_financial_baseline to get the current financial snapshot before building a scenario.
2. You MUST use get_payroll_tax_data for ANY hire scenario involving a specific location.
3. You MUST call run_scenario_calculation with the fully constructed scenario JSON.
4. You MUST cite numbers ONLY from the tool outputs. NEVER compute numbers yourself.
5. Present results in a structured format:
   - Executive Summary (2-3 sentences)
   - Runway Impact
   - Cost Breakdown
   - Key Risks
   - Recommended Actions

When constructing the scenario JSON for run_scenario_calculation:
- Use the baseline numbers from get_financial_baseline.
- Hires: use base salary from context (default $120,000/year if not specified).
- Revenue events: convert "lose biggest client" → estimate as 20% MRR drop unless specified.
- simulation_months: default to 12 unless the user specifies a different horizon.

Remember: your value is INTERPRETATION and STRATEGY, not arithmetic.
"""


# ---------------------------------------------------------------------------
# Agent Nodes
# ---------------------------------------------------------------------------


def strategist_agent_node(state: StrategistState) -> StrategistState:
    llm = get_llm(thinking=True)
    llm_with_tools = llm.bind_tools(STRATEGIST_TOOLS)
    system_msg = SystemMessage(content=_STRATEGIST_SYSTEM_PROMPT)
    response = llm_with_tools.invoke([system_msg] + state["messages"])
    return {"messages": [response]}


def strategist_tools_node(state: StrategistState) -> StrategistState:
    from langgraph.prebuilt import ToolNode
    executor = ToolNode(STRATEGIST_TOOLS)
    result = executor.invoke(state)
    msgs = result if isinstance(result, list) else result.get("messages", [])
    return {"messages": msgs}


def should_continue_strategist(
    state: StrategistState,
) -> Literal["strategist_tools", "end"]:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "strategist_tools"
    return "end"


# ---------------------------------------------------------------------------
# Graph Builder
# ---------------------------------------------------------------------------


def build_strategist_graph():
    graph = StateGraph(StrategistState)
    graph.add_node("strategist_agent", strategist_agent_node)
    graph.add_node("strategist_tools", strategist_tools_node)
    graph.set_entry_point("strategist_agent")
    graph.add_conditional_edges(
        "strategist_agent",
        should_continue_strategist,
        {"strategist_tools": "strategist_tools", "end": END},
    )
    graph.add_edge("strategist_tools", "strategist_agent")
    return graph.compile()


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def run_scenario_query(
    user_query: str,
    company_id: str,
    session_id: Optional[str] = None,
) -> str:
    """
    Run a financial scenario planning query through the Strategist Agent.

    Args:
        user_query:  The natural language scenario question.
        company_id:  Company UUID string.
        session_id:  Optional session identifier.

    Returns:
        Narrative scenario analysis as a string.
    """
    if not session_id:
        session_id = f"strategist-{uuid.uuid4().hex[:8]}"

    graph = build_strategist_graph()

    enriched_query = (
        f"{user_query}\n\n"
        f"[Context: Company ID = {company_id}. "
        f"Please start by fetching the financial baseline for this company, "
        f"then run the scenario calculation, and provide a strategic summary.]"
    )

    initial_state: StrategistState = {
        "messages": [HumanMessage(content=enriched_query)],
        "company_id": company_id,
        "session_id": session_id,
        "scenario_inputs": None,
        "scenario_result": None,
    }

    try:
        result = graph.invoke(initial_state)
        msgs = result.get("messages", []) if isinstance(result, dict) else result
        for msg in reversed(msgs):
            if isinstance(msg, AIMessage) and msg.content:
                return msg.content
        return "Scenario analysis complete but no summary was generated."
    except Exception as exc:
        logger.error("Strategist agent error: %s", exc, exc_info=True)
        return f"Scenario analysis failed: {exc}"
