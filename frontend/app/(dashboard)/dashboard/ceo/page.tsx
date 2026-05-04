"use client";

import { useEffect, useState } from "react";
import { useFinancialData } from "@/hooks/useFinancialData";
import api, { API_V1_BASE } from "@/lib/api";
import TopBar from "@/components/TopBar";
import { useAppStore } from "@/lib/store";
import {
  TrendingDown, TrendingUp, AlertCircle, Users,
  DollarSign, Activity, ArrowUpRight, ArrowDownRight,
  RefreshCw, Sparkles, ChevronRight,
} from "lucide-react";
import {
  Area, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend, ComposedChart,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
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

const FALLBACK_HISTORY = [
  { month: "Nov", burn: 920000, cash: 4800000, revenue: 680000, headcount: 15 },
  { month: "Dec", burn: 980000, cash: 4200000, revenue: 780000, headcount: 16 },
  { month: "Jan", burn: 1050000, cash: 3800000, revenue: 920000, headcount: 17 },
  { month: "Feb", burn: 1120000, cash: 3300000, revenue: 1050000, headcount: 17 },
  { month: "Mar", burn: 1190000, cash: 2900000, revenue: 1180000, headcount: 18 },
  { month: "Apr", burn: 1240000, cash: 2640000, revenue: 1350000, headcount: 18 },
];

const COST_BREAKDOWN = [
  { name: "Engineering", value: 580000, color: "#3b82f6" },
  { name: "Infrastructure", value: 180000, color: "#8b5cf6" },
  { name: "Marketing", value: 140000, color: "#f59e0b" },
  { name: "Operations", value: 120000, color: "#10b981" },
  { name: "G&A", value: 100000, color: "#6366f1" },
  { name: "Other", value: 120000, color: "#94a3b8" },
];

const HEALTH_RADAR = [
  { metric: "Revenue Growth", value: 78 },
  { metric: "Gross Margin", value: 65 },
  { metric: "Burn Efficiency", value: 55 },
  { metric: "Cash Runway", value: 42 },
  { metric: "Team Velocity", value: 82 },
  { metric: "Customer NPS", value: 71 },
];

const CUSTOM_TOOLTIP = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white border border-[#e3d6c7] rounded-xl p-3 shadow-xl text-xs min-w-[140px]">
      <p className="font-black text-[#1f1a16] mb-2">{label}</p>
      {payload.map((p: any, i: number) => (
        <div key={i} className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full" style={{ background: p.color }} />
            <span className="text-[#776b5a]">{p.name}</span>
          </div>
          <span className="font-bold text-[#2a2017]">{typeof p.value === "number" && p.value > 10000 ? fmt(p.value) : p.value}</span>
        </div>
      ))}
    </div>
  );
};

