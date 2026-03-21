"use client";

import TopBar from "@/components/TopBar";
import { useRunway, useScorecard } from "@/hooks/useFinancialData";
import { useAppStore } from "@/lib/store";
import { cn, formatCurrency } from "@/lib/utils";
import { AlertTriangle, CalendarClock, ShieldCheck, Sparkles, TrendingDown } from "lucide-react";
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

const projectionData = [
   { month: "Mar", cash: 250000, burn: 45000 },
   { month: "Apr", cash: 205000, burn: 46000 },
   { month: "May", cash: 159000, burn: 44000 },
   { month: "Jun", cash: 115000, burn: 45000 },
   { month: "Jul", cash: 70000, burn: 47000 },
   { month: "Aug", cash: 23000, burn: 45000 },
];

export default function RunwayPage() {
  const { runway } = useRunway();
  const { scorecard } = useScorecard();
  const { openChat } = useAppStore();

  const isLowRunway = runway.runway_months < 6;
  const isHealthyRunway = runway.runway_months >= 12;

  const status = isLowRunway
    ? { label: "Critical", style: "text-[#9b3a1f] bg-[#f8d8cc] border-[#e9b3a4]", icon: AlertTriangle }
    : isHealthyRunway
      ? { label: "Healthy", style: "text-[#1f6b4b] bg-[#dcf2e7] border-[#b3dfcc]", icon: ShieldCheck }
      : { label: "Watch", style: "text-[#7a4f14] bg-[#f9ecd2] border-[#e8d1a8]", icon: CalendarClock };
  const StatusIcon = status.icon;

  return (
    <div className="min-h-screen bg-[#f6f3ee] pb-14 text-[#1d1b17]">
      <TopBar title="Runway & Survival" />

      <div className="mx-auto max-w-7xl space-y-6 px-4 pt-6 sm:px-6 lg:px-8">
        <section className="rounded-3xl border border-[#d9cdbc] bg-[linear-gradient(145deg,#fff8eb_0%,#f4ebdc_100%)] p-6 shadow-[0_18px_48px_rgba(63,45,24,0.1)] sm:p-8">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className={cn("inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-semibold", status.style)}>
                <StatusIcon className="h-3.5 w-3.5" />
                {status.label} runway profile
              </p>
              <h1 className="mt-3 text-3xl font-semibold text-[#2c2013]">{runway.runway_months} months of runway</h1>
              <p className="mt-2 text-sm text-[#5f5344]">
                Current cash {formatCurrency(scorecard.total_cash)} with monthly burn {formatCurrency(scorecard.monthly_net_burn)}.
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

        <section className="grid gap-4 lg:grid-cols-3">
          <article className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] p-5">
            <p className="text-xs uppercase tracking-[0.12em] text-[#776b5a]">Terminal Date</p>
            <p className="mt-2 text-2xl font-semibold text-[#2a2017]">{runway.zero_date}</p>
          </article>
          <article className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] p-5">
            <p className="text-xs uppercase tracking-[0.12em] text-[#776b5a]">Monthly Net Burn</p>
            <p className="mt-2 text-2xl font-semibold text-[#2a2017]">{formatCurrency(scorecard.monthly_net_burn)}</p>
          </article>
          <article className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] p-5">
            <p className="text-xs uppercase tracking-[0.12em] text-[#776b5a]">Safety Buffer</p>
            <p className="mt-2 text-2xl font-semibold text-[#2a2017]">92%</p>
          </article>
        </section>

        <section className="rounded-2xl border border-[#ded2c4] bg-[#fffdf8] p-5 sm:p-6">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-[#2a2017]">Liquidity Trajectory</h2>
            <span className="inline-flex items-center gap-1 text-xs text-[#786857]"><TrendingDown className="h-3.5 w-3.5" />6-month projection</span>
          </div>
          <div className="h-[280px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={projectionData}>
                <defs>
                  <linearGradient id="cashFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ba7a1a" stopOpacity={0.35} />
                    <stop offset="95%" stopColor="#ba7a1a" stopOpacity={0.05} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="month" tickLine={false} axisLine={false} tick={{ fill: "#7b6d5b", fontSize: 12 }} />
                <YAxis tickLine={false} axisLine={false} tick={{ fill: "#7b6d5b", fontSize: 12 }} tickFormatter={(v) => `$${v / 1000}k`} />
                <Tooltip contentStyle={{ border: "1px solid #dbcdb9", borderRadius: 12, background: "#fff8ea" }} />
                <Area type="monotone" dataKey="cash" stroke="#a96a14" strokeWidth={2.2} fill="url(#cashFill)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </section>
      </div>
    </div>
  );
}

