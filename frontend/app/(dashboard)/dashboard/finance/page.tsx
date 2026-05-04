"use client";

import { useEffect, useMemo, useState } from "react";
import { useFinancialData } from "@/hooks/useFinancialData";
import api, { API_V1_BASE, FinancialRecommendationsResponse } from "@/lib/api";
import TopBar from "@/components/TopBar";
import { useAppStore } from "@/lib/store";
import {
  TrendingUp, TrendingDown, AlertCircle, Sparkles,
  Clock, ArrowUpRight, ArrowDownRight, Bot,
  RefreshCw, DollarSign, Activity, Target,
} from "lucide-react";
import {
  AreaChart, Area, BarChart, Bar, ComposedChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from "recharts";

const API_V1 = API_V1_BASE;

const fmt = (v: number) => {
  const abs = Math.abs(v);
  const sign = v < 0 ? "-" : "";
  if (abs >= 10_000_000) return `${sign}₹${(abs / 10_000_000).toFixed(1)}Cr`;
  if (abs >= 100_000)    return `${sign}₹${(abs / 100_000).toFixed(1)}L`;
  if (abs >= 1_000)      return `${sign}₹${(abs / 1_000).toFixed(1)}K`;
  return `${sign}₹${abs.toFixed(0)}`;
};

const FALLBACK_TREND = [
  { month: "Nov", revenue: 920000, burn: 1050000, cash: 4800000, gm: 58 },
  { month: "Dec", revenue: 1020000, burn: 1100000, cash: 4200000, gm: 61 },
  { month: "Jan", revenue: 1180000, burn: 1080000, cash: 3800000, gm: 63 },
  { month: "Feb", revenue: 1240000, burn: 1150000, cash: 3300000, gm: 64 },
  { month: "Mar", revenue: 1320000, burn: 1210000, cash: 2900000, gm: 65 },
  { month: "Apr", revenue: 1480000, burn: 1240000, cash: 2640000, gm: 67 },
];

const EXPENSE_MIX = [
  { name: "Engineering", value: 580000, color: "#3b82f6" },
  { name: "Infrastructure", value: 180000, color: "#8b5cf6" },
  { name: "Marketing", value: 140000, color: "#f59e0b" },
  { name: "Operations", value: 120000, color: "#10b981" },
  { name: "G&A", value: 100000, color: "#6366f1" },
  { name: "Other", value: 120000, color: "#94a3b8" },
];

const PENDING_ITEMS = [
  { category: "Vendor Bills", count: 3, amount: 284000, urgency: "high" },
  { category: "Expense Claims", count: 7, amount: 45600, urgency: "medium" },
  { category: "Journal Entries", count: 2, amount: 0, urgency: "low" },
  { category: "Bank Reconciliation", count: 12, amount: 0, urgency: "medium" },
];

const AR_AGING = [
  { bucket: "0–30 days", amount: 487000, count: 3, color: "#10b981" },
  { bucket: "31–60 days", amount: 72000, count: 1, color: "#f59e0b" },
  { bucket: "61–90 days", amount: 0, count: 0, color: "#f97316" },
  { bucket: "90+ days", amount: 0, count: 0, color: "#ef4444" },
];

const CUSTOM_TOOLTIP = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white border border-[#e3d6c7] rounded-xl p-3 shadow-xl text-xs min-w-[150px]">
      <p className="font-black text-[#1f1a16] mb-2">{label}</p>
      {payload.map((p: any, i: number) => (
        <div key={i} className="flex items-center justify-between gap-3 py-0.5">
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full" style={{ background: p.color }} />
            <span className="text-[#776b5a]">{p.name}</span>
          </div>
          <span className="font-bold text-[#2a2017]">{typeof p.value === "number" && p.value > 100 ? fmt(p.value) : p.value + (p.name === "GM %" ? "%" : "")}</span>
        </div>
      ))}
    </div>
  );
};

