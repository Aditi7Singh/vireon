"use client";

import { useState, useEffect } from "react";
import TopBar from "@/components/TopBar";
import { useAppStore } from "@/lib/store";
import { cn, formatCurrency } from "@/lib/utils";
import { BarChart3, Download, Sparkles } from "lucide-react";
import api from "@/lib/api";
import {
  BarChart, Bar, AreaChart, Area, PieChart, Pie, Cell,
  XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
  Legend, ReferenceLine,
} from "recharts";

type ReportType = "income" | "balance" | "cashflow" | "indas";
type Period = "mtd" | "q1" | "q2" | "ytd" | "annual";

const INR = (n: number, decimals = 2) =>
  n >= 10_000_000 ? `₹${(n / 10_000_000).toFixed(decimals)}Cr`
  : n >= 100_000   ? `₹${(n / 100_000).toFixed(decimals)}L`
  : `₹${n.toLocaleString("en-IN")}`;

// ─── IndAS / India statutory data ─────────────────────────────────────────────
const INDAS_BALANCE_SHEET = {
  non_current_assets: {
    "Property, Plant & Equipment (Net)"    : { current: 10_230_000, prior: 12_180_000 },
    "Right-of-Use Assets (IndAS 116)"      : { current:  6_480_000, prior:  7_200_000 },
    "Intangible Assets"                    : { current:  5_600_000, prior:  6_760_000 },
    "Deferred Tax Assets (IndAS 12)"       : { current:  1_480_000, prior:  1_152_000 },
    "Other Non-Current Assets"             : { current:  2_310_000, prior:  2_310_000 },
  },
  current_assets: {
    "Cash & Cash Equivalents"              : { current: 23_380_000, prior: 15_810_000 },
    "Bank Balances (FDs)"                  : { current: 41_200_000, prior: 20_600_000 },
    "Trade Receivables"                    : { current:  2_345_000, prior:  1_794_000 },
    "GST Input Tax Credit Receivable"      : { current:  1_242_000, prior:    824_000 },
    "Advance Tax & TDS Receivable"         : { current:  2_108_000, prior:  1_342_000 },
    "Prepaid Expenses & Other CA"          : { current:    345_000, prior:    312_000 },
  },
  equity: {
    "Share Capital"                        : { current: 24_520_000, prior: 16_280_000 },
    "Securities Premium"                   : { current: 51_840_000, prior: 29_840_000 },
    "Retained Earnings"                    : { current:  4_721_000, prior:  1_653_000 },
  },
  non_current_liabilities: {
    "Lease Liabilities — Long-term (116)"  : { current:  4_860_000, prior:  5_400_000 },
    "Deferred Tax Liability (IndAS 12)"    : { current:    148_000, prior:    115_200 },
  },
  current_liabilities: {
    "Trade Payables"                       : { current:    533_000, prior:    427_000 },
    "GST Payable (Output – ITC)"           : { current:  1_384_000, prior:    984_000 },
    "TDS Payable"                          : { current:    138_100, prior:    112_000 },
    "PF / PT Payable"                      : { current:    574_700, prior:    480_000 },
    "Advance Tax Payable"                  : { current:    920_000, prior:    640_000 },
    "Deferred Revenue (Contract Liab.)"    : { current:  1_746_000, prior:  1_382_000 },
    "Lease Liabilities — Current (116)"    : { current:    720_000, prior:    720_000 },
    "Other Current Liabilities"            : { current:    312_000, prior:    241_000 },
  },
};

const SEGMENT_REPORT = [
  { segment: "Sprout (Gangavathi)",  revenue: 62_000_000, ebitda: 14_880_000, pat: 11_160_000, assets: 21_400_000, headcount: 5 },
  { segment: "Orchard (Bengaluru)", revenue: 78_000_000, ebitda: 20_280_000, pat: 15_210_000, assets: 28_600_000, headcount: 6 },
  { segment: "AI Lab (Remote)",     revenue: 16_800_000, ebitda:  2_520_000, pat:  1_890_000, assets: 11_800_000, headcount: 4 },
  { segment: "Shared / Corporate",  revenue:         0,  ebitda: -9_680_000, pat: -7_260_000, assets: 34_122_000, headcount: 3 },
];

