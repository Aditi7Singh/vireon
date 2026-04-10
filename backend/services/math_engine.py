"""
Deterministic Math Engine
=========================
All financial scenario calculations are performed here using pure arithmetic
and NumPy/Pandas — never inside the LLM — preventing hallucinations.

Usage (called by the Strategist Agent):

    result = MathEngine.run_scenario(ScenarioInput(...))

The engine returns a fully deterministic ScenarioResult that the agent
then summarises in natural language.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data classes (inputs / outputs)
# ---------------------------------------------------------------------------


@dataclass
class HireEvent:
    """Represents a planned hire."""
    role: str
    count: int
    base_salary_usd: float
    location: str = "US"  # "US" | "Dubai" | "India" | "UK" | …
    start_month: int = 1   # 1-based month within the simulation


@dataclass
class RevenueEvent:
    """Represents a revenue change event."""
    description: str
    monthly_delta_usd: float   # negative = revenue loss
    start_month: int = 1


@dataclass
class CostEvent:
    """One-time or recurring cost event."""
    description: str
    monthly_delta_usd: float
    start_month: int = 1
    one_time: bool = False


@dataclass
class ScenarioInput:
    """Complete scenario specification for the Math Engine."""
    # Current baseline (latest monthly snapshot)
    current_cash_usd: float
    current_monthly_revenue_usd: float
    current_monthly_burn_usd: float

    # Horizon
    simulation_months: int = 12

    # Events
    hires: List[HireEvent] = field(default_factory=list)
    revenue_events: List[RevenueEvent] = field(default_factory=list)
    cost_events: List[CostEvent] = field(default_factory=list)

    # Optional override growth rate for base revenue (e.g. 0.05 = 5 %/mo)
    base_revenue_growth_rate: float = 0.0


@dataclass
class MonthlyProjection:
    month: int
    revenue: float
    burn: float
    net_cash_flow: float
    cumulative_cash: float


@dataclass
class ScenarioResult:
    baseline_runway_months: float
    scenario_runway_months: float
    runway_delta_months: float

    baseline_eom_cash: float
    scenario_eom_cash: float

    monthly_projections: List[MonthlyProjection]

    total_incremental_headcount_cost: float
    total_incremental_revenue_impact: float
    total_one_time_costs: float

    key_insights: List[str]
    zero_cash_month: Optional[int]          # None if cash stays positive
    break_even_month: Optional[int]         # None if never reached


# ---------------------------------------------------------------------------
# Location-based tax / overhead multipliers
# Fully-loaded cost = base_salary * multiplier
# ---------------------------------------------------------------------------

_OVERHEAD_MULTIPLIER: Dict[str, float] = {
    "US":     1.35,   # payroll tax + benefits + equity
    "UK":     1.30,
    "Dubai":  1.15,   # low personal tax, but housing, visa, insurance
    "India":  1.25,
    "Canada": 1.32,
    "EU":     1.40,   # high employer contributions
    "Singapore": 1.20,
    "Remote": 1.25,
}

_DEFAULT_MULTIPLIER = 1.30


def fully_loaded_cost_per_month(hire: HireEvent) -> float:
    """
    Return the fully-loaded monthly cost for a single headcount in this role/location.

    Annual salary → monthly → × overhead multiplier → × headcount.
    """
    multiplier = _OVERHEAD_MULTIPLIER.get(hire.location.strip().title(), _DEFAULT_MULTIPLIER)
    annual_fl = hire.base_salary_usd * multiplier
    monthly_fl = annual_fl / 12.0
    return monthly_fl * hire.count


# ---------------------------------------------------------------------------
# Core Simulation Loop
# ---------------------------------------------------------------------------


class MathEngine:
    """
    Deterministic financial scenario simulator.

    No randomness. No LLM.  All arithmetic — verifiable and reproducible.
    """

    @staticmethod
    def run_scenario(inputs: ScenarioInput) -> ScenarioResult:
        """Simulate the financial scenario month-by-month."""
        months = inputs.simulation_months

        # ── baseline: constant burn, constant revenue (or with growth) ──────
        baseline_runway = MathEngine._calculate_runway(
            inputs.current_cash_usd,
            inputs.current_monthly_revenue_usd,
            inputs.current_monthly_burn_usd,
        )

        # ── scenario projection ──────────────────────────────────────────────
        cash = inputs.current_cash_usd
        revenue = inputs.current_monthly_revenue_usd
        burn = inputs.current_monthly_burn_usd

        projections: List[MonthlyProjection] = []
        zero_cash_month: Optional[int] = None
        break_even_month: Optional[int] = None

        total_hc_cost = 0.0
        total_rev_impact = 0.0
        total_one_time = 0.0

        for m in range(1, months + 1):
            # ── apply revenue events ─────────────────────────────────────
            for ev in inputs.revenue_events:
                if ev.start_month == m:
                    revenue += ev.monthly_delta_usd
                    total_rev_impact += ev.monthly_delta_usd * (months - m + 1)

            # ── apply hire events ────────────────────────────────────────
            for hire in inputs.hires:
                if hire.start_month == m:
                    extra_monthly_cost = fully_loaded_cost_per_month(hire)
                    burn += extra_monthly_cost
                    total_hc_cost += extra_monthly_cost * (months - m + 1)

            # ── apply one-time / recurring cost events ───────────────────
            for ce in inputs.cost_events:
                if ce.start_month == m:
                    if ce.one_time:
                        cash -= ce.monthly_delta_usd
                        total_one_time += ce.monthly_delta_usd
                    else:
                        burn += ce.monthly_delta_usd

            # ── apply base revenue growth ────────────────────────────────
            revenue *= 1.0 + inputs.base_revenue_growth_rate

            # ── net cash flow ─────────────────────────────────────────────
            net = revenue - burn
            cash += net

            proj = MonthlyProjection(
                month=m,
                revenue=round(revenue, 2),
                burn=round(burn, 2),
                net_cash_flow=round(net, 2),
                cumulative_cash=round(cash, 2),
            )
            projections.append(proj)

            if cash <= 0 and zero_cash_month is None:
                zero_cash_month = m

            if net >= 0 and break_even_month is None:
                break_even_month = m

        # ── scenario runway ──────────────────────────────────────────────────
        scenario_runway = MathEngine._calculate_runway(
            inputs.current_cash_usd,
            inputs.current_monthly_revenue_usd,
            projections[-1].burn if projections else inputs.current_monthly_burn_usd,
        )

        eom_cash = projections[-1].cumulative_cash if projections else inputs.current_cash_usd

        insights = MathEngine._build_insights(
            inputs, projections, baseline_runway, scenario_runway,
            total_hc_cost, total_rev_impact, zero_cash_month
        )

        return ScenarioResult(
            baseline_runway_months=round(baseline_runway, 1),
            scenario_runway_months=round(scenario_runway, 1),
            runway_delta_months=round(scenario_runway - baseline_runway, 1),

            baseline_eom_cash=round(inputs.current_cash_usd, 2),
            scenario_eom_cash=round(eom_cash, 2),

            monthly_projections=projections,

            total_incremental_headcount_cost=round(total_hc_cost, 2),
            total_incremental_revenue_impact=round(total_rev_impact, 2),
            total_one_time_costs=round(total_one_time, 2),

            key_insights=insights,
            zero_cash_month=zero_cash_month,
            break_even_month=break_even_month,
        )

    # ── helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _calculate_runway(
        cash: float, revenue: float, burn: float
    ) -> float:
        net_burn = burn - revenue
        if net_burn <= 0:
            return float("inf")
        return cash / net_burn

    @staticmethod
    def _build_insights(
        inputs: ScenarioInput,
        projections: List[MonthlyProjection],
        baseline_runway: float,
        scenario_runway: float,
        hc_cost: float,
        rev_impact: float,
        zero_cash_month: Optional[int],
    ) -> List[str]:
        insights = []

        delta = scenario_runway - baseline_runway
        if abs(delta) < 0.5:
            insights.append("Runway impact is minimal (< 0.5 months).")
        elif delta < 0:
            insights.append(
                f"Scenario reduces runway by {abs(delta):.1f} months "
                f"(from {baseline_runway:.1f} → {scenario_runway:.1f} months)."
            )
        else:
            insights.append(
                f"Scenario extends runway by {delta:.1f} months "
                f"(from {baseline_runway:.1f} → {scenario_runway:.1f} months)."
            )

        if inputs.hires:
            total_heads = sum(h.count for h in inputs.hires)
            insights.append(
                f"Total headcount cost over simulation: "
                f"${hc_cost:,.0f} for {total_heads} new hire(s)."
            )
            for hire in inputs.hires:
                monthly = fully_loaded_cost_per_month(hire)
                insights.append(
                    f"  • {hire.count}× {hire.role} in {hire.location}: "
                    f"${monthly:,.0f}/month fully-loaded "
                    f"(salary ${hire.base_salary_usd:,.0f} × "
                    f"{_OVERHEAD_MULTIPLIER.get(hire.location.title(), _DEFAULT_MULTIPLIER):.2f} overhead)."
                )

        if inputs.revenue_events:
            for ev in inputs.revenue_events:
                sign = "+" if ev.monthly_delta_usd >= 0 else ""
                insights.append(
                    f"Revenue event '{ev.description}': "
                    f"{sign}${ev.monthly_delta_usd:,.0f}/month starting month {ev.start_month}."
                )

        if zero_cash_month:
            insights.append(
                f"WARNING: Cash reaches zero at month {zero_cash_month}. "
                f"Immediate action required."
            )

        if projections:
            last = projections[-1]
            if last.net_cash_flow >= 0:
                insights.append(
                    f"Profitable by month {inputs.simulation_months} "
                    f"(net flow ${last.net_cash_flow:,.0f}/month)."
                )
            else:
                insights.append(
                    f"Still cash-negative at month {inputs.simulation_months} "
                    f"(net burn ${abs(last.net_cash_flow):,.0f}/month)."
                )

        return insights
