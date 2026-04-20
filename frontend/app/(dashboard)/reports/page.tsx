"use client";

import { useState } from "react";
import TopBar from "@/components/TopBar";
import { useAppStore } from "@/lib/store";
import { cn, formatCurrency } from "@/lib/utils";
import { BarChart3, Download, Sparkles } from "lucide-react";
import {
  BarChart, Bar, AreaChart, Area, PieChart, Pie, Cell,
  XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
  Legend, ReferenceLine,
} from "recharts";

type ReportType = "income" | "balance" | "cashflow";
type Period = "mtd" | "q1" | "q2" | "ytd" | "annual";

const INCOME_STMT = {
  revenue: {
    "SaaS Subscriptions": { current: 385000, prior: 312000 },
    "Professional Services": { current: 72000, prior: 58000 },
    "Implementation Fees": { current: 28000, prior: 22000 },
  },
  cogs: {
    "Hosting & Infrastructure": { current: 54200, prior: 41800 },
    "Support Staff": { current: 38000, prior: 31000 },
    "Third-Party APIs": { current: 12400, prior: 9600 },
  },
  opex: {
    "Salaries & Benefits": { current: 186000, prior: 154000 },
    "Sales & Marketing": { current: 68000, prior: 72000 },
    "General & Administrative": { current: 34000, prior: 28000 },
    "Research & Development": { current: 52000, prior: 43000 },
    "Legal & Compliance": { current: 22500, prior: 18000 },
    "Office & Facilities": { current: 14200, prior: 13800 },
  },
};

const BALANCE_SHEET = {
  current_assets: {
    "Cash & Cash Equivalents": { current: 2840000, prior: 1920000 },
    "Accounts Receivable": { current: 285000, prior: 218000 },
    "Prepaid Expenses": { current: 42000, prior: 38000 },
    "Short-term Investments": { current: 500000, prior: 250000 },
  },
  non_current_assets: {
    "Fixed Assets (Net)": { current: 124000, prior: 148000 },
    "Intangible Assets": { current: 68000, prior: 82000 },
    "Security Deposits": { current: 28000, prior: 28000 },
  },
  current_liabilities: {
    "Accounts Payable": { current: 64800, prior: 52000 },
    "Accrued Expenses": { current: 38000, prior: 29000 },
    "Deferred Revenue": { current: 212000, prior: 168000 },
    "Short-term Debt": { current: 0, prior: 200000 },
  },
  non_current_liabilities: {
    "Long-term Debt": { current: 0, prior: 0 },
    "Deferred Tax Liability": { current: 18000, prior: 14000 },
  },
  equity: {
    "Common Stock": { current: 2980000, prior: 1980000 },
    "Retained Earnings": { current: 574200, prior: 201000 },
  },
};

const CASH_FLOW = {
  operating: {
    "Net Income": { current: 373200, prior: 261000 },
    "Depreciation & Amortization": { current: 38000, prior: 32000 },
    "Changes in AR": { current: -67000, prior: -45000 },
    "Changes in AP": { current: 12800, prior: 8000 },
    "Changes in Deferred Revenue": { current: 44000, prior: 36000 },
  },
  investing: {
    "Capital Expenditures": { current: -14000, prior: -22000 },
    "Short-term Investment Purchases": { current: -250000, prior: -250000 },
    "Proceeds from Investment Maturities": { current: 0, prior: 100000 },
  },
  financing: {
    "Proceeds from Share Issuance": { current: 1000000, prior: 0 },
    "Debt Repayment": { current: -200000, prior: -50000 },
    "Stock Buybacks": { current: 0, prior: 0 },
  },
};

// ── 12-month trend data ────────────────────────────────────────────────────

