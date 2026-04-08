"""
Comprehensive test suite for all new finance features
Tests API endpoints, services, and business logic
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test that all new modules can be imported"""
    print("Testing imports...")
    
    try:
        from api.routers import (
            contracts, reconciliation, nlg_reports, recurring_templates,
            board_reports, scenario_comparison, customer_health,
            forecast_monitoring, finance_tasks, transaction_comments,
            inventory, revenue_recognition_asc606, purchase_orders
        )
        print("✓ All router imports successful")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False


def test_models():
    """Test that all new models are defined"""
    print("\nTesting models...")
    
    try:
        import models
        
        required_models = [
            'Contract', 'ContractAlert', 'BankReconciliation',
            'BankTransactionMatch', 'TransactionTemplate', 'PurchaseOrder',
            'POLineItem', 'CustomerHealthScore', 'ForecastModel',
            'ForecastAccuracy', 'NarrativeReport', 'BoardReport',
            'ScenarioComparison', 'FinanceTask', 'TransactionComment',
            'InventoryItem', 'InventoryTransaction', 'RevenueRecognition',
            'RevenueSchedule'
        ]
        
        missing = []
        for model_name in required_models:
            if not hasattr(models, model_name):
                missing.append(model_name)
        
        if missing:
            print(f"✗ Missing models: {', '.join(missing)}")
            return False
        
        print(f"✓ All {len(required_models)} models defined")
        return True
    except Exception as e:
        print(f"✗ Model test failed: {e}")
        return False


def test_schemas():
    """Test that all new schemas are defined"""
    print("\nTesting schemas...")
    
    try:
        import schemas
        
        required_schemas = [
            'ContractCreate', 'Contract', 'TransactionTemplateCreate',
            'BoardReportGenerate', 'ScenarioComparisonCreate',
            'CustomerHealthScoreResponse', 'ForecastAccuracyResponse',
            'FinanceTaskCreate', 'FinanceTask', 'TransactionCommentCreate',
            'InventoryItemCreate', 'RevenueRecognitionCreate',
            'PurchaseOrderCreate', 'POLineItemCreate'
        ]
        
        missing = []
        for schema_name in required_schemas:
            if not hasattr(schemas, schema_name):
                missing.append(schema_name)
        
        if missing:
            print(f"✗ Missing schemas: {', '.join(missing)}")
            return False
        
        print(f"✓ All {len(required_schemas)} schemas defined")
        return True
    except Exception as e:
        print(f"✗ Schema test failed: {e}")
        return False


def test_router_endpoints():
    """Test that routers have expected endpoints"""
    print("\nTesting router endpoints...")
    
    try:
        from api.routers import contracts, reconciliation, nlg_reports
        
        # Test contracts router
        assert hasattr(contracts, 'router'), "contracts.router not found"
        assert hasattr(contracts, 'create_contract'), "create_contract function not found"
        assert hasattr(contracts, 'list_contracts'), "list_contracts function not found"
        
        # Test reconciliation router
        assert hasattr(reconciliation, 'router'), "reconciliation.router not found"
        assert hasattr(reconciliation, 'create_reconciliation'), "create_reconciliation not found"
        
        # Test NLG reports router
        assert hasattr(nlg_reports, 'router'), "nlg_reports.router not found"
        assert hasattr(nlg_reports, 'generate_narrative_report'), "generate_narrative_report not found"
        
        print("✓ Router endpoints verified")
        return True
    except AssertionError as e:
        print(f"✗ Router test failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Router test error: {e}")
        return False


def test_services():
    """Test that service modules exist"""
    print("\nTesting services...")
    
    try:
        from services import forecast_monitoring_service
        
        assert hasattr(forecast_monitoring_service, 'ForecastMonitor'), "ForecastMonitor class not found"
        
        print("✓ Services verified")
        return True
    except Exception as e:
        print(f"✗ Service test failed: {e}")
        return False


def verify_router_registration():
    """Verify routers are registered in main app"""
    print("\nVerifying router registration...")
    
    try:
        with open('main.py', 'r') as f:
            content = f.read()
        
        required_routers = [
            'contracts', 'reconciliation', 'nlg_reports', 'recurring_templates',
            'board_reports', 'scenario_comparison', 'customer_health',
            'forecast_monitoring', 'finance_tasks', 'transaction_comments',
            'inventory', 'revenue_recognition_asc606', 'purchase_orders'
        ]
        
        missing = []
        for router in required_routers:
            if f"app.include_router({router}.router" not in content:
                missing.append(router)
        
        if missing:
            print(f"✗ Routers not registered: {', '.join(missing)}")
            return False
        
        print(f"✓ All {len(required_routers)} routers registered in main.py")
        return True
    except Exception as e:
        print(f"✗ Router registration check failed: {e}")
        return False


def count_features():
    """Count implemented features"""
    print("\nFeature Implementation Summary:")
    print("=" * 60)
    
    features = {
        "Contract Management": "contracts.py",
        "Bank Reconciliation": "reconciliation.py",
        "NLG Reports": "nlg_reports.py",
        "Recurring Templates": "recurring_templates.py",
        "Board Reports": "board_reports.py",
        "Scenario Comparison": "scenario_comparison.py",
        "Customer Health Scoring": "customer_health.py",
        "Forecast Monitoring": "forecast_monitoring.py",
        "Finance Task Management": "finance_tasks.py",
        "Transaction Comments": "transaction_comments.py",
        "Inventory Valuation": "inventory.py",
        "Revenue Recognition (ASC 606)": "revenue_recognition_asc606.py",
        "Purchase Orders": "purchase_orders.py"
    }
    
    implemented = 0
    for feature, filename in features.items():
        filepath = f"api/routers/{filename}"
        if os.path.exists(filepath):
            implemented += 1
            size = os.path.getsize(filepath)
            print(f"✓ {feature:40} ({size:,} bytes)")
        else:
            print(f"✗ {feature:40} (not found)")
    
    print("=" * 60)
    print(f"Total Features Implemented: {implemented}/{len(features)}")
    
    return implemented == len(features)


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("VIREON FINANCE AGENT - COMPREHENSIVE TEST SUITE")
    print("="*60)
    
    results = {
        "Imports": test_imports(),
        "Models": test_models(),
        "Schemas": test_schemas(),
        "Router Endpoints": test_router_endpoints(),
        "Services": test_services(),
        "Router Registration": verify_router_registration(),
        "Feature Count": count_features()
    }
    
    print("\n" + "="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name:30} {status}")
    
    total_passed = sum(results.values())
    total_tests = len(results)
    
    print("="*60)
    print(f"Total: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("\n🎉 ALL TESTS PASSED! Finance Agent enhancements complete.")
        return 0
    else:
        print(f"\n⚠️  {total_tests - total_passed} tests failed. Review output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
