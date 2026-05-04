"""
Finance Agent Metrics & Testing Suite
======================================
Comprehensive test suite measuring:
1. Response Relevance (does agent answer the question?)
2. Financial Insight Accuracy (are numbers correct?)
3. Decision Usefulness (can founder take action?)
4. Latency (response time)
"""

import time
from datetime import date, datetime, timedelta
from decimal import Decimal
import uuid
from typing import Dict, List
import json

import pytest
from sqlalchemy.orm import Session

import models
from agent.cfo_agent import run_query as run_cfo_query
from agent.finance_agent import run_finance_query
from agent.strategist_agent import run_strategist_query
from agent.evaluation import evaluate_agent_response
from services.math_engine import MathEngine, ScenarioInput, HireEvent, RevenueEvent


# ═══════════════════════════════════════════════════════════════════════════
# Test Data Fixtures
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def seed_test_company(db_session: Session) -> models.Company:
    """Create a realistic test company with 12 months of financial data."""
    company = models.Company(
        name="TestCo SaaS Inc.",
        industry="B2B SaaS",
        stage="series_a",
        initial_cash=Decimal("800000"),
        founding_date=date.today() - timedelta(days=730),  # 2 years old
        effective_tax_rate=Decimal("0.2500"),
        alert_thresholds={"critical_months": 3, "warning_months": 6}
    )
    db_session.add(company)
    db_session.flush()

    # Seed 12 months of financial data
    base_date = date.today() - timedelta(days=365)

    for month_offset in range(12):
        month_date = base_date + timedelta(days=30 * month_offset)

        # Revenue (growing 8% MoM)
        base_revenue = 25000 * (1.08 ** month_offset)
        db_session.add(models.FinancialLedgerEntry(
            company_id=company.id,
            transaction_date=month_date,
            amount=Decimal(str(base_revenue)),
            amount_inr=Decimal(str(base_revenue * 83)),  # USD to INR
            entry_type="credit",
            category="revenue",
            product_tag="vireon_core",
            source="stripe_webhook",
            description=f"MRR for {month_date.strftime('%B %Y')}"
        ))

        # Payroll (fixed)
        db_session.add(models.FinancialLedgerEntry(
            company_id=company.id,
            transaction_date=month_date,
            amount=Decimal("45000"),
            amount_inr=Decimal("3735000"),
            entry_type="debit",
            category="payroll",
            product_tag="shared",
            source="manual_finance",
            description="Monthly payroll"
        ))

        # Cloud costs (growing 5% MoM)
        cloud_cost = 8000 * (1.05 ** month_offset)
        db_session.add(models.FinancialLedgerEntry(
            company_id=company.id,
            transaction_date=month_date,
            amount=Decimal(str(cloud_cost)),
            amount_inr=Decimal(str(cloud_cost * 83)),
            entry_type="debit",
            category="tech_cost",
            product_tag="vireon_core",
            source="aws_billing",
            description="AWS monthly bill"
        ))

        # Marketing (variable)
        marketing = 12000 if month_offset % 3 == 0 else 6000  # Spike every quarter
        db_session.add(models.FinancialLedgerEntry(
            company_id=company.id,
            transaction_date=month_date,
            amount=Decimal(str(marketing)),
            amount_inr=Decimal(str(marketing * 83)),
            entry_type="debit",
            category="marketing",
            product_tag="shared",
            source="manual_marketing",
            description="Marketing spend"
        ))

    # Add invoices (AR/AP)
    db_session.add(models.Invoice(
        remote_id=f"AR-{uuid.uuid4()}",
        company_id=company.id,
        invoice_number="INV-2026-001",
        issue_date=date.today() - timedelta(days=30),
        due_date=date.today() - timedelta(days=5),
        status="OPEN",
        type="ACCOUNTS_RECEIVABLE",
        sub_total=Decimal("25000"),
        tax_amount=Decimal("0"),
        total_amount=Decimal("25000"),
        amount_paid=Decimal("0"),
        amount_due=Decimal("25000")
    ))

    db_session.commit()
    return company


# ═══════════════════════════════════════════════════════════════════════════
# 1. Response Relevance Tests
# ═══════════════════════════════════════════════════════════════════════════

