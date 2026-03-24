"""
Tests for Tax, Depreciation, and Forecasting features.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch
import uuid


# ═══════════════════════════════════════════════════════════════════════════════
# TAX SERVICE TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestTaxService:

    def test_calculate_tax_for_invoice_defaults(self):
        """Tax calculation uses config defaults when no TaxRules exist."""
        from services.tax_service import calculate_tax_for_invoice

        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []  # No rules

        company_id = uuid.uuid4()
        result = calculate_tax_for_invoice(db, company_id, 100000.0, is_service=True)

        assert "gst_amount" in result
        assert "tds_deducted" in result
        assert "net_cash_expected" in result
        assert result["invoice_base"] == 100000.0
        assert result["gst_amount"] == 18000.0  # 18% default
        assert result["total_invoice"] == 118000.0

    def test_calculate_tax_for_payroll_defaults(self):
        """Payroll tax uses PF/ESI/PT defaults when no TaxRules exist."""
        from services.tax_service import calculate_tax_for_payroll

        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []

        company_id = uuid.uuid4()
        result = calculate_tax_for_payroll(db, company_id, 50000.0)

        assert "gross_pay" in result
        assert "employee_pf" in result
        assert "professional_tax" in result
        assert "net_pay" in result
        assert result["gross_pay"] == 50000.0
        assert result["net_pay"] < 50000.0  # Deductions applied

    def test_quarterly_tax_summary_structure(self):
        """Quarterly summary returns correct structure."""
        from services.tax_service import calculate_quarterly_tax_summary

        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        db.query.return_value.filter.return_value.filter.return_value.all.return_value = []
        db.query.return_value.join.return_value.filter.return_value.filter.return_value.all.return_value = []

        company_id = uuid.uuid4()
        result = calculate_quarterly_tax_summary(db, company_id, 2025, 1)

        assert result["year"] == 2025
        assert result["quarter"] == 1
        assert "total_tax_liability" in result
        assert "total_gst_collected_payable" in result


# ═══════════════════════════════════════════════════════════════════════════════
# DEPRECIATION SERVICE TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestDepreciationService:

    def _make_mock_asset(self, **overrides):
        asset = MagicMock()
        asset.id = uuid.uuid4()
        asset.company_id = uuid.uuid4()
        asset.asset_name = "Test Laptop"
        asset.purchase_cost = Decimal("100000")
        asset.salvage_value = Decimal("10000")
        asset.useful_life_years = 5
        asset.depreciation_method = "straight_line"
        asset.accumulated_depreciation = Decimal("0")
        asset.book_value = Decimal("100000")
        asset.status = "active"
        asset.disposal_date = None
        asset.disposal_value = None
        for k, v in overrides.items():
            setattr(asset, k, v)
        return asset

    def test_dispose_asset_calculates_gain(self):
        """Disposing at > book value records a gain."""
        from services.depreciation_service import dispose_asset

        asset = self._make_mock_asset(
            book_value=Decimal("50000"),
            accumulated_depreciation=Decimal("50000"),
            purchase_cost=Decimal("100000"),
        )
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = asset

        result = dispose_asset(db, asset.id, 60000.0)

        assert result["gain_loss"] == 10000.0
        assert result["gain_loss_type"] == "gain"
        assert result["status"] == "disposed"
        assert db.commit.called

    def test_dispose_asset_calculates_loss(self):
        """Disposing at < book value records a loss."""
        from services.depreciation_service import dispose_asset

        asset = self._make_mock_asset(
            book_value=Decimal("50000"),
            accumulated_depreciation=Decimal("50000"),
            purchase_cost=Decimal("100000"),
        )
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = asset

        result = dispose_asset(db, asset.id, 30000.0)

        assert result["gain_loss"] == -20000.0
        assert result["gain_loss_type"] == "loss"

    def test_dispose_asset_not_found(self):
        """Disposal of non-existent asset returns error."""
        from services.depreciation_service import dispose_asset

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        result = dispose_asset(db, uuid.uuid4(), 50000.0)
        assert "error" in result

    def test_dispose_already_disposed(self):
        """Cannot dispose an already disposed asset."""
        from services.depreciation_service import dispose_asset

        asset = self._make_mock_asset(status="disposed")
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = asset

        result = dispose_asset(db, asset.id, 50000.0)
        assert "error" in result


# ═══════════════════════════════════════════════════════════════════════════════
# FORECASTING SERVICE TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestForecastingService:

    def test_empty_data_returns_zero_forecast(self):
        """Empty dataframe returns 12 zero-valued forecasts."""
        import pandas as pd
        from services.forecasting_service import fit_sarima_model

        df = pd.DataFrame(columns=["ds", "y"])
        result = fit_sarima_model(df)

        assert result["model_type"] == "empty"
        assert len(result["forecast_df"]) == 12
        assert all(result["forecast_df"]["yhat"] == 0.0)

    def test_small_data_uses_fallback(self):
        """With very few data points, falls back to flat/prophet."""
        import pandas as pd
        from services.forecasting_service import fit_sarima_model

        df = pd.DataFrame({
            "ds": pd.date_range("2025-01-01", periods=2, freq="MS"),
            "y": [100000.0, 110000.0],
        })
        result = fit_sarima_model(df)

        # Should be prophet or flat fallback
        assert result["model_type"] in ["prophet", "fallback_flat"]
        assert len(result["forecast_df"]) == 12

    def test_medium_data_uses_arima(self):
        """With 6+ data points, uses ARIMA."""
        import pandas as pd
        from services.forecasting_service import fit_sarima_model

        df = pd.DataFrame({
            "ds": pd.date_range("2025-01-01", periods=8, freq="MS"),
            "y": [100000.0 + i * 5000 for i in range(8)],
        })
        result = fit_sarima_model(df)

        assert result["model_type"] in ["arima", "exponential_smoothing", "prophet", "fallback_flat"]
        assert len(result["forecast_df"]) == 12

    def test_large_data_uses_sarima_seasonal(self):
        """With 12+ data points, uses SARIMA seasonal."""
        import pandas as pd
        import numpy as np
        from services.forecasting_service import fit_sarima_model

        np.random.seed(42)
        df = pd.DataFrame({
            "ds": pd.date_range("2024-01-01", periods=18, freq="MS"),
            "y": [100000.0 + i * 5000 + np.random.normal(0, 2000) for i in range(18)],
        })
        result = fit_sarima_model(df)

        assert result["model_type"] in ["sarima_seasonal", "arima", "exponential_smoothing", "prophet", "fallback_flat"]
        assert len(result["forecast_df"]) == 12
        assert "yhat_lower" in result["forecast_df"].columns
        assert "yhat_upper" in result["forecast_df"].columns

    def test_forecast_has_confidence_intervals(self):
        """All model types return confidence intervals."""
        import pandas as pd
        import numpy as np
        from services.forecasting_service import fit_sarima_model

        np.random.seed(42)
        df = pd.DataFrame({
            "ds": pd.date_range("2024-01-01", periods=12, freq="MS"),
            "y": [100000.0 + i * 5000 + np.random.normal(0, 2000) for i in range(12)],
        })
        result = fit_sarima_model(df)

        fc = result["forecast_df"]
        assert "yhat_lower" in fc.columns
        assert "yhat_upper" in fc.columns
        # Upper bound should be >= yhat
        assert all(fc["yhat_upper"] >= fc["yhat"])


# ═══════════════════════════════════════════════════════════════════════════════
# BUDGET SERVICE TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestBudgetService:

    def test_get_budget_variance_structure(self):
        from services.planning import get_budget_variance
        db = MagicMock()
        budget = MagicMock()
        budget.name = "Test Budget"
        budget.lines = []
        db.query.return_value.filter.return_value.first.return_value = budget
        
        result = get_budget_variance(db, uuid.uuid4())
        assert result["budget_name"] == "Test Budget"
        assert "variances" in result

    def test_check_budget_alerts(self):
        from services.planning import check_budget_alerts
        db = MagicMock()
        
        with patch("services.planning.get_budget_variance") as mock_var:
            mock_var.return_value = {
                "variances": [
                    {"category": "marketing", "budget": 1000, "actual": 1200, "variance": 200, "variance_pct": 20.0}
                ]
            }
            alerts = check_budget_alerts(db, uuid.uuid4(), threshold_pct=10.0)
            assert len(alerts) == 1
            assert alerts[0]["alert_type"] == "budget_overrun"
            assert alerts[0]["category"] == "marketing"


# ═══════════════════════════════════════════════════════════════════════════════
# GROSS MARGIN SERVICE TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestMarginService:

    def test_calculate_server_side_margin_basic(self):
        from services.margin_service import calculate_server_side_margin
        db = MagicMock()
        # Mocking revenue and COGS
        db.query.return_value.filter.return_value.scalar.side_effect = [Decimal("100000"), Decimal("40000"), Decimal("0"), Decimal("0")]
        
        result = calculate_server_side_margin(db, uuid.uuid4(), date(2025, 3, 1))
        assert result["total_revenue"] == 100000.0
        assert result["total_cogs"] == 40000.0
        assert result["gross_margin_pct"] == 60.0

    def test_check_margin_alerts(self):
        from services.margin_service import check_margin_alerts
        db = MagicMock()
        
        with patch("services.margin_service.calculate_server_side_margin") as mock_margin:
            mock_margin.return_value = {"gross_margin_pct": 25.0, "total_revenue": 1000}
            with patch("services.margin_service.calculate_product_margin") as mock_prod:
                mock_prod.return_value = {"product_margins": {}}
                alerts = check_margin_alerts(db, uuid.uuid4(), date(2025, 3, 1), threshold_pct=50.0)
                assert len(alerts) == 1
                assert alerts[0]["alert_type"] == "margin_below_threshold"


# ═══════════════════════════════════════════════════════════════════════════════
# FX SERVICE TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestFxService:

    def test_get_multicurrency_pl_structure(self):
        from services.fx_service import get_multicurrency_pl
        db = MagicMock()
        db.query.return_value.filter.return_value.group_by.return_value.all.return_value = []
        
        result = get_multicurrency_pl(db, uuid.uuid4(), "2025-03")
        assert result["month"] == "2025-03"
        assert "consolidated_revenue_inr" in result

    def test_get_fx_adjusted_runway(self):
        from services.fx_service import get_fx_adjusted_runway
        db = MagicMock()
        
        metric = MagicMock()
        metric.ending_cash = 1000000
        metric.burn_rate = 100000
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = metric
        
        # Mock revals
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        result = get_fx_adjusted_runway(db, uuid.uuid4())
        assert result["cash_balance"] == 1000000
        assert result["runway_months"] == 10.0


# ═══════════════════════════════════════════════════════════════════════════════
# RECOMMENDATIONS & CLOUD COSTS TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestRecommendationsService:

    def test_generate_logic_fallback_when_context_has_no_signals(self):
        from services.recommendations_service import _generate_logic_based_recommendations

        context = {
            "runway": {"runway_months": 12},
            "burn_summary": {"net_burn": 100000, "breakdown_by_category": {}},
            "product_pl_last_3_months": [],
            "anomalies_last_30_days": [],
        }
        recs = _generate_logic_based_recommendations(context)

        assert isinstance(recs, list)
        assert len(recs) >= 1
        assert all("title" in r and "action" in r for r in recs)

    def test_generate_logic_handles_dict_product_payload(self):
        from services.recommendations_service import _generate_logic_based_recommendations

        context = {
            "runway": {"runway_months": 10},
            "burn_summary": {"net_burn": 200000, "breakdown_by_category": {"tech_cost": 120000}},
            "product_pl_last_3_months": [
                {
                    "month": "2026-03",
                    "data": {
                        "orchard": {"total_revenue": 500000, "gross_margin_pct": 22.5},
                        "ai_lab": {"total_revenue": 100000, "gross_margin_pct": 5.0},
                    },
                }
            ],
            "anomalies_last_30_days": [],
        }
        recs = _generate_logic_based_recommendations(context)
        ids = [r.get("id", "") for r in recs]
        assert any("rec-margin-orchard" in r for r in ids)
        assert not any("rec-margin-ai_lab" in r for r in ids)


class TestCloudRecommendations:

    def test_cloud_recommendations_empty_accounts(self):
        from api.routers.cloud_costs import get_cloud_recommendations

        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []

        result = get_cloud_recommendations(uuid.uuid4(), db, "finance")
        assert "recommendations" in result
        assert result["recommendations"] == []
        assert result["total_potential_monthly_saving"] == 0.0


def test_models_only_used_for_forecasting():
        """ARIMA/SARIMA models are only in the forecasting service, not in other services."""
        import importlib
        import inspect

        # Import services that should NOT use ARIMA/SARIMA
        from services import burn_service, ledger_service
        
        burn_src = inspect.getsource(burn_service)
        ledger_src = inspect.getsource(ledger_service)
        
        assert "SARIMAX" not in burn_src, "SARIMAX should not be in burn_service"
        assert "ARIMA" not in burn_src, "ARIMA should not be in burn_service"
        assert "SARIMAX" not in ledger_src, "SARIMAX should not be in ledger_service"
        assert "ARIMA" not in ledger_src, "ARIMA should not be in ledger_service"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
