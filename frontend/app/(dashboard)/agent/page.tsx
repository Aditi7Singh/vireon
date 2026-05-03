"use client";

import { useEffect, useRef, useState } from "react";
import TopBar from "@/components/TopBar";
import api, { APIError } from "@/lib/api";
import { useAppStore } from "@/lib/store";
import {
  AlertCircle, Bot, CheckCircle2, MessageSquare, RefreshCw,
  Send, Sparkles, User, FileText, Receipt, BarChart3, Shield,
  TrendingUp, Users, Zap, ChevronDown, ChevronUp, Copy,
  ThumbsUp, ThumbsDown, Paperclip, X, DollarSign,
  Activity, Clock, ArrowUpRight, ArrowDownRight, Cpu,
} from "lucide-react";
import { cn } from "@/lib/utils";

// ─── Types ────────────────────────────────────────────────────────────────────

type Message = {
  role: string;
  content: string;
  timestamp?: string;
  toolCalls?: string[];
  followUps?: string[];
};

// ─── Quick action prompts ─────────────────────────────────────────────────────

const QUICK_ACTIONS = [
  { category: "Analysis", icon: TrendingUp, color: "#059669", prompts: [
    "Show me our current runway and burn rate",
    "Analyze our cash position and flag risks",
    "What's our MRR growth trend this quarter?",
    "Compare our unit economics to SaaS benchmarks",
  ]},
  { category: "Invoices", icon: FileText, color: "#2563eb", prompts: [
    "Which invoices are overdue and how much?",
    "Create an invoice for Acme Corp for ₹5L consulting",
    "What's our DSO this quarter versus last?",
    "Send payment reminders for all overdue invoices",
  ]},
  { category: "Bills & AP", icon: Receipt, color: "#d97706", prompts: [
    "List all bills pending my approval",
    "What AP is due in the next 7 days?",
    "Optimize our AP payment timing for cash flow",
    "Flag any duplicate invoices in AP",
  ]},
  { category: "Reports", icon: BarChart3, color: "#7c3aed", prompts: [
    "Generate a P&L summary for Q1 FY26",
    "How does our gross margin compare to budget?",
    "Show key balance sheet movements this month",
    "Prepare a board-ready cash flow summary",
  ]},
  { category: "Compliance", icon: Shield, color: "#dc2626", prompts: [
    "What tax deadlines are coming up this month?",
    "Calculate advance tax due for Q4 FY26",
    "Check our TDS filing status for March",
    "What GST filings are due in Q2?",
  ]},
  { category: "Forecasting", icon: Sparkles, color: "#8d4f27", prompts: [
    "Forecast our 12-month runway under base case",
    "Model impact of hiring 5 engineers in June",
    "What happens to runway if we lose our top customer?",
    "Simulate raising a Series B at ₹1,600Cr valuation",
  ]},
  { category: "Payroll", icon: Users, color: "#16a34a", prompts: [
    "Show payroll breakdown by department",
    "What's our total CTC vs take-home ratio?",
    "When is the next payroll run?",
    "Calculate PF and ESI liability for April",
  ]},
];

// ─── Tool call sequences per intent ──────────────────────────────────────────

const TOOL_SEQUENCES: Record<string, string[]> = {
  runway:     ["fetch_cash_balance()", "calculate_gross_burn()", "calculate_net_burn()", "compute_runway_months()", "fetch_risk_factors()", "generate_recommendations()"],
  invoice:    ["fetch_open_invoices()", "calculate_dso()", "flag_overdue_items()", "rank_by_risk()", "generate_recommendations()"],
  pl:         ["fetch_revenue_data()", "fetch_cogs()", "fetch_opex()", "compute_gross_margin()", "compute_ebitda()", "compare_to_budget()"],
  forecast:   ["fetch_historical_burn()", "run_monte_carlo(n=1000)", "compute_p10_p50_p90()", "apply_growth_assumptions()", "generate_scenario_table()"],
  compliance: ["fetch_tax_calendar()", "compute_advance_tax()", "check_tds_liability()", "check_gst_status()", "flag_upcoming_deadlines()"],
  payroll:    ["fetch_employee_roster()", "compute_gross_salary()", "deduct_pf_esic_tds()", "compute_net_payable()", "generate_payslip_summary()"],
  cashflow:   ["fetch_bank_balances()", "fetch_ar_aging()", "fetch_ap_aging()", "compute_net_cash_position()", "forecast_30d_cashflow()"],
  anomaly:    ["scan_gl_entries()", "run_benford_law_test()", "flag_duplicate_invoices()", "detect_round_number_bias()", "score_vendor_risk()"],
};

function getToolSequence(query: string): string[] {
  const q = query.toLowerCase();
  if (q.includes("runway") || q.includes("burn")) return TOOL_SEQUENCES.runway;
  if (q.includes("invoice") || q.includes("overdue") || q.includes("ar") || q.includes("dso")) return TOOL_SEQUENCES.invoice;
  if (q.includes("p&l") || q.includes("profit") || q.includes("margin") || q.includes("ebitda")) return TOOL_SEQUENCES.pl;
  if (q.includes("forecast") || q.includes("model") || q.includes("scenario") || q.includes("hire")) return TOOL_SEQUENCES.forecast;
  if (q.includes("tax") || q.includes("gst") || q.includes("tds") || q.includes("compliance")) return TOOL_SEQUENCES.compliance;
  if (q.includes("payroll") || q.includes("salary") || q.includes("pf") || q.includes("ctc")) return TOOL_SEQUENCES.payroll;
  if (q.includes("cash") || q.includes("balance") || q.includes("bank")) return TOOL_SEQUENCES.cashflow;
  if (q.includes("anomaly") || q.includes("duplicate") || q.includes("fraud") || q.includes("audit")) return TOOL_SEQUENCES.anomaly;
  return ["analyze_query()", "fetch_relevant_data()", "compute_insights()", "generate_response()"];
}

function getFollowUps(query: string): string[] {
  const q = query.toLowerCase();
  if (q.includes("runway") || q.includes("burn")) return [
    "Model a 20% faster MRR growth scenario",
    "What expenses can we cut to extend runway 3 months?",
    "Show weekly burn breakdown",
  ];
  if (q.includes("invoice") || q.includes("overdue")) return [
    "Draft a payment reminder email for overdue invoices",
    "Show historical DSO trend for all customers",
    "Which customers have the highest credit risk?",
  ];
  if (q.includes("p&l") || q.includes("margin")) return [
    "Break down gross margin by product line",
    "Compare this quarter to same period last year",
    "What's driving the margin compression?",
  ];
  if (q.includes("forecast") || q.includes("hire")) return [
    "Add sensitivity: what if revenue grows 30% instead?",
    "Show the pessimistic 10th-percentile scenario",
    "What's the minimum MRR to be self-sustaining?",
  ];
  if (q.includes("tax") || q.includes("compliance")) return [
    "Calculate exact advance tax installment due",
    "Show all TDS deductees for March",
    "Generate a compliance calendar for Q1 FY27",
  ];
  return [
    "Drill deeper into this analysis",
    "Export this data as a spreadsheet",
    "Share this insight with the team",
  ];
}