const MONTHLY_PL = [
  { month: "May 25", revenue: 285000, cogs:  42000, opex: 218000, netIncome:  25000, cashPosition: 1420000 },
  { month: "Jun 25", revenue: 308000, cogs:  44800, opex: 221000, netIncome:  42200, cashPosition: 1462000 },
  { month: "Jul 25", revenue: 334000, cogs:  47600, opex: 224000, netIncome:  62400, cashPosition: 1524000 },
  { month: "Aug 25", revenue: 362000, cogs:  50400, opex: 228000, netIncome:  83600, cashPosition: 1608000 },
  { month: "Sep 25", revenue: 392000, cogs:  53800, opex: 232000, netIncome: 106200, cashPosition: 1714000 },
  { month: "Oct 25", revenue: 426000, cogs:  57400, opex: 237000, netIncome: 131600, cashPosition: 1846000 },
  { month: "Nov 25", revenue: 468000, cogs:  62000, opex: 243000, netIncome: 163000, cashPosition: 2009000 },
  { month: "Dec 25", revenue: 516000, cogs:  68000, opex: 251000, netIncome: 197000, cashPosition: 2206000 },
  { month: "Jan 26", revenue: 556000, cogs:  72800, opex: 257000, netIncome: 226200, cashPosition: 2432000 },
  { month: "Feb 26", revenue: 596000, cogs:  77400, opex: 263000, netIncome: 255600, cashPosition: 2688000 },
  { month: "Mar 26", revenue: 644000, cogs:  83200, opex: 271000, netIncome: 289800, cashPosition: 2978000 },
  { month: "Apr 26", revenue: 693000, cogs:  89000, opex: 279000, netIncome: 325000, cashPosition: 3303000 },
];

const OPEX_MIX = [
  { name: "Salaries & Benefits", value: 186000, pct: 50.3, color: "#8d4f27" },
  { name: "Research & Development", value: 52000, pct: 14.1, color: "#2563eb" },
  { name: "Sales & Marketing", value: 68000, pct: 18.4, color: "#059669" },
  { name: "G&A", value: 34000, pct: 9.2, color: "#d97706" },
  { name: "Legal & Compliance", value: 22500, pct: 6.1, color: "#7c3aed" },
  { name: "Office & Facilities", value: 14200, pct: 3.8, color: "#6b7280" },
];

const REVENUE_MIX = [
  { name: "SaaS Subscriptions", value: 385000, pct: 79.4, color: "#8d4f27" },
  { name: "Professional Services", value: 72000, pct: 14.8, color: "#2563eb" },
  { name: "Implementation Fees", value: 28000, pct: 5.8, color: "#059669" },
];

function pct(current: number, prior: number) {
  if (prior === 0) return null;
  return ((current - prior) / Math.abs(prior)) * 100;
}

function PctChange({ current, prior, inverse = false }: { current: number; prior: number; inverse?: boolean }) {
  const change = pct(current, prior);
  if (change === null) return null;
  const isGood = inverse ? change < 0 : change > 0;
  return (
    <span className={cn("text-xs font-semibold ml-2", isGood ? "text-emerald-600" : "text-red-600")}>
      {isGood ? "▲" : "▼"} {Math.abs(change).toFixed(1)}%
    </span>
  );
}

function SectionTable({ title, rows, isExpense = false, isTotal = false }: { title: string; rows: Record<string, { current: number; prior: number }>; isExpense?: boolean; isTotal?: boolean }) {
  const total = { current: Object.values(rows).reduce((s, r) => s + r.current, 0), prior: Object.values(rows).reduce((s, r) => s + r.prior, 0) };
  return (
    <div className="mb-2">
      <div className="bg-[#f5f0ea] px-5 py-2 border-y border-[#ede8e0]">
        <span className="text-xs font-black uppercase tracking-widest text-[#5f5344]">{title}</span>
      </div>
      {Object.entries(rows).map(([name, vals]) => (
        <div key={name} className="flex items-center justify-between px-5 py-2.5 border-b border-[#f5f0ea] hover:bg-[#faf7f3] transition-colors">
          <span className="text-sm text-[#4a3f35] pl-4">{name}</span>
          <div className="flex items-center gap-8">
            <span className="text-sm text-[#776b5a] w-28 text-right">{formatCurrency(vals.prior)}</span>
            <span className={cn("text-sm font-semibold w-28 text-right", isExpense ? "text-[#2a2017]" : "text-[#2a2017]")}>
              {formatCurrency(vals.current)}
              <PctChange current={vals.current} prior={vals.prior} inverse={isExpense} />
            </span>
          </div>
        </div>
      ))}
      <div className="flex items-center justify-between px-5 py-3 bg-[#f9f6f1] border-b border-[#ddd2c2]">
        <span className="text-sm font-bold text-[#2a2017] pl-2">Total {title}</span>
        <div className="flex items-center gap-8">
          <span className="text-sm font-semibold text-[#776b5a] w-28 text-right">{formatCurrency(total.prior)}</span>
          <span className="text-sm font-bold text-[#2a2017] w-28 text-right">{formatCurrency(total.current)}</span>
        </div>
      </div>
    </div>
  );
}