export default function FinanceDashboardPage() {
  const { openChat } = useAppStore();
  const [month, setMonth] = useState(new Date().toISOString().slice(0, 7));
  const [companyId, setCompanyId] = useState<string>("");
  const [trendSeries, setTrendSeries] = useState(FALLBACK_TREND);
  const [reconciliation, setReconciliation] = useState({ netBurn: 1240000, expenseTotal: 1180000, variance: 60000 });
  const [financialRecs, setFinancialRecs] = useState<FinancialRecommendationsResponse | null>(null);
  const [pendingReview, setPendingReview] = useState<Record<string, any[]>>({});

  const { data, isLoading } = useFinancialData(companyId, month);

  useEffect(() => {
    api.getStartupHealth().then(h => setCompanyId(h.default_company_id || "")).catch(() => {});
  }, []);

  useEffect(() => {
    if (!companyId) return;
    Promise.all([
      fetch(`${API_V1}/metrics/history/${companyId}?months=6`).then(r => r.ok ? r.json() : []).catch(() => []),
      fetch(`${API_V1}/burn/summary/${companyId}?month=${month}`).then(r => r.ok ? r.json() : {}).catch(() => ({})),
      fetch(`${API_V1}/burn/expenses/${companyId}?month=${month}`).then(r => r.ok ? r.json() : {}).catch(() => ({})),
      fetch(`${API_V1}/inputs/pending-review?company_id=${companyId}`, { headers: { "X-User-Role": "finance" } }).then(r => r.ok ? r.json() : {}).catch(() => ({})),
    ]).then(([history, burn, expenses, pending]: any[]) => {
      if (history.length > 0) {
        setTrendSeries(history.map((h: any) => ({
          month: h.month,
          revenue: Number(h.revenue || 0),
          burn: Number(h.net_burn || h.burn || 0),
          cash: Number(h.cash || 0),
          gm: Number(h.gross_margin_pct || 60),
        })));
        const latest = history[history.length - 1];
        if (latest) setMonth(latest.month);
      }
      const techTotal = Number(expenses.tech_costs?.aws_total || 0) + Number(expenses.tech_costs?.licenses_total || 0) + Number(expenses.tech_costs?.saas_total || 0);
      const nonTechTotal = Number(expenses.non_tech_costs?.marketing || 0) + Number(expenses.non_tech_costs?.office_bengaluru || 0) + Number(expenses.non_tech_costs?.misc || 0);
      const expenseTotal = techTotal + nonTechTotal;
      const netBurn = Number(burn.net_burn || 1240000);
      setReconciliation({ netBurn, expenseTotal: expenseTotal || 1180000, variance: netBurn - (expenseTotal || 1180000) });
      setPendingReview(pending.pending_review || {});
    });
  }, [companyId, month]);

  useEffect(() => {
    if (!companyId) return;
    Promise.all([api.getScorecard(), api.getRevenue(), api.getCashBalance(), api.getRunway()])
      .then(([scorecard, revenue, cashBalance, runway]) =>
        api.getFinancialRecommendations({
          company_id: companyId, company_stage: "growth",
          financial_metrics: {
            revenue: scorecard.monthly_revenue || revenue.mrr, net_income: scorecard.monthly_revenue - scorecard.monthly_net_burn,
            gross_margin: 65, current_ratio: cashBalance.net_cash > 0 ? 1.5 : 0.9,
            debt_to_equity: 0.8, cash_conversion_cycle: 45,
            monthly_burn: scorecard.monthly_net_burn, cash_balance: cashBalance.cash, runway_months: runway.runway_months,
          },
        })
      )
      .then(setFinancialRecs)
      .catch(() => setFinancialRecs(null));
  }, [companyId]);

  const rows = useMemo(() => {
    const summary = data?.dashboard?.summary;
    if (!summary?.breakdown_by_category) return [];
    return Object.entries(summary.breakdown_by_category).map(([category, amount]) => ({
      category, amount: Number(amount),
    }));
  }, [data, month]);

  const totalBurn = reconciliation.netBurn;
  const totalRevenue = trendSeries[trendSeries.length - 1]?.revenue || 1480000;
  const cashBalance = trendSeries[trendSeries.length - 1]?.cash || 2640000;
  const grossMargin = trendSeries[trendSeries.length - 1]?.gm || 65;
  const netBurnChange = trendSeries.length >= 2
    ? ((trendSeries[trendSeries.length - 1].burn - trendSeries[trendSeries.length - 2].burn) / trendSeries[trendSeries.length - 2].burn * 100)
    : 4.2;

  const expenseBreakdown = rows.length > 0
    ? rows.map((r, i) => ({ name: r.category.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase()), value: r.amount, color: EXPENSE_MIX[i % EXPENSE_MIX.length].color }))
    : EXPENSE_MIX;

  const totalPendingCount = Object.values(pendingReview).reduce((s, arr) => s + (arr?.length || 0), 0);

  async function exportLedgerCsv() {
    if (!companyId) return;
    const res = await fetch(`${API_V1}/reports/export/ledger/csv?company_id=${companyId}`);
    if (!res.ok) return;
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url; a.download = `ledger-${month}.csv`; document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
  }
  async function exportSummaryPdf() {
    if (!companyId) return;
    const res = await fetch(`${API_V1}/reports/export/summary/pdf?company_id=${companyId}`);
    if (!res.ok) return;
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url; a.download = `summary-${month}.pdf`; document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
  }

  return (
    <div className="min-h-screen bg-[#f6f3ee] text-[#1d1b19]">
      <TopBar title="Finance Control" />

      <div className="max-w-[1600px] mx-auto p-6 space-y-6">

        {/* Header */}
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-[#2c2520] to-[#8d4f27] flex items-center justify-center">
                <Bot className="h-3.5 w-3.5 text-[#fff7ef]" />
              </div>
              <h1 className="text-2xl font-black text-[#1d1b19]">Finance Control · Finley CFO</h1>
            </div>
            <p className="text-[#6f655a] text-sm">Detailed ledger analysis & CFO intelligence · {month}</p>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            <input type="month" value={month} onChange={e => setMonth(e.target.value)}
              className="bg-white border border-[#e1d3c2] rounded-xl px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-[#bf7a49]" />
            <button onClick={() => openChat("Give me a full CFO briefing with P&L, cash position, and top action items")}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-[#f0e4d0] text-[#6b3a1e] text-sm font-semibold hover:bg-[#e8d5bb] border border-[#d9c29a] transition">
              <Sparkles className="w-4 h-4" /> Ask Finley
            </button>
            <button onClick={exportLedgerCsv} className="px-4 py-2 rounded-xl bg-[#9a5d34] hover:bg-[#7f4c2a] text-white text-sm font-semibold">CSV</button>
            <button onClick={exportSummaryPdf} className="px-4 py-2 rounded-xl bg-[#1f1a16] hover:bg-[#151210] text-white text-sm font-semibold">PDF</button>
          </div>
        </div>

        {/* Pending Alert */}
        {(totalPendingCount > 0 || PENDING_ITEMS.some(p => p.urgency === "high")) && (
          <div className="rounded-2xl border border-amber-200 bg-amber-50 px-5 py-3 flex items-center gap-3">
            <AlertCircle className="h-4 w-4 text-amber-600 shrink-0" />
            <p className="text-sm text-amber-800 font-semibold">
              {PENDING_ITEMS.filter(p => p.urgency === "high").length} urgent items need your attention —{" "}
              {PENDING_ITEMS.filter(p => p.urgency === "high").map(p => `${p.count} ${p.category}`).join(", ")}
            </p>
            <button onClick={() => openChat("What items are pending my approval? Summarize and prioritize.")} className="ml-auto text-xs font-bold text-amber-700 border border-amber-300 px-3 py-1.5 rounded-lg hover:bg-amber-100 shrink-0 transition">
              Review with Finley →
            </button>
          </div>
        )}

        {/* KPI Row */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
          {[
            { label: "Net Burn", value: fmt(totalBurn), sub: `${netBurnChange > 0 ? "+" : ""}${netBurnChange.toFixed(1)}% MoM`, trend: netBurnChange < 0 ? "good" : "bad", icon: TrendingDown },
            { label: "Revenue", value: fmt(totalRevenue), sub: "+12.1% MoM", trend: "good", icon: TrendingUp },
            { label: "Cash Balance", value: fmt(cashBalance), sub: "Available", trend: "ok", icon: DollarSign },
            { label: "Gross Margin", value: `${grossMargin.toFixed(1)}%`, sub: "+2.1pp MoM", trend: "good", icon: Activity },
            { label: "Burn Multiple", value: `${(totalBurn / Math.max(totalRevenue, 1)).toFixed(2)}×`, sub: "Target: <1.5×", trend: (totalBurn / Math.max(totalRevenue, 1)) < 1.5 ? "good" : "bad", icon: Target },
            { label: "Pending Items", value: String(totalPendingCount || PENDING_ITEMS.reduce((s, p) => s + p.count, 0)), sub: "Awaiting action", trend: "bad", icon: Clock },
          ].map((kpi) => {
            const Icon = kpi.icon;
            const tColor = kpi.trend === "good" ? "text-emerald-600" : kpi.trend === "bad" ? "text-red-500" : "text-amber-600";
            const tArrow = kpi.trend === "good" ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />;
            return (
              <div key={kpi.label} className="rounded-2xl border border-[#e4d8cb] bg-white p-4">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-[9px] font-black uppercase tracking-wider text-[#9a8872]">{kpi.label}</p>
                  <Icon className="h-3.5 w-3.5 text-[#9a8872]" />
                </div>
                <p className="text-xl font-black text-[#1d1b19]">{kpi.value}</p>
                <p className={`text-[10px] mt-1 font-semibold flex items-center gap-0.5 ${tColor}`}>{tArrow}{kpi.sub}</p>
              </div>
            );
          })}
        </div>

        {/* Main Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          {/* Revenue vs Burn Trend */}
          <div className="lg:col-span-2 rounded-2xl border border-[#e4d8cb] bg-white p-5">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-sm font-black text-[#2a231d]">Revenue vs Burn — 6 Month P&L View</h2>
                <p className="text-xs text-[#9a8872] mt-0.5">Monthly financials with gross margin overlay</p>
              </div>
            </div>
            <ResponsiveContainer width="100%" height={270}>
              <ComposedChart data={trendSeries} margin={{ top: 5, right: 5, left: 0, bottom: 5 }}>
                <defs>
                  <linearGradient id="revGrad2" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0.03} />
                  </linearGradient>
                  <linearGradient id="burnGrad2" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0.02} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0e8de" vertical={false} />
                <XAxis dataKey="month" tick={{ fontSize: 11, fill: "#776b5a" }} axisLine={false} tickLine={false} />
                <YAxis yAxisId="left" tick={{ fontSize: 11, fill: "#776b5a" }} axisLine={false} tickLine={false} tickFormatter={fmt} width={55} />
                <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 10, fill: "#9a8872" }} axisLine={false} tickLine={false} tickFormatter={v => `${v}%`} domain={[0, 100]} width={35} />
                <Tooltip content={<CUSTOM_TOOLTIP />} />
                <Legend wrapperStyle={{ fontSize: 11, paddingTop: 8 }} />
                <Area yAxisId="left" type="monotone" dataKey="revenue" name="Revenue" stroke="#10b981" strokeWidth={2.5} fill="url(#revGrad2)" dot={{ r: 3, fill: "#10b981" }} />
                <Area yAxisId="left" type="monotone" dataKey="burn" name="Net Burn" stroke="#ef4444" strokeWidth={2} fill="url(#burnGrad2)" dot={false} strokeDasharray="4 3" />
                <Line yAxisId="right" type="monotone" dataKey="gm" name="GM %" stroke="#8b5cf6" strokeWidth={2} dot={{ r: 3, fill: "#8b5cf6" }} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>

          {/* Expense Mix Donut */}
          <div className="rounded-2xl border border-[#e4d8cb] bg-white p-5">
            <h2 className="text-sm font-black text-[#2a231d] mb-1">Cost Mix</h2>
            <p className="text-xs text-[#9a8872] mb-3">{month} · Total {fmt(totalBurn)}</p>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie data={expenseBreakdown} cx="50%" cy="50%" innerRadius={52} outerRadius={78} paddingAngle={3} dataKey="value">
                  {expenseBreakdown.map((_e, i) => (
                    <Cell key={i} fill={EXPENSE_MIX[i % EXPENSE_MIX.length].color} />
                  ))}
                </Pie>
                <Tooltip formatter={(v: number) => [fmt(v), ""]} contentStyle={{ borderRadius: 10, fontSize: 11 }} />
              </PieChart>
            </ResponsiveContainer>
            <div className="mt-2 space-y-1.5">
              {expenseBreakdown.slice(0, 4).map((item, i) => (
                <div key={i} className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    <div className="w-2 h-2 rounded-full" style={{ background: EXPENSE_MIX[i % EXPENSE_MIX.length].color }} />
                    <span className="text-[10px] text-[#776b5a]">{item.name}</span>
                  </div>
                  <span className="text-[10px] font-bold text-[#2a2017]">{fmt(item.value)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Middle Row: Cash Trend + AR Aging + Pending */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          {/* Cash Position Trend */}
          <div className="rounded-2xl border border-[#e4d8cb] bg-white p-5">
            <h2 className="text-sm font-black text-[#2a231d] mb-4">Cash Position Trend</h2>
            <ResponsiveContainer width="100%" height={160}>
              <AreaChart data={trendSeries} margin={{ top: 5, right: 5, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="cashGrad2" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.03} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="month" tick={{ fontSize: 10, fill: "#776b5a" }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 10, fill: "#776b5a" }} axisLine={false} tickLine={false} tickFormatter={fmt} width={45} />
                <Tooltip formatter={(v: number) => [fmt(v), "Cash"]} contentStyle={{ borderRadius: 10, fontSize: 11 }} />
                <Area type="monotone" dataKey="cash" stroke="#3b82f6" strokeWidth={2.5} fill="url(#cashGrad2)" dot={{ r: 3, fill: "#3b82f6" }} />
              </AreaChart>
            </ResponsiveContainer>
            <div className="mt-3 pt-3 border-t border-[#f0e8de] flex items-center justify-between text-xs">
              <span className="text-[#9a8872]">Runway at current burn</span>
              <span className="font-black text-[#2a2017]">{Math.round(cashBalance / totalBurn)} months</span>
            </div>
          </div>

          {/* AR Aging */}
          <div className="rounded-2xl border border-[#e4d8cb] bg-white p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-black text-[#2a231d]">AR Aging Summary</h2>
              <span className="text-xs text-emerald-700 font-bold bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full">
                {fmt(AR_AGING.reduce((s, b) => s + b.amount, 0))} total
              </span>
            </div>
            <div className="space-y-3">
              {AR_AGING.map((bucket) => {
                const totalAR = AR_AGING.reduce((s, b) => s + b.amount, 0) || 1;
                const pct = totalAR > 0 ? (bucket.amount / totalAR) * 100 : 0;
                return (
                  <div key={bucket.bucket}>
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full" style={{ background: bucket.color }} />
                        <span className="text-xs text-[#776b5a]">{bucket.bucket}</span>
                      </div>
                      <span className="text-xs font-bold text-[#2a2017]">{bucket.amount > 0 ? fmt(bucket.amount) : "—"}</span>
                    </div>
                    <div className="h-1.5 rounded-full bg-[#f0e8dc] overflow-hidden">
                      <div className="h-1.5 rounded-full transition-all duration-700" style={{ width: `${pct}%`, background: bucket.color }} />
                    </div>
                    <p className="text-[10px] text-[#9a8872] mt-0.5">{bucket.count} invoice{bucket.count !== 1 ? "s" : ""}</p>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Pending Approvals */}
          <div className="rounded-2xl border border-[#e4d8cb] bg-white p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-black text-[#2a231d]">Pending Approvals</h2>
              <span className="text-xs text-amber-700 font-bold bg-amber-50 border border-amber-200 px-2 py-0.5 rounded-full">
                {PENDING_ITEMS.reduce((s, p) => s + p.count, 0)} items
              </span>
            </div>
            <div className="space-y-2.5">
              {PENDING_ITEMS.map((item) => (
                <div key={item.category} className={`flex items-center gap-3 p-3 rounded-xl border ${item.urgency === "high" ? "border-red-200 bg-red-50" : item.urgency === "medium" ? "border-amber-200 bg-amber-50" : "border-[#ede8e0] bg-[#faf7f3]"}`}>
                  <div className={`w-2 h-2 rounded-full shrink-0 ${item.urgency === "high" ? "bg-red-500" : item.urgency === "medium" ? "bg-amber-500" : "bg-gray-400"}`} />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-semibold text-[#2a2017]">{item.category}</p>
                    {item.amount > 0 && <p className="text-[10px] text-[#9a8872]">{fmt(item.amount)}</p>}
                  </div>
                  <span className="text-xs font-black text-[#2a2017] shrink-0">{item.count}</span>
                </div>
              ))}
            </div>
            <button onClick={() => openChat("List all pending approval items and prioritize them for me")} className="mt-4 w-full rounded-xl bg-[#1f1a16] py-2 text-xs font-bold text-[#fff7eb] hover:bg-[#151210] flex items-center justify-center gap-2">
              <Sparkles className="h-3.5 w-3.5" /> Review All with Finley
            </button>
          </div>
        </div>

        {/* Expense Breakdown Bar Chart */}
        <div className="rounded-2xl border border-[#e4d8cb] bg-white p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-black text-[#2a231d]">Expense Breakdown by Category</h2>
              <p className="text-xs text-[#9a8872] mt-0.5">{month} · Reconciliation status: {Math.abs(reconciliation.variance) < 50000 ? "✓ Reconciled" : "⚠ Variance " + fmt(reconciliation.variance)}</p>
            </div>
            <div className="flex items-center gap-3 text-xs">
              <span className="text-[#9a8872]">Total Expenses: <strong className="text-[#2a2017]">{fmt(reconciliation.expenseTotal)}</strong></span>
              <span className="text-[#9a8872]">Net Burn: <strong className="text-[#2a2017]">{fmt(reconciliation.netBurn)}</strong></span>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={expenseBreakdown} margin={{ top: 5, right: 5, left: 0, bottom: 5 }} layout="vertical">
              <XAxis type="number" tick={{ fontSize: 10, fill: "#776b5a" }} axisLine={false} tickLine={false} tickFormatter={fmt} />
              <YAxis type="category" dataKey="name" tick={{ fontSize: 11, fill: "#776b5a" }} axisLine={false} tickLine={false} width={100} />
              <Tooltip formatter={(v: number) => [fmt(v), "Amount"]} contentStyle={{ borderRadius: 10, fontSize: 11 }} />
              <Bar dataKey="value" radius={[0, 6, 6, 0]}>
                {expenseBreakdown.map((_e, i) => (
                  <Cell key={i} fill={EXPENSE_MIX[i % EXPENSE_MIX.length].color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* AI Recommendations */}
        {financialRecs && financialRecs.recommendations && (
          <div className="rounded-2xl border border-[#e4d8cb] bg-white p-5">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-[#2c2520] to-[#8d4f27] flex items-center justify-center">
                <Sparkles className="w-3.5 h-3.5 text-white" />
              </div>
              <div>
                <h2 className="text-sm font-black text-[#2a231d]">Finley&apos;s CFO Recommendations</h2>
                <p className="text-xs text-[#9a8872]">AI-generated from your financial data</p>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {financialRecs.recommendations.slice(0, 3).map((item: any, idx: number) => (
                <div key={idx} className="rounded-xl border border-[#ede8e0] bg-[#faf7f3] p-4">
                  <p className="text-sm font-bold text-[#2a2017]">{String(item.title || item.area || `Recommendation ${idx + 1}`)}</p>
                  <p className="text-xs text-[#6f655a] mt-1.5 leading-relaxed">{String(item.rationale || item.finding || item.action || "Review required")}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {isLoading && (
          <div className="flex items-center justify-center gap-2 py-4 text-sm text-[#9a8872]">
            <RefreshCw className="h-4 w-4 animate-spin" /> Loading financial data…
          </div>
        )}
      </div>
    </div>
  );
}
