#!/usr/bin/env python3
"""
Finance Agent Testing Script
Tests all finance agent endpoints with real-world scenarios
"""

import requests
import json
from datetime import date, timedelta
from uuid import uuid4
import time


class FinanceAgentTester:
    def __init__(self, base_url="http://localhost:8000/api/v1"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        self.company_id = str(uuid4())
        
    def log_test(self, test_name, passed, details=""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"  → {details}")
        self.test_results.append({
            "name": test_name,
            "passed": passed,
            "details": details
        })
    
    def test_finance_agent_chat(self):
        """Test Finance Agent chat endpoint"""
        print("\n🧪 Testing Finance Agent Chat Endpoint...")
        try:
            response = self.session.post(
                f"{self.base_url}/agent/finance/chat",
                json={
                    "message": "What invoices are due this week?",
                    "session_id": str(uuid4()),
                    "company_id": self.company_id
                },
                timeout=30
            )
            passed = response.status_code in (200, 201)
            self.log_test(
                "Finance Agent Chat",
                passed,
                f"Status: {response.status_code}, Response: {response.text[:100]}"
            )
        except Exception as e:
            self.log_test("Finance Agent Chat", False, str(e))
    
    def test_finance_manager_agent_chat(self):
        """Test Finance Manager Agent chat endpoint"""
        print("\n🧪 Testing Finance Manager Agent Chat Endpoint...")
        try:
            response = self.session.post(
                f"{self.base_url}/agent/finance-manager/chat",
                json={
                    "message": "Can you validate if March 2026 close is ready?",
                    "session_id": str(uuid4()),
                    "company_id": self.company_id
                },
                timeout=30
            )
            passed = response.status_code in (200, 201)
            self.log_test(
                "Finance Manager Agent Chat",
                passed,
                f"Status: {response.status_code}, Response: {response.text[:100]}"
            )
        except Exception as e:
            self.log_test("Finance Manager Agent Chat", False, str(e))
    
    def test_close_validate(self):
        """Test close validation endpoint"""
        print("\n🧪 Testing Close Validation Endpoint...")
        try:
            response = self.session.post(
                f"{self.base_url}/close/validate",
                json={
                    "company_id": self.company_id,
                    "period": "2026-03"
                },
                timeout=10
            )
            passed = response.status_code in (200, 201)
            self.log_test(
                "Close Validate",
                passed,
                f"Status: {response.status_code}"
            )
            return response.json() if passed else None
        except Exception as e:
            self.log_test("Close Validate", False, str(e))
            return None
    
    def test_close_accruals(self):
        """Test accruals calculation"""
        print("\n🧪 Testing Accruals Calculation...")
        try:
            response = self.session.post(
                f"{self.base_url}/close/accruals",
                json={
                    "company_id": self.company_id,
                    "period": "2026-03"
                },
                timeout=10
            )
            passed = response.status_code in (200, 201)
            self.log_test(
                "Calculate Accruals",
                passed,
                f"Status: {response.status_code}"
            )
            return response.json() if passed else None
        except Exception as e:
            self.log_test("Calculate Accruals", False, str(e))
            return None
    
    def test_close_lock(self):
        """Test period locking"""
        print("\n🧪 Testing Period Lock...")
        try:
            response = self.session.post(
                f"{self.base_url}/close/lock",
                json={
                    "company_id": self.company_id,
                    "period": "2026-03",
                    "locked_by": str(uuid4())
                },
                timeout=10
            )
            passed = response.status_code in (200, 201)
            self.log_test(
                "Lock Period",
                passed,
                f"Status: {response.status_code}"
            )
            return response.json() if passed else None
        except Exception as e:
            self.log_test("Lock Period", False, str(e))
            return None
    
    def test_close_status(self):
        """Test close status retrieval"""
        print("\n🧪 Testing Close Status...")
        try:
            response = self.session.get(
                f"{self.base_url}/close/status/{self.company_id}",
                timeout=10
            )
            passed = response.status_code in (200, 404)  # 404 is ok if no data yet
            self.log_test(
                "Get Close Status",
                passed,
                f"Status: {response.status_code}"
            )
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            self.log_test("Get Close Status", False, str(e))
            return None
    
    def test_approval_workflow_creation(self):
        """Test approval workflow creation"""
        print("\n🧪 Testing Approval Workflow Creation...")
        try:
            response = self.session.post(
                f"{self.base_url}/approvals/workflows",
                json={
                    "company_id": self.company_id,
                    "name": "Finance Approvals",
                    "entity_type": "PurchaseOrder",
                    "steps": [
                        {
                            "step_order": 1,
                            "approver_role": "Manager",
                            "min_amount": "0",
                            "max_amount": "10000"
                        },
                        {
                            "step_order": 2,
                            "approver_role": "Director",
                            "min_amount": "10000",
                            "max_amount": None
                        }
                    ]
                },
                timeout=10
            )
            passed = response.status_code in (200, 201)
            self.log_test(
                "Create Approval Workflow",
                passed,
                f"Status: {response.status_code}"
            )
            result = response.json() if passed else None
            self.workflow_id = result.get("id") if result else None
            return result
        except Exception as e:
            self.log_test("Create Approval Workflow", False, str(e))
            return None
    
    def test_budget_creation(self):
        """Test budget creation"""
        print("\n🧪 Testing Budget Creation...")
        try:
            response = self.session.post(
                f"{self.base_url}/planning/budgets",
                json={
                    "company_id": self.company_id,
                    "period": "2026-Q2",
                    "budgets": {
                        "engineering": 50000.0,
                        "marketing": 20000.0,
                        "operations": 15000.0,
                        "sales": 25000.0
                    }
                },
                timeout=10
            )
            passed = response.status_code in (200, 201)
            self.log_test(
                "Create Budget",
                passed,
                f"Status: {response.status_code}"
            )
            result = response.json() if passed else None
            self.budget_id = result.get("budget_id") if result else None
            return result
        except Exception as e:
            self.log_test("Create Budget", False, str(e))
            return None
    
    def test_audit_event_logging(self):
        """Test audit event logging"""
        print("\n🧪 Testing Audit Event Logging...")
        try:
            response = self.session.post(
                f"{self.base_url}/audit/events",
                json={
                    "entity_type": "Invoice",
                    "entity_id": str(uuid4()),
                    "old_value": {"status": "OPEN"},
                    "new_value": {"status": "PAID"},
                    "user_id": str(uuid4()),
                    "company_id": self.company_id,
                    "event_type": "invoice_paid"
                },
                timeout=10
            )
            passed = response.status_code in (200, 201)
            self.log_test(
                "Log Audit Event",
                passed,
                f"Status: {response.status_code}"
            )
            return response.json() if passed else None
        except Exception as e:
            self.log_test("Log Audit Event", False, str(e))
            return None
    
    def test_consolidation_hierarchy(self):
        """Test entity hierarchy creation"""
        print("\n🧪 Testing Consolidation Hierarchy...")
        try:
            subsidiary_id = str(uuid4())
            response = self.session.post(
                f"{self.base_url}/consolidation/hierarchy/subsidiary",
                json={
                    "parent_id": self.company_id,
                    "subsidiary_id": subsidiary_id
                },
                timeout=10
            )
            passed = response.status_code in (200, 201)
            self.log_test(
                "Add Entity to Hierarchy",
                passed,
                f"Status: {response.status_code}"
            )
            self.subsidiary_id = subsidiary_id
            return response.json() if passed else None
        except Exception as e:
            self.log_test("Add Entity to Hierarchy", False, str(e))
            return None
    
    def test_all_endpoints(self):
        """Run all tests"""
        print("=" * 60)
        print("🚀 FINANCE AGENT ENDPOINT TESTING SUITE")
        print("=" * 60)
        print(f"Base URL: {self.base_url}")
        print(f"Test Company ID: {self.company_id}")
        print("=" * 60)
        
        start_time = time.time()
        
        # Run agent tests
        self.test_finance_agent_chat()
        time.sleep(1)
        self.test_finance_manager_agent_chat()
        time.sleep(1)
        
        # Run close workflow tests
        self.test_close_validate()
        time.sleep(1)
        self.test_close_accruals()
        time.sleep(1)
        self.test_close_lock()
        time.sleep(1)
        self.test_close_status()
        time.sleep(1)
        
        # Run approval tests
        self.test_approval_workflow_creation()
        time.sleep(1)
        
        # Run budget tests
        self.test_budget_creation()
        time.sleep(1)
        
        # Run audit tests
        self.test_audit_event_logging()
        time.sleep(1)
        
        # Run consolidation tests
        self.test_consolidation_hierarchy()
        
        elapsed = time.time() - start_time
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed_count = sum(1 for r in self.test_results if r["passed"])
        total_count = len(self.test_results)
        pass_rate = (passed_count / total_count) * 100 if total_count > 0 else 0
        
        print(f"Tests Passed: {passed_count}/{total_count} ({pass_rate:.1f}%)")
        print(f"Total Time: {elapsed:.2f}s")
        print("=" * 60)
        
        if pass_rate == 100:
            print("✅ All tests passed! Ready for deployment.")
        else:
            print(f"⚠️  {total_count - passed_count} test(s) failed. Review above for details.")
        
        return pass_rate == 100


def main():
    import sys
    
    # Allow custom base URL as argument
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000/api/v1"
    
    tester = FinanceAgentTester(base_url)
    success = tester.test_all_endpoints()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