const RELATED_PARTY = [
  { party: "Aditi Singh (Director)", relation: "Key Mgmt Personnel", nature: "Director Remuneration", amount: 5_040_000, balance: 0 },
  { party: "Ravi Kumar (CFO)",       relation: "Key Mgmt Personnel", nature: "Director Remuneration", amount: 3_360_000, balance: 0 },
  { party: "Seeding Lab Trust",      relation: "Promoter Entity",     nature: "Equity Contribution",   amount: 12_000_000, balance: 0 },
];

const INDAS_NOTES = [
  { std: "IndAS 115", title: "Revenue Recognition",      note: "SaaS subscription revenue recognised on a straight-line basis over contract term. Implementation fees recognised at point-of-delivery. No variable consideration components." },
  { std: "IndAS 116", title: "Leases",                   note: "Bengaluru office lease (5-yr) recognised as ROU asset ₹6.48L and lease liability ₹5.58L. Short-term leases < 12 months expensed as incurred." },
  { std: "IndAS 12",  title: "Income Taxes",             note: "Current tax at 25% (Sec 115BAA). DTA of ₹14.8L on timing differences. MAT credit not applicable — company is profitable." },
  { std: "IndAS 38",  title: "Intangible Assets",        note: "Internally developed software capitalised at ₹5.6L (net) amortised over 3 years. AI model weights assessed as internally generated — expensed." },
  { std: "IndAS 108", title: "Segment Reporting",        note: "Three operating segments reported: Sprout, Orchard, AI Lab. Shared/Corporate costs allocated pro-rata to revenue. CFO is chief operating decision maker." },
  { std: "IndAS 24",  title: "Related Party Disclosures",note: "Transactions with KMP at arm's-length. No inter-company loans. No guarantees given to related parties." },
];

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