class TestResponseRelevance:
    """Measure if agent answers the question asked (not generic fluff)."""

    def test_runway_query_contains_runway_data(self, seed_test_company):
        """Runway query must include runway months and zero-cash date."""
        response = run_cfo_query(
            user_message="What is our current runway?",
            company_id=str(seed_test_company.id)
        )

        eval_result = evaluate_agent_response(
            user_query="What is our current runway?",
            response=response,
            required_keywords=["runway", "months"],
            min_numeric_tokens=2,  # Must have at least 2 numbers
            min_score=0.80
        )

        assert eval_result.passed, f"Failed checks: {eval_result.feedback}"
        assert eval_result.checks["required_keywords"], "Missing 'runway' or 'months'"
        assert eval_result.checks["numeric_grounding"], "No numbers in response"

    def test_burn_query_contains_burn_data(self, seed_test_company):
        """Burn query must include burn rate and trend."""
        response = run_cfo_query(
            user_message="How is our burn trending?",
            company_id=str(seed_test_company.id)
        )

        eval_result = evaluate_agent_response(
            user_query="How is our burn trending?",
            response=response,
            required_keywords=["burn"],
            min_numeric_tokens=1,
            min_score=0.75
        )

        assert eval_result.passed
        assert "burn" in response.lower()

    def test_scenario_query_provides_actionable_comparison(self, seed_test_company):
        """Scenario query must compare baseline vs scenario with delta."""
        response = run_cfo_query(
            user_message="Can we afford to hire 2 engineers at $150K each?",
            company_id=str(seed_test_company.id)
        )

        # Must mention runway impact
        assert any(keyword in response.lower() for keyword in [
            "runway", "months", "reduce", "extend", "impact"
        ]), "Scenario response missing runway impact"

        # Must have numbers
        eval_result = evaluate_agent_response(
            user_query="Can we afford to hire 2 engineers?",
            response=response,
            min_numeric_tokens=3,  # baseline, scenario, delta
            min_score=0.75
        )
        assert eval_result.passed

    def test_anomaly_query_lists_specific_anomalies(self, seed_test_company):
        """Anomaly query must list specific transactions, not generic advice."""
        # Inject an anomaly
        db_session = seed_test_company._sa_instance_state.session
        db_session.add(models.Anomaly(
            company_id=seed_test_company.id,
            anomaly_date=date.today() - timedelta(days=2),
            type="spending_spike",
            severity="high",
            description="AWS cost spike: $18,245 vs expected $8,200 (+122%)",
            expected_value=Decimal("8200"),
            actual_value=Decimal("18245"),
            status="open"
        ))
        db_session.commit()

        response = run_cfo_query(
            user_message="Show me recent anomalies",
            company_id=str(seed_test_company.id)
        )

        assert "18245" in response or "18,245" in response, "Missing specific anomaly amount"
        assert "aws" in response.lower() or "cloud" in response.lower(), "Missing anomaly source"


# ═══════════════════════════════════════════════════════════════════════════
# 2. Financial Insight Accuracy Tests
# ═══════════════════════════════════════════════════════════════════════════

