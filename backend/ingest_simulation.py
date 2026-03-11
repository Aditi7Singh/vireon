import json
import os
import requests
from datetime import datetime

BASE_URL = "http://localhost:8000"
DATA_DIR = "/Users/asingh/Documents/v0/vireon/backend/data_gen_fixed/data_generation/output/json"

def load_json(filename):
    with open(os.path.join(DATA_DIR, filename), 'r') as f:
        return json.load(f)

def login():
    print(">> Logging in...")
    response = requests.post(
        f"{BASE_URL}/token",
        data={"username": "admin", "password": "password123"}
    )
    response.raise_for_status()
    return response.json()["access_token"]

def run_ingestion():
    print(f">> Starting ingestion from {DATA_DIR}...")
    
    # 1. Load data
    company_info = load_json("company_info.json")
    accounts = load_json("accounts.json")["results"]
    contacts = load_json("contacts.json")["results"]
    invoices = load_json("invoices.json")["results"]
    expenses = load_json("expenses.json")["results"]
    monthly_summary = load_json("monthly_summary.json")
    anomaly_manifest = load_json("anomaly_manifest.json")
    
    # 2. Prep SandboxData payload
    payload = {
        "company": {
            "name": company_info["name"],
            "industry": "B2B SaaS",
            "stage": "Seed",
            "initial_cash": 1000000.0,
            "founding_date": "2025-01-01"
        },
        "accounts": [],
        "contacts": [],
        "invoices": [],
        "expenses": [],
        "metrics": [],
        "anomalies": []
    }
    
    # Convert accounts
    for acc in accounts:
        payload["accounts"].append({
            "remote_id": acc["id"],
            "name": acc["name"],
            "description": acc.get("description"),
            "classification": acc["classification"],
            "type": acc["type"], # Use 'type' field directly from fixed data
            "status": acc.get("status", "ACTIVE").lower(),
            "currency": acc.get("currency", "USD")
        })

    # Convert contacts
    for c in contacts:
        payload["contacts"].append({
            "remote_id": c["id"],
            "name": c["name"],
            "type": "VENDOR" if c.get("is_supplier") else "CUSTOMER",
            "email": c.get("email_address"),
            "status": c.get("status", "ACTIVE").lower()
        })
        
    # Convert invoices
    for inv in invoices:
        payload["invoices"].append({
            "remote_id": inv["id"],
            "invoice_number": inv.get("number", inv["id"][:8]),
            "contact_remote_id": inv["contact"],
            "issue_date": inv["issue_date"][:10],
            "due_date": inv["due_date"][:10],
            "status": inv["status"].lower(),
            "type": inv["type"].upper(),
            "sub_total": inv["sub_total"],
            "total_amount": inv["total_amount"],
            "amount_due": inv.get("balance", 0.0),
            "currency": inv.get("currency", "USD")
        })
        
    # Convert expenses
    for exp in expenses:
        payload["expenses"].append({
            "remote_id": exp["id"],
            "transaction_date": exp["transaction_date"][:10],
            "account_remote_id": exp["account"],
            "contact_remote_id": exp.get("contact"),
            "total_amount": abs(exp["total_amount"]),
            "sub_total": abs(exp.get("sub_total", exp["total_amount"])),
            "tax_amount": abs(exp.get("total_tax_amount", 0)),
            "category": exp.get("memo", "General"),
            "memo": exp.get("memo", ""),
            "currency": exp.get("currency", "USD")
        })

    # Convert metrics
    for month_key, m in monthly_summary.items():
        payload["metrics"].append({
            "metric_month": f"{m['month']}-01",
            "total_revenue": m["revenue"],
            "total_expenses": m["total_expenses"],
            "net_cash_flow": m["revenue"] - m["total_expenses"],
            "ending_cash": m["cash_balance"],
            "burn_rate": m["net_burn"],
            "runway_months": m["runway_months"] if isinstance(m["runway_months"], (int, float)) else 0
        })

    # Convert anomalies
    for a in anomaly_manifest:
        # Month 1 is March 2025
        month_idx = a["month"] - 1
        year = 2025 + (3 + month_idx - 1) // 12
        month = (3 + month_idx - 1) % 12 + 1
        anomaly_date = f"{year}-{month:02d}-01"
        
        payload["anomalies"].append({
            "remote_id": a["id"],
            "anomaly_date": anomaly_date,
            "type": a["type"],
            "description": a["description"],
            "severity": "high" if a["type"] in ["absolute_spike", "duplicate_payment"] else "medium",
            "expected_value": a.get("expected_amount"),
            "actual_value": a.get("actual_amount"),
            "status": "detected"
        })
    
    # 3. Send to API
    try:
        token = login()
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(f"{BASE_URL}/sandbox/ingest?clear_existing=true", json=payload, headers=headers)
        response.raise_for_status()
        print(f"Success: {response.json()['message']}")
    except Exception as e:
        print(f"Error during ingestion: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                print(f"Validation Details: {json.dumps(e.response.json(), indent=2)}")
            except:
                print(f"Response Body: {e.response.text}")

if __name__ == "__main__":
    run_ingestion()
