# Finance Agent - Test Results

**Test Run Date:** 2026-05-04 11:24:55


## Test Results Summary

| Metric | Score/Result | Pass Rate | Status |
|--------|--------------|-----------|--------|
| Response Relevance | 93.33% | 100% | ✅ PASS |
| Financial Accuracy | 98.10% | 2/3 | ⚠️ PARTIAL |
| Decision Usefulness | 67% | 2/3 | ⚠️ PARTIAL |
| Latency (Response Time) | 2.9s avg | 4/4 | ⚠️ PARTIAL |

---

### Response Relevance

- **What is our runway?**: ✅ PASS (score: 1.0)
- **How is our burn trending?**: ✅ PASS (score: 1.0)
- **Show me recent anomalies**: ✅ PASS (score: 0.8)

### Financial Accuracy

- **runway_error_pct**: 0.1%
- **cost_error_pct**: 3.7%
- **determinism**: PASS

### Decision Usefulness

- **Critical runway (<6mo)**: ✅ Actionable
- **Scenario analysis**: ❌ Not Actionable
- **Anomaly investigation**: ✅ Actionable

### Latency (Response Time)

- **Simple Query (cash balance)**: ✅ PASS (score: N/A)
- **Complex Query (burn analysis)**: ✅ PASS (score: N/A)
- **Scenario Simulation**: ✅ PASS (score: N/A)
- **Anomaly Scan**: ✅ PASS (score: N/A)

