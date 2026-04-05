"""
Integration Tests for Financial Analysis System
===============================================
Tests for financial functions, reasoning engine, memory service, and API endpoints.
"""

import pytest
from datetime import datetime
from typing import Dict, Any

# Import test dependencies
from services.financial_functions import (
    # Cash Flow Functions
    operating_cash_flow,
    investing_cash_flow,
    financing_cash_flow,
    free_cash_flow,
    cash_conversion_cycle,
    cash_runway_extended,
    # Profitability Functions
    gross_profit,
    operating_profit,
    net_profit,
    ebitda,
    profit_margins,
    # Working Capital Functions
    current_ratio,
    quick_ratio,
    working_capital,
    working_capital_to_revenue,
    # Leverage Functions
    debt_to_equity_ratio,
    debt_to_assets_ratio,
    interest_coverage_ratio,
    debt_service_coverage_ratio,
    # Efficiency Functions
    asset_turnover_ratio,
    inventory_turnover_ratio,
    receivables_turnover_ratio,
    return_on_assets,
    # Valuation Functions
    price_to_earnings_ratio,
    price_to_sales_ratio,
    enterprise_value_to_ebitda,
    # Benchmarking
    metric_vs_benchmark,
    financial_health_score,
)

from services.reasoning_engine import (
    FinancialKnowledgeBase,
    ProfitVarianceAnalyzer,
    CashFlowAnalyzer,
    RecommendationGenerator,
)

from services.memory_service import (
    ConversationMemory,
    MemoryService,
    ConversationMessage,
    MessageRole,
)

from agent.financial_tools import get_all_financial_tools


# ============================================================================
# FINANCIAL FUNCTIONS TESTS
# ============================================================================

class TestFinancialFunctions:
    """Test suite for financial calculation functions"""
    
    def test_gross_profit_calculation(self):
        """Test gross profit calculation"""
        revenue = 100000
        cogs = 40000
        result = gross_profit(revenue, cogs)
        assert result == 60000
        assert isinstance(result, (int, float))
    
    def test_operating_profit_calculation(self):
        """Test operating profit calculation"""
        gross_profit_val = 60000
        operating_expenses = 15000
        result = operating_profit(gross_profit_val, operating_expenses)
        assert result == 45000
    
    def test_net_profit_calculation(self):
        """Test net profit calculation"""
        operating_profit_val = 45000
        interest_expense = 5000
        tax_expense = 8000
        result = net_profit(operating_profit_val, interest_expense, tax_expense)
        assert result == 32000
    
    def test_current_ratio_healthy(self):
        """Test healthy current ratio"""
        current_assets = 300000
        current_liabilities = 100000
        result = current_ratio(current_assets, current_liabilities)
        assert result == 3.0
        assert result >= 1.5  # Healthy minimum
    
    def test_current_ratio_tight(self):
        """Test tight current ratio"""
        current_assets = 100000
        current_liabilities = 90000
        result = current_ratio(current_assets, current_liabilities)
        assert 1.0 < result < 1.5
    
    def test_quick_ratio_calculation(self):
        """Test quick ratio (excluding inventory)"""
        current_assets = 300000
        inventory = 80000
        current_liabilities = 100000
        result = quick_ratio(current_assets, inventory, current_liabilities)
        assert result == (300000 - 80000) / 100000
        assert result > 0
    
    def test_debt_to_equity_ratio_conservative(self):
        """Test conservative debt to equity ratio"""
        total_debt = 50000
        total_equity = 150000
        result = debt_to_equity_ratio(total_debt, total_equity)
        assert result == 50000 / 150000
        assert result < 1.0  # Conservative
    
    def test_interest_coverage_ratio_healthy(self):
        """Test healthy interest coverage"""
        operating_profit_val = 50000
        interest_expense = 10000
        result = interest_coverage_ratio(operating_profit_val, interest_expense)
        assert result == 5.0
        assert result > 2.5  # Healthy
    
    def test_free_cash_flow_calculation(self):
        """Test free cash flow calculation"""
        operating_cf = 50000
        capex = 10000
        result = free_cash_flow(operating_cf, capex)
        assert result == 40000
    
    def test_cash_conversion_cycle(self):
        """Test cash conversion cycle calculation"""
        dio = 30
        dso = 45
        dpo = 40
        result = cash_conversion_cycle(dio, dso, dpo)
        assert result == 30 + 45 - 40
        assert result == 35
    
    def test_profit_margins(self):
        """Test all margin calculations"""
        revenue = 100000
        gross_profit_val = 60000
        operating_profit_val = 45000
        net_profit_val = 32000
        
        result = profit_margins(revenue, gross_profit_val, operating_profit_val, net_profit_val)
        
        assert result["gross_profit_margin"] == 0.60
        assert result["operating_profit_margin"] == 0.45
        assert result["net_profit_margin"] == 0.32
    
    def test_cash_runway_calculation(self):
        """Test cash runway calculation"""
        current_cash = 100000
        monthly_burn = 10000
        
        result = cash_runway_extended(current_cash, monthly_burn)
        
        assert "months_of_runway" in result
        assert result["months_of_runway"] >= 10
        assert result["critical_status"] == False
    
    def test_financial_health_score(self):
        """Test financial health score calculation"""
        profitability = 0.8
        liquidity = 0.7
        leverage = 0.6
        efficiency = 0.9
        
        result = financial_health_score(profitability, liquidity, leverage, efficiency)
        
        assert "score" in result
        assert 0 <= result["score"] <= 100
        assert "rating" in result
    
    def test_metric_vs_benchmark(self):
        """Test metric comparison to benchmark"""
        company_metric = 2.5
        benchmark = 2.0
        result = metric_vs_benchmark(company_metric, benchmark, "higher_is_better")
        
        assert "variance_pct" in result
        assert result["variance_pct"] > 0  # Better than benchmark


