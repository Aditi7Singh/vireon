"use client";

import Link from "next/link";
import { useMemo } from "react";
import {
  ArrowUpRight,
  BrainCircuit,
  Building2,
  CalendarClock,
  ChevronRight,
  CircleAlert,
  Layers3,
  Receipt,
  ShieldCheck,
  Sparkles,
  Users,
  Wallet,
} from "lucide-react";
import { Area, AreaChart, CartesianGrid, Legend, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

const burnTrendData = [
  { month: "May 25", burn: 1820000, revenue: 456000, netBurn: 1364000 },
  { month: "Jun 25", burn: 1780000, revenue: 492000, netBurn: 1288000 },
  { month: "Jul 25", burn: 1740000, revenue: 546000, netBurn: 1194000 },
  { month: "Aug 25", burn: 1710000, revenue: 602000, netBurn: 1108000 },
  { month: "Sep 25", burn: 1680000, revenue: 654000, netBurn: 1026000 },
  { month: "Oct 25", burn: 1650000, revenue: 720000, netBurn: 930000 },
  { month: "Nov 25", burn: 1630000, revenue: 810000, netBurn: 820000 },
  { month: "Dec 25", burn: 1610000, revenue: 900000, netBurn: 710000 },
  { month: "Jan 26", burn: 1590000, revenue: 984000, netBurn: 606000 },
  { month: "Feb 26", burn: 1560000, revenue: 1068000, netBurn: 492000 },
  { month: "Mar 26", burn: 1530000, revenue: 1158000, netBurn: 372000 },
  { month: "Apr 26", burn: 1490000, revenue: 1298000, netBurn: 192000 },
];

const priorityActions = [
  {
    title: "Optimize cloud spend in ML workloads",
    impact: "Estimated monthly savings: $38,400",
    owner: "CTO",
    href: "/expenses",
  },
  {
    title: "Accelerate collections for enterprise invoices",
    impact: "Improve runway by 1.2 months",
    owner: "Finance",
    href: "/revenue",
  },
  {
    title: "Recalibrate growth hiring for Q3",
    impact: "Reduce burn multiple from 1.9 to 1.6",
    owner: "CEO",
    href: "/runway",
  },
];

const moduleCards = [
  {
    title: "Runway Intelligence",
    description: "Live runway projection with growth and hiring simulation overlays.",
    icon: CalendarClock,
    href: "/runway",
  },
  {
    title: "Expense Forensics",
    description: "Vendor-level leakage discovery and spend concentration insights.",
    icon: Receipt,
    href: "/expenses",
  },
  {
    title: "Revenue Signal",
    description: "MRR quality, cohort retention, and delayed collection watch.",
    icon: Wallet,
    href: "/revenue",
  },
  {
    title: "Scenario Engine",
    description: "Compare base, conservative, and aggressive plans instantly.",
    icon: Layers3,
    href: "/scenarios",
  },
  {
    title: "Feature Hub",
    description: "Single destination for every implemented module and control.",
    icon: Sparkles,
    href: "/features",
  },
];

function formatCurrencyShort(value: number): string {
  if (value >= 1_000_000) return `₹${(value / 1_000_000).toFixed(2)}M`;
  if (value >= 1_000) return `₹${(value / 1_000).toFixed(1)}K`;
  return `₹${value.toFixed(0)}`;
}

export default function DashboardHomePage() {
  const metrics = useMemo(() => {
    const latest = burnTrendData[burnTrendData.length - 1];
    const prev = burnTrendData[burnTrendData.length - 2];
    const runwayMonths = (18_900_000 / latest.netBurn).toFixed(1);
    const burnMultiple = (latest.burn / latest.revenue).toFixed(2);
    const revGrowth = (((latest.revenue - prev.revenue) / prev.revenue) * 100).toFixed(1);

    return [
      {
        label: "Net Burn / Month",
        value: formatCurrencyShort(latest.netBurn),
        trend: `-${(((prev.netBurn - latest.netBurn) / prev.netBurn) * 100).toFixed(1)}% vs prior month`,
        positive: true,
        icon: Building2,
      },
      {
        label: "Burn Multiple",
        value: `${burnMultiple}x`,
        trend: burnMultiple <= "1.50" ? "✓ At target ≤1.5x" : "Target: ≤1.5x",
        positive: Number(burnMultiple) <= 1.5,
        icon: BrainCircuit,
      },
      {
        label: "Runway",
        value: `${runwayMonths} months`,
        trend: Number(runwayMonths) > 18 ? "✓ Healthy (>18 mo)" : "Alert at 12 months",
        positive: Number(runwayMonths) > 18,
        icon: ShieldCheck,
      },
      {
        label: "Revenue Growth",
        value: `+${revGrowth}% MoM`,
        trend: `${formatCurrencyShort(latest.revenue)} ARR run-rate`,
        positive: true,
        icon: Users,
      },
    ];
  }, []);

  return (
    <main className="min-h-screen w-full bg-[#f6f3ee] pb-14 text-[#1d1b17]">
      <section className="mx-auto w-full max-w-7xl px-4 pt-8 sm:px-6 lg:px-8">
        <div className="relative overflow-hidden rounded-[2rem] border border-[#d7cdbc] bg-gradient-to-br from-[#fff8eb] via-[#f8f0df] to-[#f1e6d3] p-6 shadow-[0_20px_80px_rgba(70,55,20,0.12)] sm:p-8">
          <div className="pointer-events-none absolute -right-12 -top-10 h-40 w-40 rounded-full bg-[#f5d07b]/40 blur-3xl" />
          <div className="pointer-events-none absolute -bottom-16 left-8 h-40 w-40 rounded-full bg-[#dfb77f]/30 blur-3xl" />

          <div className="relative flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-3xl">
              <p className="inline-flex items-center gap-2 rounded-full border border-[#d2b687] bg-[#fff4de] px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-[#8a5d12]">
                <Sparkles className="h-3.5 w-3.5" />
                Executive Control Center
              </p>
              <h1 className="mt-4 text-3xl font-semibold leading-tight text-[#2b1f12] sm:text-4xl">
                Your financial story, rendered as decisions not spreadsheets.
              </h1>
              <p className="mt-3 max-w-2xl text-sm text-[#5f5243] sm:text-base">
                Unified ERP, payroll, cloud, and revenue telemetry with AI-generated priorities for CEO, CTO, and Finance leadership.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <Link
                href="/dashboard/ceo"
                className="inline-flex items-center gap-2 rounded-xl bg-[#26201a] px-4 py-2.5 text-sm font-medium text-[#fef8ec] transition hover:bg-[#17130f]"
              >
                CEO View
                <ChevronRight className="h-4 w-4" />
              </Link>
              <Link
                href="/dashboard/finance"
                className="inline-flex items-center gap-2 rounded-xl border border-[#bca887] bg-[#fff8ea] px-4 py-2.5 text-sm font-medium text-[#4a3720] transition hover:bg-[#f6ebd5]"
              >
                Finance View
                <ArrowUpRight className="h-4 w-4" />
              </Link>
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto mt-6 grid w-full max-w-7xl gap-4 px-4 sm:grid-cols-2 sm:px-6 lg:grid-cols-4 lg:px-8">
        {metrics.map((metric) => {
          const Icon = metric.icon;
          return (
            <article
              key={metric.label}
              className="rounded-2xl border border-[#ddd3c5] bg-[#fffdf8] p-5 shadow-[0_14px_35px_rgba(60,45,25,0.06)]"
            >
              <div className="flex items-center justify-between">
                <p className="text-xs uppercase tracking-[0.12em] text-[#7b705f]">{metric.label}</p>
                <Icon className="h-4 w-4 text-[#8f6b34]" />
              </div>
              <p className="mt-2 text-2xl font-semibold text-[#2d241b]">{metric.value}</p>
              <p className={`mt-1 text-xs ${metric.positive ? "text-[#256443]" : "text-[#91572e]"}`}>
                {metric.trend}
              </p>
            </article>
          );
        })}
      </section>

      <section className="mx-auto mt-6 grid w-full max-w-7xl gap-4 px-4 sm:px-6 lg:grid-cols-3 lg:px-8">
        <article className="rounded-2xl border border-[#ddd2c1] bg-[#fffdf9] p-5 shadow-[0_14px_35px_rgba(60,45,25,0.06)] lg:col-span-2">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-[#2a2118]">Burn vs Revenue — 12-Month Trend</h2>
              <p className="text-xs text-[#7e715f]">May 2025 – Apr 2026 · Gross burn, recognized revenue, and net burn overlay.</p>
            </div>
            <Link
              href="/runway"
              className="inline-flex items-center gap-1 text-sm font-medium text-[#7d4f13] hover:text-[#603a08]"
            >
              Full runway model
              <ChevronRight className="h-4 w-4" />
            </Link>
          </div>
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={burnTrendData} margin={{ top: 8, right: 20, left: 8, bottom: 0 }}>
                <defs>
                  <linearGradient id="burnFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.18} />
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0.02} />
                  </linearGradient>
                  <linearGradient id="revenueFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.22} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0.02} />
                  </linearGradient>
                  <linearGradient id="netBurnFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.18} />
                    <stop offset="95%" stopColor="#f59e0b" stopOpacity={0.02} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0ebe3" vertical={false} />
                <XAxis
                  axisLine={false}
                  tickLine={false}
                  dataKey="month"
                  tick={{ fill: "#7f6f5e", fontSize: 11, fontWeight: 500 }}
                  interval={1}
                />
                <YAxis
                  axisLine={false}
                  tickLine={false}
                  tickFormatter={(v) => `$${Math.round(v / 1000)}k`}
                  tick={{ fill: "#7f6f5e", fontSize: 11 }}
                  width={52}
                />
                <Tooltip
                  contentStyle={{
                    borderRadius: 10,
                    border: "1px solid #e0cfc2",
                    background: "#fffbf5",
                    boxShadow: "0 4px 16px rgba(63,45,24,0.12)",
                    fontSize: 12,
                  }}
                  formatter={(value: number, name: string) => {
                    const labels: Record<string, string> = { burn: "Gross Burn", revenue: "Revenue", netBurn: "Net Burn" };
                    return [formatCurrencyShort(value), labels[name] ?? name];
                  }}
                />
                <Legend
                  wrapperStyle={{ fontSize: 11, paddingTop: 8 }}
                  formatter={(value) => {
                    const m: Record<string, string> = { burn: "Gross Burn", revenue: "Revenue", netBurn: "Net Burn" };
                    return m[value] ?? value;
                  }}
                />
                <ReferenceLine
                  y={burnTrendData[burnTrendData.length - 1].revenue}
                  stroke="#059669"
                  strokeDasharray="5 4"
                  strokeWidth={1.2}
                  label={{ value: "Break-even zone", position: "insideTopRight", fontSize: 10, fill: "#059669" }}
                />
                <Area type="monotone" dataKey="burn" stroke="#dc2626" strokeWidth={2} fill="url(#burnFill)" dot={false} />
                <Area type="monotone" dataKey="revenue" stroke="#059669" strokeWidth={2.4} fill="url(#revenueFill)" dot={false} />
                <Area type="monotone" dataKey="netBurn" stroke="#d97706" strokeWidth={1.8} fill="url(#netBurnFill)" strokeDasharray="4 3" dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-3 flex items-center justify-between pt-3 border-t border-[#ede8df]">
            <div className="flex items-center gap-5">
              {[
                { color: "bg-red-500", label: "Gross Burn" },
                { color: "bg-emerald-500", label: "Revenue" },
                { color: "bg-amber-500", label: "Net Burn" },
              ].map(({ color, label }) => (
                <div key={label} className="flex items-center gap-1.5">
                  <div className={`h-2 w-5 rounded-full ${color}`} />
                  <span className="text-xs text-[#7a6d5d]">{label}</span>
                </div>
              ))}
            </div>
            <span className="text-xs text-emerald-700 font-semibold">▲ Revenue crossing burn in Q2 2026</span>
          </div>
        </article>

        <article className="rounded-2xl border border-[#dccfbd] bg-[#fffdf8] p-5 shadow-[0_14px_35px_rgba(60,45,25,0.06)]">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-[#2a2118]">Priority Actions</h2>
            <CircleAlert className="h-4 w-4 text-[#9e6420]" />
          </div>
          <div className="mt-4 space-y-3">
            {priorityActions.map((item) => (
              <Link
                key={item.title}
                href={item.href}
                className="block rounded-xl border border-[#e4d9c9] bg-[#fffcf5] p-3 transition hover:border-[#cbb79a] hover:bg-[#fff8e9]"
              >
                <p className="text-sm font-medium text-[#34281c]">{item.title}</p>
                <p className="mt-1 text-xs text-[#6f624f]">{item.impact}</p>
                <p className="mt-2 inline-flex items-center gap-1 text-xs font-medium text-[#885114]">
                  Owner: {item.owner}
                  <ChevronRight className="h-3.5 w-3.5" />
                </p>
              </Link>
            ))}
          </div>
        </article>
      </section>

      <section className="mx-auto mt-6 grid w-full max-w-7xl gap-4 px-4 sm:grid-cols-2 sm:px-6 lg:grid-cols-4 lg:px-8">
        {moduleCards.map((module) => {
          const Icon = module.icon;
          return (
            <Link
              key={module.title}
              href={module.href}
              className="group rounded-2xl border border-[#ded3c5] bg-[#fffdf8] p-5 shadow-[0_14px_35px_rgba(60,45,25,0.06)] transition hover:-translate-y-0.5 hover:border-[#cbb191] hover:shadow-[0_20px_45px_rgba(60,45,25,0.12)]"
            >
              <Icon className="h-5 w-5 text-[#8d5f21]" />
              <h3 className="mt-3 text-sm font-semibold text-[#2f251a]">{module.title}</h3>
              <p className="mt-1 text-xs leading-relaxed text-[#6e6251]">{module.description}</p>
              <p className="mt-3 inline-flex items-center gap-1 text-xs font-medium text-[#8d5f21]">
                Open module
                <ChevronRight className="h-3.5 w-3.5 transition group-hover:translate-x-0.5" />
              </p>
            </Link>
          );
        })}
      </section>
    </main>
  );
}
