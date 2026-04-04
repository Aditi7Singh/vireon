# Vireon Error Handling & API Improvements Documentation

## Overview

This document covers the systematic improvements made to Vireon's backend data layer and frontend API client to ensure production-grade reliability, proper error handling, and comprehensive logging.

## Table of Contents

1. [Backend Improvements (metrics.py)](#backend-improvements)
2. [Frontend API Enhancements (api.ts)](#frontend-api-enhancements)
3. [Using the Enhanced Hooks](#using-the-enhanced-hooks)
4. [Error Handling Best Practices](#error-handling-best-practices)
5. [Testing & Validation](#testing--validation)

---

## Backend Improvements

### File: `backend/analytics/metrics.py`

#### What Was Fixed

1. **Duplicate Code Removal**
   - Removed 40+ lines of duplicate function definitions
   - Consolidated `calculate_net_burn()`, `calculate_runway()`, `calculate_mrr()`, etc.

2. **Added Imports**
   ```python
   import logging
   import math
   logger = logging.getLogger(__name__)
   ```

3. **Enhanced 9 Core Functions**

Each function now includes:
- ✅ Input validation (None checks, type checks)
- ✅ NaN/Infinity detection and conversion
- ✅ Range validation (negative values → 0)
- ✅ Comprehensive logging at info/warning/error levels
- ✅ Edge case handling (zero division, empty lists, malformed data)

### Function-by-Function Changes

#### 1. `calculate_net_burn(revenue, gross_burn)`
**Purpose**: Calculate monthly cash burn (revenue - expenses)

**Improvements**:
- Validates both parameters are numeric and not None
- Detects and handles NaN/Inf values
- Caps negative values to 0
- Logs calculations for audit trail

**Example**:
```python
# Before: return max(0, gross_burn - revenue)

# After: 
net_burn = calculate_net_burn(100000, 150000)  # Returns 50000
net_burn = calculate_net_burn(None, 150000)    # Raises ValueError with clear message
net_burn = calculate_net_burn(100000, float('nan'))  # Logs warning, converts to 0
```

#### 2. `calculate_runway(cash_balance, net_burn)`
**Purpose**: Calculate months of cash remaining

**Improvements**:
- Validates both parameters
- Caps maximum runway at 120 months (avoids misleading high values)
- Returns "Infinite" when burn is <= 0 (sustainable business)
- Detailed logging of calculation

**Example**:
```python
# Before: if net_burn <= 0: return "Infinite" ...

# After:
runway = calculate_runway(500000, 50000)  # Returns 10.0 months
runway = calculate_runway(500000, 0)      # Returns "Infinite"
runway = calculate_runway(500000, float('nan'))  # Logs warning, uses 0
```

#### 3. `calculate_mrr(subscription_invoices)`
**Purpose**: Calculate Monthly Recurring Revenue

**Improvements**:
- Validates invoice list format
- Skips malformed invoices with warnings (doesn't crash)
- Detects NaN/Inf amounts
- Logs invoice processing results

**Example**:
```python
# Before: return sum(inv.get('amount', 0) for inv in subscription_invoices)

# After:
data = [{"amount": 50000}, {"amount": 30000}, {"amount": None}]
mrr = calculate_mrr(data)  # Returns 80000, logs 1 skipped (None amount)

# With malformed data:
data = [{"amount": 50000}, {"amount": float('nan')}, "invalid"]
mrr = calculate_mrr(data)  # Logs warnings, returns 50000
```

#### 4. `calculate_gross_burn(expenses)`
**Purpose**: Total monthly operating expenses

**Improvements**:
- Validates expense list
- Skips invalid expense items
- Handles NaN/Inf in expense amounts
- Logs skipped items

#### 5. `calculate_arr(mrr)`
**Purpose**: Annual Recurring Revenue (MRR × 12)

**Improvements**:
- Validates MRR is numeric
- Handles NaN/Inf
- Logs calculation

#### 6. `calculate_gross_margin(revenue, cogs)`
**Purpose**: (Revenue - COGS) / Revenue

**Improvements**:
- Handles zero revenue gracefully
- Caps result to valid range [0, 1]
- Logs edge cases

#### 7. `detect_anomaly(current_value, moving_average, threshold)`
**Purpose**: Threshold-based anomaly detection

**Improvements**:
- Validates all three parameters
- Handles baseline = 0 (can't compute anomaly)
- Validates threshold > 0
- Detailed logging of threshold calculations

#### 8. `calculate_budget_variance(actual, budget)`
**Purpose**: Variance analysis

**Improvements**:
- Input validation
- Handles budget = 0 (returns 0% variance safely)
- Caps percentage variance
- Logs variance calculations

#### 9. `calculate_tax_rate(total_amount, tax_amount)`
**Purpose**: Effective tax rate

**Improvements**:
- Validates inputs
- Handles zero total safely
- Caps result to [0, 100]
- Logs calculations

### Error Handling Pattern in Backend

All functions follow this pattern:

```python
def calculate_something(value1: float, value2: float) -> float:
    """
    Description with args and returns.
    Also documents what happens on invalid inputs.
    """
    # 1. Validate inputs
    if value1 is None or value2 is None:
        logger.warning(f"calculate_something: None detected - v1={value1}, v2={value2}")
        # Either raise or use default
    
    # 2. Check type
    if not isinstance(value1, (int, float)):
        logger.error(f"calculate_something: Invalid type {type(value1)}")
        raise TypeError("...")
    
    # 3. Handle NaN/Inf
    if math.isnan(value1) or math.isinf(value1):
        logger.warning(f"calculate_something: value1 is NaN/Inf, using 0")
        value1 = 0.0
    
    # 4. Validate ranges
    if value1 < 0:
        logger.warning(f"calculate_something: Negative value {value1}, capping to 0")
        value1 = 0.0
    
    # 5. Calculate (with edge case handling)
    # 6. Cap/validate result
    # 7. Log result with details
    logger.info(f"calculate_something: v1={value1}, v2={value2}, result={result}")
    return result
```

---

## Frontend API Enhancements

### File: `frontend/lib/api.ts`

#### What Was Added

1. **APIError Class** - Typed error with status code, path, and detail
2. **Enhanced fetchAPI** - Now includes:
   - Request/response logging
   - Timeout support (30s default)
   - Automatic retry (5xx, 429)
   - Detailed error messages
3. **Helper Functions**:
   - `logRequest()` - Debug logging for outgoing requests
   - `logResponse()` - Debug logging for responses
   - `logError()` - Structured error logging
4. **safeAPICall()** - Wrapper for graceful error fallbacks

#### APIError Class

```typescript
export class APIError extends Error {
  constructor(
    public status: number,
    public path: string,
    public detail: string,
    public originalError?: any
  ) {
    super(detail);
    this.name = "APIError";
  }
}

// Usage:
try {
  const data = await api.getForecastEnsemble(companyId);
} catch (error) {
  if (error instanceof APIError) {
    console.error(`Error ${error.status} on path ${error.path}: ${error.detail}`);
  }
}
```

#### Enhanced fetchAPI Function

**Features**:

1. **Timeout Support**
```typescript
// 60 second timeout
const data = await fetchAPI(
  "/data",
  { timeout: 60000 }
);
```

2. **Automatic Retries** on transient errors
```typescript
// Retries 3 times with exponential backoff
const data = await fetchAPI(
  "/data",
  { retries: 3 }  // 2^1=2s, 2^2=4s, 2^3=8s backoff
);
```

3. **Request/Response Logging**
```
[API] GET http://localhost:8000/api/v1/forecast/ensemble/...
[API] 200 http://localhost:8000/api/v1/forecast/ensemble/... (145ms)
```

4. **Detailed Error Messages**
```
Network error: Unable to reach the API server
Request timeout: API call exceeded 30000ms
HTTP 500: Internal Server Error (details from server)
```

### safeAPICall Wrapper

For graceful error handling:

```typescript
import { safeAPICall } from '@/lib/api';

// With default/fallback value
const data = await safeAPICall(
  () => api.getForecastEnsemble(companyId),
  { /* default empty forecast */ },
  "Forecast Ensemble"
);
// Returns default if API fails
```

---

## Using the Enhanced Hooks

### Installation

The hooks are prebuilt in:
```
frontend/hooks/useFinancialDataWithErrorHandling.ts
```

### Available Hooks

1. **useFinancialDataWithErrorHandling** - Generic hook for any API call
2. **useForecastEnsembleData** - Forecast data specifically
3. **useCollectionsAgingData** - AR/AP aging
4. **useInvoiceQueueData** - Invoice queue
5. **useInvoiceDsoData** - Days Sales Outstanding
6. **useFxRatesData** - FX Rates
7. **useForecastMonitorData** - Forecast quality metrics
8. **useFinancialDataAll** - Load all 5 data sources in parallel

### Basic Usage Example

```typescript
import { useForecastEnsembleData } from '@/hooks/useFinancialDataWithErrorHandling';

export function MyComponent() {
  const { data, isLoading, error, reload } = useForecastEnsembleData(companyId);

  if (isLoading) {
    return <div>Loading forecast...</div>;
  }

  if (error) {
    return (
      <div className="error">
        <p>{error}</p>
        <button onClick={reload}>Try Again</button>
      </div>
    );
  }

  return (
    <div>
      <p>Cash: ₹{data.current_cash_inr}</p>
      <p>Runway: {data.runway_months} months</p>
    </div>
  );
}
```

### Advanced Usage with Multiple Data Sources

```typescript
import { useFinancialDataAll } from '@/hooks/useFinancialDataWithErrorHandling';

export function OperationsPage() {
  const {
    forecast,
    collections,
    invoiceQueue,
    invoiceDso,
    fxRates,
    monitor,
    isLoading,
    errors,
    reload,
  } = useFinancialDataAll(companyId);

  return (
    <div>
      {/* Show all errors at once */}
      {errors.length > 0 && (
        <ErrorSummary errors={errors} />
      )}

      {/* Individual sections with their own reload buttons */}
      <ForecastSection data={forecast} />
      <CollectionsSection data={collections} />
      <InvoiceQueueSection data={invoiceQueue} />

      {/* Global reload for all */}
      <button onClick={reload} disabled={isLoading}>
        Reload All
      </button>
    </div>
  );
}
```

---

## Error Handling Best Practices

### 1. Always Show Loading State
```typescript
{isLoading ? <LoadingSkeleton /> : <MetricsDisplay data={data} />}
```

### 2. Display User-Friendly Errors
```typescript
if (error) {
  return <Alert>{error}</Alert>; // Error messages already formatted
}
```

### 3. Provide Recovery Options
```typescript
<Button onClick={reload}>Reload Data</Button>
<Button onClick={clearError}>Dismiss Error</Button>
```

### 4. Graceful Degradation with Default Values
```typescript
// Queries return default values on error, so UI doesn't crash
<MetricCard label="Cash" value={data.current_cash_inr || 0} />
```

### 5. Log Errors for Debugging
```typescript
// All errors are logged:
console.error("[API] GET /forecast failed: Network error")
```

### 6. Implement Retry Logic (Done Automatically)
```typescript
// No need to implement! fetchAPI handles:
// - Automatic retry on 5xx errors
// - Exponential backoff (2s, 4s, 8s...)
// - User-initiated reload via reload() function
```

---

## Testing & Validation

### Backend Testing

To test the enhanced metrics functions:

```python
from backend.analytics.metrics import calculate_net_burn, calculate_runway

# Test normal case
assert calculate_net_burn(100000, 150000) == 50000

# Test edge case: NaN handling
import math
result = calculate_net_burn(100000, float('nan'))
assert result == 50000  # NaN converted to 0

# Test None handling
try:
    calculate_net_burn(None, 100000)
except ValueError as e:
    print(f"Caught expected error: {e}")
```

### Frontend Testing

To test the enhanced API client:

```typescript
import { APIError, api } from '@/lib/api';

// Test error handling
try {
  const data = await api.getForecastEnsemble('invalid-id');
} catch (error) {
  if (error instanceof APIError) {
    console.log(`Status: ${error.status}`);
    console.log(`Path: ${error.path}`);
    console.log(`Detail: ${error.detail}`);
  }
}

// Test retry behavior
// (Automatic - server will retry on 5xx/429)

// Test timeout
const data = await fetchAPI('/slow-endpoint', { timeout: 5000 });
// Will throw: "Request timeout: API call exceeded 5000ms"
```

### Manual Validation

1. **Backend Health Check**:
```bash
curl http://localhost:8000/api/v1/system/startup-health
# Should return 200 with all checks passing
```

2. **Individual Endpoints**:
```bash
curl http://localhost:8000/api/v1/forecast/ensemble/[company-id]
# Should return JSON with all numeric values (no NaN/Inf)
```

3. **Frontend Loading**:
```bash
# Open http://localhost:3000
# - Loading skeletons appear
# - Data loads after 2-3 seconds
# - If error, reload button works
```

---

## Monitoring & Logs

### Enable Debug Logging

Set environment variable:
```bash
export NEXT_PUBLIC_DEBUG_API=true
```

Then open browser console to see:
```
[API] GET http://localhost:8000/api/v1/forecast/ensemble/...
[API] 200 http://localhost:8000/api/v1/forecast/ensemble/... (245ms)
```

### Backend Logs

Check Docker logs:
```bash
docker-compose logs backend -f
```

Look for entries like:
```
[info] calculate_runway: cash_balance=500000, net_burn=50000, runway=10.0 months
[warning] calculate_mrr: Skipped 1 malformed invoices out of 5
[error] calculate_net_burn: Invalid types - revenue type=<class 'str'>
```

---

## Summary

| Component | Before | After |
|-----------|--------|-------|
| **Backend Functions** | No validation, minimal logging | Full validation, comprehensive logging |
| **Error Handling** | Crashes on NaN/None | Graceful handling with warnings |
| **API Client** | Basic fetch wrapper | Timeouts, retries, detailed errors |
| **Frontend Hooks** | None | 9 specialized hooks with error handling |
| **User Experience** | Data loads or page crashes | Loading state → Data or clear error message |

---

## Next Steps

1. **Seed Demo Data** - Ensure charts show meaningful values
2. **Build Financial Functions** - Implement 14 categories of calculations
3. **Create Reasoning Engine** - Add profit/cash flow analysis
4. **Enhance Agent** - Add 30+ new tools
5. **Add Benchmarking** - Compare vs industry standards

See [IMPLEMENTATION_CHECKLIST.md](../IMPLEMENTATION_CHECKLIST.md) for details.
