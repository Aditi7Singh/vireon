#!/usr/bin/env python3
"""
Full Financial Data Generator
Generates 12 months of realistic data for all companies with anomalies
"""

import uuid, random, json, os
from datetime import datetime, timedelta
from decimal import Decimal
from config import *


class FinancialDataGenerator:
    def __init__(self, profile):
        self.company = profile
        self.company_id = str(uuid.uuid4())
        self.start_date = GENERATION_CONFIG["start_date"]
        self.months = GENERATION_CONFIG["months_to_generate"]
        
        self.data = {
            "companies": [], "accounts": [], "invoices": [], "invoice_line_items": [],
            "expenses": [], "expense_line_items": [], "payments": [], "contacts": [],
            "employees": [], "payroll_runs": [], "cloud_costs": [],
            "monthly_metrics": [], "anomalies": []
        }
        
        self.customers, self.vendors = [], []
        self.anomalies_to_inject = []
    
    def generate_all(self):
        print(f"\n{'='*80}")
        print(f"GENERATING: {self.company['name']}")
        print(f"{'='*80}")
        
        self._create_company()
        self._create_customers()
        self._create_vendors()
        self._select_anomalies()
        
        print(f"Generating {self.months} months of data...")
        for m in range(self.months):
            print(f"  Month {m+1:2d}/12", end="")
            self._generate_month(m)
            print(" ✓")
        
        self._calculate_metrics()
        self._print_summary()
        return self.data
    
    def _create_company(self):
        self.data["companies"].append({
            "id": self.company_id,
            "name": self.company["name"],
            "industry": self.company["industry"],
            "stage": self.company["stage"],
            "initial_cash": float(self.company["initial_cash"]),
            "founding_date": self.company["founding_date"].isoformat(),
        })
    
    def _create_customers(self):
        count = self.company["customers_count"]
        for segment, config in CUSTOMER_SEGMENTS.items():
            segment_count = int(count * config["count_percentage"])
            for _ in range(segment_count):
                cust_id = str(uuid.uuid4())
                name = f"{random.choice(ADJECTIVES)} {random.choice(NOUNS)}"
                mrr = Decimal(str(random.uniform(
                    float(config["mrr_range"][0]),
                    float(config["mrr_range"][1])
                ))).quantize(Decimal("0.01"))
                
                customer = {
                    "id": cust_id, "name": name, "mrr": mrr,
                    "churn_rate": config["churn_rate"],
                    "payment_terms": config["payment_terms"],
                    "segment": segment, "status": "active"
                }
                self.customers.append(customer)
                self.data["contacts"].append({
                    "id": cust_id, "company_id": self.company_id,
                    "name": name, "type": "customer", "status": "active"
                })
    
    def _create_vendors(self):
        for category, cat_data in EXPENSE_CATEGORIES.items():
            for vendor_name, vendor_config in cat_data["vendors"].items():
                vend_id = str(uuid.uuid4())
                vendor = {
                    "id": vend_id, "name": vendor_name, "category": category,
                    "base_monthly": vendor_config["base_monthly"],
                    "variance": vendor_config.get("variance", 0.10)
                }
                self.vendors.append(vendor)
                self.data["contacts"].append({
                    "id": vend_id, "company_id": self.company_id,
                    "name": vendor_name, "type": "vendor", "status": "active"
                })
    
    def _select_anomalies(self):
        num = GENERATION_CONFIG["anomalies_per_company"]
        self.anomalies_to_inject = random.sample(ANOMALY_TEMPLATES, min(num, len(ANOMALY_TEMPLATES)))
        print(f"\nAnomalies to inject: {len(self.anomalies_to_inject)}")
        for a in self.anomalies_to_inject:
            print(f"  • Month {a['month']:2d}: {a['name']} ({a['severity']})")
    
    def _generate_month(self, month_num):
        month_date = self.start_date + timedelta(days=30 * month_num)
        
        # Generate revenue
        for customer in self.customers:
            if customer["status"] != "active":
                continue
            
            # Simulate churn
            if random.random() < customer["churn_rate"]:
                customer["status"] = "churned"
                continue
            
            # Create invoice
            inv_id = str(uuid.uuid4())
            amount = customer["mrr"] * Decimal(str(random.uniform(0.95, 1.05)))
            
            self.data["invoices"].append({
                "id": inv_id,
                "company_id": self.company_id,
                "invoice_number": f"INV-{month_date.strftime('%Y%m')}-{len(self.data['invoices'])+1:04d}",
                "contact_id": customer["id"],
                "issue_date": month_date.isoformat(),
                "total_amount": float(amount),
                "amount_due": float(amount),
                "status": "paid",
                "currency": "USD"
            })
            
            self.data["invoice_line_items"].append({
                "id": str(uuid.uuid4()),
                "invoice_id": inv_id,
                "description": f"{customer['segment'].title()} Plan",
                "quantity": 1.0,
                "unit_price": float(amount),
                "total_amount": float(amount)
            })
        
        # Generate expenses
        for vendor in self.vendors:
            # Check for anomaly
            anomaly = next((a for a in self.anomalies_to_inject
                           if a["month"] == month_num + 1
                           and a.get("vendor") == vendor["name"]
                           and a["type"] in ["expense_spike", "duplicate_payment"]), None)
            
            # Calculate amount
            variance = random.uniform(1 - vendor["variance"], 1 + vendor["variance"])
            amount = vendor["base_monthly"] * Decimal(str(variance))
            
            # Apply anomaly
            if anomaly and anomaly["type"] == "expense_spike":
                original_amount = amount
                amount *= Decimal(str(anomaly["multiplier"]))
                self._record_anomaly(month_date, anomaly, original_amount, amount, vendor["name"])
            
            # Create expense
            exp_id = str(uuid.uuid4())
            self.data["expenses"].append({
                "id": exp_id,
                "company_id": self.company_id,
                "transaction_date": month_date.isoformat(),
                "contact_id": vendor["id"],
                "total_amount": float(amount),
                "category": vendor["category"],
                "currency": "USD"
            })
            
            self.data["expense_line_items"].append({
                "id": str(uuid.uuid4()),
                "expense_id": exp_id,
                "description": f"{vendor['name']} - {vendor['category']}",
                "amount": float(amount)
            })
            
            # Generate cloud cost details
            if vendor["category"] == "Cloud":
                services = EXPENSE_CATEGORIES["Cloud"]["vendors"].get(vendor["name"], {}).get("services", ["General"])
                for service in services[:3]:  # Top 3 services
                    self.data["cloud_costs"].append({
                        "id": str(uuid.uuid4()),
                        "company_id": self.company_id,
                        "provider": vendor["name"].split()[0].lower(),
                        "service": service,
                        "billing_date": month_date.isoformat(),
                        "cost": float(amount / len(services)),
                        "currency": "USD"
                    })
            
            # Handle duplicate payment anomaly
            if anomaly and anomaly["type"] == "duplicate_payment":
                dup_date = month_date + timedelta(days=random.randint(10, 20))
                dup_id = str(uuid.uuid4())
                self.data["expenses"].append({
                    "id": dup_id,
                    "company_id": self.company_id,
                    "transaction_date": dup_date.isoformat(),
                    "contact_id": vendor["id"],
                    "total_amount": float(anomaly["amount"]),
                    "category": vendor["category"],
                    "currency": "USD"
                })
                self._record_anomaly(dup_date, anomaly, Decimal("0"), anomaly["amount"], vendor["name"])
        
        # Generate payroll (semi-monthly)
        for run in [1, 2]:
            pr_id = str(uuid.uuid4())
            run_date = month_date + timedelta(days=15 if run == 1 else 30)
            
            # Simple payroll calculation
            monthly_payroll = self.company["employee_count"] * Decimal("120000") / 12  # Average $120k salary
            payroll_amount = monthly_payroll / 2  # Semi-monthly
            
            self.data["payroll_runs"].append({
                "id": pr_id,
                "company_id": self.company_id,
                "run_date": run_date.isoformat(),
                "pay_period_start": month_date.isoformat(),
                "pay_period_end": run_date.isoformat(),
                "total_gross_pay": float(payroll_amount),
                "total_net_pay": float(payroll_amount * Decimal("0.75")),
                "status": "paid"
            })
        
        # Generate payments (cash received)
        for inv in self.data["invoices"]:
            if inv["status"] == "paid" and "payment_id" not in inv:
                payment_date = datetime.fromisoformat(inv["issue_date"]) + timedelta(days=random.randint(5, 35))
                if payment_date <= month_date + timedelta(days=30):
                    pmt_id = str(uuid.uuid4())
                    self.data["payments"].append({
                        "id": pmt_id,
                        "company_id": self.company_id,
                        "transaction_date": payment_date.isoformat(),
                        "total_amount": inv["total_amount"],
                        "type": "payment_received",
                        "currency": "USD"
                    })
                    inv["payment_id"] = pmt_id
    
    def _record_anomaly(self, date, template, expected, actual, vendor_name):
        variance = ((actual - expected) / expected * 100) if expected > 0 else 0
        
        self.data["anomalies"].append({
            "id": str(uuid.uuid4()),
            "company_id": self.company_id,
            "detected_at": datetime.now().isoformat(),
            "anomaly_date": date.isoformat(),
            "severity": template["severity"],
            "type": template["type"],
            "category": template.get("category", "Unknown"),
            "description": f"{template['description']} (Vendor: {vendor_name})",
            "expected_value": float(expected),
            "actual_value": float(actual),
            "variance_percent": float(variance),
            "variance_amount": float(actual - expected),
            "status": "open"
        })
    
    def _calculate_metrics(self):
        for m in range(self.months):
            month_date = (self.start_date + timedelta(days=30 * m)).replace(day=1)
            
            # Calculate revenue
            month_invoices = [inv for inv in self.data["invoices"]
                            if datetime.fromisoformat(inv["issue_date"]).month == month_date.month
                            and datetime.fromisoformat(inv["issue_date"]).year == month_date.year]
            total_revenue = sum(Decimal(str(inv["total_amount"])) for inv in month_invoices)
            
            # Calculate expenses
            month_expenses = [exp for exp in self.data["expenses"]
                            if datetime.fromisoformat(exp["transaction_date"]).month == month_date.month
                            and datetime.fromisoformat(exp["transaction_date"]).year == month_date.year]
            total_expenses = sum(Decimal(str(exp["total_amount"])) for exp in month_expenses)
            
            # Calculate payroll
            month_payroll = [pr for pr in self.data["payroll_runs"]
                           if datetime.fromisoformat(pr["run_date"]).month == month_date.month
                           and datetime.fromisoformat(pr["run_date"]).year == month_date.year]
            payroll_total = sum(Decimal(str(pr["total_gross_pay"])) for pr in month_payroll)
            
            # Calculate cash position
            if m == 0:
                starting_cash = self.company["initial_cash"]
            else:
                starting_cash = Decimal(str(self.data["monthly_metrics"][-1]["ending_cash"]))
            
            cash_inflow = total_revenue
            cash_outflow = total_expenses + payroll_total
            ending_cash = starting_cash + cash_inflow - cash_outflow
            
            # Calculate metrics
            burn_rate = cash_outflow - total_revenue
            runway = ending_cash / burn_rate if burn_rate > 0 else Decimal("999")
            
            self.data["monthly_metrics"].append({
                "id": str(uuid.uuid4()),
                "company_id": self.company_id,
                "metric_month": month_date.isoformat(),
                "starting_cash": float(starting_cash),
                "ending_cash": float(ending_cash),
                "cash_inflow": float(cash_inflow),
                "cash_outflow": float(cash_outflow),
                "net_cash_flow": float(cash_inflow - cash_outflow),
                "total_revenue": float(total_revenue),
                "total_expenses": float(total_expenses + payroll_total),
                "payroll_expenses": float(payroll_total),
                "burn_rate": float(burn_rate),
                "runway_months": min(float(runway), 999.0)
            })
    
    def _print_summary(self):
        print(f"\n{'='*80}")
        print(f"SUMMARY")
        print(f"{'='*80}")
        print(f"Invoices:       {len(self.data['invoices']):,}")
        print(f"Expenses:       {len(self.data['expenses']):,}")
        print(f"Payroll Runs:   {len(self.data['payroll_runs']):,}")
        print(f"Cloud Costs:    {len(self.data['cloud_costs']):,}")
        print(f"Anomalies:      {len(self.data['anomalies']):,}")
        
        if self.data['monthly_metrics']:
            final = self.data['monthly_metrics'][-1]
            print(f"\nFinal Month (Month 12):")
            print(f"  Cash:         ${final['ending_cash']:,.2f}")
            print(f"  Revenue:      ${final['total_revenue']:,.2f}")
            print(f"  Expenses:     ${final['total_expenses']:,.2f}")
            print(f"  Burn Rate:    ${final['burn_rate']:,.2f}")
            print(f"  Runway:       {final['runway_months']:.1f} months")