function SectionTable({ title, rows, isExpense = false }: { title: string; rows: Record<string, { current: number; prior: number }>; isExpense?: boolean }) {
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
  const [liveKpis, setLiveKpis] = useState<{
    revenue?: number; grossMargin?: number; ebitda?: number; netIncome?: number;
    totalAssets?: number; totalEquity?: number; netCashChange?: number;
  }>({});

  useEffect(() => {
    async function loadLiveData() {
      try {
        const health = await api.getStartupHealth();
        const cid = health.default_company_id;
        if (!cid) return;
        const now = new Date();
        const yearStart = `${now.getFullYear()}-01-01`;
        const today = now.toISOString().slice(0, 10);
        const [incomeRes, balanceRes, cashRes] = await Promise.allSettled([
          api.getIncomeStatement(cid, yearStart, today),
          api.getBalanceSheet(cid, today),
          api.getCashFlowStatement(cid, yearStart, today),
        ]);
        const kpis: typeof liveKpis = {};
        if (incomeRes.status === "fulfilled") {
          kpis.revenue = incomeRes.value.revenue.total;
          kpis.grossMargin = incomeRes.value.gross_margin_pct;
          kpis.ebitda = incomeRes.value.ebitda;
          kpis.netIncome = incomeRes.value.net_income;
        }
        if (balanceRes.status === "fulfilled") {
          kpis.totalAssets = balanceRes.value.assets.total;
          kpis.totalEquity = balanceRes.value.equity.total;
        }
        if (cashRes.status === "fulfilled") {
          kpis.netCashChange = cashRes.value.summary.net_change;
        }
        if (Object.keys(kpis).length > 0) setLiveKpis(kpis);
      } catch {
        // fall back to hardcoded data
      }
    }
    loadLiveData();
  }, []);

  const fallbackRevenue = Object.values(INCOME_STMT.revenue).reduce((s, r) => s + r.current, 0);
  const fallbackCOGS = Object.values(INCOME_STMT.cogs).reduce((s, r) => s + r.current, 0);
  const fallbackGrossProfit = fallbackRevenue - fallbackCOGS;
  const fallbackOpex = Object.values(INCOME_STMT.opex).reduce((s, r) => s + r.current, 0);

  const totalRevenue = liveKpis.revenue ?? fallbackRevenue;
  const totalCOGS = fallbackCOGS;
  const grossProfit = liveKpis.revenue != null ? totalRevenue - totalCOGS : fallbackGrossProfit;
  const grossMargin = liveKpis.grossMargin ?? (grossProfit / totalRevenue) * 100;
  const totalOpex = fallbackOpex;
  const ebitda = liveKpis.ebitda ?? (grossProfit - totalOpex);
  const netIncome = liveKpis.netIncome ?? CASH_FLOW.operating["Net Income"].current;

  const totalCurrentAssets = Object.values(BALANCE_SHEET.current_assets).reduce((s, r) => s + r.current, 0);
  const totalNonCurrentAssets = Object.values(BALANCE_SHEET.non_current_assets).reduce((s, r) => s + r.current, 0);
  const totalAssets = liveKpis.totalAssets ?? (totalCurrentAssets + totalNonCurrentAssets);
  const totalCurrentLiab = Object.values(BALANCE_SHEET.current_liabilities).reduce((s, r) => s + r.current, 0);
  const totalNonCurrentLiab = Object.values(BALANCE_SHEET.non_current_liabilities).reduce((s, r) => s + r.current, 0);
  const totalEquity = liveKpis.totalEquity ?? Object.values(BALANCE_SHEET.equity).reduce((s, r) => s + r.current, 0);

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
              {([["income", "Income Statement"], ["balance", "Balance Sheet"], ["cashflow", "Cash Flow"], ["indas", "IndAS / India"]] as const).map(([key, label]) => (
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
              {report === "income" ? "Vireon Seeding Lab Pvt. Ltd. — Income Statement" : report === "balance" ? "Vireon Seeding Lab Pvt. Ltd. — Balance Sheet" : "Vireon Seeding Lab Pvt. Ltd. — Cash Flow Statement"}
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

          {report === "indas" && (
            <div>
              {/* Schedule III Balance Sheet — IndAS format */}
              <div className="bg-[#f5f0ea] px-5 py-2 border-y border-[#ede8e0] flex items-center justify-between">
                <span className="text-xs font-black uppercase tracking-widest text-[#5f5344]">Schedule III Balance Sheet (IndAS) — ₹ Figures</span>
                <span className="text-[10px] font-bold text-[#8a7968]">Companies Act 2013 · As at Mar 31, 2026</span>
              </div>

              {[
                { title: "Non-Current Assets", rows: INDAS_BALANCE_SHEET.non_current_assets },
                { title: "Current Assets", rows: INDAS_BALANCE_SHEET.current_assets },
              ].map(({ title, rows }) => (
                <div key={title} className="mb-1">
                  <div className="bg-[#f9f5ef] px-5 py-1.5 border-b border-[#ede8e0]">
                    <span className="text-[11px] font-black text-[#7a6a56] uppercase tracking-wider">{title}</span>
                  </div>
                  {Object.entries(rows).map(([name, vals]) => (
                    <div key={name} className="flex items-center justify-between px-5 py-2.5 border-b border-[#f5f0ea] hover:bg-[#faf7f3]">
                      <span className="text-sm text-[#4a3f35] pl-4">{name}</span>
                      <div className="flex items-center gap-8">
                        <span className="text-sm text-[#776b5a] w-32 text-right">{INR(vals.prior)}</span>
                        <span className="text-sm font-semibold text-[#2a2017] w-32 text-right">{INR(vals.current)}</span>
                      </div>
                    </div>
                  ))}
                  <div className="flex items-center justify-between px-5 py-2.5 bg-[#f9f6f1] border-b border-[#ddd2c2]">
                    <span className="text-sm font-bold text-[#2a2017] pl-2">Total {title}</span>
                    <div className="flex gap-8">
                      <span className="text-sm font-semibold text-[#776b5a] w-32 text-right">{INR(Object.values(rows).reduce((s, r) => s + r.prior, 0))}</span>
                      <span className="text-sm font-bold text-[#2a2017] w-32 text-right">{INR(Object.values(rows).reduce((s, r) => s + r.current, 0))}</span>
                    </div>
                  </div>
                </div>
              ))}

              {[
                { title: "Equity", rows: INDAS_BALANCE_SHEET.equity },
                { title: "Non-Current Liabilities", rows: INDAS_BALANCE_SHEET.non_current_liabilities },
                { title: "Current Liabilities", rows: INDAS_BALANCE_SHEET.current_liabilities },
              ].map(({ title, rows }) => (
                <div key={title} className="mb-1">
                  <div className="bg-[#f9f5ef] px-5 py-1.5 border-b border-[#ede8e0]">
                    <span className="text-[11px] font-black text-[#7a6a56] uppercase tracking-wider">{title}</span>
                  </div>
                  {Object.entries(rows).map(([name, vals]) => (
                    <div key={name} className="flex items-center justify-between px-5 py-2.5 border-b border-[#f5f0ea] hover:bg-[#faf7f3]">
                      <span className="text-sm text-[#4a3f35] pl-4">{name}</span>
                      <div className="flex items-center gap-8">
                        <span className="text-sm text-[#776b5a] w-32 text-right">{INR(vals.prior)}</span>
                        <span className="text-sm font-semibold text-[#2a2017] w-32 text-right">{INR(vals.current)}</span>
                      </div>
                    </div>
                  ))}
                  <div className="flex items-center justify-between px-5 py-2.5 bg-[#f9f6f1] border-b border-[#ddd2c2]">
                    <span className="text-sm font-bold text-[#2a2017] pl-2">Total {title}</span>
                    <div className="flex gap-8">
                      <span className="text-sm font-semibold text-[#776b5a] w-32 text-right">{INR(Object.values(rows).reduce((s, r) => s + r.prior, 0))}</span>
                      <span className="text-sm font-bold text-[#2a2017] w-32 text-right">{INR(Object.values(rows).reduce((s, r) => s + r.current, 0))}</span>
                    </div>
                  </div>
                </div>
              ))}

              {/* Segment Report (IndAS 108) */}
              <div className="bg-[#f5f0ea] px-5 py-2 border-y border-[#ede8e0] mt-2">
                <span className="text-xs font-black uppercase tracking-widest text-[#5f5344]">Segment Report — IndAS 108 · FY 2025-26</span>
              </div>
              <table className="w-full text-xs border-b border-[#ddd2c2]">
                <thead className="bg-[#faf5ef]">
                  <tr>
                    {["Segment", "Revenue", "EBITDA", "EBITDA %", "PAT", "Total Assets", "Headcount"].map((h) => (
                      <th key={h} className="px-4 py-2.5 text-left text-[10px] font-black uppercase tracking-widest text-[#9e8e7a]">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {SEGMENT_REPORT.map((seg) => (
                    <tr key={seg.segment} className="border-t border-[#f5ede4] hover:bg-[#fdf8f2]">
                      <td className="px-4 py-2.5 font-semibold text-[#1d1b19]">{seg.segment}</td>
                      <td className="px-4 py-2.5 text-[#6a6054]">{INR(seg.revenue)}</td>
                      <td className={`px-4 py-2.5 font-bold ${seg.ebitda >= 0 ? "text-emerald-700" : "text-red-600"}`}>{INR(seg.ebitda)}</td>
                      <td className="px-4 py-2.5 text-[#6a6054]">{seg.revenue > 0 ? `${((seg.ebitda / seg.revenue) * 100).toFixed(1)}%` : "—"}</td>
                      <td className={`px-4 py-2.5 font-bold ${seg.pat >= 0 ? "text-emerald-700" : "text-red-600"}`}>{INR(seg.pat)}</td>
                      <td className="px-4 py-2.5 text-[#6a6054]">{INR(seg.assets)}</td>
                      <td className="px-4 py-2.5 text-[#6a6054]">{seg.headcount}</td>
                    </tr>
                  ))}
                  <tr className="border-t-2 border-[#ddd2c2] bg-[#f9f6f1] font-black">
                    <td className="px-4 py-2.5 text-[#2a2017]">Total</td>
                    <td className="px-4 py-2.5 text-[#2a2017]">{INR(SEGMENT_REPORT.reduce((s, r) => s + r.revenue, 0))}</td>
                    <td className="px-4 py-2.5 text-emerald-700">{INR(SEGMENT_REPORT.reduce((s, r) => s + r.ebitda, 0))}</td>
                    <td className="px-4 py-2.5 text-[#6a6054]">—</td>
                    <td className="px-4 py-2.5 text-emerald-700">{INR(SEGMENT_REPORT.reduce((s, r) => s + r.pat, 0))}</td>
                    <td className="px-4 py-2.5 text-[#2a2017]">{INR(SEGMENT_REPORT.reduce((s, r) => s + r.assets, 0))}</td>
                    <td className="px-4 py-2.5 text-[#2a2017]">{SEGMENT_REPORT.reduce((s, r) => s + r.headcount, 0)}</td>
                  </tr>
                </tbody>
              </table>

              {/* Related Party Disclosures (IndAS 24) */}
              <div className="bg-[#f5f0ea] px-5 py-2 border-y border-[#ede8e0] mt-2">
                <span className="text-xs font-black uppercase tracking-widest text-[#5f5344]">Related Party Transactions — IndAS 24</span>
              </div>
              <table className="w-full text-xs border-b border-[#ddd2c2]">
                <thead className="bg-[#faf5ef]">
                  <tr>
                    {["Related Party", "Relationship", "Nature of Transaction", "Amount (FY26)", "Closing Balance"].map((h) => (
                      <th key={h} className="px-4 py-2.5 text-left text-[10px] font-black uppercase tracking-widest text-[#9e8e7a]">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {RELATED_PARTY.map((r) => (
                    <tr key={r.party} className="border-t border-[#f5ede4] hover:bg-[#fdf8f2]">
                      <td className="px-4 py-3 font-semibold text-[#1d1b19]">{r.party}</td>
                      <td className="px-4 py-3 text-[#6a6054]">{r.relation}</td>
                      <td className="px-4 py-3 text-[#6a6054]">{r.nature}</td>
                      <td className="px-4 py-3 font-bold text-[#1d1b19]">{INR(r.amount)}</td>
                      <td className="px-4 py-3 text-[#9e8e7a]">{r.balance === 0 ? "Nil" : INR(r.balance)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {/* IndAS Notes */}
              <div className="bg-[#f5f0ea] px-5 py-2 border-y border-[#ede8e0] mt-2">
                <span className="text-xs font-black uppercase tracking-widest text-[#5f5344]">Significant Accounting Policies & Notes</span>
              </div>
              <div className="grid grid-cols-2 gap-0">
                {INDAS_NOTES.map((n, i) => (
                  <div key={n.std} className={`px-5 py-3 border-b border-[#f5ede4] ${i % 2 === 0 ? "border-r border-r-[#ede8e0]" : ""} hover:bg-[#faf7f3]`}>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-[10px] font-black bg-[#1d1b19] text-white px-2 py-0.5 rounded-md">{n.std}</span>
                      <span className="text-xs font-bold text-[#2a2017]">{n.title}</span>
                    </div>
                    <p className="text-[11px] text-[#6a6054] leading-relaxed">{n.note}</p>
                  </div>
                ))}
              </div>

              <div className="flex items-center justify-between px-5 py-4 bg-[#231c15]">
                <span className="text-sm font-black text-white pl-2">Vireon Seeding Lab Pvt. Ltd. · CIN: U72900KA2022PTC123456</span>
                <span className="text-xs text-[#b8a898]">Prepared per IndAS · Companies Act 2013 · ICAI Standards</span>
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