# ============================================================================
# REASONING ENGINE TESTS
# ============================================================================

class TestReasoningEngine:
    """Test suite for financial reasoning engine"""
    
    def test_knowledge_base_initialization(self):
        """Test financial knowledge base"""
        kb = FinancialKnowledgeBase()
        assert kb is not None
    
    def test_knowledge_base_concept_retrieval(self):
        """Test retrieving financial concepts"""
        kb = FinancialKnowledgeBase()
        concept = kb.get_concept("current_ratio")
        assert concept is not None
        assert hasattr(concept, "definition")
        assert hasattr(concept, "interpretation")
    
    def test_knowledge_base_explanation(self):
        """Test getting concept explanation"""
        kb = FinancialKnowledgeBase()
        explanation = kb.explain("gross_margin")
        assert isinstance(explanation, str)
        assert len(explanation) > 0
    
    def test_profit_variance_analyzer(self):
        """Test profit variance analysis"""
        kb = FinancialKnowledgeBase()
        analyzer = ProfitVarianceAnalyzer(kb)
        
        result = analyzer.analyze_margin_variance(
            actual_margin=0.25,
            expected_margin=0.30
        )
        
        assert "variance" in result
        assert "favorable" in result or "unfavorable" in result[0:20].lower()
    
    def test_cash_flow_analyzer(self):
        """Test cash flow quality analysis"""
        kb = FinancialKnowledgeBase()
        analyzer = CashFlowAnalyzer(kb)
        
        result = analyzer.analyze_cf_quality(
            net_income=50000,
            operating_cash_flow=60000
        )
        
        assert "quality_score" in result or "quality" in str(result).lower()
    
    def test_recommendation_generator(self):
        """Test recommendation generation"""
        kb = FinancialKnowledgeBase()
        rec_gen = RecommendationGenerator(kb)
        
        financial_metrics = {
            "revenue": 1000000,
            "net_income": 100000,
            "gross_margin": 0.60,
            "current_ratio": 1.5,
            "debt_to_equity": 0.8,
            "cash_conversion_cycle": 45,
        }
        
        recommendations = rec_gen.generate_recommendations(
            financial_metrics,
            company_stage="growth"
        )
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        assert all("priority" in r for r in recommendations)


# ============================================================================
# MEMORY SERVICE TESTS
# ============================================================================

class TestMemoryService:
    """Test suite for conversation memory service"""
    
    def test_conversation_message_creation(self):
        """Test creating a conversation message"""
        msg = ConversationMessage(
            role=MessageRole.USER,
            content="What is my cash runway?"
        )
        
        assert msg.role == MessageRole.USER
        assert msg.content == "What is my cash runway?"
        assert msg.timestamp is not None
    
    def test_memory_service_initialization(self):
        """Test memory service initialization"""
        service = MemoryService()
        assert service is not None
    
    def test_conversation_memory_initialization(self):
        """Test conversation memory"""
        service = MemoryService()
        memory = ConversationMemory(memory_service=service)
        
        assert memory is not None
    
    def test_get_or_create_session(self):
        """Test session creation"""
        service = MemoryService()
        memory = ConversationMemory(memory_service=service)
        
        session_id = "test_session_123"
        session = memory.get_or_create_session(
            session_id=session_id,
            user_id="user_123",
            company_id="company_123"
        )
        
        assert session is not None
    
    def test_add_messages_to_memory(self):
        """Test adding messages to memory"""
        service = MemoryService()
        memory = ConversationMemory(memory_service=service)
        
        memory.get_or_create_session("test_session")
        memory.add_user_message("What is my burn rate?")
        memory.add_assistant_message("Your burn rate is ₹50,000 per month")
        
        context = memory.get_context_for_llm()
        assert len(context) > 0


# ============================================================================
# AGENT TOOLS TESTS
# ============================================================================

class TestFinancialTools:
    """Test suite for agent financial tools"""
    
    def test_tools_registry(self):
        """Test that all financial tools are available"""
        tools = get_all_financial_tools()
        
        assert isinstance(tools, dict)
        assert len(tools) > 30
    
    def test_tool_descriptions(self):
        """Test that all tools have descriptions"""
        tools = get_all_financial_tools()
        
        for tool_name, tool in tools.items():
            assert hasattr(tool, "name")
            assert hasattr(tool, "description")
            assert len(tool.description) > 0