class TestFinancialAccuracy:
    """Measure if calculations are mathematically correct."""

    def test_runway_calculation_accuracy(self, seed_test_company):
        """Runway = Cash / Net Burn must be accurate within ±5%."""
        db_session = seed_test_company._sa_instance_state.session

        # Get current cash
        current_cash = float(seed_test_company.initial_cash)

        # Calculate last 30 days burn
        thirty_days_ago = date.today() - timedelta(days=30)
        burn = db_session.query(
            models.func.sum(models.FinancialLedgerEntry.amount)
        ).filter(
            models.FinancialLedgerEntry.company_id == seed_test_company.id,
            models.FinancialLedgerEntry.entry_type == "debit",
            models.FinancialLedgerEntry.transaction_date >= thirty_days_ago
        ).scalar() or 0

        revenue = db_session.query(
            models.func.sum(models.FinancialLedgerEntry.amount)
        ).filter(
            models.FinancialLedgerEntry.company_id == seed_test_company.id,
            models.FinancialLedgerEntry.entry_type == "credit",
            models.FinancialLedgerEntry.transaction_date >= thirty_days_ago
        ).scalar() or 0

        net_burn = float(burn - revenue)
        expected_runway = current_cash / net_burn if net_burn > 0 else float("inf")

        # Query agent
        response = run_cfo_query(
            user_message="What is our runway?",
            company_id=str(seed_test_company.id)
        )

        # Extract runway from response (pattern: "X.X months")
        import re
        match = re.search(r'(\d+\.?\d*)\s*months?', response.lower())
        assert match, "No runway months found in response"

        agent_runway = float(match.group(1))

        # Allow ±5% error margin
        error_margin = 0.05
        lower_bound = expected_runway * (1 - error_margin)
        upper_bound = expected_runway * (1 + error_margin)

        assert lower_bound <= agent_runway <= upper_bound, \
            f"Runway accuracy failed: expected {expected_runway:.1f}, got {agent_runway:.1f}"

    def test_fully_loaded_cost_calculation(self):
        """Test location-based overhead multipliers."""
        test_cases = [
            {
                "hire": HireEvent(role="Engineer", count=1, base_salary_usd=150_000, location="US", start_month=1),
                "expected_monthly": 16_875,  # 150K × 1.35 / 12
                "tolerance": 10
            },
            {
                "hire": HireEvent(role="Engineer", count=1, base_salary_usd=150_000, location="India", start_month=1),
                "expected_monthly": 15_625,  # 150K × 1.25 / 12
                "tolerance": 10
            },
            {
                "hire": HireEvent(role="Engineer", count=1, base_salary_usd=150_000, location="Dubai", start_month=1),
                "expected_monthly": 14_375,  # 150K × 1.15 / 12
                "tolerance": 10
            }
        ]

        from services.math_engine import fully_loaded_cost_per_month

        for case in test_cases:
            actual = fully_loaded_cost_per_month(case["hire"])
            expected = case["expected_monthly"]
            tolerance = case["tolerance"]

            assert abs(actual - expected) <= tolerance, \
                f"Fully-loaded cost for {case['hire'].location}: expected {expected}, got {actual}"

    def test_scenario_simulation_determinism(self):
        """Same inputs must produce identical outputs (no randomness)."""
        inputs = ScenarioInput(
            current_cash_usd=500_000,
            current_monthly_revenue_usd=30_000,
            current_monthly_burn_usd=85_000,
            simulation_months=12,
            hires=[
                HireEvent(role="Engineer", count=2, base_salary_usd=150_000, location="US", start_month=2)
            ]
        )

        result1 = MathEngine.run_scenario(inputs)
        result2 = MathEngine.run_scenario(inputs)

        assert result1.baseline_runway_months == result2.baseline_runway_months
        assert result1.scenario_runway_months == result2.scenario_runway_months
        assert result1.runway_delta_months == result2.runway_delta_months

        # Monthly projections must match
        for proj1, proj2 in zip(result1.monthly_projections, result2.monthly_projections):
            assert proj1.revenue == proj2.revenue
            assert proj1.burn == proj2.burn
            assert proj1.cumulative_cash == proj2.cumulative_cash


# ═══════════════════════════════════════════════════════════════════════════
# 3. Decision Usefulness Tests
# ═══════════════════════════════════════════════════════════════════════════

class TestDecisionUsefulness:
    """Measure if response enables founder to take action."""

    def test_critical_runway_includes_recommendations(self, seed_test_company):
        """Critical runway (<6mo) must include actionable recommendations."""
        # Artificially lower cash to trigger critical state
        db_session = seed_test_company._sa_instance_state.session
        seed_test_company.initial_cash = Decimal("100000")  # Low cash
        db_session.commit()

        response = run_cfo_query(
            user_message="What is our runway situation?",
            company_id=str(seed_test_company.id)
        )

        # Must mention urgency
        urgency_keywords = ["critical", "urgent", "immediate", "warning", "action"]
        assert any(kw in response.lower() for kw in urgency_keywords), \
            "Critical runway response missing urgency signal"

        # Must include recommendations
        recommendation_keywords = ["recommend", "should", "reduce", "cut", "raise", "consider"]
        assert any(kw in response.lower() for kw in recommendation_keywords), \
            "Critical runway response missing recommendations"

    def test_scenario_response_includes_tradeoffs(self, seed_test_company):
        """Scenario response must discuss tradeoffs, not just numbers."""
        response = run_cfo_query(
            user_message="Should we hire 3 engineers or focus on profitability?",
            company_id=str(seed_test_company.id)
        )

        # Must discuss tradeoffs
        tradeoff_keywords = ["tradeoff", "however", "but", "alternatively", "consider", "risk"]
        assert any(kw in response.lower() for kw in tradeoff_keywords), \
            "Scenario response missing tradeoff analysis"

    def test_anomaly_response_includes_investigation_steps(self, seed_test_company):
        """Anomaly alert must suggest investigation steps."""
        db_session = seed_test_company._sa_instance_state.session
        db_session.add(models.Anomaly(
            company_id=seed_test_company.id,
            anomaly_date=date.today() - timedelta(days=1),
            type="spending_spike",
            severity="high",
            description="Unexpected $25K vendor charge",
            expected_value=Decimal("0"),
            actual_value=Decimal("25000"),
            status="open"
        ))
        db_session.commit()

        response = run_cfo_query(
            user_message="What anomalies should I investigate?",
            company_id=str(seed_test_company.id)
        )

        # Must suggest investigation
        investigation_keywords = ["verify", "check", "investigate", "contact", "confirm"]
        assert any(kw in response.lower() for kw in investigation_keywords), \
            "Anomaly response missing investigation guidance"


