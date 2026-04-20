"use client";

import TopBar from "@/components/TopBar";
import { useRunway, useScorecard } from "@/hooks/useFinancialData";
import { useAppStore } from "@/lib/store";
import { cn, formatCurrency } from "@/lib/utils";
import { AlertTriangle, CalendarClock, ShieldCheck, Sparkles, TrendingDown, DollarSign, Users, TrendingUp } from "lucide-react";
import { useState } from "react";
import {
  Area, Bar, CartesianGrid, ComposedChart, Legend, Line,
  ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";

const PROJECTION = [
  { month: "May 25", cash: 4200000, burn: 620000, revenue: 456000, netBurn: 164000 },
  { month: "Jun 25", cash: 4036000, burn: 608000, revenue: 528000, netBurn:  80000 },
  { month: "Jul 25", cash: 3956000, burn: 595000, revenue: 621000, netBurn: -26000 },
  { month: "Aug 25", cash: 3982000, burn: 582000, revenue: 732000, netBurn: -150000 },
  { month: "Sep 25", cash: 4132000, burn: 568000, revenue: 863000, netBurn: -295000 },
  { month: "Oct 25", cash: 4427000, burn: 556000, revenue: 1002000, netBurn: -446000 },
  { month: "Nov 25", cash: 4873000, burn: 544000, revenue: 1159000, netBurn: -615000 },
  { month: "Dec 25", cash: 5488000, burn: 531000, revenue: 1321000, netBurn: -790000 },
  { month: "Jan 26", cash: 6278000, burn: 520000, revenue: 1390000, netBurn: -870000 },
  { month: "Feb 26", cash: 7148000, burn: 510000, revenue: 1495000, netBurn: -985000 },
  { month: "Mar 26", cash: 8133000, burn: 499000, revenue: 1596000, netBurn: -1097000 },
  { month: "Apr 26", cash: 9230000, burn: 490000, revenue: 1677000, netBurn: -1187000 },
];

const LEGEND_LABELS: Record<string, string> = {
  cash: "Cash Position", burn: "Monthly Burn", revenue: "Monthly Revenue", netBurn: "Net Burn",
};

export default function RunwayPage() {
  const { runway } = useRunway();
  const { scorecard } = useScorecard();
  const { openChat } = useAppStore();
  const [scenario, setScenario] = useState({ burnReduction: 0, hiringImpact: 0, revenueGrowth: 0 });

  const baseBurn = scorecard.monthly_net_burn || 490000;
  const adjustedBurn = baseBurn * (1 - scenario.burnReduction / 100) * (1 + scenario.hiringImpact / 100);
  const adjustedRunway = scorecard.total_cash / adjustedBurn;
  const runwayImprovement = adjustedRunway - runway.runway_months;
  const isLowRunway = runway.runway_months < 6;
  const isHealthyRunway = runway.runway_months >= 12;

  const status = isLowRunway
    ? { label: "Critical", style: "text-[#9b3a1f] bg-[#f8d8cc] border-[#e9b3a4]", icon: AlertTriangle }
    : isHealthyRunway
      ? { label: "Healthy", style: "text-[#1f6b4b] bg-[#dcf2e7] border-[#b3dfcc]", icon: ShieldCheck }
      : { label: "Watch",   style: "text-[#7a4f14] bg-[#f9ecd2] border-[#e8d1a8]", icon: CalendarClock };
  const StatusIcon = status.icon;

  return (
    <div className="min-h-screen bg-[#f6f3ee] pb-14 text-[#1d1b17]">
      <TopBar title="Runway & Survival" />

      <div className="mx-auto max-w-7xl space-y-6 px-4 pt-6 sm:px-6 lg:px-8">

        {/* Hero */}
        <section className="rounded-3xl border border-[#d9cdbc] bg-[linear-gradient(145deg,#fff8eb_0%,#f4ebdc_100%)] p-6 shadow-[0_18px_48px_rgba(63,45,24,0.1)] sm:p-8">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className={cn("inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-semibold", status.style)}>
                <StatusIcon className="h-3.5 w-3.5" />
                {status.label} runway profile
              </p>
              <h1 className="mt-3 text-3xl font-semibold text-[#2c2013]">{runway.runway_months} months of runway</h1>
              <p className="mt-2 text-sm text-[#5f5344]">
                Current cash {formatCurrency(scorecard.total_cash)} · Monthly burn {formatCurrency(scorecard.monthly_net_burn)}
              </p>
            </div>
            <button
              onClick={() => openChat("Runway Strategic Analysis")}
              className="inline-flex items-center gap-2 rounded-xl bg-[#231c15] px-4 py-2.5 text-sm font-medium text-[#fff7eb] hover:bg-[#17120d]"
            >
              <Sparkles className="h-4 w-4" />
              Forecast analysis
            </button>
          </div>
        </section>

        {/* KPI Cards */}
        <section className="grid gap-4 lg:grid-cols-3">
          <article className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] p-5">
            <p className="text-xs uppercase tracking-[0.12em] text-[#776b5a]">Terminal Date</p>
            <p className="mt-2 text-2xl font-semibold text-[#2a2017]">{runway.zero_date}</p>
            <p className="mt-0.5 text-xs text-[#9a8878]">Without further fundraising</p>
          </article>
          <article className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] p-5">
            <p className="text-xs uppercase tracking-[0.12em] text-[#776b5a]">Monthly Net Burn</p>
            <p className="mt-2 text-2xl font-semibold text-[#2a2017]">{formatCurrency(scorecard.monthly_net_burn)}</p>
            <p className="mt-0.5 text-xs text-emerald-600">Declining — revenue outpacing spend</p>
          </article>
          <article className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] p-5">
            <p className="text-xs uppercase tracking-[0.12em] text-[#776b5a]">Break-even Month</p>
            <p className="mt-2 text-2xl font-semibold text-[#2a2017]">Jul 2025</p>
            <p className="mt-0.5 text-xs text-emerald-600">Revenue exceeded gross burn</p>
          </article>
        </section>

        {/* Liquidity Trajectory — Dual Axis ComposedChart */}
        <section className="rounded-2xl border border-[#ded2c4] bg-[#fffdf8] p-5 sm:p-6">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-[#2a2017]">Cash Position vs. Burn Rate — 12 Months</h2>
              <p className="text-xs text-[#7b6d5b]">Left axis: cash balance · Right axis: monthly burn & revenue flows</p>
            </div>
            <span className="inline-flex items-center gap-1 text-xs text-[#786857]">
              <TrendingDown className="h-3.5 w-3.5 text-emerald-600" />
              Net burn flipped positive in Jul 25
            </span>
          </div>
          <div className="h-[320px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={PROJECTION} margin={{ top: 10, right: 70, left: 10, bottom: 0 }}>
                <defs>
                  <linearGradient id="cashGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#8d4f27" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#8d4f27" stopOpacity={0.02} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0ebe3" vertical={false} />
                <XAxis dataKey="month" tickLine={false} axisLine={false} tick={{ fill: "#7b6d5b", fontSize: 11 }} />
                <YAxis
                  yAxisId="cash"
                  tickLine={false} axisLine={false}
                  tick={{ fill: "#7b6d5b", fontSize: 11 }}
                  tickFormatter={(v) => `$${(v / 1000000).toFixed(1)}M`}
                />
                <YAxis
                  yAxisId="flows"
                  orientation="right"
                  tickLine={false} axisLine={false}
                  tick={{ fill: "#7b6d5b", fontSize: 11 }}
                  tickFormatter={(v) => `$${v / 1000}k`}
                />
                <Tooltip
                  contentStyle={{ border: "1px solid #dbcdb9", borderRadius: 12, background: "#fff8ea", fontSize: 12 }}
                  formatter={(v: number, name: string) => [formatCurrency(Math.abs(v)), LEGEND_LABELS[name] ?? name]}
                />
                <Legend formatter={(v: string) => (LEGEND_LABELS as Record<string,string>)[v] ?? v} wrapperStyle={{ fontSize: 12, paddingTop: 8 }} />

                {/* Reference lines */}
                <ReferenceLine yAxisId="cash" y={2000000} stroke="#fb923c" strokeDasharray="4 3"
                  label={{ value: "$2M reserve floor", fill: "#fb923c", fontSize: 11 }} />
                <ReferenceLine yAxisId="flows" y={0} stroke="#10b981" strokeDasharray="4 3"
                  label={{ value: "Break-even", fill: "#10b981", fontSize: 11, position: "insideTopRight" }} />

                {/* Cash position area */}
                <Area yAxisId="cash" type="monotone" dataKey="cash" stroke="#8d4f27" strokeWidth={2.5} fill="url(#cashGrad)" />

                {/* Monthly burn bar */}
                <Bar yAxisId="flows" dataKey="burn" fill="#ef444455" radius={[2,2,0,0]} />

                {/* Revenue line */}
                <Line yAxisId="flows" type="monotone" dataKey="revenue" stroke="#10b981" strokeWidth={2} dot={{ r: 3, fill: "#10b981" }} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </section>

        {/* Scenario Planner */}
        <section className="rounded-2xl border border-[#ded2c4] bg-[#fffdf8] p-5 sm:p-6 space-y-6">
          <div>
            <h2 className="text-lg font-semibold text-[#2a2017] mb-1">Scenario Planner</h2>
            <p className="text-xs text-[#7b6d5b]">Model what-if scenarios to extend runway and reach cash-flow positive earlier</p>
          </div>

          <div className="grid md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-[#5f5344] flex items-center gap-2">
                <DollarSign className="h-4 w-4" />
                Reduce Spend
              </label>
              <input type="range" min="0" max="50" value={scenario.burnReduction}
                onChange={(e) => setScenario(prev => ({ ...prev, burnReduction: Number(e.target.value) }))}
                className="w-full h-2 bg-[#f0ebe3] rounded-lg appearance-none cursor-pointer"
              />
              <div className="flex justify-between text-xs text-[#7b6d5b]">
                <span>0%</span>
                <span className="font-bold text-[#2a2017]">{scenario.burnReduction}%</span>
                <span>50%</span>
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-[#5f5344] flex items-center gap-2">
                <Users className="h-4 w-4" />
                Add Headcount
              </label>
              <input type="range" min="0" max="50" value={scenario.hiringImpact}
                onChange={(e) => setScenario(prev => ({ ...prev, hiringImpact: Number(e.target.value) }))}
                className="w-full h-2 bg-[#f0ebe3] rounded-lg appearance-none cursor-pointer"
              />
              <div className="flex justify-between text-xs text-[#7b6d5b]">
                <span>None</span>
                <span className="font-bold text-[#2a2017]">+{scenario.hiringImpact}%</span>
                <span>50%</span>
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-[#5f5344] flex items-center gap-2">
                <TrendingUp className="h-4 w-4" />
                Revenue Growth
              </label>
              <input type="range" min="0" max="150" value={scenario.revenueGrowth}
                onChange={(e) => setScenario(prev => ({ ...prev, revenueGrowth: Number(e.target.value) }))}
                className="w-full h-2 bg-[#f0ebe3] rounded-lg appearance-none cursor-pointer"
              />
              <div className="flex justify-between text-xs text-[#7b6d5b]">
                <span>0%</span>
                <span className="font-bold text-[#2a2017]">+{scenario.revenueGrowth}%</span>
                <span>150%</span>
              </div>
            </div>
          </div>

          <div className={`pt-4 rounded-lg border ${runwayImprovement > 0 ? "border-green-200 bg-green-50" : "border-[#ede8df] bg-[#f9f7f3]"} p-4 space-y-2`}>
            <div className="flex items-center justify-between">
              <span className="text-sm text-[#6f6251]">Base Monthly Burn</span>
              <span className="font-bold text-[#2a2017]">{formatCurrency(baseBurn)}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-[#6f6251]">Scenario Monthly Burn</span>
              <span className="font-bold text-[#2a2017]">{formatCurrency(adjustedBurn)}</span>
            </div>
            <div className="flex items-center justify-between pt-2 border-t border-current/10">
              <span className="text-sm font-semibold text-[#2a2017]">New Runway</span>
              <span className={`text-2xl font-bold ${runwayImprovement > 0 ? "text-green-600" : runwayImprovement < 0 ? "text-red-600" : "text-[#2a2017]"}`}>
                {adjustedRunway.toFixed(1)} months
              </span>
            </div>
            {runwayImprovement !== 0 && (
              <div className="text-xs font-semibold pt-1">
                <span className={runwayImprovement > 0 ? "text-green-600" : "text-red-600"}>
                  {runwayImprovement > 0 ? "+" : ""}{runwayImprovement.toFixed(1)} months impact
                </span>
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