# ============================================================================
# INTEGRATION TESTS (Financial Analysis Flow)
# ============================================================================

class TestIntegrationFlow:
    """Test integrated financial analysis flows"""
    
    def test_full_profitability_analysis(self):
        """Test comprehensive profitability analysis"""
        # Setup
        revenue = 500000
        cogs = 200000
        opex = 150000
        interest = 5000
        taxes = 15000
        
        # Execute
        gp = gross_profit(revenue, cogs)
        op = operating_profit(gp, opex)
        np = net_profit(op, interest, taxes)
        margins = profit_margins(revenue, gp, op, np)
        
        # Verify
        assert gp == 300000
        assert op == 150000
        assert np == 130000
        assert margins["gross_profit_margin"] == 0.6
        assert margins["operating_profit_margin"] == 0.3
        assert margins["net_profit_margin"] == 0.26
    
    def test_full_liquidity_analysis(self):
        """Test comprehensive liquidity analysis"""
        # Setup
        current_assets = 250000
        inventory = 50000
        current_liabilities = 100000
        
        # Execute
        cr = current_ratio(current_assets, current_liabilities)
        qr = quick_ratio(current_assets, inventory, current_liabilities)
        wc = working_capital(current_assets, current_liabilities)
        
        # Verify
        assert cr == 2.5  # Healthy
        assert qr == 2.0  # Very healthy
        assert wc == 150000
    
    def test_full_leverage_analysis(self):
        """Test comprehensive leverage analysis"""
        # Setup
        total_debt = 100000
        total_equity = 300000
        operating_profit_val = 75000
        interest_expense = 5000
        
        # Execute
        de = debt_to_equity_ratio(total_debt, total_equity)
        icr = interest_coverage_ratio(operating_profit_val, interest_expense)
        
        # Verify
        assert de == (100000 / 300000)
        assert de < 1.0  # Conservative
        assert icr == 15.0  # Very healthy
    
    def test_cash_flow_to_runway_flow(self):
        """Test flow from cash flow analysis to runway"""
        # Setup
        operating_cf = 80000
        capex = 20000
        current_cash = 500000
        monthly_burn = 30000
        
        # Execute
        fcf = free_cash_flow(operating_cf, capex)
        runway = cash_runway_extended(current_cash, monthly_burn)
        
        # Verify
        assert fcf == 60000
        assert "months_of_runway" in runway
    
    def test_health_score_from_metrics(self):
        """Test generating health score from all metric categories"""
        # Setup: Mixed financial metrics
        profitability = 0.12 / 0.5  # 12% net margin / 50% max
        liquidity = 2.5 / 3.0  # 2.5 current ratio / 3.0 max
        leverage = 0.8  # D/E ratio (inverted)
        efficiency = 1.0  # Normalized
        
        # Execute
        health = financial_health_score(
            profitability, liquidity, leverage, efficiency
        )
        
        # Verify
        assert "score" in health
        assert 0 <= health["score"] <= 100
    
    def test_reasoning_with_metrics(self):
        """Test generating recommendations from calculated metrics"""
        # Setup
        kb = FinancialKnowledgeBase()
        rec_gen = RecommendationGenerator(kb)
        
        revenue = 500000
        cogs = 200000
        gp = gross_profit(revenue, cogs)
        op = operating_profit(gp, 100000)
        np = net_profit(op, 5000, 15000)
        
        cr = current_ratio(250000, 100000)
        de = debt_to_equity_ratio(100000, 300000)
        
        metrics = {
            "revenue": revenue,
            "net_income": np,
            "gross_margin": gp / revenue,
            "current_ratio": cr,
            "debt_to_equity": de,
            "cash_conversion_cycle": 35,
        }
        
        # Execute
        recommendations = rec_gen.generate_recommendations(
            metrics, "growth"
        )
        
        # Verify
        assert len(recommendations) > 0
        assert all("priority" in r for r in recommendations)


# ============================================================================
# EDGE CASE & VALIDATION TESTS
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_zero_revenue_handling(self):
        """Test handling of zero revenue"""
        result = gross_profit(0, 0)
        assert result == 0
    
    def test_negative_net_income(self):
        """Test handling of losses"""
        result = net_profit(-10000, 5000, 0)
        assert result == -15000  # Loss
    
    def test_zero_division_protection(self):
        """Test zero division protection in ratios"""
        # These should not raise exceptions
        result = current_ratio(100, 0)
        result = price_to_earnings_ratio(1000000, 0)
    
    def test_health_score_bounds(self):
        """Test health score stays within bounds"""
        for prof in [0, 0.5, 1.0]:
            for liq in [0, 0.5, 1.0]:
                for lev in [0, 0.5, 1.0]:
                    for eff in [0, 0.5, 1.0]:
                        score = financial_health_score(prof, liq, lev, eff)
                        assert 0 <= score["score"] <= 100


# ============================================================================
# PYTEST EXECUTION
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
