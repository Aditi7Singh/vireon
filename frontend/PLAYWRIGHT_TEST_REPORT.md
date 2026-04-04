# Vireon Frontend — Playwright Test Report

**Generated:** 2026-04-04 13:20:05  
**Framework:** Playwright 1.58.2  
**Base URL:** http://localhost:3000  
**Browser Projects:** chromium, firefox, mobile-chrome

---

## Executive Summary

| Metric | Value |
|--------|-------|
| **Total Tests** | 489 |
| **Passed** | ✅ 369 |
| **Failed** | ❌ 119 |
| **Skipped** | ⏭️ 0 |
| **Flaky** | ⚠️ 1 |
| **Pass Rate** | **75.5%** |
| **Total Duration** | 3723.8s |

> ❌ **75.5% pass rate.** Significant failures detected — immediate attention required.

---

## Test Coverage Matrix

| Module | Tests | Passed | Failed | Pass Rate |
|--------|-------|--------|--------|-----------|
| ✅ Landing Page | 5 | 5 | 0 | 100% |
| ❌ Dashboard | 5 | 3 | 2 | 60% |
| ❌ Form Controls | 5 | 4 | 1 | 80% |
| ❌ Visual Hierarchy | 1 | 0 | 1 | 0% |
| ❌ AI Agent Page | 12 | 8 | 4 | 67% |
| ❌ Anomalies & Financial Risk Page | 22 | 1 | 21 | 5% |
| ✅ Vireon E2E Tests | 1 | 1 | 0 | 100% |
| ❌ Benchmarking / Performance Intelligence Page | 12 | 7 | 5 | 58% |
| ❌ CEO Dashboard Page | 27 | 26 | 1 | 96% |
| ❌ Chat Drawer Component | 9 | 8 | 1 | 89% |
| ❌ Cross-Feature Integration & User Journey Tests | 11 | 4 | 6 | 36% |
| ❌ CTO Dashboard Page | 27 | 25 | 2 | 93% |
| ❌ Dashboard Home Page | 20 | 16 | 4 | 80% |
| ❌ Expenses / Capital Allocations Page | 11 | 9 | 2 | 82% |
| ❌ Feature Hub / Action Hub Page | 33 | 31 | 2 | 94% |
| ❌ Finance Dashboard Page | 17 | 10 | 7 | 59% |
| ❌ Cross-Page Navigation & Integration | 4 | 3 | 1 | 75% |
| ❌ Dashboard Layout Integration | 2 | 1 | 1 | 50% |
| ✅ Responsive Layout Tests | 3 | 3 | 0 | 100% |
| ✅ Landing Page (Home) | 15 | 15 | 0 | 100% |
| ❌ Operations Center Page | 15 | 13 | 2 | 87% |
| ✅ Page Load Times | 16 | 16 | 0 | 100% |
| ✅ Console Error Checks | 7 | 7 | 0 | 100% |
| ✅ Resource Loading | 2 | 2 | 0 | 100% |
| ❌ Viewport Stability | 2 | 1 | 1 | 50% |
| ❌ Responsive Layout Tests - All Pages | 67 | 39 | 28 | 58% |
| ❌ Revenue Intelligence Page | 20 | 17 | 3 | 85% |
| ❌ Runway & Survival Page | 17 | 16 | 1 | 94% |
| ❌ Scenarios / Strategic Simulations Page | 26 | 23 | 3 | 88% |
| ❌ Settings Page | 19 | 14 | 5 | 74% |
| ✅ Sidebar Navigation | 23 | 23 | 0 | 100% |
| ❌ Tax Compliance Hub Page | 19 | 18 | 1 | 95% |
| ❌ Visual Regression & Screenshot Tests | 14 | 0 | 14 | 0% |

---

## ❌ Failed Tests Detail