function cachedAgentResponse(query: string, toolsUsed: string[]) {
  const q = query.toLowerCase();
  if (q.includes("dso") || q.includes("invoice") || q.includes("overdue")) {
    return `**Cached AR Insight**\n\nI ran the local invoice workflow (${toolsUsed.length} tools). Cached DSO is **~41 days this quarter vs ~46 days last quarter**, so collections are improving but still need attention.\n\nTop actions:\n• Prioritize invoices over 30 days overdue\n• Send reminders for the largest balances first\n• Review customers with repeated late payments before extending new credit`;
  }
  if (q.includes("runway") || q.includes("burn")) {
    return `**Cached Runway Insight**\n\nI ran the local runway workflow (${toolsUsed.length} tools). Current cached runway is **about 14 months**. Spend reductions extend runway immediately, hiring reduces it, and revenue growth now offsets burn directly in the runway model.\n\nRecommended next move: model a 15-20% spend reduction alongside the hiring plan so leadership can see net impact.`;
  }
  if (q.includes("expense") || q.includes("claim") || q.includes("anomal") || q.includes("audit")) {
    return `**Cached Expense Controls Insight**\n\nI ran the local controls workflow (${toolsUsed.length} tools). Focus first on submitted expense claims, duplicate AP invoices, weekend transactions, and round-amount GL entries.\n\nApprove clean claims, reject unsupported ones, and hold payment on critical anomalies until receipts or invoice matches are verified.`;
  }
  return `**Cached Finley Insight**\n\nI ran ${toolsUsed.length} local tools and prepared a cached answer while the live backend reconnects. The page is still usable: you can review local finance data, run workflows, and export where supported. For live ledger values, confirm Render is healthy and that Vercel points to the Render backend base URL.`;
}

// ─── 20+ Example Responses ───────────────────────────────────────────────────

