"use client";

import { useState, useEffect } from "react";
import TopBar from "@/components/TopBar";
import { useAppStore } from "@/lib/store";
import api, { type SaasSummary, type MrrWaterfallMonth } from "@/lib/api";
import { cn, formatCurrency } from "@/lib/utils";
import {
  TrendingUp, Sparkles, ArrowUpRight, Users,
  DollarSign, Repeat, Activity, BarChart2, Target,
} from "lucide-react";
import {
  AreaChart, Area, Bar, LineChart, Line, XAxis, YAxis,
  Tooltip, ResponsiveContainer, CartesianGrid, Legend, ReferenceLine,
  ComposedChart,
} from "recharts";

// 12-month MRR waterfall — May 2025 → Apr 2026
const MRR_WATERFALL = [
  { month: "May 25", new: 3800, expansion: 900,  contraction: 600, churn: 1100, mrr: 38000 },
  { month: "Jun 25", new: 4600, expansion: 1200, contraction: 700, churn: 1300, mrr: 41800 },
  { month: "Jul 25", new: 5200, expansion: 1400, contraction: 550, churn: 1150, mrr: 46700 },
  { month: "Aug 25", new: 5800, expansion: 1600, contraction: 620, churn: 1200, mrr: 52280 },
  { month: "Sep 25", new: 6400, expansion: 1900, contraction: 680, churn: 1320, mrr: 58580 },
  { month: "Oct 25", new: 7200, expansion: 2200, contraction: 740, churn: 1440, mrr: 65820 },
  { month: "Nov 25", new: 8200, expansion: 2600, contraction: 820, churn: 1680, mrr: 74120 },
  { month: "Dec 25", new: 9400, expansion: 3100, contraction: 890, churn: 1830, mrr: 83900 },
  { month: "Jan 26", new: 11200, expansion: 3600, contraction: 960, churn: 1940, mrr: 95800 },
  { month: "Feb 26", new: 8800, expansion: 4200, contraction: 720, churn: 1480, mrr: 106600 },
  { month: "Mar 26", new: 12400, expansion: 4600, contraction: 840, churn: 1760, mrr: 121000 },
  { month: "Apr 26", new: 15600, expansion: 5200, contraction: 620, churn: 1380, mrr: 139800 },
];

// 8 quarterly cohorts for LTV/CAC
const LTV_CAC = [
  { cohort: "Q1 24", ltv: 38000, cac: 5200, ratio: 7.3, payback: 22 },
  { cohort: "Q2 24", ltv: 42000, cac: 5000, ratio: 8.4, payback: 20 },
  { cohort: "Q3 24", ltv: 46000, cac: 4800, ratio: 9.6, payback: 18 },
  { cohort: "Q4 24", ltv: 50000, cac: 4600, ratio: 10.9, payback: 17 },
  { cohort: "Q1 25", ltv: 54000, cac: 4400, ratio: 12.3, payback: 15 },
  { cohort: "Q2 25", ltv: 59000, cac: 4700, ratio: 12.6, payback: 15 },
  { cohort: "Q3 25", ltv: 64000, cac: 4900, ratio: 13.1, payback: 14 },
  { cohort: "Q4 25", ltv: 70000, cac: 4800, ratio: 14.6, payback: 13 },
  { cohort: "Q1 26", ltv: 78000, cac: 5100, ratio: 15.3, payback: 12 },
];