export default function ReportsPage() {
  const { openChat } = useAppStore();
  const [report, setReport] = useState<ReportType>("income");
  const [period, setPeriod] = useState<Period>("ytd");

  const totalRevenue = Object.values(INCOME_STMT.revenue).reduce((s, r) => s + r.current, 0);
  const totalCOGS = Object.values(INCOME_STMT.cogs).reduce((s, r) => s + r.current, 0);
  const grossProfit = totalRevenue - totalCOGS;
  const grossMargin = (grossProfit / totalRevenue) * 100;
  const totalOpex = Object.values(INCOME_STMT.opex).reduce((s, r) => s + r.current, 0);
  const ebitda = grossProfit - totalOpex;
  const netIncome = CASH_FLOW.operating["Net Income"].current;

  const totalCurrentAssets = Object.values(BALANCE_SHEET.current_assets).reduce((s, r) => s + r.current, 0);
  const totalNonCurrentAssets = Object.values(BALANCE_SHEET.non_current_assets).reduce((s, r) => s + r.current, 0);
  const totalAssets = totalCurrentAssets + totalNonCurrentAssets;
  const totalCurrentLiab = Object.values(BALANCE_SHEET.current_liabilities).reduce((s, r) => s + r.current, 0);
  const totalNonCurrentLiab = Object.values(BALANCE_SHEET.non_current_liabilities).reduce((s, r) => s + r.current, 0);
  const totalEquity = Object.values(BALANCE_SHEET.equity).reduce((s, r) => s + r.current, 0);

  const totalOpCF = Object.values(CASH_FLOW.operating).reduce((s, r) => s + r.current, 0);
  const totalInvCF = Object.values(CASH_FLOW.investing).reduce((s, r) => s + r.current, 0);
  const totalFinCF = Object.values(CASH_FLOW.financing).reduce((s, r) => s + r.current, 0);

  return (
    <div className="min-h-screen bg-[#f6f3ee] pb-14 text-[#1d1b17]">
      <TopBar title="Financial Reports" />

      <div className="mx-auto max-w-7xl space-y-6 px-4 pt-6 sm:px-6 lg:px-8">

        <section className="rounded-3xl border border-[#d9cdbc] bg-[linear-gradient(145deg,#fff8ec_0%,#f3eadb_100%)] p-6 shadow-[0_18px_48px_rgba(63,45,24,0.1)] sm:p-8">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <p className="inline-flex items-center gap-2 rounded-full border border-[#d9c29a] bg-[#fff4dd] px-3 py-1 text-xs font-semibold text-[#8c5c19]">
                <BarChart3 className="h-3.5 w-3.5" /> GAAP Financial Statements
              </p>
              <h1 className="mt-2 text-2xl font-bold text-[#2c2013]">Financial Reports</h1>
              <p className="mt-1 text-sm text-[#5f5344]">Income Statement · Balance Sheet · Cash Flow Statement</p>
            </div>
            <div className="flex items-center gap-3">
              <button onClick={() => openChat("Analyze our financial statements and identify areas of concern")} className="inline-flex items-center gap-2 rounded-xl border border-[#d9c29a] bg-white/80 px-4 py-2.5 text-sm font-medium text-[#6b4c1e] hover:bg-white">
                <Sparkles className="h-4 w-4" /> AI Commentary
              </button>
              <button className="inline-flex items-center gap-2 rounded-xl bg-[#231c15] px-4 py-2.5 text-sm font-medium text-[#fff7eb] hover:bg-[#17120d]">
                <Download className="h-4 w-4" /> Export PDF
              </button>
            </div>
          </div>
        </section>

        {/* KPI Summary */}
        {report === "income" && (
          <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[
              { label: "Total Revenue", value: formatCurrency(totalRevenue), change: "+23.4%", positive: true },
              { label: "Gross Margin", value: `${grossMargin.toFixed(1)}%`, change: "+2.1pp", positive: true },
              { label: "EBITDA", value: formatCurrency(ebitda), change: ebitda > 0 ? "Profitable" : "Loss", positive: ebitda > 0 },
              { label: "Net Income", value: formatCurrency(netIncome), change: "+43.0%", positive: true },
            ].map(s => (
              <article key={s.label} className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] p-5">
                <p className="text-xs uppercase tracking-[0.12em] text-[#776b5a]">{s.label}</p>
                <p className="mt-2 text-2xl font-bold text-[#2a2017]">{s.value}</p>
                <p className={cn("mt-1 text-xs font-semibold", s.positive ? "text-emerald-600" : "text-red-600")}>{s.change}</p>
              </article>
            ))}
          </section>
        )}

        {/* Visual Charts — Income View */}
        {report === "income" && (
          <section className="grid gap-4 lg:grid-cols-3">

            {/* Revenue vs Expenses 12-month trend */}
            <article className="lg:col-span-2 rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] p-5">
              <div className="flex items-center justify-between mb-1">
                <h3 className="text-sm font-bold text-[#2a2017]">Revenue · COGS · Net Income — 12-Month Trend</h3>
                <span className="text-xs text-emerald-600 font-semibold">+143% Net Income YoY</span>
              </div>
              <p className="text-xs text-[#776b5a] mb-3">Monthly actuals May 2025 – Apr 2026. Reference at break-even.</p>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={MONTHLY_PL} margin={{ top: 8, right: 16, left: 4, bottom: 0 }} barCategoryGap="28%">
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0ebe3" vertical={false} />
                    <XAxis dataKey="month" tick={{ fill: "#7b6d5b", fontSize: 10 }} tickLine={false} axisLine={false} />
                    <YAxis tick={{ fill: "#7b6d5b", fontSize: 10 }} tickLine={false} axisLine={false}
                      tickFormatter={v => `$${(v / 1000).toFixed(0)}k`} width={44} />
                    <Tooltip
                      contentStyle={{ borderRadius: 10, border: "1px solid #e0cfc2", background: "#fffbf5", fontSize: 12 }}
                      formatter={(v: number, name: string) => [formatCurrency(v), ({ revenue: "Revenue", cogs: "COGS", netIncome: "Net Income" } as Record<string,string>)[name] ?? name]}
                    />
                    <Legend wrapperStyle={{ fontSize: 11, paddingTop: 6 }}
                      formatter={(v: string) => ({ revenue: "Revenue", cogs: "COGS", netIncome: "Net Income" } as Record<string,string>)[v] ?? v} />
                    <ReferenceLine y={0} stroke="#e0cfc2" strokeWidth={1} />
                    <Bar dataKey="revenue" name="revenue" fill="#8d4f27" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="cogs" name="cogs" fill="#d4b896" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="netIncome" name="netIncome" fill="#059669" radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </article>

            {/* OpEx mix donut */}
            <article className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] p-5">
              <h3 className="text-sm font-bold text-[#2a2017] mb-1">OpEx Mix (YTD 2026)</h3>
              <p className="text-xs text-[#776b5a] mb-3">Total OpEx: {formatCurrency(OPEX_MIX.reduce((s, i) => s + i.value, 0))}</p>
              <div className="h-44">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={OPEX_MIX} cx="50%" cy="50%" innerRadius={48} outerRadius={72}
                      dataKey="value" nameKey="name" paddingAngle={2}>
                      {OPEX_MIX.map((entry) => <Cell key={entry.name} fill={entry.color} />)}
                    </Pie>
                    <Tooltip
                      contentStyle={{ borderRadius: 10, border: "1px solid #e0cfc2", background: "#fffbf5", fontSize: 12 }}
                      formatter={(v: number, name: string) => [formatCurrency(v), name]}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="space-y-1.5 mt-2">
                {OPEX_MIX.map(item => (
                  <div key={item.name} className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-1.5">
                      <div className="h-2 w-2 rounded-full shrink-0" style={{ background: item.color }} />
                      <span className="text-[#5f5344]">{item.name}</span>
                    </div>
                    <span className="font-semibold text-[#2a2017]">{item.pct}%</span>
                  </div>
                ))}
              </div>
            </article>

            {/* Cash position + gross margin trend */}
            <article className="lg:col-span-2 rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] p-5">
              <div className="flex items-center justify-between mb-1">
                <h3 className="text-sm font-bold text-[#2a2017]">Cash Position Trajectory</h3>
                <span className="text-xs text-emerald-600 font-semibold">$3.3M ending cash · +133% YoY</span>
              </div>
              <p className="text-xs text-[#776b5a] mb-3">Cumulative cash balance month-end. Dashed line at Series A close ($2M raise).</p>
              <div className="h-56">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={MONTHLY_PL} margin={{ top: 8, right: 16, left: 4, bottom: 0 }}>
                    <defs>
                      <linearGradient id="cashGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#2563eb" stopOpacity={0.18} />
                        <stop offset="95%" stopColor="#2563eb" stopOpacity={0.01} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0ebe3" vertical={false} />
                    <XAxis dataKey="month" tick={{ fill: "#7b6d5b", fontSize: 10 }} tickLine={false} axisLine={false} />
                    <YAxis tick={{ fill: "#7b6d5b", fontSize: 10 }} tickLine={false} axisLine={false}
                      tickFormatter={v => `$${(v / 1000000).toFixed(1)}M`} width={44} />
                    <Tooltip
                      contentStyle={{ borderRadius: 10, border: "1px solid #e0cfc2", background: "#fffbf5", fontSize: 12 }}
                      formatter={(v: number) => [formatCurrency(v), "Cash Position"]}
                    />
                    <ReferenceLine y={2000000} stroke="#8d4f27" strokeDasharray="6 4" strokeWidth={1.2}
                      label={{ value: "Series A close", position: "insideTopLeft", fontSize: 10, fill: "#8d4f27" }} />
                    <Area type="monotone" dataKey="cashPosition" name="cashPosition"
                      stroke="#2563eb" strokeWidth={2.4} fill="url(#cashGrad)" dot={false} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </article>

            {/* Revenue mix donut */}
            <article className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] p-5">
              <h3 className="text-sm font-bold text-[#2a2017] mb-1">Revenue Mix (YTD 2026)</h3>
              <p className="text-xs text-[#776b5a] mb-3">Total: {formatCurrency(REVENUE_MIX.reduce((s, i) => s + i.value, 0))}</p>
              <div className="h-44">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={REVENUE_MIX} cx="50%" cy="50%" innerRadius={48} outerRadius={72}
                      dataKey="value" nameKey="name" paddingAngle={2}>
                      {REVENUE_MIX.map((entry) => <Cell key={entry.name} fill={entry.color} />)}
                    </Pie>
                    <Tooltip
                      contentStyle={{ borderRadius: 10, border: "1px solid #e0cfc2", background: "#fffbf5", fontSize: 12 }}
                      formatter={(v: number, name: string) => [formatCurrency(v), name]}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="space-y-1.5 mt-2">
                {REVENUE_MIX.map(item => (
                  <div key={item.name} className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-1.5">
                      <div className="h-2 w-2 rounded-full shrink-0" style={{ background: item.color }} />
                      <span className="text-[#5f5344]">{item.name}</span>
                    </div>
                    <span className="font-semibold text-[#2a2017]">{item.pct}%</span>
                  </div>
                ))}
              </div>
            </article>

          </section>
        )}

        {/* Report Controls */}
        <section className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] overflow-hidden">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 p-5 border-b border-[#ede8e0]">
            <div className="flex gap-1 bg-[#f0ebe3] rounded-xl p-1">
              {([["income", "Income Statement"], ["balance", "Balance Sheet"], ["cashflow", "Cash Flow"]] as const).map(([key, label]) => (
                <button key={key} onClick={() => setReport(key)} className={cn("rounded-lg px-4 py-2 text-xs font-bold transition-all", report === key ? "bg-white text-[#2a2017] shadow-sm" : "text-[#776b5a] hover:text-[#2a2017]")}>
                  {label}
                </button>
              ))}
            </div>
            <div className="flex items-center gap-3">
              <select value={period} onChange={e => setPeriod(e.target.value as Period)} className="rounded-xl border border-[#ddd2c2] bg-[#f9f6f1] px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-[#9a5d34]/20">
                {[["mtd", "Month to Date"], ["q1", "Q1 2026"], ["q2", "Q2 2026"], ["ytd", "Year to Date"], ["annual", "FY 2025"]].map(([v, l]) => <option key={v} value={v}>{l}</option>)}
              </select>
            </div>
          </div>

          {/* Column Headers */}
          <div className="flex items-center justify-between px-5 py-3 border-b border-[#ddd2c2] bg-[#faf7f3]">
            <span className="text-sm font-bold text-[#2a2017]">
              {report === "income" ? "Orchard Analytics Inc. — Income Statement" : report === "balance" ? "Orchard Analytics Inc. — Balance Sheet" : "Orchard Analytics Inc. — Cash Flow Statement"}
            </span>
            <div className="flex items-center gap-8">
              <span className="text-xs font-bold text-[#776b5a] w-28 text-right">FY 2025</span>
              <span className="text-xs font-bold text-[#2a2017] w-28 text-right">YTD 2026</span>
            </div>
          </div>

          {report === "income" && (
            <div>
              <SectionTable title="Revenue" rows={INCOME_STMT.revenue} />
              <div className="flex items-center justify-between px-5 py-3 bg-emerald-50 border-b border-emerald-200">
                <span className="text-sm font-bold text-emerald-800 pl-2">Gross Profit</span>
                <div className="flex gap-8">
                  <span className="text-sm font-semibold text-emerald-700 w-28 text-right">{formatCurrency(Object.values(INCOME_STMT.revenue).reduce((s, r) => s + r.prior, 0) - Object.values(INCOME_STMT.cogs).reduce((s, r) => s + r.prior, 0))}</span>
                  <span className="text-sm font-bold text-emerald-800 w-28 text-right">{formatCurrency(grossProfit)}</span>
                </div>
              </div>
              <SectionTable title="Cost of Revenue (COGS)" rows={INCOME_STMT.cogs} isExpense />
              <SectionTable title="Operating Expenses" rows={INCOME_STMT.opex} isExpense />
              <div className="flex items-center justify-between px-5 py-3 bg-[#f0ebe3] border-b border-[#ddd2c2]">
                <span className="text-sm font-bold text-[#2a2017] pl-2">EBITDA</span>
                <div className="flex gap-8">
                  <span className="text-sm font-semibold text-[#776b5a] w-28 text-right">{formatCurrency(261000)}</span>
                  <span className={cn("text-sm font-bold w-28 text-right", ebitda > 0 ? "text-emerald-700" : "text-red-600")}>{formatCurrency(ebitda)}</span>
                </div>
              </div>
              <div className="flex items-center justify-between px-5 py-4 bg-[#231c15]">
                <span className="text-sm font-black text-white pl-2">Net Income</span>
                <div className="flex gap-8">
                  <span className="text-sm font-semibold text-[#b8a898] w-28 text-right">{formatCurrency(261000)}</span>
                  <span className={cn("text-sm font-black w-28 text-right", netIncome > 0 ? "text-emerald-400" : "text-red-400")}>{formatCurrency(netIncome)}</span>
                </div>
              </div>
            </div>
          )}

          {report === "balance" && (
            <div>
              <SectionTable title="Current Assets" rows={BALANCE_SHEET.current_assets} />
              <SectionTable title="Non-Current Assets" rows={BALANCE_SHEET.non_current_assets} />
              <div className="flex items-center justify-between px-5 py-3 bg-blue-50 border-b border-blue-200">
                <span className="text-sm font-bold text-blue-800 pl-2">Total Assets</span>
                <div className="flex gap-8">
                  <span className="text-sm font-semibold text-blue-700 w-28 text-right">{formatCurrency(Object.values({...BALANCE_SHEET.current_assets,...BALANCE_SHEET.non_current_assets}).reduce((s, r) => s + r.prior, 0))}</span>
                  <span className="text-sm font-bold text-blue-800 w-28 text-right">{formatCurrency(totalAssets)}</span>
                </div>
              </div>
              <SectionTable title="Current Liabilities" rows={BALANCE_SHEET.current_liabilities} isExpense />
              <SectionTable title="Non-Current Liabilities" rows={BALANCE_SHEET.non_current_liabilities} isExpense />
              <SectionTable title="Shareholders' Equity" rows={BALANCE_SHEET.equity} />
              <div className="flex items-center justify-between px-5 py-4 bg-[#231c15]">
                <span className="text-sm font-black text-white pl-2">Total Liabilities + Equity</span>
                <div className="flex gap-8">
                  <span className="text-sm font-semibold text-[#b8a898] w-28 text-right">{formatCurrency(totalCurrentLiab + totalNonCurrentLiab + totalEquity)}</span>
                  <span className="text-sm font-black text-emerald-400 w-28 text-right">{formatCurrency(totalCurrentLiab + totalNonCurrentLiab + totalEquity)}</span>
                </div>
              </div>
            </div>
          )}

          {report === "cashflow" && (
            <div>
              <SectionTable title="Operating Activities" rows={CASH_FLOW.operating} />
              <div className="flex items-center justify-between px-5 py-3 bg-blue-50 border-b border-blue-200">
                <span className="text-sm font-bold text-blue-800 pl-2">Net Cash from Operations</span>
                <div className="flex gap-8">
                  <span className="text-sm font-semibold text-blue-700 w-28 text-right">{formatCurrency(Object.values(CASH_FLOW.operating).reduce((s, r) => s + r.prior, 0))}</span>
                  <span className={cn("text-sm font-bold w-28 text-right", totalOpCF >= 0 ? "text-blue-800" : "text-red-700")}>{formatCurrency(totalOpCF)}</span>
                </div>
              </div>
              <SectionTable title="Investing Activities" rows={CASH_FLOW.investing} />
              <SectionTable title="Financing Activities" rows={CASH_FLOW.financing} />
              <div className="flex items-center justify-between px-5 py-4 bg-[#231c15]">
                <span className="text-sm font-black text-white pl-2">Net Change in Cash</span>
                <div className="flex gap-8">
                  <span className="text-sm font-semibold text-[#b8a898] w-28 text-right">{formatCurrency(Object.values({...CASH_FLOW.operating,...CASH_FLOW.investing,...CASH_FLOW.financing}).reduce((s, r) => s + r.prior, 0))}</span>
                  <span className={cn("text-sm font-black w-28 text-right", (totalOpCF + totalInvCF + totalFinCF) >= 0 ? "text-emerald-400" : "text-red-400")}>{formatCurrency(totalOpCF + totalInvCF + totalFinCF)}</span>
                </div>
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