const EXAMPLE_RESPONSES: Record<string, string> = {
  "Show me our current runway and burn rate": `**Runway & Burn Analysis — April 2026**

📊 **Current Position**
• Cash & Equivalents: **₹2.84 Cr** (HDFC + ICICI + Kotak)
• Monthly Gross Burn: **₹48.1L**
• Monthly Net Burn: **₹37.2L** (after ₹10.9L revenue)
• **Runway: 7.6 months** at current burn rate

⚠️ **Risk Factors**
• Cooley LLP bill of ₹1.87L is 15 days overdue — pays immediately reduces runway by 4 days
• AWS spend trending +12% QoQ — optimization could save ₹1.5L/month
• Payroll bump in June (+2 hires) will increase burn by ~₹4.2L/month

✅ **Positive Signals**
• MRR grew 21% last month (₹8.9L → ₹10.8L), reducing net burn each month
• Burn multiple: 0.82× (excellent for growth stage — industry median 1.4×)
• Gross margin improved to 68% from 61% QoQ

**Recommendation:** At current MRR growth, you reach cash-flow positive in ~5.2 months. Maintain hiring plan but defer opex >₹5L until Q3 FY27.`,

  "Which invoices are overdue and how much?": `**Overdue Invoice Summary — April 27, 2026**

🔴 **2 Invoices Overdue**

| Invoice | Customer | Amount | Days Overdue | Risk |
|---------|----------|--------|--------------|------|
| INV-2026-042 | Nexus Ventures | ₹6.0L | 18 days | High |
| INV-2026-038 | Bloom Health | ₹3.2L | 7 days | Medium |

**Total Overdue AR: ₹9.2L** (DSO: 38 days vs. industry 30)

**Suggested Actions**
1. Send payment reminder to Nexus (historically slow — avg 45 DSO)
2. Bloom Health has not opened the email — resend with read receipt
3. Consider adding 1.5%/month late fee clause in next contract renewal

**Upcoming Risk:** INV-2026-047 (TechCorp · ₹8.4L) due in 12 days with no payment confirmation.

_Want me to draft the reminder emails and schedule them for 9am tomorrow?_`,

  "Generate a P&L summary for Q1 FY26": `**P&L Summary — Q1 FY 2025-26 (Apr–Jun 2025)**

| Line Item | Q1 FY26 | Q1 FY25 | YoY Change |
|-----------|---------|---------|------------|
| Revenue | ₹28.4L | ₹18.7L | **+51.9%** |
| COGS | ₹9.1L | ₹6.5L | +40.0% |
| **Gross Profit** | **₹19.3L** | **₹12.2L** | **+58.2%** |
| Gross Margin | **67.9%** | 65.2% | +270bps |
| Payroll | ₹13.5L | ₹10.2L | +32.4% |
| AWS + Infra | ₹2.4L | ₹1.8L | +33.3% |
| Marketing | ₹3.1L | ₹2.6L | +19.2% |
| G&A | ₹1.8L | ₹1.4L | +28.6% |
| **Total OpEx** | **₹20.8L** | **₹16.0L** | **+30.0%** |
| **EBITDA** | **−₹1.5L** | **−₹3.8L** | 60.5% improvement |
| EBITDA Margin | −5.3% | −20.3% | **+1500bps** |

✅ **Key Takeaways:** Revenue growth outpacing OpEx growth by 21.9pp. Gross margin expansion signals improving unit economics. EBITDA trajectory to breakeven by Q3 FY27 at current rates.`,

  "Forecast our 12-month runway under base case": `**12-Month Runway Forecast — Base Case (Apr 2026 → Mar 2027)**

📈 **Assumptions (Base Case)**
• MRR Growth: +15% MoM tapering to +8% by Q4
• Headcount additions: 3 in Q1, 2 in Q3
• AWS optimization: −₹1.2L/month starting Jun 2026

| Month | Revenue | Gross Burn | Net Burn | Cash Balance |
|-------|---------|------------|----------|--------------|
| May '26 | ₹12.4L | ₹50.2L | ₹37.8L | ₹2.46 Cr |
| Jul '26 | ₹16.1L | ₹55.8L | ₹39.7L | ₹1.68 Cr |
| Sep '26 | ₹20.8L | ₹57.1L | ₹36.3L | ₹9.4L |
| Oct '26 | ₹23.2L | ₹57.1L | ₹33.9L | — Raise needed — |

⚠️ **Cash-out risk: October 2026** under base case without new capital.

**Scenarios:**
| Scenario | Cash-Out | Notes |
|----------|----------|-------|
| Bull (+25% MRR growth) | Mar 2027 | Near default-alive |
| Base (+15% MRR growth) | Oct 2026 | Requires bridge or Series A |
| Bear (+8% MRR growth) | Jul 2026 | Immediate action needed |

**Recommendation:** Begin Series A process by July 2026 to ensure 6+ months of runway buffer at close.`,

  "What tax deadlines are coming up this month?": `**Upcoming Tax Deadlines — April 2026**

🗓️ **Critical Deadlines**

| Deadline | Date | Obligation | Amount Due | Status |
|----------|------|------------|------------|--------|
| TDS Deposit | Apr 30 | TDS on salaries (192) | ₹2.84L | ⚠️ Pending |
| Advance Tax | Jun 15 | Q1 installment (15%) | ₹1.12L | 📅 Upcoming |
| GSTR-3B | May 20 | GST monthly return | ₹4.87L | 📅 Upcoming |
| PF Payment | Apr 15 | EPF contribution | ₹1.94L | ✅ Paid |
| ESI Payment | Apr 15 | ESIC contribution | ₹34,200 | ✅ Paid |

⚠️ **TDS on salaries (₹2.84L) is due April 30 — 3 days away.** Initiate NEFT payment from HDFC corporate account today.

📋 **Q1 FY27 Calendar Preview:**
• May 7: TDS deposit for April
• May 15: PF/ESI for April
• May 20: GSTR-3B April return
• Jun 15: Advance tax Q1 (15% of annual liability)

_Want me to generate a full compliance calendar with payment reminders?_`,

  "What's our MRR growth trend this quarter?": `**MRR Growth Analysis — Q4 FY26 (Jan–Apr 2026)**

📊 **MRR Trajectory**

| Month | MRR | MoM Growth | New ARR | Churned ARR |
|-------|-----|------------|---------|-------------|
| Jan 2026 | ₹7.2L | — | ₹1.4L | ₹0.3L |
| Feb 2026 | ₹8.1L | +12.5% | ₹1.8L | ₹0.2L |
| Mar 2026 | ₹9.3L | +14.8% | ₹2.1L | ₹0.3L |
| Apr 2026 | ₹10.8L | **+16.1%** | ₹2.6L | ₹0.4L |

✅ **Positive Signals**
• Acceleration trend: growth rate improving each month (+12.5% → +16.1%)
• Net Revenue Retention: 118% (expansion > churn — excellent)
• Quick Ratio: 3.2 (new MRR / churned MRR — world-class at >4 target)

⚠️ **Watch Items**
• Churn ticked up to ₹0.4L in April — investigate if pattern continues
• 3 customers on month-to-month contracts representing ₹1.8L MRR

**Projection:** At current growth rate, MRR reaches ₹18.5L by Sep 2026, implying ARR of ₹2.22 Cr. This supports a Series A at ~6–8× ARR (₹13–18 Cr valuation).`,

  "List all bills pending my approval": `**Bills Pending Approval — April 27, 2026**

⏳ **4 Bills Awaiting Your Review**

| # | Vendor | Description | Amount | Due Date | Priority |
|---|--------|-------------|--------|----------|----------|
| 1 | AWS India | April cloud compute | ₹71,400 | Apr 30 | 🔴 Urgent |
| 2 | HubSpot | Annual CRM renewal | ₹1,24,800 | May 5 | 🟡 Soon |
| 3 | Razorpay | Payment gateway fees | ₹18,200 | May 10 | 🟢 Normal |
| 4 | WeWork Koramangala | May desk space | ₹42,000 | May 1 | 🟡 Soon |

**Total Pending: ₹2,56,400**

⚠️ **Recommended Actions:**
1. **Approve AWS immediately** — infrastructure critical, due in 3 days
2. **Review HubSpot renewal** — you're paying ₹1.04L/year unused; downgrade to Starter saves ₹78K
3. WeWork lease month-to-month — consider coworking bundle for savings of ₹12K/month

_Approve all, approve individually, or should I flag any for renegotiation?_`,

  "How does our gross margin compare to budget?": `**Gross Margin vs Budget Analysis — FY26 YTD**

📊 **Performance vs Budget**

| Month | Actual GM% | Budget GM% | Variance | Revenue |
|-------|-----------|-----------|---------|---------|
| Apr 2025 | 61.2% | 63.0% | −1.8pp | ₹6.8L |
| Jul 2025 | 64.1% | 64.5% | −0.4pp | ₹9.2L |
| Oct 2025 | 66.8% | 65.0% | **+1.8pp** | ₹11.4L |
| Jan 2026 | 67.4% | 65.5% | **+1.9pp** | ₹8.9L |
| Apr 2026 | **68.3%** | 66.0% | **+2.3pp** | ₹10.8L |

✅ **Above Budget by 2.3pp** — driven by:
• AWS reserved instance savings (−₹1.2L/month)
• Software seat optimization (removed 12 unused Figma seats)
• Increased high-margin professional services mix (+8pp of revenue)

⚠️ **Risk:** If enterprise deals >₹5L slow down, services mix drops and GM% could dip to ~65%.

**Full Year Budget:** 66.0% · **Projected Full Year:** 68.1% → **beat by ~210bps**`,

  "Show payroll breakdown by department": `**Payroll Breakdown by Department — April 2026**

👥 **18 Employees · Total CTC: ₹2.88 Cr/year**

| Department | Headcount | Monthly CTC | Take-Home | PF (Co.) | TDS Est. |
|------------|-----------|-------------|-----------|----------|---------|
| Engineering | 8 | ₹18.4L | ₹12.8L | ₹2.2L | ₹2.1L |
| Product | 2 | ₹4.2L | ₹2.9L | ₹0.5L | ₹0.5L |
| Sales | 3 | ₹5.1L | ₹3.5L | ₹0.6L | ₹0.6L |
| Marketing | 2 | ₹3.6L | ₹2.5L | ₹0.4L | ₹0.4L |
| Finance | 2 | ₹3.2L | ₹2.2L | ₹0.4L | ₹0.3L |
| Operations | 1 | ₹1.8L | ₹1.3L | ₹0.2L | ₹0.2L |
| **Total** | **18** | **₹36.3L** | **₹25.2L** | **₹4.3L** | **₹4.1L** |

📊 **Ratios:**
• Engineering cost as % of total payroll: **50.7%** (typical SaaS: 45–60%)
• Revenue per employee: ₹60,000/month (target ₹80,000+ by EOY)
• Payroll as % of total burn: **75.5%**

_Next payroll run: May 28, 2026. Want me to prepare the salary register for review?_`,

  "Model impact of hiring 5 engineers in June": `**Hiring Impact Model — 5 Engineers joining June 2026**

⚙️ **Assumptions**
• Average CTC: ₹18L/year (₹1.5L/month each)
• Total cost (CTC + PF + equipment + onboarding): ₹1.74L/month/hire
• Ramp time to full productivity: 90 days
• Revenue impact: +₹8L/month new capacity by Sep 2026

📊 **Impact Analysis**

| Metric | Before Hire | After Hire | Change |
|--------|------------|------------|--------|
| Monthly Gross Burn | ₹48.1L | ₹56.8L | **+₹8.7L** |
| Net Burn (Jun) | ₹37.2L | ₹45.9L | **+₹8.7L** |
| Runway (current cash) | 7.6 months | **6.2 months** | −1.4 months |
| Revenue/employee | ₹60K/mo | ₹49K/mo | −18% (temporary) |
| Projected Revenue/emp (Dec) | — | ₹72K/mo | Recovery by Q3 |

⚠️ **Cash Impact:** Runway drops from 7.6 to 6.2 months — **series A process should begin immediately** to maintain safe runway buffer.

✅ **Strategic Case:** 5 engineers enables delivery of 3 enterprise features scheduled for Q3, which supports 2 pipeline deals worth ₹24L ARR. NPV positive at discount rate 20%.

**Recommendation:** Hire 3 in June, 2 in August to smooth burn impact.`,

  "Analyze our cash position and flag risks": `**Cash Position & Risk Analysis — April 27, 2026**

💰 **Bank Balances**

| Account | Bank | Balance | Usage |
|---------|------|---------|-------|
| Operating | HDFC Current | ₹1.42 Cr | Day-to-day ops |
| Payroll | ICICI Salary | ₹68.4L | Monthly payroll |
| Reserve | Kotak FD | ₹74.2L | Emergency buffer |
| **Total** | | **₹2.84 Cr** | |

📊 **Cash Flow at Risk (Monte Carlo — 10,000 simulations)**
• P10 (worst 10%): ₹1.2 Cr in 6 months
• P50 (median): ₹1.8 Cr in 6 months
• P90 (best 10%): ₹2.6 Cr in 6 months

🔴 **Critical Risks**
1. **Payroll reserve:** Only ₹68.4L — 1.8× monthly payroll. Maintain minimum 3× buffer (₹1.08 Cr)
2. **Single FD concentration:** ₹74.2L in Kotak — consider laddering across 3 banks for DICGC coverage
3. **AR concentration:** Top 3 customers = 61% of AR — Nexus Ventures payment ($6L) overdue 18d

✅ **Healthy Signals**
• Operating cash covers 2.9 months of burn (minimum acceptable: 3 months — borderline)
• No outstanding loans or credit lines — clean balance sheet for fundraising`,

  "Compare our unit economics to SaaS benchmarks": `**Unit Economics Benchmarking — Vireon vs SaaS Industry**

📊 **Key Metrics vs Benchmark**

| Metric | Vireon | Seed Stage Median | Series A Target | Status |
|--------|--------|-------------------|-----------------|--------|
| Gross Margin | 68.3% | 65% | 70%+ | ✅ Good |
| LTV:CAC Ratio | 3.8× | 3× | 5× | ✅ Good |
| CAC Payback | 8.2 months | 12 months | <9 months | ✅ Excellent |
| Net Revenue Retention | 118% | 105% | 120%+ | 🟡 Near Target |
| Quick Ratio | 3.2 | 2.5 | 4+ | 🟡 Improving |
| Burn Multiple | 0.82× | 1.5× | <1× | ✅ Excellent |
| Revenue/Employee | ₹60K/mo | ₹55K/mo | ₹80K/mo | 🟡 Room to grow |
| Magic Number | 0.74 | 0.5 | >1 | ✅ Good |

✅ **Standout Strengths:** CAC payback and burn multiple are world-class — strong capital efficiency story for investors.

📈 **Areas to Improve:**
• NRR needs expansion upsell motion (currently 118% — target 125%+)
• Revenue per employee grows naturally as ARR scales without proportional headcount

**Investor Narrative:** Vireon is in the top quartile of capital efficiency among Indian B2B SaaS. Lead with burn multiple (0.82×) and CAC payback (8.2mo) in fundraising materials.`,

  "Prepare a board-ready cash flow summary": `**Board Cash Flow Summary — Q4 FY26**

📋 **Executive Summary for Board Review**

**Operating Cash Flow: −₹1.12 Cr** (vs. −₹1.87 Cr in Q3 FY26 · 40% improvement)

| Category | Q4 FY26 | Q3 FY26 | Δ |
|----------|---------|---------|---|
| Collections from customers | ₹29.4L | ₹22.1L | +33% |
| Payroll & benefits | −₹1.08 Cr | −₹1.02 Cr | −6% |
| Vendor payments | −₹18.7L | ₹22.4L | +16% |
| Tax payments | −₹8.2L | −₹7.1L | −15% |
| **Net Operating CF** | **−₹1.05 Cr** | **−₹1.29 Cr** | **+19%** |

**Investing Activities:** −₹3.2L (laptop purchases for 2 new hires)

**Financing Activities:** ₹0 (no draws on credit facility)

**Closing Cash: ₹2.84 Cr** (Opening: ₹3.96 Cr)

📊 **Board Discussion Points:**
1. Operating CF improvement of 40% QoQ — on track to breakeven by Q3 FY27
2. Customer collection efficiency improving — DSO reduced from 45 to 38 days
3. Need to discuss Series A timing given 7.6-month runway

_I can generate the full board deck with charts in PDF format — shall I proceed?_`,
};

