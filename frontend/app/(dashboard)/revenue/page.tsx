"use client";

import TopBar from "@/components/TopBar";
import { useRevenue, useAlerts } from "@/hooks/useFinancialData";
import { useAppStore } from "@/lib/store";
import { formatCurrency } from "@/lib/utils";
import {
  Area, AreaChart, Bar, CartesianGrid, ComposedChart, Legend, Line,
  PieChart, Pie, Cell, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { ArrowUpRight, Repeat, Sparkles, TrendingDown, TrendingUp, AlertCircle, Users } from "lucide-react";

const MRR_HISTORY = [
  { month: "May 25", mrr: 38000,  new: 3800,  expansion: 900,  contraction: 600, churn: 1100, nrr: 104 },
  { month: "Jun 25", mrr: 44200,  new: 5200,  expansion: 1400, contraction: 700, churn: 1300, nrr: 106 },
  { month: "Jul 25", mrr: 51800,  new: 6500,  expansion: 1900, contraction: 600, churn: 1200, nrr: 107 },
  { month: "Aug 25", mrr: 61000,  new: 7800,  expansion: 2200, contraction: 550, churn: 1250, nrr: 108 },
  { month: "Sep 25", mrr: 71900,  new: 9200,  expansion: 2600, contraction: 500, churn: 1400, nrr: 109 },
  { month: "Oct 25", mrr: 83500,  new: 10200, expansion: 3100, contraction: 480, churn: 1220, nrr: 110 },
  { month: "Nov 25", mrr: 96600,  new: 11200, expansion: 3500, contraction: 450, churn: 1350, nrr: 112 },
  { month: "Dec 25", mrr: 110100, new: 12000, expansion: 4000, contraction: 400, churn: 1100, nrr: 113 },
  { month: "Jan 26", mrr: 115800, new: 8000,  expansion: 3200, contraction: 500, churn: 3000, nrr: 112 },
  { month: "Feb 26", mrr: 124600, new: 10800, expansion: 4200, contraction: 560, churn: 1640, nrr: 114 },
  { month: "Mar 26", mrr: 133000, new: 12800, expansion: 4600, contraction: 600, churn: 1400, nrr: 115 },
  { month: "Apr 26", mrr: 139800, new: 15600, expansion: 5200, contraction: 620, churn: 1380, nrr: 118 },
];

const ARR_TREND = MRR_HISTORY.map((m) => ({
  month: m.month,
  arr: m.mrr * 12,
  target: Math.round(m.mrr * 12 * 1.08),
}));

const SEGMENT_COLORS = ["#8d4f27", "#c28040", "#e8c27a", "#b5763e"];
const REVENUE_SEGMENTS = [
  { name: "SaaS Subscriptions", pct: 79.4, amount: Math.round(139800 * 0.794), color: "#8d4f27" },
  { name: "Professional Services", pct: 13.2, amount: Math.round(139800 * 0.132), color: "#c28040" },
  { name: "Usage / Overage", pct: 7.4,  amount: Math.round(139800 * 0.074), color: "#e8c27a" },
];

const LEGEND_LABELS: Record<string, string> = {
  new: "New MRR", expansion: "Expansion", contraction: "Contraction", churn: "Churn MRR", mrr: "Total MRR",
};

export default function RevenuePage() {
  const { revenue } = useRevenue();
  const { alerts } = useAlerts();
  const revenueAlerts = alerts.alerts.filter((a) =>
    ["revenue_spike", "revenue_drop", "churn_spike"].includes(a.alert_type)
  );
  const { openChat } = useAppStore();

  const latestMRR = MRR_HISTORY[MRR_HISTORY.length - 1].mrr;
  const prevMRR   = MRR_HISTORY[MRR_HISTORY.length - 2].mrr;
  const mrrGrowth = ((latestMRR - prevMRR) / prevMRR * 100).toFixed(1);

  return (
    <div className="min-h-screen bg-[#f6f3ee] pb-14 text-[#1d1b17]">
      <TopBar title="Revenue Intelligence" />

      <div className="mx-auto max-w-7xl space-y-6 px-4 pt-6 sm:px-6 lg:px-8">

        {/* Hero */}
        <section className="rounded-3xl border border-[#d9cdbc] bg-[linear-gradient(145deg,#fff8ec_0%,#f3eadb_100%)] p-6 shadow-[0_18px_48px_rgba(63,45,24,0.1)] sm:p-8">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="inline-flex items-center gap-2 rounded-full border border-[#d9c29a] bg-[#fff4dd] px-3 py-1 text-xs font-semibold text-[#8c5c19]">
                <TrendingUp className="h-3.5 w-3.5" />
                Revenue performance · 12-month view
              </p>
              <h1 className="mt-3 text-3xl font-semibold text-[#2c2013]">Growth & Retention</h1>
              <p className="mt-2 text-sm text-[#5f5344]">MRR waterfall, ARR trajectory, segment mix, and NRR health — one narrative.</p>
            </div>
            <button
              onClick={() => openChat("Revenue growth strategy")}
              className="inline-flex items-center gap-2 rounded-xl bg-[#231c15] px-4 py-2.5 text-sm font-medium text-[#fff7eb] hover:bg-[#17120d]"
            >
              <Sparkles className="h-4 w-4" />
              Run strategy audit
            </button>
          </div>
        </section>

        {/* KPI Cards */}
        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { label: "Current MRR",   value: formatCurrency(latestMRR), sub: `+${mrrGrowth}% MoM`, icon: TrendingUp,   positive: true },
            { label: "Projected ARR", value: formatCurrency(latestMRR * 12), sub: "Annualised run-rate", icon: ArrowUpRight, positive: true },
            { label: "Net Retention", value: `${revenue.nrr ?? 118}%`, sub: "Target ≥ 110%", icon: Repeat, positive: (revenue.nrr ?? 118) >= 110 },
            { label: "Gross Churn",   value: `${revenue.churn_rate ?? 1.0}%`, sub: "Monthly logo churn", icon: TrendingDown, positive: false },
          ].map((item) => (
            <article key={item.label} className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] p-5">
              <div className="flex items-center justify-between">
                <p className="text-xs uppercase tracking-[0.12em] text-[#776b5a]">{item.label}</p>
                <item.icon className={`h-4 w-4 ${item.positive ? "text-emerald-600" : "text-rose-500"}`} />
              </div>
              <p className="mt-2 text-2xl font-semibold text-[#2a2017]">{item.value}</p>
              <p className="mt-0.5 text-xs text-[#9a8878]">{item.sub}</p>
            </article>
          ))}
        </section>

        {/* MRR Waterfall ComposedChart */}
        <section className="rounded-2xl border border-[#ded2c4] bg-[#fffdf8] p-5 sm:p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-lg font-semibold text-[#2a2017]">MRR Waterfall — 12 Months</h2>
              <p className="text-xs text-[#7b6d5b]">New, expansion, contraction, churn decomposition vs. total MRR trend</p>
            </div>
            <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-700">
              +{mrrGrowth}% MoM
            </span>
          </div>
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={MRR_HISTORY} margin={{ top: 10, right: 60, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0ebe3" vertical={false} />
                <XAxis dataKey="month" tickLine={false} axisLine={false} tick={{ fill: "#7b6d5b", fontSize: 11 }} />
                <YAxis yAxisId="left" tickLine={false} axisLine={false} tick={{ fill: "#7b6d5b", fontSize: 11 }} tickFormatter={(v) => `$${v / 1000}k`} />
                <YAxis yAxisId="right" orientation="right" tickLine={false} axisLine={false} tick={{ fill: "#7b6d5b", fontSize: 11 }} tickFormatter={(v) => `$${v / 1000}k`} />
                <Tooltip
                  contentStyle={{ border: "1px solid #dbcdb9", borderRadius: 12, background: "#fff8ea", fontSize: 12 }}
                  formatter={(v: number, name: string) => [`$${v.toLocaleString()}`, LEGEND_LABELS[name] ?? name]}
                />
                <Legend formatter={(v: string) => (LEGEND_LABELS as Record<string,string>)[v] ?? v} wrapperStyle={{ fontSize: 12, paddingTop: 8 }} />
                <Bar yAxisId="left" dataKey="new" stackId="inflow" fill="#10b981" radius={[2,2,0,0]} />
                <Bar yAxisId="left" dataKey="expansion" stackId="inflow" fill="#34d399" radius={[2,2,0,0]} />
                <Bar yAxisId="left" dataKey="contraction" stackId="outflow" fill="#fb923c" radius={[0,0,2,2]} />
                <Bar yAxisId="left" dataKey="churn" stackId="outflow" fill="#ef4444" radius={[0,0,2,2]} />
                <Line yAxisId="right" type="monotone" dataKey="mrr" stroke="#8d4f27" strokeWidth={2.5} dot={{ r: 3, fill: "#8d4f27" }} />
                <ReferenceLine yAxisId="right" y={100000} stroke="#c28040" strokeDasharray="5 3" label={{ value: "$100k MRR", fill: "#c28040", fontSize: 11 }} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </section>

        {/* ARR Trajectory + Revenue by Segment */}
        <section className="grid gap-4 lg:grid-cols-2">

          {/* ARR Trajectory */}
          <div className="rounded-2xl border border-[#ded2c4] bg-[#fffdf8] p-5 sm:p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-lg font-semibold text-[#2a2017]">ARR Trajectory</h2>
                <p className="text-xs text-[#7b6d5b]">Actual vs. 8% growth target</p>
              </div>
              <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-amber-100 text-amber-700">
                {formatCurrency(latestMRR * 12)} ARR
              </span>
            </div>
            <div className="h-[260px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={ARR_TREND} margin={{ top: 10, right: 16, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="arrFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#8d4f27" stopOpacity={0.25} />
                      <stop offset="95%" stopColor="#8d4f27" stopOpacity={0.02} />
                    </linearGradient>
                    <linearGradient id="targetFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#c28040" stopOpacity={0.12} />
                      <stop offset="95%" stopColor="#c28040" stopOpacity={0.01} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0ebe3" vertical={false} />
                  <XAxis dataKey="month" tickLine={false} axisLine={false} tick={{ fill: "#7b6d5b", fontSize: 11 }} />
                  <YAxis tickLine={false} axisLine={false} tick={{ fill: "#7b6d5b", fontSize: 11 }} tickFormatter={(v) => `$${(v / 1000000).toFixed(1)}M`} />
                  <Tooltip
                    contentStyle={{ border: "1px solid #dbcdb9", borderRadius: 12, background: "#fff8ea", fontSize: 12 }}
                    formatter={(v: number, name: string) => [formatCurrency(v), name === "arr" ? "ARR" : "Target ARR"]}
                  />
                  <ReferenceLine y={1000000} stroke="#10b981" strokeDasharray="4 3" label={{ value: "$1M ARR", fill: "#10b981", fontSize: 11 }} />
                  <Area type="monotone" dataKey="target" stroke="#c28040" strokeWidth={1.5} strokeDasharray="4 3" fill="url(#targetFill)" />
                  <Area type="monotone" dataKey="arr" stroke="#8d4f27" strokeWidth={2.5} fill="url(#arrFill)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Revenue by Segment — donut */}
          <div className="rounded-2xl border border-[#ded2c4] bg-[#fffdf8] p-5 sm:p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-lg font-semibold text-[#2a2017]">Revenue Mix</h2>
                <p className="text-xs text-[#7b6d5b]">Segment breakdown — current month</p>
              </div>
              <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-[#f4e7d8] text-[#7d4f13]">
                {formatCurrency(latestMRR)}/mo
              </span>
            </div>
            <div className="flex items-center gap-6">
              <div className="h-[200px] w-[200px] flex-shrink-0">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={REVENUE_SEGMENTS} cx="50%" cy="50%" innerRadius={55} outerRadius={85} dataKey="amount" paddingAngle={3}>
                      {REVENUE_SEGMENTS.map((seg, i) => (
                        <Cell key={seg.name} fill={SEGMENT_COLORS[i % SEGMENT_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{ border: "1px solid #dbcdb9", borderRadius: 10, background: "#fff8ea", fontSize: 12 }}
                      formatter={(v: number, name: string) => [formatCurrency(v), name]}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="flex-1 space-y-3">
                {REVENUE_SEGMENTS.map((seg, i) => (
                  <div key={seg.name} className="space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="flex items-center gap-1.5 text-xs font-medium text-[#2a2017]">
                        <span className="inline-block h-2 w-2 rounded-sm" style={{ background: SEGMENT_COLORS[i] }} />
                        {seg.name}
                      </span>
                      <span className="text-xs font-semibold text-[#5f5344]">{seg.pct}%</span>
                    </div>
                    <div className="h-1.5 bg-[#ede8e0] rounded-full overflow-hidden">
                      <div className="h-full rounded-full" style={{ width: `${seg.pct}%`, background: SEGMENT_COLORS[i] }} />
                    </div>
                    <p className="text-xs text-[#9a8878]">{formatCurrency(seg.amount)}/mo</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* NRR Trend */}
        <section className="rounded-2xl border border-[#ded2c4] bg-[#fffdf8] p-5 sm:p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-lg font-semibold text-[#2a2017]">Net Revenue Retention — 12 Months</h2>
              <p className="text-xs text-[#7b6d5b]">Expansion-driven growth; benchmark: 110% world-class, 100% healthy</p>
            </div>
            <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-700">
              {MRR_HISTORY[MRR_HISTORY.length - 1].nrr}% NRR
            </span>
          </div>
          <div className="h-[220px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={MRR_HISTORY} margin={{ top: 10, right: 16, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="nrrFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0.02} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0ebe3" vertical={false} />
                <XAxis dataKey="month" tickLine={false} axisLine={false} tick={{ fill: "#7b6d5b", fontSize: 11 }} />
                <YAxis domain={[95, 125]} tickLine={false} axisLine={false} tick={{ fill: "#7b6d5b", fontSize: 11 }} tickFormatter={(v) => `${v}%`} />
                <Tooltip
                  contentStyle={{ border: "1px solid #dbcdb9", borderRadius: 12, background: "#fff8ea", fontSize: 12 }}
                  formatter={(v: number) => [`${v}%`, "NRR"]}
                />
                <ReferenceLine y={110} stroke="#10b981" strokeDasharray="4 3" label={{ value: "110% world-class", fill: "#10b981", fontSize: 11 }} />
                <ReferenceLine y={100} stroke="#fb923c" strokeDasharray="4 3" label={{ value: "100% healthy", fill: "#fb923c", fontSize: 11 }} />
                <Area type="monotone" dataKey="nrr" stroke="#059669" strokeWidth={2.5} fill="url(#nrrFill)" dot={{ r: 3, fill: "#059669" }} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </section>

        {/* Revenue Anomaly Alerts */}
        {revenueAlerts.length > 0 && (
          <section className="rounded-2xl border border-[#e2d1c3] bg-[#fdfaf7] p-5 sm:p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <AlertCircle className="h-5 w-5 text-[#9a461f]" />
                <h3 className="font-semibold text-[#4a3f35]">Revenue Anomalies</h3>
              </div>
              <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-orange-100 text-orange-700">{revenueAlerts.length} Active</span>
            </div>
            <ul className="space-y-2">
              {revenueAlerts.map((alert) => (
                <li key={alert.id} className="flex items-center justify-between py-3 px-4 rounded-lg bg-white/50 border border-[#eee0d5]">
                  <div className="flex items-center gap-3">
                    {alert.alert_type === "churn_spike" ? <Users className="h-4 w-4 text-orange-600" /> :
                     alert.alert_type === "revenue_spike" ? <TrendingUp className="h-4 w-4 text-orange-600" /> :
                     <TrendingDown className="h-4 w-4 text-red-600" />}
                    <div>
                      <p className="text-sm font-medium text-[#4a3f35]">{alert.description}</p>
                      <p className="text-xs text-[#7b6d5b]">Detected: {new Date(alert.created_at).toLocaleDateString()}</p>
                    </div>
                  </div>
                  <span className={`text-xs font-medium px-2 py-0.5 rounded-full border ${
                    alert.severity === "critical" ? "border-red-300 text-red-700" : "border-orange-300 text-orange-700"
                  }`}>{alert.severity}</span>
                </li>
              ))}
            </ul>
          </section>
        )}
      </div>
    </div>
  );
}