### `dashboard has semantic main content area`
- **Suite:** accessibility.spec.ts > Accessibility & Semantic Structure Tests > Dashboard
- **Browser:** chromium
- **Duration:** 14.60s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('main')
Expected: visible
Error: strict mode violation: locator('main') resolved to 2 elemen`

### `interactive buttons have visible text or aria-label`
- **Suite:** accessibility.spec.ts > Accessibility & Semantic Structure Tests > Dashboard
- **Browser:** chromium
- **Duration:** 12.98s
- **Error:** `Error: [2mexpect([22m[31mreceived[39m[2m).[22mtoBeTruthy[2m()[22m

Received: [31mnull[39m`

### `anomaly search input has placeholder text`
- **Suite:** accessibility.spec.ts > Accessibility & Semantic Structure Tests > Form Controls
- **Browser:** chromium
- **Duration:** 15.06s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('input[placeholder="Search anomalies"]')
Expected: visible
Timeout: 5000ms
Error: element(s)`

### `each dashboard page has a clear h1 heading`
- **Suite:** accessibility.spec.ts > Accessibility & Semantic Structure Tests > Visual Hierarchy
- **Browser:** chromium
- **Duration:** 30.61s
- **Error:** `[31mTest timeout of 30000ms exceeded.[39m`

### `renders page title "Vireon AI Assistant"`
- **Suite:** ai-agent.spec.ts > AI Agent Page
- **Browser:** chromium
- **Duration:** 11.06s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Vireon AI Assistant')
Expected: visible
Timeout: 5000ms
Error: element(s) not found

C`

### `renders chat message area`
- **Suite:** ai-agent.spec.ts > AI Agent Page
- **Browser:** chromium
- **Duration:** 9.56s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=/ready to help|Unable to load/')
Expected: visible
Timeout: 5000ms
Error: element(s) n`

### `clicking a quick action populates chat with user message`
- **Suite:** ai-agent.spec.ts > AI Agent Page
- **Browser:** chromium
- **Duration:** 4.16s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Survival path audit')
Expected: visible
Error: strict mode violation: locator('text=Su`

### `assistant messages appear on the left side`
- **Suite:** ai-agent.spec.ts > AI Agent Page
- **Browser:** chromium
- **Duration:** 7.68s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('.justify-start').first()
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Cal`

### `renders page title "Financial Risk & Anomalies"`
- **Suite:** anomalies.spec.ts > Anomalies & Financial Risk Page
- **Browser:** chromium
- **Duration:** 7.54s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Financial Risk & Anomalies')
Expected: visible
Timeout: 5000ms
Error: element(s) not f`

### `displays heading "Financial Risk Dashboard"`
- **Suite:** anomalies.spec.ts > Anomalies & Financial Risk Page
- **Browser:** chromium
- **Duration:** 10.05s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('h1:has-text("Financial Risk Dashboard")')
Expected: visible
Timeout: 5000ms
Error: element(`

### `shows Real-time monitoring badge`
- **Suite:** anomalies.spec.ts > Anomalies & Financial Risk Page
- **Browser:** chromium
- **Duration:** 7.05s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Real-time monitoring')
Expected: visible
Timeout: 5000ms
Error: element(s) not found

`

### `has Test Email button`
- **Suite:** anomalies.spec.ts > Anomalies & Financial Risk Page
- **Browser:** chromium
- **Duration:** 8.89s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('button:has-text("Test Email")')
Expected: visible
Timeout: 5000ms
Error: element(s) not fou`

### `has Send Alerts Now button`
- **Suite:** anomalies.spec.ts > Anomalies & Financial Risk Page
- **Browser:** chromium
- **Duration:** 10.12s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('button:has-text("Send Alerts Now")')
Expected: visible
Timeout: 5000ms
Error: element(s) no`

### `has Configure button`
- **Suite:** anomalies.spec.ts > Anomalies & Financial Risk Page
- **Browser:** chromium
- **Duration:** 10.37s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('button:has-text("Configure")')
Expected: visible
Timeout: 5000ms
Error: element(s) not foun`

### `displays Risk Score card`
- **Suite:** anomalies.spec.ts > Anomalies & Financial Risk Page
- **Browser:** chromium
- **Duration:** 9.58s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Risk Score')
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call log:
`

### `displays Anomalies count card`
- **Suite:** anomalies.spec.ts > Anomalies & Financial Risk Page
- **Browser:** chromium
- **Duration:** 9.54s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('.grid.gap-4').locator('text=Anomalies').first()
Expected: visible
Timeout: 5000ms
Error: el`

### `displays Alerts Sent card`
- **Suite:** anomalies.spec.ts > Anomalies & Financial Risk Page
- **Browser:** chromium
- **Duration:** 10.11s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Alerts Sent')
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call log:`

### `renders Detected Anomalies section`
- **Suite:** anomalies.spec.ts > Anomalies & Financial Risk Page
- **Browser:** chromium
- **Duration:** 9.98s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Detected Anomalies')
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Ca`

### `has severity filter buttons (all, critical, warning, info)`
- **Suite:** anomalies.spec.ts > Anomalies & Financial Risk Page
- **Browser:** chromium
- **Duration:** 12.86s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('button:has-text("all")')
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Cal`

### `clicking filter button updates active state`
- **Suite:** anomalies.spec.ts > Anomalies & Financial Risk Page
- **Browser:** chromium
- **Duration:** 21.37s
- **Error:** `TimeoutError: locator.click: Timeout 15000ms exceeded.
Call log:
[2m  - waiting for locator('button:has-text("critical")')[22m
`

### `has anomaly search input`
- **Suite:** anomalies.spec.ts > Anomalies & Financial Risk Page
- **Browser:** chromium
- **Duration:** 10.54s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('input[placeholder="Search anomalies"]')
Expected: visible
Timeout: 5000ms
Error: element(s)`

### `typing in search filters anomalies list`
- **Suite:** anomalies.spec.ts > Anomalies & Financial Risk Page
- **Browser:** chromium
- **Duration:** 21.55s
- **Error:** `TimeoutError: locator.fill: Timeout 15000ms exceeded.
Call log:
[2m  - waiting for locator('input[placeholder="Search anomalies"]')[22m
`

### `clicking Configure opens email alert configuration panel`
- **Suite:** anomalies.spec.ts > Anomalies & Financial Risk Page
- **Browser:** chromium
- **Duration:** 26.93s
- **Error:** `TimeoutError: page.click: Timeout 15000ms exceeded.
Call log:
[2m  - waiting for locator('button:has-text("Configure")')[22m
`

### `configuration panel has CEO Email input`
- **Suite:** anomalies.spec.ts > Anomalies & Financial Risk Page
- **Browser:** chromium
- **Duration:** 26.98s
- **Error:** `TimeoutError: page.click: Timeout 15000ms exceeded.
Call log:
[2m  - waiting for locator('button:has-text("Configure")')[22m
`

### `configuration panel has Finance Team textarea`
- **Suite:** anomalies.spec.ts > Anomalies & Financial Risk Page
- **Browser:** chromium
- **Duration:** 21.13s
- **Error:** `TimeoutError: page.click: Timeout 15000ms exceeded.
Call log:
[2m  - waiting for locator('button:has-text("Configure")')[22m
`

### `configuration panel has Additional Recipients textarea`
- **Suite:** anomalies.spec.ts > Anomalies & Financial Risk Page
- **Browser:** chromium
- **Duration:** 21.04s
- **Error:** `TimeoutError: page.click: Timeout 15000ms exceeded.
Call log:
[2m  - waiting for locator('button:has-text("Configure")')[22m
`

### `configuration panel has Save and Cancel buttons`
- **Suite:** anomalies.spec.ts > Anomalies & Financial Risk Page
- **Browser:** chromium
- **Duration:** 20.97s
- **Error:** `TimeoutError: page.click: Timeout 15000ms exceeded.
Call log:
[2m  - waiting for locator('button:has-text("Configure")')[22m
`

### `clicking Cancel closes configuration panel`
- **Suite:** anomalies.spec.ts > Anomalies & Financial Risk Page
- **Browser:** chromium
- **Duration:** 25.50s
- **Error:** `TimeoutError: page.click: Timeout 15000ms exceeded.
Call log:
[2m  - waiting for locator('button:has-text("Configure")')[22m
`

### `shows Currently Configured section within config panel`
- **Suite:** anomalies.spec.ts > Anomalies & Financial Risk Page
- **Browser:** chromium
- **Duration:** 25.51s
- **Error:** `TimeoutError: page.click: Timeout 15000ms exceeded.
Call log:
[2m  - waiting for locator('button:has-text("Configure")')[22m
`

### `renders page title "Performance Intelligence"`
- **Suite:** benchmarking.spec.ts > Benchmarking / Performance Intelligence Page
- **Browser:** chromium
- **Duration:** 17.27s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Performance Intelligence')
Expected: visible
Timeout: 5000ms
Error: element(s) not fou`

### `displays at least 3 benchmark metric cards`
- **Suite:** benchmarking.spec.ts > Benchmarking / Performance Intelligence Page
- **Browser:** chromium
- **Duration:** 4.86s
- **Error:** `Error: [2mexpect([22m[31mreceived[39m[2m).[22mtoBeGreaterThanOrEqual[2m([22m[32mexpected[39m[2m)[22m

Expected: >= [32m3[39m
Received:    [31m0[39m`

### `each metric card has a Target label`
- **Suite:** benchmarking.spec.ts > Benchmarking / Performance Intelligence Page
- **Browser:** chromium
- **Duration:** 2.73s
- **Error:** `Error: [2mexpect([22m[31mreceived[39m[2m).[22mtoBeGreaterThanOrEqual[2m([22m[32mexpected[39m[2m)[22m

Expected: >= [32m3[39m
Received:    [31m0[39m`

### `each metric card has a status badge`
- **Suite:** benchmarking.spec.ts > Benchmarking / Performance Intelligence Page
- **Browser:** chromium
- **Duration:** 2.69s
- **Error:** `Error: [2mexpect([22m[31mreceived[39m[2m).[22mtoBeGreaterThanOrEqual[2m([22m[32mexpected[39m[2m)[22m

Expected: >= [32m3[39m
Received:    [31m0[39m`

### `each metric card has Get advice button`
- **Suite:** benchmarking.spec.ts > Benchmarking / Performance Intelligence Page
- **Browser:** chromium
- **Duration:** 3.10s
- **Error:** `Error: [2mexpect([22m[31mreceived[39m[2m).[22mtoBeGreaterThanOrEqual[2m([22m[32mexpected[39m[2m)[22m

Expected: >= [32m3[39m
Received:    [31m0[39m`

### `displays Headcount KPI card`
- **Suite:** ceo-dashboard.spec.ts > CEO Dashboard Page
- **Browser:** chromium
- **Duration:** 5.46s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Headcount')
Expected: visible
Error: strict mode violation: locator('text=Headcount') `

### `chat drawer has close button`
- **Suite:** chat-drawer.spec.ts > Chat Drawer Component
- **Browser:** chromium
- **Duration:** 18.29s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=AI Financial Assistant').locator('..').locator('..').locator('button').last()
Expected`

### `CEO full journey: landing → dashboard → CEO → export → scenarios`
- **Suite:** cross-feature-journeys.spec.ts > Cross-Feature Integration & User Journey Tests
- **Browser:** chromium
- **Duration:** 30.93s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Strategic Simulations')
Expected: visible
Timeout: 5000ms
Error: element(s) not found
`

### `anomaly workflow: features → seed anomalies → view anomalies → configure`
- **Suite:** cross-feature-journeys.spec.ts > Cross-Feature Integration & User Journey Tests
- **Browser:** chromium
- **Duration:** 22.20s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Financial Risk & Anomalies')
Expected: visible
Timeout: 5000ms
Error: element(s) not f`

### `AI agent journey: features hub → agent page → quick actions`
- **Suite:** cross-feature-journeys.spec.ts > Cross-Feature Integration & User Journey Tests
- **Browser:** chromium
- **Duration:** 18.88s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Vireon AI Assistant')
Expected: visible
Timeout: 5000ms
Error: element(s) not found

C`

### `revenue analysis to benchmarking journey`
- **Suite:** cross-feature-journeys.spec.ts > Cross-Feature Integration & User Journey Tests
- **Browser:** chromium
- **Duration:** 12.93s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Revenue Intelligence')
Expected: visible
Timeout: 5000ms
Error: element(s) not found

`

### `runway analysis to expense deep dive`
- **Suite:** cross-feature-journeys.spec.ts > Cross-Feature Integration & User Journey Tests
- **Browser:** chromium
- **Duration:** 11.66s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Runway & Survival')
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Cal`

### `settings full configuration workflow`
- **Suite:** cross-feature-journeys.spec.ts > Cross-Feature Integration & User Journey Tests
- **Browser:** chromium
- **Duration:** 9.19s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Connector Conflict Policy')
Expected: visible
Error: strict mode violation: locator('t`

### `displays AWS Cost card`
- **Suite:** cto-dashboard.spec.ts > CTO Dashboard Page
- **Browser:** chromium
- **Duration:** 2.88s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=AWS Cost')
Expected: visible
Error: strict mode violation: locator('text=AWS Cost') re`

### `CTO dashboard renders on mobile viewport`
- **Suite:** cto-dashboard.spec.ts > CTO Dashboard Page
- **Browser:** chromium
- **Duration:** 9.44s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator:  locator('text=Total Tech Spend')
Expected: visible
Received: hidden
Timeout:  5000ms

Call log:
[2`

### `displays 4 KPI metric cards`
- **Suite:** dashboard.spec.ts > Dashboard Home Page
- **Browser:** chromium
- **Duration:** 5.34s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Burn Multiple')
Expected: visible
Error: strict mode violation: locator('text=Burn Mul`

### `chart has burn and revenue legend items`
- **Suite:** dashboard.spec.ts > Dashboard Home Page
- **Browser:** chromium
- **Duration:** 4.39s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Revenue')
Expected: visible
Error: strict mode violation: locator('text=Revenue') reso`

### `displays module navigation cards`
- **Suite:** dashboard.spec.ts > Dashboard Home Page
- **Browser:** chromium
- **Duration:** 5.69s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Feature Hub')
Expected: visible
Error: strict mode violation: locator('text=Feature Hu`

### `module cards link to correct pages`
- **Suite:** dashboard.spec.ts > Dashboard Home Page
- **Browser:** chromium
- **Duration:** 9.97s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoHaveAttribute[2m([22m[32mexpected[39m[2m)[22m failed

Locator: locator('a').filter({ hasText: 'Feature Hub' })
Expected: [32m"/features"[39`

### `renders page title "Capital Allocations"`
- **Suite:** expenses.spec.ts > Expenses / Capital Allocations Page
- **Browser:** chromium
- **Duration:** 13.80s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Capital Allocations')
Expected: visible
Timeout: 5000ms
Error: element(s) not found

C`

### `displays Compliance status card`
- **Suite:** expenses.spec.ts > Expenses / Capital Allocations Page
- **Browser:** chromium
- **Duration:** 4.05s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Audited')
Expected: visible
Error: strict mode violation: locator('text=Audited') reso`

### `has Refresh button`
- **Suite:** features-hub.spec.ts > Feature Hub / Action Hub Page
- **Browser:** chromium
- **Duration:** 5.16s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('button:has-text("Refresh")')
Expected: visible
Error: strict mode violation: locator('butto`

### `shows health status badge (Healthy or Attention needed)`
- **Suite:** features-hub.spec.ts > Feature Hub / Action Hub Page
- **Browser:** chromium
- **Duration:** 12.02s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=/Healthy|Attention needed/')
Expected: visible
Timeout: 5000ms
Error: element(s) not f`

### `displays Net Burn summary card`
- **Suite:** finance-dashboard.spec.ts > Finance Dashboard Page
- **Browser:** chromium
- **Duration:** 8.35s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Net Burn').first()
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call`

### `displays Total Expenses summary card`
- **Suite:** finance-dashboard.spec.ts > Finance Dashboard Page
- **Browser:** chromium
- **Duration:** 10.79s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Total Expenses')
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call l`

### `displays Variance summary card`
- **Suite:** finance-dashboard.spec.ts > Finance Dashboard Page
- **Browser:** chromium
- **Duration:** 7.77s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Variance')
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call log:
[`

### `Net Burn card shows monthly cash burn rate label`
- **Suite:** finance-dashboard.spec.ts > Finance Dashboard Page
- **Browser:** chromium
- **Duration:** 8.36s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Monthly cash burn rate')
Expected: visible
Timeout: 5000ms
Error: element(s) not found`

### `Total Expenses card shows tech + non-tech label`
- **Suite:** finance-dashboard.spec.ts > Finance Dashboard Page
- **Browser:** chromium
- **Duration:** 8.39s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Tech + Non-tech costs')
Expected: visible
Timeout: 5000ms
Error: element(s) not found
`

### `Variance card shows burn vs expenses label`
- **Suite:** finance-dashboard.spec.ts > Finance Dashboard Page
- **Browser:** chromium
- **Duration:** 8.42s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Burn vs expenses')
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call`

### `Finance dashboard renders on tablet viewport`
- **Suite:** finance-dashboard.spec.ts > Finance Dashboard Page
- **Browser:** chromium
- **Duration:** 9.51s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Net Burn').first()
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call`

### `navigating between all major pages without errors`
- **Suite:** integration.spec.ts > Cross-Page Navigation & Integration
- **Browser:** chromium
- **Duration:** 39.04s
- **Error:** `[31mTest timeout of 30000ms exceeded.[39m`

### `dashboard layout renders sidebar, content area, and ambient gradients`
- **Suite:** integration.spec.ts > Dashboard Layout Integration
- **Browser:** chromium
- **Duration:** 5.91s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('main')
Expected: visible
Error: strict mode violation: locator('main') resolved to 2 elemen`

### `has Refresh button`
- **Suite:** operations.spec.ts > Operations Center Page
- **Browser:** chromium
- **Duration:** 9.73s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('button:has-text("Refresh")')
Expected: visible
Error: strict mode violation: locator('butto`

### `shows Open AR, Open AP, DSO, Overdue AR`
- **Suite:** operations.spec.ts > Operations Center Page
- **Browser:** chromium
- **Duration:** 14.40s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=DSO')
Expected: visible
Error: strict mode violation: locator('text=DSO') resolved to `

### `dashboard content area fills available space`
- **Suite:** performance.spec.ts > Performance & Load Time Tests > Viewport Stability
- **Browser:** chromium
- **Duration:** 4.93s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('main')
Expected: visible
Error: strict mode violation: locator('main') resolved to 2 elemen`

### `Runway renders correctly at mobile (375x812)`
- **Suite:** responsive-layout.spec.ts > Responsive Layout Tests - All Pages
- **Browser:** chromium
- **Duration:** 19.96s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Runway & Survival').first()
Expected: visible
Timeout: 15000ms
Error: element(s) not f`

### `Expenses renders correctly at mobile (375x812)`
- **Suite:** responsive-layout.spec.ts > Responsive Layout Tests - All Pages
- **Browser:** chromium
- **Duration:** 19.91s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Capital Allocations').first()
Expected: visible
Timeout: 15000ms
Error: element(s) not`

### `Revenue renders correctly at mobile (375x812)`
- **Suite:** responsive-layout.spec.ts > Responsive Layout Tests - All Pages
- **Browser:** chromium
- **Duration:** 19.89s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Revenue Intelligence').first()
Expected: visible
Timeout: 15000ms
Error: element(s) no`

### `Scenarios renders correctly at mobile (375x812)`
- **Suite:** responsive-layout.spec.ts > Responsive Layout Tests - All Pages
- **Browser:** chromium
- **Duration:** 19.56s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Strategic Simulations').first()
Expected: visible
Timeout: 15000ms
Error: element(s) n`

### `Anomalies renders correctly at mobile (375x812)`
- **Suite:** responsive-layout.spec.ts > Responsive Layout Tests - All Pages
- **Browser:** chromium
- **Duration:** 19.94s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Financial Risk').first()
Expected: visible
Timeout: 15000ms
Error: element(s) not foun`

### `Benchmarking renders correctly at mobile (375x812)`
- **Suite:** responsive-layout.spec.ts > Responsive Layout Tests - All Pages
- **Browser:** chromium
- **Duration:** 17.40s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Performance Intelligence').first()
Expected: visible
Timeout: 15000ms
Error: element(s`

### `AI Agent renders correctly at mobile (375x812)`
- **Suite:** responsive-layout.spec.ts > Responsive Layout Tests - All Pages
- **Browser:** chromium
- **Duration:** 19.10s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Vireon AI Assistant').first()
Expected: visible
Timeout: 15000ms
Error: element(s) not`

### `Runway renders correctly at tablet (768x1024)`
- **Suite:** responsive-layout.spec.ts > Responsive Layout Tests - All Pages
- **Browser:** chromium
- **Duration:** 19.01s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Runway & Survival').first()
Expected: visible
Timeout: 15000ms
Error: element(s) not f`

### `Expenses renders correctly at tablet (768x1024)`
- **Suite:** responsive-layout.spec.ts > Responsive Layout Tests - All Pages
- **Browser:** chromium
- **Duration:** 18.37s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Capital Allocations').first()
Expected: visible
Timeout: 15000ms
Error: element(s) not`

### `Revenue renders correctly at tablet (768x1024)`
- **Suite:** responsive-layout.spec.ts > Responsive Layout Tests - All Pages
- **Browser:** chromium
- **Duration:** 18.63s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Revenue Intelligence').first()
Expected: visible
Timeout: 15000ms
Error: element(s) no`

### `Scenarios renders correctly at tablet (768x1024)`
- **Suite:** responsive-layout.spec.ts > Responsive Layout Tests - All Pages
- **Browser:** chromium
- **Duration:** 18.31s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Strategic Simulations').first()
Expected: visible
Timeout: 15000ms
Error: element(s) n`

### `Anomalies renders correctly at tablet (768x1024)`
- **Suite:** responsive-layout.spec.ts > Responsive Layout Tests - All Pages
- **Browser:** chromium
- **Duration:** 17.91s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Financial Risk').first()
Expected: visible
Timeout: 15000ms
Error: element(s) not foun`

### `Benchmarking renders correctly at tablet (768x1024)`
- **Suite:** responsive-layout.spec.ts > Responsive Layout Tests - All Pages
- **Browser:** chromium
- **Duration:** 18.66s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Performance Intelligence').first()
Expected: visible
Timeout: 15000ms
Error: element(s`

### `AI Agent renders correctly at tablet (768x1024)`
- **Suite:** responsive-layout.spec.ts > Responsive Layout Tests - All Pages
- **Browser:** chromium
- **Duration:** 17.88s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Vireon AI Assistant').first()
Expected: visible
Timeout: 15000ms
Error: element(s) not`

### `Runway renders correctly at desktop (1440x900)`
- **Suite:** responsive-layout.spec.ts > Responsive Layout Tests - All Pages
- **Browser:** chromium
- **Duration:** 18.68s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Runway & Survival').first()
Expected: visible
Timeout: 15000ms
Error: element(s) not f`

### `Expenses renders correctly at desktop (1440x900)`
- **Suite:** responsive-layout.spec.ts > Responsive Layout Tests - All Pages
- **Browser:** chromium
- **Duration:** 18.43s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Capital Allocations').first()
Expected: visible
Timeout: 15000ms
Error: element(s) not`

### `Revenue renders correctly at desktop (1440x900)`
- **Suite:** responsive-layout.spec.ts > Responsive Layout Tests - All Pages
- **Browser:** chromium
- **Duration:** 18.50s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Revenue Intelligence').first()
Expected: visible
Timeout: 15000ms
Error: element(s) no`

### `Scenarios renders correctly at desktop (1440x900)`
- **Suite:** responsive-layout.spec.ts > Responsive Layout Tests - All Pages
- **Browser:** chromium
- **Duration:** 18.40s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Strategic Simulations').first()
Expected: visible
Timeout: 15000ms
Error: element(s) n`

### `Anomalies renders correctly at desktop (1440x900)`
- **Suite:** responsive-layout.spec.ts > Responsive Layout Tests - All Pages
- **Browser:** chromium
- **Duration:** 19.00s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Financial Risk').first()
Expected: visible
Timeout: 15000ms
Error: element(s) not foun`

### `Benchmarking renders correctly at desktop (1440x900)`
- **Suite:** responsive-layout.spec.ts > Responsive Layout Tests - All Pages
- **Browser:** chromium
- **Duration:** 19.19s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Performance Intelligence').first()
Expected: visible
Timeout: 15000ms
Error: element(s`

### `AI Agent renders correctly at desktop (1440x900)`
- **Suite:** responsive-layout.spec.ts > Responsive Layout Tests - All Pages
- **Browser:** chromium
- **Duration:** 18.39s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Vireon AI Assistant').first()
Expected: visible
Timeout: 15000ms
Error: element(s) not`

### `Runway renders correctly at fullhd (1920x1080)`
- **Suite:** responsive-layout.spec.ts > Responsive Layout Tests - All Pages
- **Browser:** chromium
- **Duration:** 17.46s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Runway & Survival').first()
Expected: visible
Timeout: 15000ms
Error: element(s) not f`

### `Expenses renders correctly at fullhd (1920x1080)`
- **Suite:** responsive-layout.spec.ts > Responsive Layout Tests - All Pages
- **Browser:** chromium
- **Duration:** 18.20s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Capital Allocations').first()
Expected: visible
Timeout: 15000ms
Error: element(s) not`

### `Revenue renders correctly at fullhd (1920x1080)`
- **Suite:** responsive-layout.spec.ts > Responsive Layout Tests - All Pages
- **Browser:** chromium
- **Duration:** 18.48s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Revenue Intelligence').first()
Expected: visible
Timeout: 15000ms
Error: element(s) no`

### `Scenarios renders correctly at fullhd (1920x1080)`
- **Suite:** responsive-layout.spec.ts > Responsive Layout Tests - All Pages
- **Browser:** chromium
- **Duration:** 18.15s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Strategic Simulations').first()
Expected: visible
Timeout: 15000ms
Error: element(s) n`

### `Anomalies renders correctly at fullhd (1920x1080)`
- **Suite:** responsive-layout.spec.ts > Responsive Layout Tests - All Pages
- **Browser:** chromium
- **Duration:** 18.69s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Financial Risk').first()
Expected: visible
Timeout: 15000ms
Error: element(s) not foun`

### `Benchmarking renders correctly at fullhd (1920x1080)`
- **Suite:** responsive-layout.spec.ts > Responsive Layout Tests - All Pages
- **Browser:** chromium
- **Duration:** 18.91s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Performance Intelligence').first()
Expected: visible
Timeout: 15000ms
Error: element(s`

### `AI Agent renders correctly at fullhd (1920x1080)`
- **Suite:** responsive-layout.spec.ts > Responsive Layout Tests - All Pages
- **Browser:** chromium
- **Duration:** 18.84s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Vireon AI Assistant').first()
Expected: visible
Timeout: 15000ms
Error: element(s) not`

### `renders page title "Revenue Intelligence"`
- **Suite:** revenue.spec.ts > Revenue Intelligence Page
- **Browser:** chromium
- **Duration:** 12.94s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Revenue Intelligence')
Expected: visible
Timeout: 5000ms
Error: element(s) not found

`

### `segment percentages are displayed`
- **Suite:** revenue.spec.ts > Revenue Intelligence Page
- **Browser:** chromium
- **Duration:** 1.78s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=10%')
Expected: visible
Error: strict mode violation: locator('text=10%') resolved to `

### `shows Total Monthly value`
- **Suite:** revenue.spec.ts > Revenue Intelligence Page
- **Browser:** chromium
- **Duration:** 2.83s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=$45,000')
Expected: visible
Error: strict mode violation: locator('text=$45,000') reso`

### `renders the page title "Runway & Survival"`
- **Suite:** runway.spec.ts > Runway & Survival Page
- **Browser:** chromium
- **Duration:** 7.97s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Runway & Survival')
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Cal`

### `renders page title "Strategic Simulations"`
- **Suite:** scenarios.spec.ts > Scenarios / Strategic Simulations Page
- **Browser:** chromium
- **Duration:** 8.86s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Strategic Simulations')
Expected: visible
Timeout: 5000ms
Error: element(s) not found
`

### `has Cash Policy section with two options`
- **Suite:** scenarios.spec.ts > Scenarios / Strategic Simulations Page
- **Browser:** chromium
- **Duration:** 2.89s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Cash Policy')
Expected: visible
Error: strict mode violation: locator('text=Cash Polic`

### `adjusting hiring count slider changes burden value`
- **Suite:** scenarios.spec.ts > Scenarios / Strategic Simulations Page
- **Browser:** chromium
- **Duration:** 19.76s
- **Error:** `TimeoutError: locator.innerText: Timeout 15000ms exceeded.
Call log:
[2m  - waiting for locator('article').filter({ hasText: 'Monthly Hiring Burden' }).locator('p.text-xl')[22m
`

### `renders Settings page title`
- **Suite:** settings.spec.ts > Settings Page
- **Browser:** chromium
- **Duration:** 3.69s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Settings')
Expected: visible
Error: strict mode violation: locator('text=Settings') re`

### `has Refresh button`
- **Suite:** settings.spec.ts > Settings Page
- **Browser:** chromium
- **Duration:** 3.22s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('button:has-text("Refresh")')
Expected: visible
Error: strict mode violation: locator('butto`

### `renders Connector Conflict Policy section`
- **Suite:** settings.spec.ts > Settings Page
- **Browser:** chromium
- **Duration:** 6.86s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Connector Conflict Policy')
Expected: visible
Error: strict mode violation: locator('t`

### `displays team members`
- **Suite:** settings.spec.ts > Settings Page
- **Browser:** chromium
- **Duration:** 7.36s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=VIREON AI')
Expected: visible
Error: strict mode violation: locator('text=VIREON AI') `

### `shows team member roles`
- **Suite:** settings.spec.ts > Settings Page
- **Browser:** chromium
- **Duration:** 8.40s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=CFO')
Expected: visible
Error: strict mode violation: locator('text=CFO') resolved to `

### `displays TDS Filing card`
- **Suite:** tax.spec.ts > Tax Compliance Hub Page
- **Browser:** chromium
- **Duration:** 9.72s
- **Error:** `Error: [2mexpect([22m[31mlocator[39m[2m).[22mtoBeVisible[2m([22m[2m)[22m failed

Locator: locator('text=Quarterly')
Expected: visible
Error: strict mode violation: locator('text=Quarterly') `

### `landing page visual snapshot - desktop`
- **Suite:** visual-regression.spec.ts > Visual Regression & Screenshot Tests
- **Browser:** chromium
- **Duration:** 7.14s
- **Error:** `Error: A snapshot doesn't exist at C:\Users\yagna\OneDrive\Desktop\My Proj\CAPSTONE\vireon\frontend\tests\visual-regression.spec.ts-snapshots\landing-desktop-chromium-win32.png, writing actual.`

### `landing page visual snapshot - mobile`
- **Suite:** visual-regression.spec.ts > Visual Regression & Screenshot Tests
- **Browser:** chromium
- **Duration:** 8.62s
- **Error:** `Error: A snapshot doesn't exist at C:\Users\yagna\OneDrive\Desktop\My Proj\CAPSTONE\vireon\frontend\tests\visual-regression.spec.ts-snapshots\landing-mobile-chromium-win32.png, writing actual.`

### `dashboard page visual snapshot`
- **Suite:** visual-regression.spec.ts > Visual Regression & Screenshot Tests
- **Browser:** chromium
- **Duration:** 7.81s
- **Error:** `Error: A snapshot doesn't exist at C:\Users\yagna\OneDrive\Desktop\My Proj\CAPSTONE\vireon\frontend\tests\visual-regression.spec.ts-snapshots\dashboard-desktop-chromium-win32.png, writing actual.`

### `runway page visual snapshot`
- **Suite:** visual-regression.spec.ts > Visual Regression & Screenshot Tests
- **Browser:** chromium
- **Duration:** 7.36s
- **Error:** `Error: A snapshot doesn't exist at C:\Users\yagna\OneDrive\Desktop\My Proj\CAPSTONE\vireon\frontend\tests\visual-regression.spec.ts-snapshots\runway-desktop-chromium-win32.png, writing actual.`

### `expenses page visual snapshot`
- **Suite:** visual-regression.spec.ts > Visual Regression & Screenshot Tests
- **Browser:** chromium
- **Duration:** 6.11s
- **Error:** `Error: A snapshot doesn't exist at C:\Users\yagna\OneDrive\Desktop\My Proj\CAPSTONE\vireon\frontend\tests\visual-regression.spec.ts-snapshots\expenses-desktop-chromium-win32.png, writing actual.`

### `revenue page visual snapshot`
- **Suite:** visual-regression.spec.ts > Visual Regression & Screenshot Tests
- **Browser:** chromium
- **Duration:** 4.71s
- **Error:** `Error: A snapshot doesn't exist at C:\Users\yagna\OneDrive\Desktop\My Proj\CAPSTONE\vireon\frontend\tests\visual-regression.spec.ts-snapshots\revenue-desktop-chromium-win32.png, writing actual.`

### `scenarios page visual snapshot`
- **Suite:** visual-regression.spec.ts > Visual Regression & Screenshot Tests
- **Browser:** chromium
- **Duration:** 4.48s
- **Error:** `Error: A snapshot doesn't exist at C:\Users\yagna\OneDrive\Desktop\My Proj\CAPSTONE\vireon\frontend\tests\visual-regression.spec.ts-snapshots\scenarios-desktop-chromium-win32.png, writing actual.`

### `tax page visual snapshot`
- **Suite:** visual-regression.spec.ts > Visual Regression & Screenshot Tests
- **Browser:** chromium
- **Duration:** 3.79s
- **Error:** `Error: A snapshot doesn't exist at C:\Users\yagna\OneDrive\Desktop\My Proj\CAPSTONE\vireon\frontend\tests\visual-regression.spec.ts-snapshots\tax-desktop-chromium-win32.png, writing actual.`

### `anomalies page visual snapshot`
- **Suite:** visual-regression.spec.ts > Visual Regression & Screenshot Tests
- **Browser:** chromium
- **Duration:** 3.73s
- **Error:** `Error: A snapshot doesn't exist at C:\Users\yagna\OneDrive\Desktop\My Proj\CAPSTONE\vireon\frontend\tests\visual-regression.spec.ts-snapshots\anomalies-desktop-chromium-win32.png, writing actual.`

### `benchmarking page visual snapshot`
- **Suite:** visual-regression.spec.ts > Visual Regression & Screenshot Tests
- **Browser:** chromium
- **Duration:** 3.52s
- **Error:** `Error: A snapshot doesn't exist at C:\Users\yagna\OneDrive\Desktop\My Proj\CAPSTONE\vireon\frontend\tests\visual-regression.spec.ts-snapshots\benchmarking-desktop-chromium-win32.png, writing actual.`

### `settings page visual snapshot`
- **Suite:** visual-regression.spec.ts > Visual Regression & Screenshot Tests
- **Browser:** chromium
- **Duration:** 8.23s
- **Error:** `Error: A snapshot doesn't exist at C:\Users\yagna\OneDrive\Desktop\My Proj\CAPSTONE\vireon\frontend\tests\visual-regression.spec.ts-snapshots\settings-desktop-chromium-win32.png, writing actual.`

### `CEO dashboard visual snapshot`
- **Suite:** visual-regression.spec.ts > Visual Regression & Screenshot Tests
- **Browser:** chromium
- **Duration:** 9.01s
- **Error:** `Error: A snapshot doesn't exist at C:\Users\yagna\OneDrive\Desktop\My Proj\CAPSTONE\vireon\frontend\tests\visual-regression.spec.ts-snapshots\ceo-dashboard-chromium-win32.png, writing actual.`

### `CTO dashboard visual snapshot`
- **Suite:** visual-regression.spec.ts > Visual Regression & Screenshot Tests
- **Browser:** chromium
- **Duration:** 3.81s
- **Error:** `Error: A snapshot doesn't exist at C:\Users\yagna\OneDrive\Desktop\My Proj\CAPSTONE\vireon\frontend\tests\visual-regression.spec.ts-snapshots\cto-dashboard-chromium-win32.png, writing actual.`

### `Finance dashboard visual snapshot`
- **Suite:** visual-regression.spec.ts > Visual Regression & Screenshot Tests
- **Browser:** chromium
- **Duration:** 2.59s
- **Error:** `Error: A snapshot doesn't exist at C:\Users\yagna\OneDrive\Desktop\My Proj\CAPSTONE\vireon\frontend\tests\visual-regression.spec.ts-snapshots\finance-dashboard-chromium-win32.png, writing actual.`

---

## Full Test Inventory

### Landing Page

| # | Test | Status | Duration |
|---|------|--------|----------|
| 1 | has proper heading hierarchy with single h1 | ✅ expected | 12.37s |
| 2 | all images have alt text or are decorative | ✅ expected | 12.22s |
| 3 | CTA links are focusable and have visible focus | ✅ expected | 12.23s |
| 4 | page has proper lang attribute | ✅ expected | 12.40s |
| 5 | all links have accessible names | ✅ expected | 13.27s |

### Dashboard

| # | Test | Status | Duration |
|---|------|--------|----------|
| 1 | dashboard has semantic main content area | ❌ unexpected | 14.60s |
| 2 | sidebar uses aside element | ✅ expected | 14.59s |
| 3 | sidebar navigation uses nav element | ✅ expected | 14.76s |
| 4 | navigation links are keyboard accessible | ✅ expected | 4.05s |
| 5 | interactive buttons have visible text or aria-label | ❌ unexpected | 12.98s |

### Form Controls

| # | Test | Status | Duration |
|---|------|--------|----------|
| 1 | tax checklist checkboxes are keyboard operable | ✅ expected | 14.36s |
| 2 | expense department dropdown is keyboard accessible | ✅ expected | 12.27s |
| 3 | anomaly search input has placeholder text | ❌ unexpected | 15.06s |
| 4 | AI agent chat input has clear placeholder | ✅ expected | 10.68s |
| 5 | scenario sliders are interactive via keyboard | ✅ expected | 10.74s |

### Visual Hierarchy

| # | Test | Status | Duration |
|---|------|--------|----------|
| 1 | each dashboard page has a clear h1 heading | ❌ unexpected | 30.61s |

### AI Agent Page

| # | Test | Status | Duration |
|---|------|--------|----------|
| 1 | renders page title "Vireon AI Assistant" | ❌ unexpected | 11.06s |
| 2 | displays Financial intelligence core badge | ✅ expected | 5.87s |
| 3 | shows backend connection status | ✅ expected | 5.40s |
| 4 | renders chat message area | ❌ unexpected | 9.56s |
| 5 | has message input field | ✅ expected | 2.83s |
| 6 | has send button | ✅ expected | 2.44s |
| 7 | displays quick action buttons | ✅ expected | 2.59s |
| 8 | can type a message in the input field | ✅ expected | 4.25s |
| 9 | clicking a quick action populates chat with user message | ❌ unexpected | 4.16s |
| 10 | submitting a message shows loading state | ✅ expected | 3.85s |
| 11 | user messages appear on the right side | ✅ expected | 5.37s |
| 12 | assistant messages appear on the left side | ❌ unexpected | 7.68s |

### Anomalies & Financial Risk Page

| # | Test | Status | Duration |
|---|------|--------|----------|
| 1 | renders page title "Financial Risk & Anomalies" | ❌ unexpected | 7.54s |
| 2 | displays heading "Financial Risk Dashboard" | ❌ unexpected | 10.05s |
| 3 | shows Real-time monitoring badge | ❌ unexpected | 7.05s |
| 4 | has Test Email button | ❌ unexpected | 8.89s |
| 5 | has Send Alerts Now button | ❌ unexpected | 10.12s |
| 6 | has Configure button | ❌ unexpected | 10.37s |
| 7 | displays Risk Score card | ❌ unexpected | 9.58s |
| 8 | displays Anomalies count card | ❌ unexpected | 9.54s |
| 9 | displays Runway card | ✅ expected | 4.22s |
| 10 | displays Alerts Sent card | ❌ unexpected | 10.11s |
| 11 | renders Detected Anomalies section | ❌ unexpected | 9.98s |
| 12 | has severity filter buttons (all, critical, warning, info) | ❌ unexpected | 12.86s |
| 13 | clicking filter button updates active state | ❌ unexpected | 21.37s |
| 14 | has anomaly search input | ❌ unexpected | 10.54s |
| 15 | typing in search filters anomalies list | ❌ unexpected | 21.55s |
| 16 | clicking Configure opens email alert configuration panel | ❌ unexpected | 26.93s |
| 17 | configuration panel has CEO Email input | ❌ unexpected | 26.98s |
| 18 | configuration panel has Finance Team textarea | ❌ unexpected | 21.13s |
| 19 | configuration panel has Additional Recipients textarea | ❌ unexpected | 21.04s |
| 20 | configuration panel has Save and Cancel buttons | ❌ unexpected | 20.97s |
| 21 | clicking Cancel closes configuration panel | ❌ unexpected | 25.50s |
| 22 | shows Currently Configured section within config panel | ❌ unexpected | 25.51s |

### Vireon E2E Tests

| # | Test | Status | Duration |
|---|------|--------|----------|
| 1 | Dashboard loads correctly | ✅ expected | 1.25s |

### Benchmarking / Performance Intelligence Page

| # | Test | Status | Duration |
|---|------|--------|----------|
| 1 | renders page title "Performance Intelligence" | ❌ unexpected | 17.27s |
| 2 | displays "Operational Benchmarking" heading | ✅ expected | 5.82s |
| 3 | shows Live benchmark feed badge | ✅ expected | 5.75s |
| 4 | has Consult AI advisor button | ✅ expected | 7.40s |
| 5 | displays at least 3 benchmark metric cards | ❌ unexpected | 4.86s |
| 6 | shows Rule of 40 metric card | ✅ expected | 8.16s |
| 7 | shows Burn Multiple metric card | ✅ expected | 8.17s |
| 8 | shows Net Revenue Retention metric card | ✅ expected | 7.68s |
| 9 | each metric card has a Target label | ❌ unexpected | 2.73s |
| 10 | each metric card has a status badge | ❌ unexpected | 2.69s |
| 11 | each metric card has Get advice button | ❌ unexpected | 3.10s |
| 12 | metric cards have hover class for elevation | ✅ expected | 5.93s |

### CEO Dashboard Page

| # | Test | Status | Duration |
|---|------|--------|----------|
| 1 | renders CEO Dashboard heading | ✅ expected | 9.84s |
| 2 | shows financial health subtitle with month | ✅ expected | 11.70s |
| 3 | has month selector input | ✅ expected | 6.80s |
| 4 | changing month selector updates data context | ✅ expected | 2.75s |
| 5 | has CSV export button | ✅ expected | 10.01s |
| 6 | has PDF export button | ✅ expected | 9.89s |
| 7 | displays Net Burn KPI card | ✅ expected | 9.60s |
| 8 | displays Burn Multiple KPI card | ✅ expected | 10.43s |
| 9 | displays Cash Balance KPI card | ✅ expected | 5.45s |
| 10 | displays Headcount KPI card | ❌ unexpected | 5.46s |
| 11 | displays GM Avg KPI card | ✅ expected | 1.71s |
| 12 | Burn Multiple shows industry target reference | ✅ expected | 5.02s |
| 13 | Net Burn shows month-over-month change | ✅ expected | 6.02s |
| 14 | renders 6-Month Burn & Cash Trajectory chart | ✅ expected | 4.34s |
| 15 | renders Cost Breakdown chart | ✅ expected | 4.10s |
| 16 | renders Top Cost Drivers section | ✅ expected | 4.17s |
| 17 | renders Key Metrics & Ratios section | ✅ expected | 5.02s |
| 18 | shows Revenue per Employee metric | ✅ expected | 5.45s |
| 19 | shows Avg Cost per Employee metric | ✅ expected | 11.21s |
| 20 | shows Headcount Ratio metric | ✅ expected | 10.97s |
| 21 | shows Cash Position metric | ✅ expected | 11.03s |
| 22 | renders Product Performance & Profitability table | ✅ expected | 10.95s |
| 23 | product table has correct headers | ✅ expected | 8.96s |
| 24 | renders AI-Powered Recommendations section | ✅ expected | 8.80s |
| 25 | recommendations section shows content or empty state | ✅ expected | 2.48s |
| 26 | all 5 KPI cards are rendered in grid | ✅ expected | 7.14s |
| 27 | CEO dashboard renders on mobile viewport | ✅ expected | 6.72s |

### Chat Drawer Component

| # | Test | Status | Duration |
|---|------|--------|----------|
| 1 | chat drawer is hidden initially | ✅ expected | 5.66s |
| 2 | clicking AI-related button on dashboard opens chat drawer | ✅ expected | 15.04s |
| 3 | chat drawer has close button | ❌ unexpected | 18.29s |
| 4 | chat drawer shows Smart Financial Manager subtitle | ✅ expected | 15.43s |
| 5 | chat drawer has message input area | ✅ expected | 14.85s |
| 6 | chat drawer shows quick prompt suggestions initially | ✅ expected | 14.49s |
| 7 | chat drawer has send button | ✅ expected | 13.22s |
| 8 | chat drawer shows Enter keyboard shortcut hint | ✅ expected | 12.26s |
| 9 | chat drawer shows powered by text | ✅ expected | 11.16s |

### Cross-Feature Integration & User Journey Tests

| # | Test | Status | Duration |
|---|------|--------|----------|
| 1 | CEO full journey: landing → dashboard → CEO → export → scenarios | ❌ unexpected | 30.93s |
| 2 | CTO journey: dashboard → CTO planner → tech cost entry → features | ✅ expected | 26.51s |
| 3 | Finance journey: dashboard → finance view → tax → settings | ⚠️ flaky | 30.65s |
| 4 | anomaly workflow: features → seed anomalies → view anomalies → configure | ❌ unexpected | 22.20s |
| 5 | tax compliance workflow: features → generate liability → tax page | ✅ expected | 20.09s |
| 6 | scenario planning: mode toggle → slider interactions → decision signal | ✅ expected | 10.57s |
| 7 | AI agent journey: features hub → agent page → quick actions | ❌ unexpected | 18.88s |
| 8 | operations center: all sections render and are interactive | ✅ expected | 8.98s |
| 9 | revenue analysis to benchmarking journey | ❌ unexpected | 12.93s |
| 10 | runway analysis to expense deep dive | ❌ unexpected | 11.66s |
| 11 | settings full configuration workflow | ❌ unexpected | 9.19s |

### CTO Dashboard Page

| # | Test | Status | Duration |
|---|------|--------|----------|
| 1 | renders CTO Dashboard heading | ✅ expected | 5.87s |
| 2 | has Export CSV button | ✅ expected | 8.01s |
| 3 | has Export PDF button | ✅ expected | 2.93s |
| 4 | displays Total Tech Spend card | ✅ expected | 3.85s |
| 5 | displays AWS Cost card | ❌ unexpected | 2.88s |
| 6 | displays Software Licenses card | ✅ expected | 7.83s |
| 7 | displays Tech % of Burn card | ✅ expected | 2.87s |
| 8 | renders Tech Cost Trend chart section | ✅ expected | 4.72s |
| 9 | tech cost trend shows Last 6 months label | ✅ expected | 4.48s |
| 10 | tech cost trend chart has recharts container | ✅ expected | 2.64s |
| 11 | renders AWS Cost Breakdown by Product section | ✅ expected | 2.65s |
| 12 | AWS breakdown shows product data or empty state | ✅ expected | 4.69s |
| 13 | renders Quick Entry - Tech Cost section | ✅ expected | 3.02s |
| 14 | has cost type dropdown with options | ✅ expected | 3.25s |
| 15 | has vendor name input field | ✅ expected | 4.18s |
| 16 | has amount input field | ✅ expected | 4.45s |
| 17 | has description input field | ✅ expected | 4.34s |
| 18 | has Submit Tech Cost button | ✅ expected | 4.25s |
| 19 | can fill in tech cost form fields | ✅ expected | 4.91s |
| 20 | renders Recent Entries table | ✅ expected | 4.49s |
| 21 | recent entries table has Amount column | ✅ expected | 5.26s |
| 22 | renders Hiring Impact Calculator section | ✅ expected | 5.08s |
| 23 | shows hiring impact description | ✅ expected | 5.10s |
| 24 | has Annual CTC input field | ✅ expected | 5.02s |
| 25 | has Calculate Impact button | ✅ expected | 4.36s |
| 26 | CTC input has default value of 1800000 | ✅ expected | 4.22s |
| 27 | CTO dashboard renders on mobile viewport | ❌ unexpected | 9.44s |

### Dashboard Home Page

| # | Test | Status | Duration |
|---|------|--------|----------|
| 1 | renders hero with Executive Control Center badge | ✅ expected | 4.64s |
| 2 | displays main heading about financial story | ✅ expected | 4.88s |
| 3 | shows subtitle about ERP, payroll, cloud, and revenue | ✅ expected | 4.86s |
| 4 | has CEO View button linking to /dashboard/ceo | ✅ expected | 5.03s |
| 5 | has Finance View button linking to /dashboard/finance | ✅ expected | 3.58s |
| 6 | clicking CEO View navigates successfully | ✅ expected | 6.91s |
| 7 | displays 4 KPI metric cards | ❌ unexpected | 5.34s |
| 8 | Net Burn metric shows formatted currency value | ✅ expected | 4.67s |
| 9 | Runway metric shows months | ✅ expected | 4.65s |
| 10 | Burn Multiple metric shows multiplier | ✅ expected | 4.58s |
| 11 | renders Burn vs Revenue Momentum chart section | ✅ expected | 4.30s |
| 12 | chart has burn and revenue legend items | ❌ unexpected | 4.39s |
| 13 | chart container is visible with recharts SVG | ✅ expected | 5.28s |
| 14 | chart has Explore runway link | ✅ expected | 5.24s |
| 15 | displays Priority Actions section | ✅ expected | 5.10s |
| 16 | shows 3 priority action items | ✅ expected | 5.42s |
| 17 | priority actions have owner labels | ✅ expected | 5.09s |
| 18 | displays module navigation cards | ❌ unexpected | 5.69s |
| 19 | module cards link to correct pages | ❌ unexpected | 9.97s |
| 20 | clicking a module card navigates to the module page | ✅ expected | 9.91s |

### Expenses / Capital Allocations Page

| # | Test | Status | Duration |
|---|------|--------|----------|
| 1 | renders page title "Capital Allocations" | ❌ unexpected | 13.80s |
| 2 | displays Audited expense ledger badge | ✅ expected | 9.47s |
| 3 | shows Expense Control Center heading | ✅ expected | 3.78s |
| 4 | has department filter dropdown | ✅ expected | 3.51s |
| 5 | department dropdown has all department options | ✅ expected | 2.57s |
| 6 | changing department filter updates the view | ✅ expected | 2.55s |
| 7 | displays Total Expenses card | ✅ expected | 5.13s |
| 8 | displays Compliance status card | ❌ unexpected | 4.05s |
| 9 | has AI leakage audit button | ✅ expected | 2.88s |
| 10 | category cards display progress bars | ✅ expected | 2.83s |
| 11 | shows total outflow text | ✅ expected | 3.68s |

### Feature Hub / Action Hub Page

| # | Test | Status | Duration |
|---|------|--------|----------|
| 1 | renders Action Hub heading | ✅ expected | 4.28s |
| 2 | displays "Operate The Smart CFO Features" heading | ✅ expected | 5.01s |
| 3 | has Refresh button | ❌ unexpected | 5.16s |
| 4 | renders Platform Health section | ✅ expected | 3.12s |
| 5 | shows health status badge (Healthy or Attention needed) | ❌ unexpected | 12.02s |
| 6 | displays Default Company info | ✅ expected | 6.65s |
| 7 | displays Issues count | ✅ expected | 6.81s |
| 8 | displays Actionable Fixes count | ✅ expected | 6.78s |
| 9 | displays Missing Credentials count | ✅ expected | 7.18s |
| 10 | renders Anomaly Operations section | ✅ expected | 6.32s |
| 11 | has Seed demo anomalies button | ✅ expected | 8.59s |
| 12 | has Run anomaly scan button | ✅ expected | 9.16s |
| 13 | has Open anomalies link | ✅ expected | 4.64s |
| 14 | renders Tax Operations section | ✅ expected | 7.29s |
| 15 | has Generate quarterly liability button | ✅ expected | 6.54s |
| 16 | has Open tax page link | ✅ expected | 3.66s |
| 17 | renders AI Stack Cost Capture section | ✅ expected | 3.36s |
| 18 | has Claude monthly cost input field | ✅ expected | 3.33s |
| 19 | has Product allocation dropdown | ✅ expected | 5.27s |
| 20 | has Capture Claude subscription button | ✅ expected | 9.25s |
| 21 | renders Hiring Impact Calculator section | ✅ expected | 4.77s |
| 22 | has Annual CTC input | ✅ expected | 8.27s |
| 23 | has Join month input | ✅ expected | 4.87s |
| 24 | has Calculate impact button | ✅ expected | 4.91s |
| 25 | has Open CTO planner link | ✅ expected | 3.78s |
| 26 | renders Smart CFO Agent section | ✅ expected | 4.95s |
| 27 | has CEO risk brief button | ✅ expected | 5.20s |
| 28 | has Board narrative button | ✅ expected | 8.28s |
| 29 | has Hiring trade-off analysis button | ✅ expected | 8.81s |
| 30 | has Cost-cutting plan button | ✅ expected | 9.95s |
| 31 | has Leadership summary button | ✅ expected | 10.72s |
| 32 | has Run full leadership drill button | ✅ expected | 10.31s |
| 33 | has Open full AI agent link | ✅ expected | 8.29s |

### Finance Dashboard Page

| # | Test | Status | Duration |
|---|------|--------|----------|
| 1 | renders Finance Control heading | ✅ expected | 8.30s |
| 2 | shows ledger analysis subtitle | ✅ expected | 5.37s |
| 3 | has month selector input | ✅ expected | 5.50s |
| 4 | has Export CSV button | ✅ expected | 4.94s |
| 5 | has Export PDF button | ✅ expected | 3.89s |
| 6 | displays Net Burn summary card | ❌ unexpected | 8.35s |
| 7 | displays Total Expenses summary card | ❌ unexpected | 10.79s |
| 8 | displays Variance summary card | ❌ unexpected | 7.77s |
| 9 | Net Burn card shows monthly cash burn rate label | ❌ unexpected | 8.36s |
| 10 | Total Expenses card shows tech + non-tech label | ❌ unexpected | 8.39s |
| 11 | Variance card shows burn vs expenses label | ❌ unexpected | 8.42s |
| 12 | renders 6-Month Financial Trends chart | ✅ expected | 3.25s |
| 13 | renders Expense Breakdown by Category table | ✅ expected | 2.25s |
| 14 | expense table has correct headers | ✅ expected | 2.38s |
| 15 | expense table shows data rows or empty state | ✅ expected | 2.28s |
| 16 | Finance dashboard renders on mobile viewport | ✅ expected | 4.69s |
| 17 | Finance dashboard renders on tablet viewport | ❌ unexpected | 9.51s |

### Cross-Page Navigation & Integration

| # | Test | Status | Duration |
|---|------|--------|----------|
| 1 | full user journey: landing → dashboard → runway → expenses | ✅ expected | 8.61s |
| 2 | full user journey: dashboard → scenarios → save snapshot flow | ✅ expected | 7.31s |
| 3 | navigating between all major pages without errors | ❌ unexpected | 39.04s |
| 4 | sidebar active state changes when navigating | ✅ expected | 8.27s |

### Dashboard Layout Integration

| # | Test | Status | Duration |
|---|------|--------|----------|
| 1 | dashboard layout renders sidebar, content area, and ambient gradients | ❌ unexpected | 5.91s |
| 2 | startup health banner appears when issues exist | ✅ expected | 5.11s |

### Responsive Layout Tests

| # | Test | Status | Duration |
|---|------|--------|----------|
| 1 | landing page is responsive on mobile | ✅ expected | 4.43s |
| 2 | dashboard works on tablet viewport | ✅ expected | 5.05s |
| 3 | dashboard works on desktop viewport | ✅ expected | 3.69s |

### Landing Page (Home)

| # | Test | Status | Duration |
|---|------|--------|----------|
| 1 | renders the Vireon Times masthead | ✅ expected | 3.38s |
| 2 | displays the hero tagline — AI CFO Takes The Helm | ✅ expected | 2.65s |
| 3 | shows the meta subtitle with ERP transformation message | ✅ expected | 2.51s |
| 4 | renders the header metadata strip (Vol, Copilot, Price) | ✅ expected | 3.13s |
| 5 | renders all 3 highlight cards with titles | ✅ expected | 2.89s |
| 6 | each highlight card has a subtitle and blurb | ✅ expected | 2.29s |
| 7 | has "Open Vireon Dashboard" CTA that links to /dashboard | ✅ expected | 2.39s |
| 8 | clicking "Open Vireon Dashboard" navigates to dashboard | ✅ expected | 4.02s |
| 9 | has "Go to Vireon" secondary CTA | ✅ expected | 2.43s |
| 10 | renders anomaly alert section with 45% spike | ✅ expected | 2.82s |
| 11 | shows AI Chat Insight snippet | ✅ expected | 3.31s |
| 12 | shows runway forecast with cash and months | ✅ expected | 3.41s |
| 13 | renders the expense bar chart (12 bars) | ✅ expected | 3.00s |
| 14 | displays footer capability strip with all 4 items | ✅ expected | 7.96s |
| 15 | page renders content correctly on mobile viewport | ✅ expected | 8.04s |

### Operations Center Page

| # | Test | Status | Duration |
|---|------|--------|----------|
| 1 | renders Operations Center page title | ✅ expected | 17.31s |
| 2 | displays Finance Operations Controls heading | ✅ expected | 10.59s |
| 3 | shows Ops Coverage badge | ✅ expected | 11.22s |
| 4 | has Refresh button | ❌ unexpected | 9.73s |
| 5 | renders Live FX section | ✅ expected | 12.86s |
| 6 | has Sync live FX button | ✅ expected | 10.58s |
| 7 | renders Forecast Governance section | ✅ expected | 9.79s |
| 8 | has Retrain now button | ✅ expected | 12.87s |
| 9 | shows forecast MAPE and MAE metrics | ✅ expected | 12.79s |
| 10 | renders Collections & DSO section | ✅ expected | 14.35s |
| 11 | shows Open AR, Open AP, DSO, Overdue AR | ❌ unexpected | 14.40s |
| 12 | renders Invoice Queue Priority section | ✅ expected | 13.53s |
| 13 | renders Document Workflow Actions section | ✅ expected | 11.41s |
| 14 | has Document ID and Workflow note inputs | ✅ expected | 11.12s |
| 15 | has Classify, Approve, Reject, Post to ledger buttons | ✅ expected | 11.14s |

### Page Load Times

| # | Test | Status | Duration |
|---|------|--------|----------|
| 1 | Landing page loads within acceptable time | ✅ expected | 4.12s |
| 2 | Dashboard page loads within acceptable time | ✅ expected | 4.20s |
| 3 | CEO Dashboard page loads within acceptable time | ✅ expected | 8.28s |
| 4 | CTO Dashboard page loads within acceptable time | ✅ expected | 8.69s |
| 5 | Finance Dashboard page loads within acceptable time | ✅ expected | 7.87s |
| 6 | Runway page loads within acceptable time | ✅ expected | 7.57s |
| 7 | Expenses page loads within acceptable time | ✅ expected | 7.19s |
| 8 | Revenue page loads within acceptable time | ✅ expected | 7.51s |
| 9 | Scenarios page loads within acceptable time | ✅ expected | 10.72s |
| 10 | Tax page loads within acceptable time | ✅ expected | 10.00s |
| 11 | Anomalies page loads within acceptable time | ✅ expected | 10.17s |
| 12 | Benchmarking page loads within acceptable time | ✅ expected | 9.78s |
| 13 | AI Agent page loads within acceptable time | ✅ expected | 10.05s |
| 14 | Features Hub page loads within acceptable time | ✅ expected | 7.45s |
| 15 | Operations page loads within acceptable time | ✅ expected | 7.51s |
| 16 | Settings page loads within acceptable time | ✅ expected | 10.29s |

### Console Error Checks

| # | Test | Status | Duration |
|---|------|--------|----------|
| 1 | Landing page has no critical JS errors | ✅ expected | 4.28s |
| 2 | Dashboard page has no critical JS errors | ✅ expected | 4.64s |
| 3 | Runway page has no critical JS errors | ✅ expected | 7.28s |
| 4 | Expenses page has no critical JS errors | ✅ expected | 9.79s |
| 5 | Revenue page has no critical JS errors | ✅ expected | 8.40s |
| 6 | Scenarios page has no critical JS errors | ✅ expected | 7.46s |
| 7 | Tax page has no critical JS errors | ✅ expected | 6.34s |

### Resource Loading

| # | Test | Status | Duration |
|---|------|--------|----------|
| 1 | landing page has no 404 resource errors | ✅ expected | 4.17s |
| 2 | dashboard has no 404 resource errors | ✅ expected | 4.77s |

### Viewport Stability

| # | Test | Status | Duration |
|---|------|--------|----------|
| 1 | no horizontal overflow on mobile viewport | ✅ expected | 4.39s |
| 2 | dashboard content area fills available space | ❌ unexpected | 4.93s |

### Responsive Layout Tests - All Pages

| # | Test | Status | Duration |
|---|------|--------|----------|
| 1 | Landing renders correctly at mobile (375x812) | ✅ expected | 4.11s |
| 2 | Dashboard renders correctly at mobile (375x812) | ✅ expected | 3.79s |
| 3 | CEO Dashboard renders correctly at mobile (375x812) | ✅ expected | 3.38s |
| 4 | CTO Dashboard renders correctly at mobile (375x812) | ✅ expected | 3.40s |
| 5 | Finance Dashboard renders correctly at mobile (375x812) | ✅ expected | 4.04s |
| 6 | Runway renders correctly at mobile (375x812) | ❌ unexpected | 19.96s |
| 7 | Expenses renders correctly at mobile (375x812) | ❌ unexpected | 19.91s |
| 8 | Revenue renders correctly at mobile (375x812) | ❌ unexpected | 19.89s |
| 9 | Scenarios renders correctly at mobile (375x812) | ❌ unexpected | 19.56s |
| 10 | Tax renders correctly at mobile (375x812) | ✅ expected | 6.25s |
| 11 | Anomalies renders correctly at mobile (375x812) | ❌ unexpected | 19.94s |
| 12 | Benchmarking renders correctly at mobile (375x812) | ❌ unexpected | 17.40s |
| 13 | AI Agent renders correctly at mobile (375x812) | ❌ unexpected | 19.10s |
| 14 | Features Hub renders correctly at mobile (375x812) | ✅ expected | 1.11s |
| 15 | Operations renders correctly at mobile (375x812) | ✅ expected | 4.07s |
| 16 | Settings renders correctly at mobile (375x812) | ✅ expected | 1.38s |
| 17 | Landing renders correctly at tablet (768x1024) | ✅ expected | 1.24s |
| 18 | Dashboard renders correctly at tablet (768x1024) | ✅ expected | 2.69s |
| 19 | CEO Dashboard renders correctly at tablet (768x1024) | ✅ expected | 3.38s |
| 20 | CTO Dashboard renders correctly at tablet (768x1024) | ✅ expected | 2.14s |
| 21 | Finance Dashboard renders correctly at tablet (768x1024) | ✅ expected | 1.93s |
| 22 | Runway renders correctly at tablet (768x1024) | ❌ unexpected | 19.01s |
| 23 | Expenses renders correctly at tablet (768x1024) | ❌ unexpected | 18.37s |
| 24 | Revenue renders correctly at tablet (768x1024) | ❌ unexpected | 18.63s |
| 25 | Scenarios renders correctly at tablet (768x1024) | ❌ unexpected | 18.31s |
| 26 | Tax renders correctly at tablet (768x1024) | ✅ expected | 4.96s |
| 27 | Anomalies renders correctly at tablet (768x1024) | ❌ unexpected | 17.91s |
| 28 | Benchmarking renders correctly at tablet (768x1024) | ❌ unexpected | 18.66s |
| 29 | AI Agent renders correctly at tablet (768x1024) | ❌ unexpected | 17.88s |
| 30 | Features Hub renders correctly at tablet (768x1024) | ✅ expected | 2.16s |
| 31 | Operations renders correctly at tablet (768x1024) | ✅ expected | 4.68s |
| 32 | Settings renders correctly at tablet (768x1024) | ✅ expected | 1.53s |
| 33 | Landing renders correctly at desktop (1440x900) | ✅ expected | 1.14s |
| 34 | Dashboard renders correctly at desktop (1440x900) | ✅ expected | 1.41s |
| 35 | CEO Dashboard renders correctly at desktop (1440x900) | ✅ expected | 1.61s |
| 36 | CTO Dashboard renders correctly at desktop (1440x900) | ✅ expected | 1.42s |
| 37 | Finance Dashboard renders correctly at desktop (1440x900) | ✅ expected | 1.45s |
| 38 | Runway renders correctly at desktop (1440x900) | ❌ unexpected | 18.68s |
| 39 | Expenses renders correctly at desktop (1440x900) | ❌ unexpected | 18.43s |
| 40 | Revenue renders correctly at desktop (1440x900) | ❌ unexpected | 18.50s |
| 41 | Scenarios renders correctly at desktop (1440x900) | ❌ unexpected | 18.40s |
| 42 | Tax renders correctly at desktop (1440x900) | ✅ expected | 5.34s |
| 43 | Anomalies renders correctly at desktop (1440x900) | ❌ unexpected | 19.00s |
| 44 | Benchmarking renders correctly at desktop (1440x900) | ❌ unexpected | 19.19s |
| 45 | AI Agent renders correctly at desktop (1440x900) | ❌ unexpected | 18.39s |
| 46 | Features Hub renders correctly at desktop (1440x900) | ✅ expected | 1.70s |
| 47 | Operations renders correctly at desktop (1440x900) | ✅ expected | 4.49s |
| 48 | Settings renders correctly at desktop (1440x900) | ✅ expected | 1.23s |
| 49 | Landing renders correctly at fullhd (1920x1080) | ✅ expected | 1.12s |
| 50 | Dashboard renders correctly at fullhd (1920x1080) | ✅ expected | 1.70s |
| 51 | CEO Dashboard renders correctly at fullhd (1920x1080) | ✅ expected | 1.76s |
| 52 | CTO Dashboard renders correctly at fullhd (1920x1080) | ✅ expected | 2.19s |
| 53 | Finance Dashboard renders correctly at fullhd (1920x1080) | ✅ expected | 1.37s |
| 54 | Runway renders correctly at fullhd (1920x1080) | ❌ unexpected | 17.46s |
| 55 | Expenses renders correctly at fullhd (1920x1080) | ❌ unexpected | 18.20s |
| 56 | Revenue renders correctly at fullhd (1920x1080) | ❌ unexpected | 18.48s |
| 57 | Scenarios renders correctly at fullhd (1920x1080) | ❌ unexpected | 18.15s |
| 58 | Tax renders correctly at fullhd (1920x1080) | ✅ expected | 5.59s |
| 59 | Anomalies renders correctly at fullhd (1920x1080) | ❌ unexpected | 18.69s |
| 60 | Benchmarking renders correctly at fullhd (1920x1080) | ❌ unexpected | 18.91s |
| 61 | AI Agent renders correctly at fullhd (1920x1080) | ❌ unexpected | 18.84s |
| 62 | Features Hub renders correctly at fullhd (1920x1080) | ✅ expected | 2.41s |
| 63 | Operations renders correctly at fullhd (1920x1080) | ✅ expected | 4.57s |
| 64 | Settings renders correctly at fullhd (1920x1080) | ✅ expected | 1.61s |
| 65 | sidebar is visible on desktop dashboard | ✅ expected | 1.58s |
| 66 | sidebar is visible on tablet dashboard | ✅ expected | 1.80s |
| 67 | recharts containers resize at different viewports | ✅ expected | 5.28s |

### Revenue Intelligence Page

| # | Test | Status | Duration |
|---|------|--------|----------|
| 1 | renders page title "Revenue Intelligence" | ❌ unexpected | 12.94s |
| 2 | displays Revenue performance badge | ✅ expected | 1.97s |
| 3 | shows Growth and Retention heading | ✅ expected | 2.09s |
| 4 | shows description about MRR, ARR, NRR, and churn | ✅ expected | 7.47s |
| 5 | displays Current MRR card | ✅ expected | 7.44s |
| 6 | displays Projected ARR card | ✅ expected | 2.23s |
| 7 | displays Net Retention card | ✅ expected | 3.37s |
| 8 | displays Churn card | ✅ expected | 3.25s |
| 9 | renders MRR Momentum chart section | ✅ expected | 1.88s |
| 10 | MRR chart shows YoY growth badge | ✅ expected | 7.46s |
| 11 | MRR chart has recharts container | ✅ expected | 7.50s |
| 12 | MRR chart shows Last 6 months label | ✅ expected | 2.04s |
| 13 | renders Revenue by Segment section | ✅ expected | 1.65s |
| 14 | shows segment breakdown (Orchard, Vineyard, Others) | ✅ expected | 2.85s |
| 15 | segment percentages are displayed | ❌ unexpected | 1.78s |
| 16 | shows Total Monthly value | ❌ unexpected | 2.83s |
| 17 | renders Retention & Churn Health section | ✅ expected | 2.66s |
| 18 | shows NRR value | ✅ expected | 2.33s |
| 19 | shows Target > 110% label | ✅ expected | 2.35s |
| 20 | has Run strategy audit button | ✅ expected | 2.54s |

### Runway & Survival Page

| # | Test | Status | Duration |
|---|------|--------|----------|
| 1 | renders the page title "Runway & Survival" | ❌ unexpected | 7.97s |
| 2 | shows runway status badge (Critical/Watch/Healthy) | ✅ expected | 3.42s |
| 3 | displays runway months in header | ✅ expected | 3.33s |
| 4 | shows current cash and monthly burn info | ✅ expected | 8.39s |
| 5 | has Forecast analysis button | ✅ expected | 2.81s |
| 6 | renders Scenario Planner section | ✅ expected | 3.84s |
| 7 | has Reduce Spend slider | ✅ expected | 3.49s |
| 8 | has Add Headcount slider | ✅ expected | 3.13s |
| 9 | has Revenue Growth slider | ✅ expected | 4.20s |
| 10 | adjusting Reduce Spend slider updates scenario results | ✅ expected | 3.49s |
| 11 | scenario results show Base and Scenario Monthly Burn | ✅ expected | 3.16s |
| 12 | displays Terminal Date card | ✅ expected | 3.16s |
| 13 | displays Monthly Net Burn card | ✅ expected | 3.47s |
| 14 | displays Safety Buffer card | ✅ expected | 3.31s |
| 15 | renders Liquidity Trajectory chart section | ✅ expected | 3.30s |
| 16 | chart has 6-month projection label | ✅ expected | 4.29s |
| 17 | recharts SVG is rendered in chart container | ✅ expected | 4.24s |

### Scenarios / Strategic Simulations Page

| # | Test | Status | Duration |
|---|------|--------|----------|
| 1 | renders page title "Strategic Simulations" | ❌ unexpected | 8.86s |
| 2 | displays heading about planning decisions | ✅ expected | 4.17s |
| 3 | shows Scenario engine badge | ✅ expected | 4.36s |
| 4 | has Planning Mode section with three modes | ✅ expected | 4.33s |
| 5 | Balanced mode is selected by default | ✅ expected | 4.16s |
| 6 | switching to Defensive mode updates note text | ✅ expected | 4.74s |
| 7 | switching to Aggressive mode updates note text | ✅ expected | 4.41s |
| 8 | has Cash Policy section with two options | ❌ unexpected | 2.89s |
| 9 | toggling cash policy updates sensitivity note | ✅ expected | 8.33s |
| 10 | displays Monthly Hiring Burden card | ✅ expected | 3.89s |
| 11 | displays Annual Hiring Cost card | ✅ expected | 7.91s |
| 12 | displays Revenue Effect card | ✅ expected | 2.26s |
| 13 | displays Net Runway Effect card | ✅ expected | 7.96s |
| 14 | renders Hiring Simulation section | ✅ expected | 2.53s |
| 15 | has new hires range slider | ✅ expected | 1.85s |
| 16 | has average salary range slider | ✅ expected | 3.34s |
| 17 | shows runway pressure from hiring | ✅ expected | 2.12s |
| 18 | has Save Snapshot button for hiring | ✅ expected | 7.97s |
| 19 | renders Revenue Stress Test section | ✅ expected | 2.54s |
| 20 | has revenue shift slider | ✅ expected | 2.26s |
| 21 | shows Potential runway contribution | ✅ expected | 3.55s |
| 22 | shows Finance Decision Signal section | ✅ expected | 3.23s |
| 23 | displays operating signal badge (healthy/caution/high-risk) | ✅ expected | 3.45s |
| 24 | has Ask finance agent for plan button | ✅ expected | 3.06s |
| 25 | has Generate executive memo button | ✅ expected | 2.33s |
| 26 | adjusting hiring count slider changes burden value | ❌ unexpected | 19.76s |

### Settings Page

| # | Test | Status | Duration |
|---|------|--------|----------|
| 1 | renders Settings page title | ❌ unexpected | 3.69s |
| 2 | displays Platform Settings heading | ✅ expected | 3.47s |
| 3 | shows System configuration badge | ✅ expected | 3.13s |
| 4 | has Refresh button | ❌ unexpected | 3.22s |
| 5 | shows Startup Readiness section | ✅ expected | 2.75s |
| 6 | displays Status field | ✅ expected | 5.52s |
| 7 | displays Companies count | ✅ expected | 5.60s |
| 8 | displays Ledger rows count | ✅ expected | 5.54s |
| 9 | displays Missing keys count | ✅ expected | 7.38s |
| 10 | renders Connector Conflict Policy section | ❌ unexpected | 6.86s |
| 11 | has merge, plaid, and cloud costs dropdowns | ✅ expected | 8.00s |
| 12 | policy dropdowns have correct options | ✅ expected | 7.97s |
| 13 | changing policy dropdown works | ✅ expected | 7.76s |
| 14 | has Save policy button | ✅ expected | 7.57s |
| 15 | renders Team Access section | ✅ expected | 7.33s |
| 16 | displays team members | ❌ unexpected | 7.36s |
| 17 | shows team member roles | ❌ unexpected | 8.40s |
| 18 | shows team member emails | ✅ expected | 8.26s |
| 19 | shows VIREON AI configured as CFO note | ✅ expected | 8.17s |

### Sidebar Navigation

| # | Test | Status | Duration |
|---|------|--------|----------|
| 1 | sidebar is visible on dashboard pages | ✅ expected | 5.98s |
| 2 | sidebar contains Vireon logo | ✅ expected | 2.01s |
| 3 | displays "Dashboard" navigation link | ✅ expected | 2.13s |
| 4 | displays "Feature Hub" navigation link | ✅ expected | 2.82s |
| 5 | displays "Operations" navigation link | ✅ expected | 2.73s |
| 6 | displays "CTO Planner" navigation link | ✅ expected | 3.91s |
| 7 | displays "Runway" navigation link | ✅ expected | 3.95s |
| 8 | displays "Expenses" navigation link | ✅ expected | 3.80s |
| 9 | displays "Revenue" navigation link | ✅ expected | 3.81s |
| 10 | displays "Tax" navigation link | ✅ expected | 3.54s |
| 11 | displays "Scenarios" navigation link | ✅ expected | 3.42s |
| 12 | displays "Benchmarking" navigation link | ✅ expected | 3.61s |
| 13 | displays "AI Agent" navigation link | ✅ expected | 3.76s |
| 14 | displays "Anomalies" navigation link | ✅ expected | 3.78s |
| 15 | displays "Settings" navigation link | ✅ expected | 4.19s |
| 16 | navigating to Runway page via sidebar | ✅ expected | 6.93s |
| 17 | navigating to Expenses page via sidebar | ✅ expected | 5.81s |
| 18 | navigating to Revenue page via sidebar | ✅ expected | 6.34s |
| 19 | navigating to Scenarios page via sidebar | ✅ expected | 5.51s |
| 20 | navigating to Settings page via sidebar | ✅ expected | 7.74s |
| 21 | dashboard link shows active state on dashboard page | ✅ expected | 3.19s |
| 22 | sidebar toggle button collapses/expands sidebar | ✅ expected | 10.51s |
| 23 | displays user info card at bottom of sidebar | ✅ expected | 3.91s |

### Tax Compliance Hub Page

| # | Test | Status | Duration |
|---|------|--------|----------|
| 1 | renders Tax Compliance Hub heading | ✅ expected | 6.71s |
| 2 | shows current year in subtitle | ✅ expected | 7.87s |
| 3 | has Refresh button | ✅ expected | 8.16s |
| 4 | displays GST Status card | ✅ expected | 8.45s |
| 5 | displays TDS Filing card | ❌ unexpected | 9.72s |
| 6 | displays Quarter Filing card | ✅ expected | 8.81s |
| 7 | displays Outstanding card | ✅ expected | 8.70s |
| 8 | renders Current Quarter Liability section | ✅ expected | 9.31s |
| 9 | shows GST Liability value | ✅ expected | 9.39s |
| 10 | shows TDS Payable value | ✅ expected | 8.62s |
| 11 | shows Total Due value | ✅ expected | 10.70s |
| 12 | renders Tax Payment Schedule section | ✅ expected | 11.23s |
| 13 | renders Tax Filing Checklist section | ✅ expected | 9.73s |
| 14 | checklist has 6 items | ✅ expected | 9.17s |
| 15 | checklist items have checkboxes | ✅ expected | 8.95s |
| 16 | renders GST on Sales reference card | ✅ expected | 8.56s |
| 17 | renders TDS on Salary & Vendors reference card | ✅ expected | 8.22s |
| 18 | has Generate Quarterly Liability button | ✅ expected | 8.38s |
| 19 | has Mark Payment as Received button | ✅ expected | 8.42s |

### Visual Regression & Screenshot Tests

| # | Test | Status | Duration |
|---|------|--------|----------|
| 1 | landing page visual snapshot - desktop | ❌ unexpected | 7.14s |
| 2 | landing page visual snapshot - mobile | ❌ unexpected | 8.62s |
| 3 | dashboard page visual snapshot | ❌ unexpected | 7.81s |
| 4 | runway page visual snapshot | ❌ unexpected | 7.36s |
| 5 | expenses page visual snapshot | ❌ unexpected | 6.11s |
| 6 | revenue page visual snapshot | ❌ unexpected | 4.71s |
| 7 | scenarios page visual snapshot | ❌ unexpected | 4.48s |
| 8 | tax page visual snapshot | ❌ unexpected | 3.79s |
| 9 | anomalies page visual snapshot | ❌ unexpected | 3.73s |
| 10 | benchmarking page visual snapshot | ❌ unexpected | 3.52s |
| 11 | settings page visual snapshot | ❌ unexpected | 8.23s |
| 12 | CEO dashboard visual snapshot | ❌ unexpected | 9.01s |
| 13 | CTO dashboard visual snapshot | ❌ unexpected | 3.81s |
| 14 | Finance dashboard visual snapshot | ❌ unexpected | 2.59s |

---

## Feature Coverage Mapping

| Frontend Feature | Test File(s) | Status |
|------------------|-------------|--------|
| Landing Page | `landing-page.spec.ts` | ✅ Comprehensive |
| Dashboard Home | `dashboard.spec.ts` | ✅ Comprehensive |
| CEO Dashboard | `ceo-dashboard.spec.ts` | ✅ Comprehensive |
| CTO Dashboard | `cto-dashboard.spec.ts` | ✅ Comprehensive |
| Finance Dashboard | `finance-dashboard.spec.ts` | ✅ Comprehensive |
| Runway Analysis | `runway.spec.ts` | ✅ Comprehensive |
| Expenses | `expenses.spec.ts` | ✅ Comprehensive |
| Revenue Intelligence | `revenue.spec.ts` | ✅ Comprehensive |
| Scenarios | `scenarios.spec.ts` | ✅ Comprehensive |
| Tax Compliance | `tax.spec.ts` | ✅ Comprehensive |
| Anomalies | `anomalies.spec.ts` | ✅ Comprehensive |
| Benchmarking | `benchmarking.spec.ts` | ✅ Comprehensive |
| AI Agent | `ai-agent.spec.ts` | ✅ Comprehensive |
| Features Hub | `features-hub.spec.ts` | ✅ Comprehensive |
| Operations Center | `operations.spec.ts` | ✅ Comprehensive |
| Settings | `settings.spec.ts` | ✅ Comprehensive |
| Sidebar Navigation | `sidebar-navigation.spec.ts` | ✅ Comprehensive |
| Chat Drawer | `chat-drawer.spec.ts` | ✅ Comprehensive |
| Cross-Feature Journeys | `cross-feature-journeys.spec.ts` | ✅ Comprehensive |
| Responsive Layout | `responsive-layout.spec.ts` | ✅ All Viewports |
| Accessibility | `accessibility.spec.ts` | ✅ Semantic + A11y |
| Performance | `performance.spec.ts` | ✅ Load + Errors |
| Visual Regression | `visual-regression.spec.ts` | ✅ Screenshots |
| Basic Smoke | `basic.spec.ts` | ✅ Smoke |
| Integration Flows | `integration.spec.ts` | ✅ Cross-Page |

---

## How to Run Tests

```bash
# Run all tests (all browsers)
npm run test:e2e

# Run tests in chromium only (fastest)
npm run test:e2e:chromium

# Run tests with report generation
npm run test:e2e:report

# Run tests in headed mode (visible browser)
npm run test:e2e:headed

# Run tests in Playwright UI mode
npm run test:e2e:ui

# Debug failing tests
npm run test:e2e:debug

# Update visual regression baselines
npm run test:visual
```

## Report Artifacts

| Artifact | Location |
|----------|----------|
| HTML Report | `frontend/playwright-report/index.html` |
| JSON Results | `frontend/test-results/results.json` |
| JUnit XML | `frontend/test-results/results.xml` |
| Markdown Report | `frontend/PLAYWRIGHT_TEST_REPORT.md` |
| Failure Screenshots | `frontend/test-results/` |
| Failure Videos | `frontend/test-results/` |
| Visual Snapshots | `frontend/tests/*.spec.ts-snapshots/` |

---

*Report generated automatically by `scripts/generate-test-report.js`*