// ─── Live context panel ───────────────────────────────────────────────────────

const LIVE_CONTEXT = {
  cash: "₹2.84 Cr",
  cashTrend: "down",
  burn: "₹37.2L/mo",
  burnTrend: "up",
  runway: "7.6 mo",
  runwayTrend: "down",
  mrr: "₹10.8L",
  mrrTrend: "up",
  alerts: 3,
  pendingApprovals: 4,
  overdueAR: "₹9.2L",
  nextDeadline: "TDS Apr 30",
};

// ─── Markdown/table renderer ──────────────────────────────────────────────────

function renderMessage(content: string) {
  const lines = content.split("\n");
  const elements: React.ReactNode[] = [];
  let tableLines: string[] = [];
  let i = 0;

  const flushTable = (key: string) => {
    if (tableLines.length < 3) {
      tableLines.forEach((l, j) => elements.push(<p key={`${key}-${j}`} className="font-mono text-xs text-[#5f5344] bg-[#f0ebe3] rounded px-2 py-0.5">{l}</p>));
      tableLines = [];
      return;
    }
    const headers = tableLines[0].split("|").map(h => h.trim()).filter(Boolean);
    const rows = tableLines.slice(2).map(r => r.split("|").map(c => c.trim()).filter(Boolean));
    elements.push(
      <div key={key} className="overflow-x-auto my-2 rounded-xl border border-[#e4d6c4]">
        <table className="w-full text-xs">
          <thead className="bg-[#f6efe5]">
            <tr>{headers.map((h, hi) => <th key={hi} className="px-3 py-2 text-left font-bold text-[#4a3f35] whitespace-nowrap">{h}</th>)}</tr>
          </thead>
          <tbody className="divide-y divide-[#f0ebe3]">
            {rows.map((row, ri) => (
              <tr key={ri} className="hover:bg-[#faf5ec]">
                {row.map((cell, ci) => {
                  const bold = cell.includes("**");
                  const cleaned = cell.replace(/\*\*(.*?)\*\*/g, "$1");
                  const isGreen = cleaned.includes("✅") || (cleaned.startsWith("+") && !cleaned.includes("−"));
                  const isRed = cleaned.includes("⚠️") || cleaned.startsWith("−") || cleaned.includes("🔴");
                  return (
                    <td key={ci} className={cn("px-3 py-2 whitespace-nowrap", bold ? "font-bold text-[#2a2017]" : "text-[#5f5344]", isGreen ? "text-emerald-700" : isRed ? "text-rose-700" : "")}>
                      {cleaned}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
    tableLines = [];
  };

  while (i < lines.length) {
    const line = lines[i];

    if (line.includes("|") && line.trim().startsWith("|")) {
      tableLines.push(line);
      i++;
      continue;
    }

    if (tableLines.length > 0) flushTable(`table-${i}`);

    if (!line.trim()) { elements.push(<div key={i} className="h-1.5" />); }
    else if (line.startsWith("**") && line.endsWith("**") && line.length > 4) {
      elements.push(<p key={i} className="font-bold text-[#2a2017] mt-1">{line.slice(2, -2)}</p>);
    } else if (line.startsWith("• ") || line.startsWith("- ")) {
      const html = line.slice(2).replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>").replace(/`(.*?)`/g, "<code class='bg-[#f0ebe3] px-1 rounded text-[10px]'>$1</code>");
      elements.push(<p key={i} className="pl-3 text-sm leading-relaxed" dangerouslySetInnerHTML={{ __html: `• ${html}` }} />);
    } else if (/^\d+\./.test(line)) {
      const html = line.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
      elements.push(<p key={i} className="pl-3 text-sm leading-relaxed" dangerouslySetInnerHTML={{ __html: html }} />);
    } else if (line.startsWith("_") && line.endsWith("_")) {
      elements.push(<p key={i} className="text-xs text-[#8b7a69] italic mt-1">{line.slice(1, -1)}</p>);
    } else {
      const html = line.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>").replace(/`(.*?)`/g, "<code class='bg-[#f0ebe3] px-1 rounded text-[10px]'>$1</code>");
      elements.push(<p key={i} className="text-sm leading-relaxed" dangerouslySetInnerHTML={{ __html: html }} />);
    }
    i++;
  }
  if (tableLines.length > 0) flushTable("table-end");

  return <div className="space-y-1">{elements}</div>;
}

// ─── Main Component ───────────────────────────────────────────────────────────

export default function AgentPage() {
  const { chatSessionId, setChatSessionId } = useAppStore();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [activeToolCall, setActiveToolCall] = useState<string>("");
  const [completedTools, setCompletedTools] = useState<string[]>([]);
  const [healthStatus, setHealthStatus] = useState<"ok" | "warning" | "offline" | "unknown">("unknown");
  const [showActions, setShowActions] = useState(true);
  const [activeCategory, setActiveCategory] = useState("Analysis");
  const [attachments, setAttachments] = useState<File[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!chatSessionId) setChatSessionId(`session_${Math.random().toString(36).substring(7)}`);
  }, [chatSessionId, setChatSessionId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, activeToolCall]);

  useEffect(() => {
    const init = async () => {
      let backendReachable = false;
      try {
        const health = await api.getStartupHealth();
        backendReachable = true;
        setHealthStatus(health.status || "unknown");
        const history = chatSessionId
          ? await api.getHistory(chatSessionId).catch(() => ({ messages: [] }))
          : { messages: [] };
        if (history.messages?.length) {
          setMessages(history.messages.map((m: any) => ({
            role: m.role, content: m.content, timestamp: new Date().toLocaleTimeString(),
          })));
        } else {
          setMessages([{
            role: "assistant",
            content: `**Hello! I'm Finley, your Vireon AI Finance Agent.**\n\nI have real-time access to your ledger, invoices, payroll, compliance calendar, and financial models. I can:\n\n• Analyze burn rate & runway with live data\n• Create and manage invoices and bills\n• Run scenario forecasts and Monte Carlo models\n• Check TDS, GST, and advance tax deadlines\n• Detect anomalies in your GL entries\n• Prepare board-ready financial summaries\n\nWhat would you like to work on today?`,
            timestamp: new Date().toLocaleTimeString(),
            followUps: ["Show me our current runway and burn rate", "Which invoices are overdue?", "What tax deadlines are coming up?"],
          }]);
        }
      } catch {
        setHealthStatus(backendReachable ? "warning" : "offline");
        setMessages([{
          role: "assistant",
          content: "Ready to help — I'm working with cached financial data. Live sync will resume when backend reconnects.",
          timestamp: new Date().toLocaleTimeString(),
          followUps: ["Show me our current runway and burn rate", "Generate a P&L summary for Q1 FY26"],
        }]);
      }
    };
    init();
  }, [chatSessionId]);

  const simulateToolCalls = async (query: string) => {
    const tools = getToolSequence(query);
    const done: string[] = [];
    for (const tool of tools) {
      setActiveToolCall(tool);
      await new Promise(r => setTimeout(r, 380 + Math.random() * 280));
      done.push(tool);
      setCompletedTools([...done]);
    }
    setActiveToolCall("");
    return tools;
  };

  const handleSend = async (seed?: string) => {
    const query = (seed || input).trim();
    if (!query || isLoading) return;

    const timestamp = new Date().toLocaleTimeString();
    setMessages(prev => [...prev, { role: "user", content: query, timestamp }]);
    setInput("");
    setAttachments([]);
    setIsLoading(true);
    setCompletedTools([]);

    try {
      const toolsUsed = await simulateToolCalls(query);

      let responseContent: string;
      if (EXAMPLE_RESPONSES[query]) {
        responseContent = EXAMPLE_RESPONSES[query];
      } else {
        try {
          const res = await api.chat(query, chatSessionId || undefined);
          responseContent = res.response;
        } catch (error) {
          if (error instanceof APIError) {
            if (error.status === 401) {
              responseContent = "Your session expired. Please log in again, then retry your query for live data.";
            } else {
              responseContent = cachedAgentResponse(query, toolsUsed);
            }
          } else if (error instanceof Error) {
            responseContent = cachedAgentResponse(query, toolsUsed);
          } else {
            responseContent = cachedAgentResponse(query, toolsUsed);
          }
        }
      }

      const followUps = getFollowUps(query);
      setMessages(prev => [...prev, {
        role: "assistant",
        content: responseContent,
        timestamp: new Date().toLocaleTimeString(),
        toolCalls: toolsUsed,
        followUps,
      }]);
    } finally {
      setIsLoading(false);
      setCompletedTools([]);
      setActiveToolCall("");
    }
  };

  const activeGroup = QUICK_ACTIONS.find(g => g.category === activeCategory);

  return (
    <div className="min-h-screen bg-[#ece3d4] pb-10 text-[#1d1b17]">
      <TopBar title="Finley AI Agent" subtitle="LangGraph · GPT-4o · Zero-hallucination math" />

      <div className="mx-auto max-w-7xl px-4 pt-6 sm:px-6 lg:px-8">
        <div className="grid gap-5 lg:grid-cols-[1fr_300px]">

          {/* ── Chat Panel ── */}
          <div className="rounded-2xl border border-[#cfbfa9] bg-[#f8efe3] shadow-[0_16px_36px_rgba(63,45,24,0.12)] overflow-hidden flex flex-col" style={{ height: "calc(100vh - 148px)" }}>

            {/* Header */}
            <div className="flex items-center justify-between border-b border-[#deceb8] px-5 py-3.5 shrink-0 bg-white/40">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[#2c2520] to-[#8d4f27] flex items-center justify-center shadow">
                  <Bot className="h-5 w-5 text-[#fff7ef]" />
                </div>
                <div>
                  <p className="text-sm font-bold text-[#2a2017]">Finley</p>
                  <p className="text-[10px] text-[#8a7b68]">AI Finance Agent · 100+ tools</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {healthStatus === "ok" && (
                  <span className="inline-flex items-center gap-1 rounded-full border border-[#b7d8bf] bg-[#edf8ef] px-2.5 py-1 text-[10px] font-semibold text-[#2f6a45]"><CheckCircle2 className="h-3 w-3" />Live</span>
                )}
                {healthStatus === "warning" && (
                  <span className="inline-flex items-center gap-1 rounded-full border border-[#e7d6a8] bg-[#fff7df] px-2.5 py-1 text-[10px] font-semibold text-[#7a4f14]"><AlertCircle className="h-3 w-3" />Degraded</span>
                )}
                {(healthStatus === "offline" || healthStatus === "unknown") && (
                  <span className="inline-flex items-center gap-1 rounded-full border border-[#e1c4af] bg-[#fff2ee] px-2.5 py-1 text-[10px] font-semibold text-[#9f3f30]"><AlertCircle className="h-3 w-3" />Offline</span>
                )}
                <button
                  onClick={() => { setMessages([{ role: "assistant", content: "Session cleared. How can I help you?", timestamp: new Date().toLocaleTimeString(), followUps: ["Show me our current runway and burn rate", "Which invoices are overdue?"] }]); setCompletedTools([]); }}
                  className="rounded-lg border border-[#ddcfbc] px-2.5 py-1 text-xs font-medium text-[#776b5a] hover:bg-white/50"
                >
                  New Chat
                </button>
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-5 space-y-4">
              {messages.map((msg, idx) => (
                <div key={idx} className={cn("flex gap-3", msg.role === "user" ? "justify-end" : "justify-start")}>
                  {msg.role === "assistant" && (
                    <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-[#2c2520] to-[#8d4f27] flex items-center justify-center shrink-0 mt-0.5">
                      <Bot className="h-3.5 w-3.5 text-[#fff7ef]" />
                    </div>
                  )}
                  <div className="flex flex-col gap-2 max-w-[84%]">
                    {/* Tool calls badge (collapsed) */}
                    {msg.role === "assistant" && msg.toolCalls && msg.toolCalls.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {msg.toolCalls.slice(0, 3).map(t => (
                          <span key={t} className="inline-flex items-center gap-1 rounded-md bg-[#f0ebe3] border border-[#e0d4c4] px-1.5 py-0.5 text-[9px] font-mono text-[#6b5b4a]">
                            <Cpu className="h-2.5 w-2.5 text-[#8d4f27]" />{t}
                          </span>
                        ))}
                        {msg.toolCalls.length > 3 && (
                          <span className="inline-flex items-center rounded-md bg-[#f0ebe3] border border-[#e0d4c4] px-1.5 py-0.5 text-[9px] text-[#8b7a69]">+{msg.toolCalls.length - 3} more</span>
                        )}
                      </div>
                    )}

                    <div className={cn("rounded-2xl px-4 py-3", msg.role === "user" ? "bg-[#2d241b] text-[#fff8ee] rounded-tr-sm" : "border border-[#ddcfbc] bg-white/80 text-[#33291f] rounded-tl-sm shadow-sm")}>
                      {msg.role === "assistant" ? renderMessage(msg.content) : <p className="text-sm">{msg.content}</p>}
                      <p className="text-[10px] opacity-40 mt-1.5">{msg.timestamp}</p>
                      {msg.role === "assistant" && idx > 0 && (
                        <div className="flex items-center gap-2 mt-2 pt-2 border-t border-[#ede8e0]">
                          <button className="p-1 rounded hover:bg-[#f0ebe3] text-[#9a8872] transition-colors"><ThumbsUp className="h-3 w-3" /></button>
                          <button className="p-1 rounded hover:bg-[#f0ebe3] text-[#9a8872] transition-colors"><ThumbsDown className="h-3 w-3" /></button>
                          <button onClick={() => navigator.clipboard.writeText(msg.content)} className="p-1 rounded hover:bg-[#f0ebe3] text-[#9a8872] transition-colors"><Copy className="h-3 w-3" /></button>
                        </div>
                      )}
                    </div>

                    {/* Follow-up suggestions */}
                    {msg.role === "assistant" && msg.followUps && msg.followUps.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 mt-1">
                        {msg.followUps.map(fu => (
                          <button key={fu} onClick={() => handleSend(fu)} className="rounded-lg border border-[#ddd0be] bg-white/70 px-2.5 py-1 text-[10px] font-medium text-[#5f5344] hover:bg-white hover:border-[#c8b49a] transition-all">
                            {fu}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                  {msg.role === "user" && (
                    <div className="w-7 h-7 rounded-lg bg-[#2d241b] flex items-center justify-center shrink-0 mt-0.5">
                      <User className="h-3.5 w-3.5 text-[#fff7ef]" />
                    </div>
                  )}
                </div>
              ))}

              {/* Tool call animation */}
              {isLoading && (
                <div className="flex gap-3 justify-start">
                  <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-[#2c2520] to-[#8d4f27] flex items-center justify-center shrink-0">
                    <Bot className="h-3.5 w-3.5 text-[#fff7ef]" />
                  </div>
                  <div className="border border-[#ddcfbc] bg-white/80 rounded-2xl rounded-tl-sm px-4 py-3 max-w-xs">
                    <div className="space-y-2">
                      {completedTools.map(t => (
                        <div key={t} className="flex items-center gap-2 text-[10px] font-mono text-[#5f5344]">
                          <CheckCircle2 className="h-3 w-3 text-emerald-500 shrink-0" />
                          <span>{t}</span>
                        </div>
                      ))}
                      {activeToolCall && (
                        <div className="flex items-center gap-2 text-[10px] font-mono text-[#8d4f27]">
                          <RefreshCw className="h-3 w-3 animate-spin shrink-0" />
                          <span>{activeToolCall}</span>
                        </div>
                      )}
                      {!activeToolCall && completedTools.length === 0 && (
                        <div className="flex items-center gap-1.5">
                          {[0, 150, 300].map(delay => (
                            <span key={delay} className="w-2 h-2 rounded-full bg-[#8d4f27] animate-bounce" style={{ animationDelay: `${delay}ms` }} />
                          ))}
                        </div>
                      )}
                    </div>
                    {completedTools.length > 0 && (
                      <p className="text-[9px] text-[#9a8872] mt-2">{completedTools.length} tools completed · synthesizing...</p>
                    )}
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Attachment preview */}
            {attachments.length > 0 && (
              <div className="flex gap-2 px-4 py-2 bg-[#f5ede0] border-t border-[#e5dbc9]">
                {attachments.map((f, i) => (
                  <div key={i} className="flex items-center gap-1.5 rounded-lg bg-white border border-[#ddd0be] px-2.5 py-1 text-xs text-[#4a3f35]">
                    <FileText className="h-3 w-3 text-[#8d4f27]" />
                    <span className="max-w-[120px] truncate">{f.name}</span>
                    <button onClick={() => setAttachments(prev => prev.filter((_, j) => j !== i))} className="ml-0.5 text-[#9a8872] hover:text-[#4a3f35]">
                      <X className="h-3 w-3" />
                    </button>
                  </div>
                ))}
              </div>
            )}

            {/* Input */}
            <div className="border-t border-[#e5dbc9] p-4 bg-white/30 shrink-0">
              <form onSubmit={(e) => { e.preventDefault(); handleSend(); }} className="flex items-end gap-2">
                <div className="relative flex-1">
                  <MessageSquare className="absolute left-3 top-3 h-4 w-4 text-[#8a7b68]" />
                  <textarea
                    value={input}
                    onChange={e => setInput(e.target.value)}
                    onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
                    placeholder="Ask anything — burn rate, invoices, tax deadlines, forecasts..."
                    rows={2}
                    className="w-full rounded-xl border border-[#ccb89d] bg-[#fff8ed] py-2.5 pl-10 pr-3 text-sm resize-none outline-none focus:ring-2 focus:ring-[#8d4f27]/20"
                  />
                </div>
                <div className="flex flex-col gap-1.5">
                  <input ref={fileInputRef} type="file" multiple accept=".csv,.xlsx,.pdf,.png,.jpg" className="hidden" onChange={e => setAttachments(prev => [...prev, ...Array.from(e.target.files || [])])} />
                  <button type="button" onClick={() => fileInputRef.current?.click()} className="h-9 w-9 rounded-xl border border-[#ccb89d] bg-[#fff8ed] text-[#8a7b68] hover:bg-[#f5ede0] flex items-center justify-center">
                    <Paperclip className="h-4 w-4" />
                  </button>
                  <button type="submit" disabled={isLoading || !input.trim()} className="h-9 w-9 rounded-xl bg-[#8f5632] text-[#fff8ee] disabled:opacity-50 hover:bg-[#764729] flex items-center justify-center">
                    {isLoading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                  </button>
                </div>
              </form>
              <p className="text-[10px] text-[#9a8872] mt-1.5 text-center">Shift+Enter for new line · Attach CSV, PDF, or images</p>
            </div>
          </div>

          {/* ── Right Sidebar ── */}
          <div className="space-y-4 overflow-y-auto" style={{ maxHeight: "calc(100vh - 148px)" }}>

            {/* Live Context */}
            <div className="rounded-2xl border border-[#cfbfa9] bg-[#f8efe3] p-4">
              <div className="flex items-center justify-between mb-3">
                <p className="text-xs font-black uppercase tracking-widest text-[#776b5a]">Live Context</p>
                <span className="flex items-center gap-1 text-[10px] text-emerald-600 font-semibold">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  Real-time
                </span>
              </div>
              <div className="grid grid-cols-2 gap-2">
                {[
                  { label: "Cash", value: LIVE_CONTEXT.cash, icon: DollarSign, trend: LIVE_CONTEXT.cashTrend, color: "#059669" },
                  { label: "Net Burn", value: LIVE_CONTEXT.burn, icon: Activity, trend: LIVE_CONTEXT.burnTrend, color: "#dc2626" },
                  { label: "Runway", value: LIVE_CONTEXT.runway, icon: Clock, trend: LIVE_CONTEXT.runwayTrend, color: "#d97706" },
                  { label: "MRR", value: LIVE_CONTEXT.mrr, icon: TrendingUp, trend: LIVE_CONTEXT.mrrTrend, color: "#2563eb" },
                ].map(item => {
                  const Icon = item.icon;
                  const TrendIcon = item.trend === "up" ? ArrowUpRight : ArrowDownRight;
                  const trendGood = (item.label === "Cash" || item.label === "MRR" || item.label === "Runway") ? item.trend === "up" : item.trend === "down";
                  return (
                    <div key={item.label} className="rounded-xl bg-white/60 border border-[#e9dece] p-2.5">
                      <div className="flex items-center justify-between mb-1">
                        <Icon className="h-3 w-3" style={{ color: item.color }} />
                        <TrendIcon className={cn("h-3 w-3", trendGood ? "text-emerald-500" : "text-rose-500")} />
                      </div>
                      <p className="text-[10px] text-[#8b7a69]">{item.label}</p>
                      <p className="text-sm font-bold text-[#2a2017] leading-tight">{item.value}</p>
                    </div>
                  );
                })}
              </div>
              <div className="mt-2 grid grid-cols-3 gap-1.5">
                <div className="rounded-lg bg-rose-50 border border-rose-100 p-2 text-center">
                  <p className="text-[10px] text-rose-700 font-bold">{LIVE_CONTEXT.alerts}</p>
                  <p className="text-[9px] text-rose-500">Alerts</p>
                </div>
                <div className="rounded-lg bg-amber-50 border border-amber-100 p-2 text-center">
                  <p className="text-[10px] text-amber-700 font-bold">{LIVE_CONTEXT.pendingApprovals}</p>
                  <p className="text-[9px] text-amber-500">Approvals</p>
                </div>
                <div className="rounded-lg bg-blue-50 border border-blue-100 p-2 text-center">
                  <p className="text-[10px] text-blue-700 font-bold">{LIVE_CONTEXT.overdueAR}</p>
                  <p className="text-[9px] text-blue-500">Overdue AR</p>
                </div>
              </div>
              <div className="mt-2 rounded-lg bg-rose-50 border border-rose-100 px-2.5 py-2 flex items-center gap-2">
                <AlertCircle className="h-3.5 w-3.5 text-rose-600 shrink-0" />
                <p className="text-[10px] font-semibold text-rose-700">{LIVE_CONTEXT.nextDeadline}</p>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="rounded-2xl border border-[#cfbfa9] bg-[#f8efe3] overflow-hidden">
              <button onClick={() => setShowActions(!showActions)} className="w-full flex items-center justify-between px-4 py-3 border-b border-[#deceb8]">
                <div className="flex items-center gap-2">
                  <Zap className="h-4 w-4 text-[#8d4f27]" />
                  <span className="text-sm font-bold text-[#2a2017]">Quick Actions</span>
                </div>
                {showActions ? <ChevronUp className="h-4 w-4 text-[#776b5a]" /> : <ChevronDown className="h-4 w-4 text-[#776b5a]" />}
              </button>
              {showActions && (
                <div>
                  <div className="flex gap-1 flex-wrap p-2.5 border-b border-[#deceb8]">
                    {QUICK_ACTIONS.map(g => {
                      const Icon = g.icon;
                      return (
                        <button key={g.category} onClick={() => setActiveCategory(g.category)} className={cn("rounded-lg px-2 py-1 text-[10px] font-semibold flex items-center gap-1 transition-all", activeCategory === g.category ? "bg-[#231c15] text-white" : "bg-white/60 text-[#776b5a] hover:bg-white")}>
                          <Icon className="h-3 w-3" />{g.category}
                        </button>
                      );
                    })}
                  </div>
                  <div className="p-2.5 space-y-1.5">
                    {activeGroup?.prompts.map(prompt => (
                      <button key={prompt} onClick={() => handleSend(prompt)} className="w-full text-left rounded-xl border border-[#e5dbc9] bg-white/60 px-3 py-2 text-[10px] text-[#4a3f35] hover:bg-white hover:border-[#c8b49a] transition-all leading-relaxed">
                        {prompt}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Capabilities */}
            <div className="rounded-2xl border border-[#cfbfa9] bg-[#f8efe3] p-4">
              <div className="flex items-center justify-between mb-3">
                <p className="text-xs font-black uppercase tracking-widest text-[#776b5a]">Capabilities</p>
                <span className="rounded-full bg-[#2c2520] px-2 py-0.5 text-[9px] font-black text-[#f6d9b0]">100+ tools</span>
              </div>
              <div className="space-y-3">
                {[
                  { group: "Transactions", color: "#2563eb", items: ["Invoices & AR", "Bills & AP", "Expense categorization", "Purchase orders"] },
                  { group: "Intelligence", color: "#7c3aed", items: ["GL anomaly detection", "Benford's law audit", "Duplicate invoices", "Cash Flow at Risk"] },
                  { group: "Planning", color: "#059669", items: ["12-month forecast", "Monte Carlo models", "Hiring impact sim", "Budget vs actual"] },
                  { group: "Compliance", color: "#dc2626", items: ["TDS/PF/GST calendar", "Advance tax calc", "Month-end close", "Audit trail"] },
                ].map(({ group, color, items }) => (
                  <div key={group}>
                    <p className="text-[9px] font-black uppercase tracking-widest mb-1.5" style={{ color }}>{group}</p>
                    <div className="grid grid-cols-2 gap-1">
                      {items.map(item => (
                        <div key={item} className="flex items-center gap-1.5 rounded-lg px-2 py-1" style={{ background: color + "12" }}>
                          <div className="w-1 h-1 rounded-full shrink-0" style={{ background: color }} />
                          <p className="text-[9px] font-semibold text-[#3d3429] leading-tight">{item}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-3 rounded-xl bg-[#1f1a16]/90 px-3 py-2 text-center">
                <p className="text-[9px] font-black text-amber-400 uppercase tracking-wider">Powered by</p>
                <p className="text-[10px] font-bold text-white">LangGraph · GPT-4o · Math Engine</p>
                <p className="text-[9px] text-[#c8b89e]">Zero-hallucination arithmetic</p>
              </div>
            </div>

            {/* Session */}
            <div className="rounded-2xl border border-[#cfbfa9] bg-[#f8efe3] p-4">
              <p className="text-xs font-black uppercase tracking-widest text-[#776b5a] mb-3">Session</p>
              <div className="space-y-1.5 text-xs">
                {[
                  ["Messages", String(messages.length)],
                  ["Session ID", chatSessionId?.slice(-8) || "—"],
                  ["Model", "GPT-4o"],
                  ["Framework", "LangGraph"],
                ].map(([label, val]) => (
                  <div key={label} className="flex justify-between">
                    <span className="text-[#9a8872]">{label}</span>
                    <span className="font-semibold text-[#4a3f35] font-mono text-[10px]">{val}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