// Monthly retention cohorts — M0 through M12
const RETENTION_COHORT = [
  { month: "M0",  "Jan 25": 100, "Apr 25": 100, "Jul 25": 100, "Oct 25": 100, "Jan 26": 100 },
  { month: "M1",  "Jan 25":  97, "Apr 25":  97, "Jul 25":  98, "Oct 25":  98, "Jan 26":  99 },
  { month: "M2",  "Jan 25":  94, "Apr 25":  95, "Jul 25":  96, "Oct 25":  97, "Jan 26":  98 },
  { month: "M3",  "Jan 25":  91, "Apr 25":  92, "Jul 25":  94, "Oct 25":  95, "Jan 26":  97 },
  { month: "M4",  "Jan 25":  88, "Apr 25":  90, "Jul 25":  92, "Oct 25":  94, "Jan 26":  96 },
  { month: "M5",  "Jan 25":  86, "Apr 25":  88, "Jul 25":  90, "Oct 25":  92 },
  { month: "M6",  "Jan 25":  83, "Apr 25":  86, "Jul 25":  88, "Oct 25":  91 },
  { month: "M7",  "Jan 25":  81, "Apr 25":  84, "Jul 25":  87 },
  { month: "M8",  "Jan 25":  79, "Apr 25":  82, "Jul 25":  85 },
  { month: "M9",  "Jan 25":  77, "Apr 25":  80, "Jul 25":  84 },
  { month: "M10", "Jan 25":  75, "Apr 25":  79 },
  { month: "M11", "Jan 25":  74, "Apr 25":  78 },
  { month: "M12", "Jan 25":  73, "Apr 25":  77 },
];

// 12-month quick ratio trend
const QUICK_RATIO_DATA = [
  { month: "May 25", ratio: 2.4, nrr: 104 },
  { month: "Jun 25", ratio: 2.8, nrr: 106 },
  { month: "Jul 25", ratio: 3.1, nrr: 108 },
  { month: "Aug 25", ratio: 3.4, nrr: 110 },
  { month: "Sep 25", ratio: 3.6, nrr: 112 },
  { month: "Oct 25", ratio: 3.9, nrr: 114 },
  { month: "Nov 25", ratio: 4.1, nrr: 115 },
  { month: "Dec 25", ratio: 4.4, nrr: 116 },
  { month: "Jan 26", ratio: 4.6, nrr: 117 },
  { month: "Feb 26", ratio: 4.8, nrr: 118 },
  { month: "Mar 26", ratio: 5.1, nrr: 119 },
  { month: "Apr 26", ratio: 5.4, nrr: 121 },
];

// Monthly ARR trend for the ARR growth chart
const ARR_TREND = MRR_WATERFALL.map(m => ({
  month: m.month,
  arr: m.mrr * 12,
  target: m.mrr * 12 * 1.05,  // 5% above-plan stretch target
}));

const COHORT_COLORS = ["#2563eb", "#7c3aed", "#059669", "#d97706", "#dc2626"];