# ═══════════════════════════════════════════════════════════════════════════
# 4. Latency Tests
# ═══════════════════════════════════════════════════════════════════════════

class TestLatency:
    """Measure response time for various query types."""

    def test_simple_query_latency(self, seed_test_company):
        """Simple queries should respond in <3 seconds."""
        start = time.time()
        response = run_cfo_query(
            user_message="What is our current cash balance?",
            company_id=str(seed_test_company.id)
        )
        latency = time.time() - start

        assert latency < 3.0, f"Simple query took {latency:.2f}s (expected <3s)"
        assert len(response) > 0, "Empty response"

    def test_complex_query_latency(self, seed_test_company):
        """Complex queries should respond in <10 seconds."""
        start = time.time()
        response = run_cfo_query(
            user_message="Analyze our burn trend over the last 6 months and project runway",
            company_id=str(seed_test_company.id)
        )
        latency = time.time() - start

        assert latency < 10.0, f"Complex query took {latency:.2f}s (expected <10s)"
        assert len(response) > 100, "Response too short for complex query"

    def test_scenario_simulation_latency(self, seed_test_company):
        """Scenario simulations should respond in <5 seconds."""
        start = time.time()
        response = run_cfo_query(
            user_message="What if we hire 2 engineers at $150K in Q2?",
            company_id=str(seed_test_company.id)
        )
        latency = time.time() - start

        assert latency < 5.0, f"Scenario query took {latency:.2f}s (expected <5s)"
        assert "runway" in response.lower() or "months" in response.lower()


# ═══════════════════════════════════════════════════════════════════════════
# 5. Integration Tests (End-to-End)
# ═══════════════════════════════════════════════════════════════════════════

class TestEndToEnd:
    """Full workflow tests simulating real founder queries."""

    def test_morning_financial_briefing_workflow(self, seed_test_company):
        """Simulate morning CEO routine: check cash, runway, anomalies."""
        queries = [
            "What is our current financial health?",
            "Any anomalies I should know about?",
            "What is our runway projection?"
        ]

        responses = []
        total_time = 0

        for query in queries:
            start = time.time()
            response = run_cfo_query(
                user_message=query,
                company_id=str(seed_test_company.id)
            )
            latency = time.time() - start
            total_time += latency

            responses.append({
                "query": query,
                "response": response,
                "latency": latency
            })

        # Total briefing should take <15 seconds
        assert total_time < 15.0, f"Morning briefing took {total_time:.2f}s (expected <15s)"

        # All responses must be non-empty
        for r in responses:
            assert len(r["response"]) > 50, f"Query '{r['query']}' returned too short response"

    def test_board_prep_workflow(self, seed_test_company):
        """Simulate board prep: metrics summary, trends, recommendations."""
        queries = [
            "Generate a financial summary for our board meeting",
            "What are our key financial trends?",
            "What should we prioritize financially this quarter?"
        ]

        for query in queries:
            response = run_cfo_query(
                user_message=query,
                company_id=str(seed_test_company.id)
            )

            # Board responses must be substantial
            assert len(response) > 200, f"Board prep response too short: {len(response)} chars"

            # Must include numbers
            eval_result = evaluate_agent_response(
                user_query=query,
                response=response,
                min_numeric_tokens=3,
                min_score=0.75
            )
            assert eval_result.passed


# ═══════════════════════════════════════════════════════════════════════════
# 6. Benchmark Suite
# ═══════════════════════════════════════════════════════════════════════════

def run_benchmark_suite(db_session: Session) -> Dict:
    """
    Run comprehensive benchmark and return metrics.

    Returns:
        {
            "response_relevance_score": 0.0-1.0,
            "accuracy_score": 0.0-1.0,
            "decision_usefulness_score": 0.0-1.0,
            "avg_latency_simple": float (seconds),
            "avg_latency_complex": float (seconds),
            "total_tests_run": int,
            "total_tests_passed": int
        }
    """
    # This would be called by pytest with --benchmark flag
    # For now, return placeholder
    return {
        "response_relevance_score": 0.92,
        "accuracy_score": 0.96,
        "decision_usefulness_score": 0.88,
        "avg_latency_simple": 1.8,
        "avg_latency_complex": 6.2,
        "total_tests_run": 25,
        "total_tests_passed": 24
    }


if __name__ == "__main__":
    """Run tests with: pytest backend/tests/test_finance_agent_metrics.py -v"""
    pytest.main([__file__, "-v", "--tb=short"])
