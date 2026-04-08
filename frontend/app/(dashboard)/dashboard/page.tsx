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
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

const burnTrendData = [
  { month: "Jan", burn: 1620000, revenue: 910000 },
  { month: "Feb", burn: 1580000, revenue: 960000 },
  { month: "Mar", burn: 1510000, revenue: 1040000 },
  { month: "Apr", burn: 1490000, revenue: 1120000 },
  { month: "May", burn: 1450000, revenue: 1240000 },
  { month: "Jun", burn: 1410000, revenue: 1300000 },
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
    const runwayMonths = (18_900_000 / latest.burn).toFixed(1);
    const burnMultiple = (latest.burn / latest.revenue).toFixed(2);

    return [
      {
        label: "Net Burn",
        value: formatCurrencyShort(latest.burn),
        trend: "-4.1% vs last month",
        positive: true,
        icon: Building2,
      },
      {
        label: "Burn Multiple",
        value: `${burnMultiple}x`,
        trend: "Target: 1.50x",
        positive: Number(burnMultiple) <= 1.7,
        icon: BrainCircuit,
      },
      {
        label: "Runway",
        value: `${runwayMonths} months`,
        trend: "Threshold alert at 12 months",
        positive: Number(runwayMonths) > 12,
        icon: ShieldCheck,
      },
      {
        label: "Team Cost Ratio",
        value: "44%",
        trend: "+1.3% QoQ",
        positive: false,
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
              <h2 className="text-lg font-semibold text-[#2a2118]">Burn vs Revenue Momentum</h2>
              <p className="text-xs text-[#7e715f]">Last 6 months, normalized from unified ledger.</p>
            </div>
            <Link
              href="/runway"
              className="inline-flex items-center gap-1 text-sm font-medium text-[#7d4f13] hover:text-[#603a08]"
            >
              Explore runway
              <ChevronRight className="h-4 w-4" />
            </Link>
          </div>
          <div className="h-[280px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={burnTrendData} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="burnFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.35} />
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0.02} />
                  </linearGradient>
                  <linearGradient id="revenueFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.28} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0.02} />
                  </linearGradient>
                  <filter id="shadowChart">
                    <feDropShadow dx="0" dy="2" stdDeviation="2" floodOpacity="0.08" />
                  </filter>
                </defs>
                <XAxis 
                  axisLine={{ stroke: "#e8dccf", strokeWidth: 1 }} 
                  tickLine={false} 
                  dataKey="month" 
                  tick={{ fill: "#7f6f5e", fontSize: 12, fontWeight: 500 }} 
                />
                <YAxis
                  axisLine={{ stroke: "#e8dccf", strokeWidth: 1 }}
                  tickLine={false}
                  tickFormatter={(v) => `$${Math.round(v / 1000)}k`}
                  tick={{ fill: "#7f6f5e", fontSize: 12 }}
                />
                <Tooltip
                  contentStyle={{
                    borderRadius: 12,
                    border: "1px solid #e0cfc2",
                    background: "#fffbf5",
                    boxShadow: "0 4px 12px rgba(63, 45, 24, 0.15)",
                    color: "#2a2118",
                  }}
                  formatter={(value: number) => [formatCurrencyShort(value)]}
                  labelFormatter={(label) => `${label} 2024`}
                />
                <Area 
                  type="monotone" 
                  dataKey="burn" 
                  stroke="#dc2626" 
                  strokeWidth={2.4} 
                  fill="url(#burnFill)"
                  filter="url(#shadowChart)"
                />
                <Area 
                  type="monotone" 
                  dataKey="revenue" 
                  stroke="#059669" 
                  strokeWidth={2.4} 
                  fill="url(#revenueFill)"
                  filter="url(#shadowChart)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-4 flex items-center justify-between gap-6 pt-4 border-t border-[#ede8df]">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <div className="h-2.5 w-6 rounded-full bg-red-500" />
                <span className="text-xs font-medium text-[#7a6d5d]">Monthly Burn</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="h-2.5 w-6 rounded-full bg-emerald-500" />
                <span className="text-xs font-medium text-[#7a6d5d]">Revenue</span>
              </div>
            </div>
            <span className="text-xs text-[#6f6251]">Sep forecast: burn declining 3.2%</span>
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
