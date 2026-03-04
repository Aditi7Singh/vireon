# Finance Agent - Phase 1: Data Generation Complete

## 📊 Overview
Successfully generated **realistic financial data for 5 SaaS companies** with 12 months of transactions, following **Merge.dev API architecture** standards, including **strategically injected anomalies** for AI testing.

---

## 🎯 What Was Delivered

### 1. **Database Schema** (`schema.sql`)
- ✅ **18 tables** following Merge.dev structure
- ✅ **25+ indexes** for query performance
- ✅ **3 views** for common queries (cash position, burn rate, AR aging)
- ✅ **2 functions** (runway calculation, account balance updates)
- ✅ Full relational integrity with foreign keys

**Key Tables:**
- `companies`, `accounts`, `invoices`, `expenses`, `payments`
- `contacts` (customers & vendors), `employees`, `payroll_runs`
- `cloud_costs` (detailed service breakdown)
- `monthly_metrics` (aggregated financial KPIs)
- `anomalies` (detected financial irregularities)

### 2. **Configuration** (`config.py`)
- ✅ **5 company profiles** (seed to Series B stages)
- ✅ **50+ realistic vendors** across 7 expense categories
- ✅ **3 customer segments** (Enterprise, Mid-Market, SMB)
- ✅ **8 anomaly templates** (expense spikes, duplicates, revenue drops)
- ✅ **15 employee role templates**

### 3. **Data Generator** (`generate_full_data.py`)
- ✅ Generates **12 months** of financial data per company
- ✅ **Realistic revenue growth** patterns (5-15% monthly)
- ✅ **Seasonal adjustments** (holiday revenue boosts)
- ✅ **Vendor payment cycles** with variance
- ✅ **Customer churn** simulation (2-6% monthly by segment)
- ✅ **Payroll processing** (semi-monthly runs)
- ✅ **Cloud cost breakdowns** by service
- ✅ **Strategic anomaly injection** at specified months

### 4. **Generated Data** (`generated_data/`)
- ✅ **1,936 invoices** across all companies
- ✅ **1,925 expenses** with realistic variance
- ✅ **120 payroll runs** (2 per month per company)
- ✅ **600+ cloud cost records** (detailed by service)
- ✅ **16 injected anomalies** for AI detection testing
- ✅ **60 monthly metric records** (12 per company)

**File Sizes:**
- `all_companies.json` - 3.4 MB (combined data)
- Individual company files - 300KB - 1.4MB each

---

## 📈 Generated Companies

| Company | Stage | Initial Cash | Employees | Customers | Monthly Revenue | Burn Rate |
|---------|-------|--------------|-----------|-----------|-----------------|-----------|
| **SeedlingLabs** | Series A | $1,000,000 | 8 | 25 | $45,000 | $80,000 |
| **CloudMetrics Inc** | Seed | $500,000 | 4 | 15 | $12,000 | $45,000 |
| **DataPulse Analytics** | Series B | $3,000,000 | 35 | 120 | $180,000 | $220,000 |
| **APIFlow Systems** | Seed | $750,000 | 5 | 8 | $8,000 | $55,000 |
| **SecureAuth Platform** | Series A | $1,500,000 | 15 | 45 | $75,000 | $120,000 |

---

## 🔴 Injected Anomalies (Examples)

### Critical Anomalies
1. **AWS Cost Spike** (Month 8) - 52% increase due to unoptimized EC2 instances
2. **Duplicate Vendor Payment** (Month 5) - Same invoice paid twice
3. **Marketing Budget Overrun** (Month 10) - 130% increase, campaign cap removed
4. **Database Cost Explosion** (Month 9) - 220% increase, upgraded without analysis
5. **Large Customer Churn** (Month 11) - $15K MRR loss

### Warning Anomalies
- Unauthorized SaaS subscriptions
- Unusual legal fee spikes
- Payroll processing errors

---

## 🏗️ Implementation Plan Summary

### **Your Original Plan (Phase 1)**
✅ **Tech Stack Defined**
- Frontend: Next.js + Tailwind CSS + Tremor.so charts
- Backend: Python + FastAPI
- Database: PostgreSQL (recommend **Neon** instead of Supabase)
- AI: LLM for function calling

✅ **Sandbox Data Generated**
- 12 months of realistic financial history
- Hidden anomalies for AI discovery
- Merge.dev API-compliant structure

✅ **Database Schema Created**
- Follows real-world fintech standards
- Ready for both sandbox and live data

### **What's Next (Your Phases 2-5)**

**Phase 2: Math Engine**
- Implement Python calculation functions:
  - `calculate_runway(cash, burn_rate)`
  - `calculate_burn(expenses, revenue)`
  - `scenario_modifier(action, amount)` - e.g., "hire 2 engineers"

**Phase 3: AI Integration**
- Implement LLM function calling
- Connect to backend calculation functions
- Natural language → function execution → response

**Phase 4: Anomaly Detection**
- 90-day moving average baseline
- Flag transactions >15% above baseline
- Generate alerts in real-time

**Phase 5: Frontend Dashboard**
- Build Next.js UI with Tremor charts
- Display metrics, runway projections, alerts

**Phase 6: Live Data**
- Integrate Merge.dev API (free tier)
- Swap sandbox data for live accounting data
- Zero logic changes needed (same structure)

---

## 💡 Database Alternatives (Supabase Replacement)

Since Supabase was removed, here are the **best alternatives**:

### **Recommended: Neon** ⭐⭐⭐
- **Why**: Serverless Postgres, auto-scaling, generous free tier
- **Free Tier**: 512MB storage, branches (like Git for databases)
- **Setup**: `npx neon init` → instant Postgres connection string
- **Best For**: Your use case - instant Postgres with modern DX