export default function CEODashboardPage() {
  const { openChat } = useAppStore();
  const [companyId, setCompanyId] = useState<string>("");
  const [selectedMonth, setSelectedMonth] = useState<string>(new Date().toISOString().slice(0, 7));
  const [history, setHistory] = useState<any[]>(FALLBACK_HISTORY);
  const [, setExpenses] = useState<any>(null);

  const { data, isLoading } = useFinancialData(companyId, selectedMonth);

  useEffect(() => {
    api.getStartupHealth().then(h => setCompanyId(h.default_company_id || "")).catch(() => {});
  }, []);

  useEffect(() => {
    if (!companyId) return;
    fetch(`${API_V1}/metrics/history/${companyId}?months=6`)
      .then(r => r.ok ? r.json() : [])
      .then(payload => { if (payload.length > 0) setHistory(payload); })
      .catch(() => {});
  }, [companyId]);

  useEffect(() => {
    if (!companyId) return;
    fetch(`${API_V1}/burn/expenses/${companyId}?month=${selectedMonth}`)
      .then(r => r.ok ? r.json() : {})
      .then(setExpenses)
      .catch(() => {});
  }, [companyId, selectedMonth]);

  const summary = data?.dashboard?.summary || {};
  const products = data?.dashboard?.products || {};
  const headcount = data?.dashboard?.headcount || {};
  const recommendations = data?.recommendations?.recommendations || [];
  const alerts = data?.alerts || [];
  const burnMultiple = data?.dashboard?.multiple?.burn_multiple || 1.85;

  const totalBurn    = summary?.net_burn || 1240000;
  const cashBalance  = summary?.total_credits || 2640000;
  const momChange    = summary?.mom_change_pct || 4.2;
  const runway       = cashBalance > 0 ? Math.round(cashBalance / (totalBurn || 1)) : 0;

  const breakdown = summary?.breakdown_by_category || {};
  const costByCategory = Object.keys(breakdown).length > 0
    ? Object.entries(breakdown).map(([cat, amount]: any) => ({
        name: cat.replace(/_/g, " ").charAt(0).toUpperCase() + cat.slice(1).replace(/_/g, " "),
        value: Number(amount) || 0,
        color: ["#3b82f6", "#8b5cf6", "#f59e0b", "#10b981", "#6366f1", "#94a3b8"][0],
      }))
    : COST_BREAKDOWN;

  const chartHistory = history.slice(-6).map((h: any) => ({
    month: h.month,
    "Net Burn":  Number(h.burn || h.net_burn || 0),
    "Revenue":   Number(h.revenue || 0),
    "Cash":      Number(h.cash || 0),
    "Headcount": Number(h.headcount || 0),
  }));

  const handleExportCsv = () => {
    if (!companyId) return;
    window.location.href = `${API_V1}/reports/export/ledger/csv?company_id=${companyId}`;
  };
  const handleExportPdf = () => {
    if (!companyId) return;
    window.location.href = `${API_V1}/reports/export/summary/pdf?company_id=${companyId}`;
  };

  const kpis = [
    {
      label: "Net Burn", value: fmt(totalBurn), sub: `${momChange > 0 ? "+" : ""}${momChange.toFixed(1)}% vs last month`,
      trend: momChange < 0 ? "good" : "bad", color: "from-red-50 to-red-100/40", border: "border-red-200",
      Icon: TrendingDown,
    },
    {
      label: "Cash Balance", value: fmt(cashBalance), sub: `${runway} days runway`,
      trend: cashBalance > 2000000 ? "good" : "bad", color: "from-emerald-50 to-emerald-100/40", border: "border-emerald-200",
      Icon: DollarSign,
    },
    {
      label: "Burn Multiple", value: `${burnMultiple.toFixed(2)}×`, sub: "Target: 1.5x",
      trend: burnMultiple < 1.5 ? "good" : burnMultiple < 2 ? "ok" : "bad", color: "from-amber-50 to-amber-100/40", border: "border-amber-200",
      Icon: Activity,
    },
    {
      label: "GM Avg", value: "64.8%", sub: "+2.1pp MoM",
      trend: "good", color: "from-blue-50 to-blue-100/40", border: "border-blue-200",
      Icon: TrendingUp,
    },
    {
      label: "Headcount", value: String(headcount.total_headcount || 18), sub: `₹${Math.round((headcount.per_employee_cost || 840000) / 12 / 1000)}K/mo avg`,
      trend: "ok", color: "from-purple-50 to-purple-100/40", border: "border-purple-200",
      Icon: Users,
    },
  ];

  return (
    <div className="min-h-screen bg-[#f6f3ee] text-[#1d1b19]">
      <TopBar title="CEO Dashboard" />

      <div className="max-w-[1600px] mx-auto p-6 space-y-6">

        {/* Header */}
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-black text-[#1d1b19]">CEO Dashboard</h1>
            <p className="text-[#6f655a] mt-1 text-sm">Financial health & strategic metrics · {selectedMonth}</p>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            <input type="month" value={selectedMonth} onChange={e => setSelectedMonth(e.target.value)}
              className="bg-white border border-[#e1d3c2] rounded-xl px-3 py-2 text-sm font-medium outline-none focus:ring-2 focus:ring-[#bf7a49]" />
            <button onClick={() => openChat("Give me a full financial health briefing for this month")}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-[#f0e4d0] text-[#6b3a1e] text-sm font-semibold hover:bg-[#e8d5bb] border border-[#d9c29a] transition">
              <Sparkles className="w-4 h-4" /> AI Brief
            </button>
            <button onClick={handleExportCsv} className="px-4 py-2 rounded-xl bg-[#9a5d34] hover:bg-[#7f4c2a] text-white text-sm font-semibold transition">CSV</button>
            <button onClick={handleExportPdf} className="px-4 py-2 rounded-xl bg-[#1f1a16] hover:bg-[#151210] text-white text-sm font-semibold transition">PDF</button>
          </div>
        </div>

        {/* Runway Alert */}
        {(alerts.length > 0 || runway < 90) && (
          <div className="rounded-2xl border border-red-300 bg-red-50 px-5 py-4 flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="font-bold text-red-900">Runway Alert</p>
              <p className="text-sm text-red-700 mt-0.5">⚠ Only {runway} days of cash remaining. Review burn rate and revenue projections.</p>
            </div>
            <button onClick={() => openChat("Analyze my runway and suggest immediate cost reduction actions")} className="text-xs font-bold text-red-700 border border-red-300 px-3 py-1.5 rounded-lg hover:bg-red-100 transition shrink-0">
              AI Action Plan →
            </button>
          </div>
        )}

        {/* KPI Cards */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
          {kpis.map((kpi) => {
            const Icon = kpi.Icon;
            return (
              <div key={kpi.label} className={`rounded-2xl border bg-gradient-to-br p-4 ${kpi.color} ${kpi.border}`}>
                <div className="flex items-center justify-between mb-2">
                  <p className="text-xs font-black uppercase tracking-wider text-[#6f655a]">{kpi.label}</p>
                  <Icon className="h-4 w-4 text-[#9a8872]" />
                </div>
                <p className="text-2xl font-black text-[#1d1b19]">{kpi.value}</p>
                <p className={`text-xs mt-1.5 font-semibold flex items-center gap-1 ${kpi.trend === "good" ? "text-emerald-600" : kpi.trend === "bad" ? "text-red-600" : "text-amber-600"}`}>
                  {kpi.trend === "good" ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                  {kpi.sub}
                </p>
              </div>
            );
          })}
        </div>

        {/* Main Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          {/* Burn & Revenue Trend */}
          <div className="lg:col-span-2 rounded-2xl border border-[#e4d8cb] bg-white p-5">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-sm font-black text-[#2a231d]">6-Month Burn & Cash Trajectory</h2>
                <p className="text-xs text-[#9a8872] mt-0.5">Monthly financials overview</p>
              </div>
            </div>
            <ResponsiveContainer width="100%" height={260}>
              <ComposedChart data={chartHistory} margin={{ top: 5, right: 5, left: 0, bottom: 5 }}>
                <defs>
                  <linearGradient id="burnGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="revenueGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="cashGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0e8de" vertical={false} />
                <XAxis dataKey="month" tick={{ fontSize: 11, fill: "#776b5a" }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: "#776b5a" }} axisLine={false} tickLine={false} tickFormatter={fmt} width={55} />
                <Tooltip content={<CUSTOM_TOOLTIP />} />
                <Legend wrapperStyle={{ fontSize: 11, paddingTop: 8 }} />
                <Area type="monotone" dataKey="Cash" fill="url(#cashGrad)" stroke="#3b82f6" strokeWidth={2.5} dot={false} />
                <Area type="monotone" dataKey="Revenue" fill="url(#revenueGrad)" stroke="#10b981" strokeWidth={2} dot={{ r: 3, fill: "#10b981" }} />
                <Line type="monotone" dataKey="Net Burn" stroke="#ef4444" strokeWidth={2.5} dot={{ r: 3.5, fill: "#ef4444" }} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>

          {/* Cost Breakdown Donut */}
          <div className="rounded-2xl border border-[#e4d8cb] bg-white p-5">
            <h2 className="text-sm font-black text-[#2a231d] mb-1">Cost Breakdown</h2>
            <p className="text-xs text-[#9a8872] mb-3">{selectedMonth}</p>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={costByCategory.slice(0, 6)}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={80}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {costByCategory.slice(0, 6).map((_entry, i) => (
                    <Cell key={i} fill={COST_BREAKDOWN[i]?.color || "#94a3b8"} />
                  ))}
                </Pie>
                <Tooltip formatter={(v: number) => [fmt(v), ""]} contentStyle={{ borderRadius: 12, fontSize: 11 }} />
                <Legend wrapperStyle={{ fontSize: 10 }} />
              </PieChart>
            </ResponsiveContainer>
            <div className="mt-2 space-y-1.5">
              {costByCategory.slice(0, 3).map((item: any, i) => (
                <div key={i} className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    <div className="w-2 h-2 rounded-full" style={{ background: COST_BREAKDOWN[i]?.color }} />
                    <span className="text-xs text-[#776b5a] capitalize">{item.name}</span>
                  </div>
                  <span className="text-xs font-bold text-[#2a2017]">{fmt(item.value)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Second row: Health Radar + Product Table + Top Drivers */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          {/* Radar Chart */}
          <div className="rounded-2xl border border-[#e4d8cb] bg-white p-5">
            <h2 className="text-sm font-black text-[#2a231d] mb-1">Business Health Score</h2>
            <p className="text-xs text-[#9a8872] mb-2">6 key dimensions · 0-100 scale</p>
            <ResponsiveContainer width="100%" height={230}>
              <RadarChart data={HEALTH_RADAR}>
                <PolarGrid stroke="#f0e8de" />
                <PolarAngleAxis dataKey="metric" tick={{ fontSize: 9, fill: "#776b5a" }} />
                <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />
                <Radar name="Health" dataKey="value" stroke="#b3622d" fill="#b3622d" fillOpacity={0.25} strokeWidth={2} />
                <Tooltip contentStyle={{ borderRadius: 10, fontSize: 11 }} />
              </RadarChart>
            </ResponsiveContainer>
          </div>

          {/* Top Cost Drivers */}
          <div className="rounded-2xl border border-[#e4d8cb] bg-white p-5">
            <h2 className="text-sm font-black text-[#2a231d] mb-4">Top Cost Drivers</h2>
            <div className="space-y-3">
              {costByCategory.slice(0, 5).map((item: any, idx: number) => {
                const pct = totalBurn > 0 ? (item.value / totalBurn) * 100 : 0;
                return (
                  <div key={idx}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-semibold text-[#2a2017] capitalize">{item.name}</span>
                      <span className="text-xs text-[#9a8872] font-bold">{fmt(item.value)}</span>
                    </div>
                    <div className="h-2 rounded-full bg-[#f0e8dc] overflow-hidden">
                      <div className="h-2 rounded-full transition-all duration-700"
                        style={{ width: `${pct}%`, background: COST_BREAKDOWN[idx]?.color || "#b3622d" }} />
                    </div>
                    <p className="text-[10px] text-[#9a8872] mt-0.5">{pct.toFixed(1)}% of total burn</p>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Key Metrics */}
          <div className="rounded-2xl border border-[#e4d8cb] bg-white p-5">
            <h2 className="text-sm font-black text-[#2a231d] mb-4">Key Metrics & Ratios</h2>
            <div className="space-y-3">
              {[
                { label: "Revenue per Employee", value: fmt((summary.total_credits || 1350000) / Math.max(headcount.total_headcount || 18, 1)) + "/mo" },
                { label: "Avg Cost per Employee", value: fmt((headcount.per_employee_cost || 840000) / 12) + "/mo" },
                { label: "Headcount Ratio", value: "1.8:1" },
                { label: "Cash Position", value: fmt(cashBalance) },
                { label: "Gross Margin", value: "64.8%" },
                { label: "Net Revenue Retention", value: "112%" },
                { label: "Cash Efficiency", value: `${((summary.total_credits || 1350000) / (totalBurn || 1)).toFixed(2)}x` },
              ].map(({ label, value }) => (
                <div key={label} className="flex items-center justify-between py-2 border-b border-[#f3ede5] last:border-0">
                  <span className="text-xs text-[#776b5a]">{label}</span>
                  <span className="text-sm font-bold text-[#2a2017]">{value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Product Performance */}
        {Object.keys(products).length > 0 && (
          <div className="rounded-2xl border border-[#e4d8cb] bg-white p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-black text-[#2a231d]">Product Performance & Profitability</h2>
              <button className="text-xs font-semibold text-[#8d4f27] flex items-center gap-1 hover:text-[#6b3a1e]">
                View All <ChevronRight className="h-3.5 w-3.5" />
              </button>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-[#776b5a]">
                    {["Product", "Revenue", "Cost", "Gross Margin", "Margin %", "Status"].map(h => (
                      <th key={h} className="text-left text-xs font-bold uppercase tracking-wide pb-3 px-3">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#f3ede5]">
                  {Object.entries(products)
                    .sort((a: any, b: any) => (b[1]?.gross_margin || 0) - (a[1]?.gross_margin || 0))
                    .map(([name, value]: any) => {
                      const marginPct = value.gross_margin_pct || 0;
                      const status = marginPct > 50 ? "Healthy" : marginPct > 30 ? "Monitor" : "Critical";
                      const statusColors = { Healthy: "text-emerald-700 bg-emerald-50 border-emerald-200", Monitor: "text-amber-700 bg-amber-50 border-amber-200", Critical: "text-red-700 bg-red-50 border-red-200" };
                      return (
                        <tr key={name} className="hover:bg-[#fdf9f4] transition-colors">
                          <td className="px-3 py-3 font-semibold capitalize">{name.replace(/_/g, " ")}</td>
                          <td className="px-3 py-3">{fmt(value.total_revenue || 0)}</td>
                          <td className="px-3 py-3 text-[#9a8872]">{fmt(value.total_cost || 0)}</td>
                          <td className="px-3 py-3 font-bold">{fmt(value.gross_margin || 0)}</td>
                          <td className="px-3 py-3">
                            <div className="flex items-center gap-2">
                              <div className="w-16 h-1.5 rounded-full bg-[#f0e8dc] overflow-hidden">
                                <div className="h-1.5 rounded-full bg-emerald-500" style={{ width: `${Math.min(marginPct, 100)}%` }} />
                              </div>
                              <span className="text-xs font-bold">{marginPct.toFixed(1)}%</span>
                            </div>
                          </td>
                          <td className="px-3 py-3">
                            <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-bold border ${statusColors[status as keyof typeof statusColors]}`}>{status}</span>
                          </td>
                        </tr>
                      );
                    })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* AI Recommendations */}
        <div className="rounded-2xl border border-[#e4d8cb] bg-white p-5">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-[#d97706] to-[#b45309] flex items-center justify-center">
              <Sparkles className="w-3.5 h-3.5 text-white" />
            </div>
            <div>
              <h2 className="text-sm font-black text-[#2a231d]">AI-Powered Recommendations</h2>
              <p className="text-xs text-[#9a8872]">Based on your current financial data</p>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {(recommendations.length > 0 ? recommendations : [
              { priority: "high", title: "Extend Runway", finding: "At current burn rate, raise bridge or cut $180K from non-essential spend in Q2." },
              { priority: "medium", title: "Improve Billing Efficiency", finding: "3 overdue invoices totaling ₹7.2L — follow up with automated reminders." },
              { priority: "medium", title: "Optimize Cloud Spend", finding: "Infrastructure costs grew 22% MoM. Review unused EC2 instances and S3 buckets." },
              { priority: "low", title: "Headcount Planning", finding: "Engineering:Revenue ratio is healthy. Consider 2 new hires in Sales for Q3." },
              { priority: "low", title: "Gross Margin", finding: "Orchard product margin at 34% — review pricing or COGS reduction opportunities." },
              { priority: "high", title: "Tax Provisioning", finding: "Advance tax due June 15. Set aside ₹3.8L based on projected FY profits." },
            ]).slice(0, 6).map((rec: any, idx: number) => {
              const colors = {
                high: { bg: "bg-red-50", border: "border-red-200", title: "text-red-900", body: "text-red-700", badge: "bg-red-100 text-red-700" },
                medium: { bg: "bg-amber-50", border: "border-amber-200", title: "text-amber-900", body: "text-amber-700", badge: "bg-amber-100 text-amber-700" },
                low: { bg: "bg-emerald-50", border: "border-emerald-200", title: "text-emerald-900", body: "text-emerald-700", badge: "bg-emerald-100 text-emerald-700" },
              };
              const c = colors[rec.priority as keyof typeof colors] || colors.low;
              return (
                <div key={idx} className={`rounded-xl border p-4 ${c.bg} ${c.border}`}>
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <p className={`font-bold text-sm ${c.title}`}>{rec.title || `Action ${idx + 1}`}</p>
                    <span className={`text-[9px] font-black uppercase px-1.5 py-0.5 rounded-full shrink-0 ${c.badge}`}>{rec.priority}</span>
                  </div>
                  <p className={`text-xs leading-relaxed ${c.body}`}>{rec.finding || rec.action}</p>
                </div>
              );
            })}
          </div>
        </div>

        {isLoading && (
          <div className="flex items-center justify-center gap-2 py-4 text-sm text-[#9a8872]">
            <RefreshCw className="h-4 w-4 animate-spin" />
            Loading financial data…
          </div>
        )}
      </div>
    </div>
  );
}