def main():
    print("\n" + "="*80)
    print("FINANCIAL DATA GENERATOR - FULL RUN")
    print("="*80)
    
    os.makedirs("generated_data", exist_ok=True)
    
    all_data = {}
    
    for profile in COMPANY_PROFILES:
        generator = FinancialDataGenerator(profile)
        company_data = generator.generate_all()
        all_data[profile["name"]] = company_data
        
        # Save individual company file
        filename = f"generated_data/{profile['name'].lower().replace(' ', '_')}.json"
        with open(filename, 'w') as f:
            json.dump(company_data, f, indent=2)
        print(f"\n→ Saved: {filename}\n")
    
    # Save combined file
    with open("generated_data/all_companies.json", 'w') as f:
        json.dump(all_data, f, indent=2)
    
    # Print overall summary
    print("\n" + "="*80)
    print("GENERATION COMPLETE!")
    print("="*80)
    print(f"Companies:      {len(COMPANY_PROFILES)}")
    print(f"Total Invoices: {sum(len(d['invoices']) for d in all_data.values()):,}")
    print(f"Total Expenses: {sum(len(d['expenses']) for d in all_data.values()):,}")
    print(f"Total Anomalies: {sum(len(d['anomalies']) for d in all_data.values()):,}")
    print(f"\nFiles saved in: generated_data/")
    print(f"  • {len(all_data)} individual company JSON files")
    print(f"  • 1 combined all_companies.json file")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