export default function SaasMetricsPage() {
  const { openChat } = useAppStore();
  const [activeTab, setActiveTab] = useState<"mrr" | "retention" | "unit_econ">("mrr");
  const [summary, setSummary] = useState<SaasSummary | null>(null);
  const [waterfall, setWaterfall] = useState<MrrWaterfallMonth[]>(
    MRR_WATERFALL.map(m => ({ month: m.month, mrr: m.mrr, new: m.new, expansion: m.expansion, contraction: m.contraction, churn: m.churn }))
  );

  useEffect(() => {
    async function load() {
      try {
        const health = await api.getStartupHealth();
        const cid = health.default_company_id;
        if (!cid) return;
        const [sumRes, watRes] = await Promise.allSettled([
          api.getSaasSummary(cid),
          api.getMrrWaterfall(cid, 6),
        ]);
        if (sumRes.status === "fulfilled") setSummary(sumRes.value);
        if (watRes.status === "fulfilled" && watRes.value.months.length > 0) setWaterfall(watRes.value.months);
      } catch {
        // keep mock data
      }
    }
    load();
  }, []);

  const lastMonth = MRR_WATERFALL[MRR_WATERFALL.length - 1];
  const prevMonth = MRR_WATERFALL[MRR_WATERFALL.length - 2];
  const currentMRR = summary?.mrr ?? lastMonth.mrr;
  const currentARR = summary?.arr ?? currentMRR * 12;
  const latestLTV = summary?.ltv ?? LTV_CAC[LTV_CAC.length - 1].ltv;
  const latestCAC = summary?.cac ?? LTV_CAC[LTV_CAC.length - 1].cac;
  const ltvCacRatio = summary?.ltv_cac_ratio ?? (latestLTV / latestCAC);
  const paybackMonths = summary?.cac_payback_months ?? LTV_CAC[LTV_CAC.length - 1].payback;
  const quickRatio = QUICK_RATIO_DATA[QUICK_RATIO_DATA.length - 1].ratio;

  const mrrGrowthMoM = summary?.mrr_growth_pct ?? ((lastMonth.mrr - prevMonth.mrr) / prevMonth.mrr) * 100;
  const nrr = summary?.nrr ?? QUICK_RATIO_DATA[QUICK_RATIO_DATA.length - 1].nrr;
  const rule40 = summary?.rule_of_40 ?? (mrrGrowthMoM * 12 + 42);

  const metrics = [
    { label: "MRR", value: formatCurrency(currentMRR), change: `+${mrrGrowthMoM.toFixed(1)}% MoM`, positive: true, icon: DollarSign },
    { label: "ARR", value: formatCurrency(currentARR), change: "Annualized", positive: true, icon: TrendingUp },
    { label: "Net Revenue Retention", value: `${nrr}%`, change: "World class >110%", positive: true, icon: Repeat },
    { label: "Quick Ratio", value: quickRatio.toFixed(1), change: quickRatio >= 4 ? "Excellent (>4)" : "Healthy (>2)", positive: quickRatio >= 2, icon: Activity },
    { label: "LTV/CAC", value: `${ltvCacRatio.toFixed(1)}x`, change: "Healthy (>3x)", positive: ltvCacRatio >= 3, icon: Target },
    { label: "CAC Payback", value: `${Math.round(paybackMonths)}mo`, change: paybackMonths < 18 ? "Excellent (<18mo)" : "Needs work", positive: paybackMonths < 18, icon: Users },
    { label: "Rule of 40", value: `${Math.round(rule40)}`, change: rule40 >= 40 ? "Passes (>40)" : "Below target", positive: rule40 >= 40, icon: BarChart2 },
    { label: "Gross Margin", value: "72%", change: "Industry avg 70%", positive: true, icon: ArrowUpRight },
  ];

  return (
    <div className="min-h-screen bg-[#f6f3ee] pb-14 text-[#1d1b17]">
      <TopBar title="SaaS Metrics" />

      <div className="mx-auto max-w-7xl space-y-6 px-4 pt-6 sm:px-6 lg:px-8">

        <section className="rounded-3xl border border-[#d9cdbc] bg-[linear-gradient(145deg,#fff8ec_0%,#f3eadb_100%)] p-6 shadow-[0_18px_48px_rgba(63,45,24,0.1)] sm:p-8">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <p className="inline-flex items-center gap-2 rounded-full border border-[#d9c29a] bg-[#fff4dd] px-3 py-1 text-xs font-semibold text-[#8c5c19]">
                <TrendingUp className="h-3.5 w-3.5" /> SaaS Intelligence
              </p>
              <h1 className="mt-2 text-2xl font-bold text-[#2c2013]">SaaS Metrics Dashboard</h1>
              <p className="mt-1 text-sm text-[#5f5344]">MRR waterfall, unit economics, cohort retention, and startup benchmarks.</p>
            </div>
            <button onClick={() => openChat("Analyze our SaaS metrics and compare to industry benchmarks")} className="inline-flex items-center gap-2 rounded-xl border border-[#d9c29a] bg-white/80 px-4 py-2.5 text-sm font-medium text-[#6b4c1e] hover:bg-white self-start lg:self-auto">
              <Sparkles className="h-4 w-4" /> Benchmark Analysis
            </button>
          </div>
        </section>

        {/* KPI Grid */}
        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {metrics.map((m) => {
            const Icon = m.icon;
            return (
              <article key={m.label} className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] p-5">
                <div className="flex items-center justify-between mb-1">
                  <p className="text-xs uppercase tracking-[0.12em] text-[#776b5a]">{m.label}</p>
                  <Icon className="h-4 w-4 text-[#8d4f27]" />
                </div>
                <p className="text-2xl font-bold text-[#2a2017] mt-2">{m.value}</p>
                <p className={cn("mt-1 text-xs font-semibold", m.positive ? "text-emerald-600" : "text-red-600")}>{m.change}</p>
              </article>
            );
          })}
        </section>

        {/* Tabs */}
        <section className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] overflow-hidden">
          <div className="flex gap-1 bg-[#f0ebe3] p-1 m-5 rounded-xl w-fit">
            {([["mrr", "MRR Waterfall"], ["retention", "Cohort Retention"], ["unit_econ", "Unit Economics"]] as const).map(([key, label]) => (
              <button key={key} onClick={() => setActiveTab(key)} className={cn("rounded-lg px-4 py-2 text-xs font-bold transition-all", activeTab === key ? "bg-white text-[#2a2017] shadow-sm" : "text-[#776b5a] hover:text-[#2a2017]")}>
                {label}
              </button>
            ))}
          </div>

          <div className="px-5 pb-6">
            {activeTab === "mrr" && (
              <div className="space-y-8">
                {/* MRR Waterfall stacked bars */}
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <h3 className="text-sm font-bold text-[#2a2017]">MRR Movement Waterfall — 12 Months</h3>
                    <span className="text-xs text-[#9a8872]">Stacked: New · Expansion · Contraction · Churn</span>
                  </div>
                  <p className="text-xs text-[#776b5a] mb-3">Monthly MRR inflows (green/blue) vs outflows (amber/red). Net MRR line overlaid.</p>
                  <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <ComposedChart data={waterfall} margin={{ top: 10, right: 24, left: 8, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#f0ebe3" vertical={false} />
                        <XAxis dataKey="month" tick={{ fill: "#7b6d5b", fontSize: 11 }} tickLine={false} axisLine={false} />
                        <YAxis yAxisId="left" tick={{ fill: "#7b6d5b", fontSize: 11 }} tickLine={false} axisLine={false} tickFormatter={v => `$${(v/1000).toFixed(0)}k`} width={48} />
                        <YAxis yAxisId="right" orientation="right" tick={{ fill: "#7b6d5b", fontSize: 11 }} tickLine={false} axisLine={false} tickFormatter={v => `$${(v/1000).toFixed(0)}k`} width={52} />
                        <Tooltip
                          contentStyle={{ borderRadius: 10, border: "1px solid #e0cfc2", background: "#fffbf5", fontSize: 12 }}
                          formatter={(v: number, name: string) => {
                            const labels: Record<string,string> = { new: "New MRR", expansion: "Expansion", contraction: "Contraction", churn: "Churn", mrr: "Total MRR" };
                            return [formatCurrency(v), labels[name] ?? name];
                          }}
                        />
                        <Legend wrapperStyle={{ fontSize: 11, paddingTop: 8 }} formatter={(v: string) => ({ new:"New MRR", expansion:"Expansion", contraction:"Contraction", churn:"Churn", mrr:"Total MRR" } as Record<string,string>)[v] ?? v} />
                        <Bar yAxisId="left" dataKey="new" name="new" stackId="inflow" fill="#059669" radius={[2,2,0,0]} />
                        <Bar yAxisId="left" dataKey="expansion" name="expansion" stackId="inflow" fill="#2563eb" />
                        <Bar yAxisId="left" dataKey="contraction" name="contraction" stackId="outflow" fill="#f59e0b" radius={[0,0,2,2]} />
                        <Bar yAxisId="left" dataKey="churn" name="churn" stackId="outflow" fill="#ef4444" />
                        <Line yAxisId="right" type="monotone" dataKey="mrr" name="mrr" stroke="#8d4f27" strokeWidth={2.5} dot={{ r: 3, fill: "#8d4f27" }} />
                      </ComposedChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* ARR Trajectory vs Stretch Target */}
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <h3 className="text-sm font-bold text-[#2a2017]">ARR Trajectory vs Stretch Target</h3>
                    <span className="text-xs text-emerald-600 font-semibold">$1.68M ARR · +267% YoY</span>
                  </div>
                  <p className="text-xs text-[#776b5a] mb-3">Actual ARR (solid) vs 5% above-plan stretch target (dashed). Reference line at $1M ARR milestone.</p>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={ARR_TREND} margin={{ top: 10, right: 24, left: 8, bottom: 0 }}>
                        <defs>
                          <linearGradient id="arrGrad" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#8d4f27" stopOpacity={0.22} />
                            <stop offset="95%" stopColor="#8d4f27" stopOpacity={0.01} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#f0ebe3" vertical={false} />
                        <XAxis dataKey="month" tick={{ fill: "#7b6d5b", fontSize: 11 }} tickLine={false} axisLine={false} />
                        <YAxis tick={{ fill: "#7b6d5b", fontSize: 11 }} tickLine={false} axisLine={false} tickFormatter={v => `$${(v/1000).toFixed(0)}k`} width={52} />
                        <Tooltip
                          contentStyle={{ borderRadius: 10, border: "1px solid #e0cfc2", background: "#fffbf5", fontSize: 12 }}
                          formatter={(v: number, name: string) => [formatCurrency(v), name === "arr" ? "ARR" : "Stretch Target"]}
                        />
                        <ReferenceLine y={1000000} stroke="#2563eb" strokeDasharray="6 4" strokeWidth={1.2}
                          label={{ value: "$1M ARR milestone", position: "insideTopLeft", fontSize: 10, fill: "#2563eb" }} />
                        <Area type="monotone" dataKey="arr" name="arr" stroke="#8d4f27" strokeWidth={2.4} fill="url(#arrGrad)" dot={false} />
                        <Line type="monotone" dataKey="target" name="target" stroke="#d97706" strokeWidth={1.6} strokeDasharray="5 4" dot={false} />
                        <Legend wrapperStyle={{ fontSize: 11, paddingTop: 6 }} formatter={v => v === "arr" ? "Actual ARR" : "Stretch Target (+5%)"} />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>
            )}

            {activeTab === "retention" && (
              <div className="space-y-6">
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <h3 className="text-sm font-bold text-[#2a2017]">Logo Retention by Cohort — M0 to M12</h3>
                    <span className="text-xs text-[#9a8872]">% of customers still active each month after acquisition</span>
                  </div>
                  <p className="text-xs text-[#776b5a] mb-3">Reference lines at 90% (world-class) and 80% (healthy). Newer cohorts track above older ones.</p>
                  <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={RETENTION_COHORT} margin={{ top: 10, right: 24, left: 8, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#f0ebe3" vertical={false} />
                        <XAxis dataKey="month" tick={{ fill: "#7b6d5b", fontSize: 11 }} tickLine={false} axisLine={false} />
                        <YAxis domain={[65, 102]} tick={{ fill: "#7b6d5b", fontSize: 11 }} tickLine={false} axisLine={false}
                          tickFormatter={v => `${v}%`} width={40} />
                        <Tooltip
                          contentStyle={{ borderRadius: 10, border: "1px solid #e0cfc2", background: "#fffbf5", fontSize: 12 }}
                          formatter={(v: number, name: string) => [`${v}%`, name]}
                        />
                        <Legend wrapperStyle={{ fontSize: 11, paddingTop: 8 }} />
                        <ReferenceLine y={90} stroke="#059669" strokeDasharray="5 4" strokeWidth={1}
                          label={{ value: "World-class 90%", position: "insideTopRight", fontSize: 10, fill: "#059669" }} />
                        <ReferenceLine y={80} stroke="#d97706" strokeDasharray="5 4" strokeWidth={1}
                          label={{ value: "Healthy 80%", position: "insideTopRight", fontSize: 10, fill: "#d97706" }} />
                        {(["Jan 25", "Apr 25", "Jul 25", "Oct 25", "Jan 26"] as const).map((cohort, i) => (
                          <Line key={cohort} type="monotone" dataKey={cohort} stroke={COHORT_COLORS[i]}
                            strokeWidth={2} dot={{ r: 2.5, fill: COHORT_COLORS[i] }} connectNulls={false} />
                        ))}
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                  {[
                    { label: "M12 Retention (Jan 25)", value: "73%", color: "text-emerald-700", sub: "Improving trend" },
                    { label: "M12 Retention (Apr 25)", value: "77%", color: "text-emerald-700", sub: "+4pp cohort-over-cohort" },
                    { label: "Best M2 Retention", value: "99% (Jan 26)", color: "text-blue-700", sub: "Onboarding improving" },
                    { label: "Avg Logo Churn/mo", value: "2.1%", color: "text-amber-700", sub: "Industry avg 3-5%" },
                  ].map(m => (
                    <div key={m.label} className="rounded-xl bg-[#f9f6f1] border border-[#ede8e0] p-4">
                      <p className="text-xs text-[#776b5a]">{m.label}</p>
                      <p className={`text-xl font-bold mt-1 ${m.color}`}>{m.value}</p>
                      <p className="text-xs text-[#9a8872] mt-0.5">{m.sub}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeTab === "unit_econ" && (
              <div className="space-y-8">
                {/* LTV vs CAC grouped bars */}
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <h3 className="text-sm font-bold text-[#2a2017]">LTV vs CAC by Cohort — 9 Quarters</h3>
                    <span className="text-xs text-emerald-600 font-semibold">LTV/CAC 15.3x · World-class (&gt;3x)</span>
                  </div>
                  <p className="text-xs text-[#776b5a] mb-3">LTV (brown) vs CAC (tan) per quarterly cohort. Reference at 3x LTV/CAC threshold.</p>
                  <div className="h-72">
                    <ResponsiveContainer width="100%" height="100%">
                      <ComposedChart data={LTV_CAC} margin={{ top: 10, right: 24, left: 8, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#f0ebe3" vertical={false} />
                        <XAxis dataKey="cohort" tick={{ fill: "#7b6d5b", fontSize: 11 }} tickLine={false} axisLine={false} />
                        <YAxis yAxisId="left" tick={{ fill: "#7b6d5b", fontSize: 11 }} tickLine={false} axisLine={false}
                          tickFormatter={v => `$${(v/1000).toFixed(0)}k`} width={48} />
                        <YAxis yAxisId="right" orientation="right" domain={[0, 20]} tick={{ fill: "#7b6d5b", fontSize: 11 }}
                          tickLine={false} axisLine={false} tickFormatter={v => `${v}x`} width={36} />
                        <Tooltip
                          contentStyle={{ borderRadius: 10, border: "1px solid #e0cfc2", background: "#fffbf5", fontSize: 12 }}
                          formatter={(v: number, name: string) => {
                            if (name === "ratio") return [`${v}x`, "LTV/CAC Ratio"];
                            if (name === "payback") return [`${v} mo`, "CAC Payback"];
                            return [formatCurrency(v), name === "ltv" ? "LTV" : "CAC"];
                          }}
                        />
                        <Legend wrapperStyle={{ fontSize: 11, paddingTop: 8 }}
                          formatter={(v: string) => ({ ltv:"LTV", cac:"CAC", ratio:"LTV/CAC Ratio", payback:"Payback (mo)" } as Record<string,string>)[v] ?? v} />
                        <Bar yAxisId="left" dataKey="ltv" name="ltv" fill="#8d4f27" radius={[3,3,0,0]} />
                        <Bar yAxisId="left" dataKey="cac" name="cac" fill="#d4b896" radius={[3,3,0,0]} />
                        <Line yAxisId="right" type="monotone" dataKey="ratio" name="ratio" stroke="#2563eb" strokeWidth={2.2} dot={{ r: 3 }} />
                        <ReferenceLine yAxisId="right" y={3} stroke="#dc2626" strokeDasharray="5 4" strokeWidth={1.2}
                          label={{ value: "Min 3x threshold", position: "insideTopLeft", fontSize: 10, fill: "#dc2626" }} />
                      </ComposedChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Quick Ratio + NRR dual-axis */}
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <h3 className="text-sm font-bold text-[#2a2017]">Quick Ratio & NRR Trend — 12 Months</h3>
                    <span className="text-xs text-[#9a8872]">Quick Ratio left axis · NRR % right axis</span>
                  </div>
                  <p className="text-xs text-[#776b5a] mb-3">Quick Ratio target &gt;4 (dashed green). NRR benchmark &gt;110% (dashed blue).</p>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <ComposedChart data={QUICK_RATIO_DATA} margin={{ top: 10, right: 24, left: 8, bottom: 0 }}>
                        <defs>
                          <linearGradient id="qrGrad" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#059669" stopOpacity={0.2} />
                            <stop offset="95%" stopColor="#059669" stopOpacity={0.01} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#f0ebe3" vertical={false} />
                        <XAxis dataKey="month" tick={{ fill: "#7b6d5b", fontSize: 11 }} tickLine={false} axisLine={false} />
                        <YAxis yAxisId="left" domain={[1, 7]} tick={{ fill: "#7b6d5b", fontSize: 11 }} tickLine={false}
                          axisLine={false} tickFormatter={v => `${v}x`} width={36} />
                        <YAxis yAxisId="right" orientation="right" domain={[98, 126]} tick={{ fill: "#7b6d5b", fontSize: 11 }}
                          tickLine={false} axisLine={false} tickFormatter={v => `${v}%`} width={40} />
                        <Tooltip
                          contentStyle={{ borderRadius: 10, border: "1px solid #e0cfc2", background: "#fffbf5", fontSize: 12 }}
                          formatter={(v: number, name: string) => name === "ratio" ? [`${v}x`, "Quick Ratio"] : [`${v}%`, "NRR"]}
                        />
                        <Legend wrapperStyle={{ fontSize: 11, paddingTop: 8 }}
                          formatter={v => v === "ratio" ? "Quick Ratio" : "Net Revenue Retention"} />
                        <ReferenceLine yAxisId="left" y={4} stroke="#059669" strokeDasharray="5 4" strokeWidth={1.2}
                          label={{ value: "Target 4x", position: "insideTopRight", fontSize: 10, fill: "#059669" }} />
                        <ReferenceLine yAxisId="right" y={110} stroke="#2563eb" strokeDasharray="5 4" strokeWidth={1.2}
                          label={{ value: "Benchmark 110%", position: "insideBottomRight", fontSize: 10, fill: "#2563eb" }} />
                        <Area yAxisId="left" type="monotone" dataKey="ratio" name="ratio"
                          stroke="#059669" strokeWidth={2.4} fill="url(#qrGrad)" dot={{ r: 3, fill: "#059669" }} />
                        <Line yAxisId="right" type="monotone" dataKey="nrr" name="nrr"
                          stroke="#2563eb" strokeWidth={2} dot={{ r: 2.5, fill: "#2563eb" }} />
                      </ComposedChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                  {[
                    { label: "Current LTV", value: formatCurrency(latestLTV), sub: "Per customer lifetime" },
                    { label: "Blended CAC", value: formatCurrency(latestCAC), sub: "Sales + marketing cost" },
                    { label: "LTV / CAC", value: `${ltvCacRatio.toFixed(1)}x`, sub: ltvCacRatio >= 10 ? "Exceptional (>10x)" : "Healthy (>3x)" },
                    { label: "CAC Payback", value: `${Math.round(paybackMonths)} months`, sub: "Time to recover CAC" },
                  ].map(m => (
                    <div key={m.label} className="rounded-xl bg-[#f9f6f1] border border-[#ede8e0] p-4">
                      <p className="text-xs text-[#776b5a]">{m.label}</p>
                      <p className="text-xl font-bold text-[#2a2017] mt-1">{m.value}</p>
                      <p className="text-xs text-[#9a8872]">{m.sub}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