### Alternative: **Railway**
- **Why**: $5/month free credit, deploy backend + database together
- **Best For**: Full-stack deployment with automatic SSL

### Alternative: **Vercel Postgres**
- **Why**: Native Next.js integration (powered by Neon)
- **Best For**: If deploying on Vercel already

### Alternative: **Self-hosted**
- Docker Postgres + deploy to Fly.io/Render
- **Best For**: Complete control, learning infrastructure

---

## 🤖 LLM Recommendations

### **Best Overall: Claude 3.5 Sonnet** ⭐⭐⭐
- **Why**: Best function calling accuracy (99%+), excellent numerical reasoning
- **Pricing**: $3/$15 per million tokens (input/output)
- **Best For**: Complex scenario analysis, financial explanations
- **Example**: "What if we hire 2 engineers?" → Executes function → Clear explanation

### Alternative: **GPT-4o**
- **Why**: Excellent function calling, fast, well-documented
- **Pricing**: $2.50/$10 per million tokens
- **Best For**: General-purpose finance intelligence

### Budget: **GPT-4o-mini**
- **Why**: 15-20x cheaper, still capable
- **Pricing**: $0.15/$0.60 per million tokens
- **Best For**: High-volume simple queries

### **Recommended Strategy: Hybrid**
```python
# Route based on complexity
if query_complexity == "simple":
    use GPT-4o-mini  # 90% of requests
elif query_complexity == "complex":
    use Claude Sonnet  # 10% of requests

# Cost: ~$15-20/month vs $150+ using only premium
```

---

## 🚀 How to Use This Data

### **1. Load into PostgreSQL**
```bash
# Create database
createdb finance_agent

# Load schema
psql -d finance_agent -f schema.sql

# Load data (Python script)
python load_data_to_db.py
```

### **2. Test with Sample Queries**
```sql
-- Current cash position
SELECT * FROM v_current_cash_position;

-- Recent burn rate
SELECT * FROM v_recent_burn_rate;

-- Find anomalies
SELECT * FROM anomalies 
WHERE severity = 'critical' 
ORDER BY anomaly_date DESC;

-- Monthly runway trend
SELECT metric_month, runway_months, burn_rate
FROM monthly_metrics
WHERE company_id = 'your-company-id'
ORDER BY metric_month;
```

### **3. Build AI Function Calling**
```python
# Example function for LLM to call
def calculate_hiring_impact(num_engineers, avg_salary=150000):
    """Calculate runway impact of new hires"""
    current_burn = get_current_burn_rate()
    additional_burn = (num_engineers * avg_salary) / 12
    new_burn = current_burn + additional_burn
    
    current_cash = get_cash_balance()
    new_runway = current_cash / new_burn
    
    return {
        "current_runway": current_runway_months,
        "new_runway": new_runway,
        "impact": current_runway_months - new_runway
    }
```

---

## 📁 File Structure

```
/outputs/
├── schema.sql                      # PostgreSQL database schema
├── config.py                       # Company profiles & configuration
├── generate_full_data.py           # Main data generator
├── test_generator.py               # Test suite
├── generated_data/
│   ├── all_companies.json          # Combined data (3.4 MB)
│   ├── seedlinglabs.json           # SeedlingLabs data
│   ├── cloudmetrics_inc.json       # CloudMetrics data
│   ├── datapulse_analytics.json    # DataPulse data
│   ├── apiflow_systems.json        # APIFlow data
│   └── secureauth_platform.json    # SecureAuth data
└── README.md                       # This file
```

---

## ✅ Tests to Run

```bash
# Test 1: Verify configuration
python3 test_generator.py

# Test 2: Verify schema
psql -d finance_agent -f schema.sql --dry-run

# Test 3: Sample data query
python3 -c "
import json
with open('generated_data/seedlinglabs.json') as f:
    data = json.load(f)
    print(f'Invoices: {len(data[\"invoices\"])}')
    print(f'Anomalies: {len(data[\"anomalies\"])}')
"
```

---

## 🎓 Key Design Decisions

1. **Merge.dev Compliance**: Schema matches real API structure → easy to swap sandbox for live data
2. **Realistic Variance**: 8-15% variance in expenses/revenue → not perfectly uniform
3. **Strategic Anomalies**: Injected at specific months with realistic causes
4. **Relational Integrity**: Full foreign keys → data consistency guaranteed
5. **Performance Optimized**: 25+ indexes for common queries

---

## 📊 Sample Data Insights

### SeedlingLabs (Final Month)
- **Cash**: $323,487
- **Revenue**: $65,814/month
- **Burn**: $75,449/month
- **Runway**: 4.3 months ⚠️ (needs action!)

### DataPulse Analytics (Final Month)
- **Cash**: $2,048,669
- **Revenue**: $265,656/month
- **Burn**: $46,634/month
- **Runway**: 43.9 months ✅ (healthy!)

---

## 🔥 Next Steps

1. **Set up Neon PostgreSQL** database
2. **Load schema.sql** into database
3. **Import generated JSON data** into tables
4. **Build Phase 2**: Python calculation functions
5. **Build Phase 3**: LLM integration with Claude Sonnet
6. **Build Phase 4**: Anomaly detection engine
7. **Build Phase 5**: Next.js dashboard

---

## 📞 Support

For questions about:
- **Database setup**: Check Neon documentation
- **LLM integration**: Anthropic/OpenAI API docs
- **Data structure**: Review `schema.sql` comments
- **Anomaly patterns**: See `config.py` ANOMALY_TEMPLATES

---

**Generated**: March 3, 2026  
**Data Volume**: 6.5 MB, 1,936 invoices, 1,925 expenses, 16 anomalies  
**Status**: ✅ Phase 1 Complete - Ready for Phase 2
